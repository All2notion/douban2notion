import re
import json
import time
import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class DoubanScraper:
    BASE_URL = "https://movie.douban.com"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }

    def __init__(self, user_id: str, cookies: str = None, delay: float = 1.0):
        self.user_id = user_id
        self.cookies = self._parse_cookies(cookies) if cookies else {}
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def _parse_cookies(self, cookies_str: str) -> Dict[str, str]:
        cookie_dict = {}
        for item in cookies_str.split(";"):
            item = item.strip()
            if "=" in item:
                key, value = item.split("=", 1)
                cookie_dict[key.strip()] = value.strip()
        return cookie_dict

    def fetch_watched_movies(self, max_pages: int = 10) -> List[Dict]:
        all_movies = []
        logger.info(f"开始抓取用户 {self.user_id} 的观影记录，最多 {max_pages} 页")

        for page in range(1, max_pages + 1):
            try:
                movies = self._fetch_page(page)
                if not movies:
                    logger.warning(f"第 {page} 页没有获取到电影，可能Cookie已失效或页面结构变化")
                    break
                all_movies.extend(movies)
                logger.info(f"已抓取第 {page} 页，获取 {len(movies)} 部电影")
                time.sleep(self.delay)
            except Exception as e:
                logger.error(f"抓取第 {page} 页失败: {e}")
                continue

        logger.info(f"共获取 {len(all_movies)} 部电影")
        return all_movies

    def _fetch_page(self, page: int) -> List[Dict]:
        url = f"https://movie.douban.com/people/{self.user_id}/collect?start={(page - 1) * 30}&sort=date&rating=all&filter=all&mode=grid"
        logger.info(f"请求URL: {url}")

        response = self.session.get(url, cookies=self.cookies, timeout=30)
        logger.info(f"响应状态码: {response.status_code}")
        
        if response.encoding == "ISO-8859-1":
            response.encoding = response.apparent_encoding
            
        logger.info(f"响应编码: {response.encoding}")
        logger.info(f"响应内容长度: {len(response.text)} 字符")

        if response.status_code != 200:
            logger.error(f"请求失败，状态码: {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")

        movie_items = soup.select("div.item")
        logger.info(f"找到 {len(movie_items)} 个电影条目")

        if len(movie_items) == 0:
            logger.warning("未找到电影条目，可能原因：")
            logger.warning("1. Cookie已失效，返回的是登录页面")
            logger.warning("2. 豆瓣页面结构已变化")
            logger.warning(f"页面标题: {soup.title.string if soup.title else '无标题'}")
            logger.info(f"页面内容前500字符: {response.text[:500]}")

        movies = []

        for idx, item in enumerate(movie_items):
            logger.debug(f"正在解析第 {idx+1} 个电影条目...")
            movie = self._parse_movie_item(item)
            if movie:
                movies.append(movie)
                logger.debug(f"成功解析电影: {movie.get('name', '未知')}")

        return movies

    def _parse_movie_item(self, item) -> Optional[Dict]:
        try:
            item_html = str(item)
            logger.debug(f"条目HTML前1000字符: {item_html[:1000]}")
            
            title_elem = item.select_one("li.pic a") or item.select_one("a.nbg")
            if not title_elem:
                logger.warning("未找到标题链接元素")
                title_elem = item.select_one("a")
            
            if not title_elem:
                logger.warning("未找到任何链接元素")
                return None

            douban_url = title_elem.get("href", "")
            logger.debug(f"电影链接: {douban_url}")
            
            movie_id = self._extract_movie_id(douban_url)
            logger.debug(f"电影ID: {movie_id}")

            title_elem_for_name = title_elem
            name_elem = item.select_one("li.title a") or item.select_one("a.title")
            if not name_elem:
                name_elem = title_elem_for_name
                
            name = name_elem.get("title", "") or name_elem.get_text(strip=True)
            logger.debug(f"电影名称: {name}")

            rating_elem = item.select_one("span.rating_nums") or item.select_one("span[class*='rating']")
            rating = rating_elem.get_text(strip=True) if rating_elem else "N/A"
            logger.debug(f"我的评分: {rating}")

            date_elem = item.select_one("span.date")
            watched_date = date_elem.get_text(strip=True) if date_elem else ""
            logger.debug(f"观看日期: {watched_date}")

            movie_info = self.fetch_movie_detail(movie_id)

            return {
                "douban_id": movie_id,
                "douban_url": douban_url,
                "name": name,
                "rating": rating,
                "watched_date": watched_date,
                **movie_info,
            }
        except Exception as e:
            logger.error(f"解析电影条目失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def _extract_movie_id(self, url: str) -> str:
        match = re.search(r"subject/(\d+)", url)
        return match.group(1) if match else ""

    def fetch_movie_detail(self, movie_id: str) -> Dict:
        url = f"{self.BASE_URL}/subject/{movie_id}/"
        for attempt in range(3):
            try:
                response = self.session.get(url, cookies=self.cookies, timeout=30)
                response.raise_for_status()
                return self._parse_movie_page(response.text)
            except Exception as e:
                logger.warning(f"获取电影详情失败 (尝试 {attempt + 1}/3): {e}")
                time.sleep(self.delay)
        return {}

    def _parse_movie_page(self, html: str) -> Dict:
        soup = BeautifulSoup(html, "html.parser")

        info = {}
        info["poster_url"] = self._extract_poster(soup)
        info["directors"] = self._extract_field(html, "导演")
        info["screenwriters"] = self._extract_field(html, "编剧")
        info["actors"] = self._extract_field(html, "主演")
        info["genres"] = self._extract_genres(soup)
        info["countries"] = self._extract_field(html, "制片国家/地区")
        info["languages"] = self._extract_field(html, "语言")
        info["release_date"] = self._extract_field(html, "上映日期")
        info["duration"] = self._extract_duration(soup)
        info["IMDb"] = self._extract_imdb(html)
        info["douban_rating"] = self._extract_douban_rating(soup)

        return info

    def _extract_poster(self, soup) -> str:
        main_pic = soup.select_one("div.toppic img")
        if main_pic:
            return main_pic.get("src", "")
        return ""

    def _extract_field(self, html: str, field_name: str) -> str:
        pattern = rf'<[^>]*>{re.escape(field_name)}[^<]*</[^>]*>\s*<[^>]*>([^<]+)</[^>]*>'
        match = re.search(pattern, html)
        if match:
            return match.group(1).strip()

        soup = BeautifulSoup(html, "html.parser")
        info_div = soup.select_one("#info")
        if not info_div:
            return ""

        for span in info_div.select("span.attrs"):
            label = span.select_one("span.pl")
            if label and field_name in label.get_text():
                text = span.get_text(strip=True)
                text = text.replace(field_name, "").strip()
                return text

        return ""

    def _extract_genres(self, soup) -> str:
        genres = soup.select('span[property="v:genre"]')
        return "/".join([g.get_text(strip=True) for g in genres])

    def _extract_duration(self, soup) -> str:
        duration = soup.select_one('span[property="v:runtime"]')
        return duration.get("content", "") + "分钟" if duration else ""

    def _extract_imdb(self, html: str) -> str:
        match = re.search(r"tt\d+", html)
        return match.group(0) if match else ""

    def _extract_douban_rating(self, soup) -> str:
        rating = soup.select_one("strong.rating_num")
        return rating.get_text(strip=True) if rating else "N/A"
