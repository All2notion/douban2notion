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
    USER_URL = "https://movie.douban.com/people/{user_id}/collect"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
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
        url = f"{self.USER_URL}?start={(page - 1) * 30}&sort=date&rating=all&filter=all&mode=grid"
        logger.info(f"请求URL: {url}")

        response = self.session.get(url, cookies=self.cookies, timeout=30)
        logger.info(f"响应状态码: {response.status_code}")
        logger.info(f"响应内容长度: {len(response.text)} 字符")

        if response.status_code != 200:
            logger.error(f"请求失败，状态码: {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")

        movie_items = soup.select("div.item")
        logger.info(f"找到 {len(movie_items)} 个电影条目")

        movies = []

        for item in movie_items:
            movie = self._parse_movie_item(item)
            if movie:
                movies.append(movie)

        return movies

    def _parse_movie_item(self, item) -> Optional[Dict]:
        try:
            title_elem = item.select_one("div.info div.hd a")
            if not title_elem:
                return None

            douban_url = title_elem.get("href", "")
            movie_id = self._extract_movie_id(douban_url)

            detail = item.select_one("div.info div.bd")
            if not detail:
                return None

            info_text = detail.get_text(strip=True)

            rating_elem = item.select_one("span.rating_nums")
            rating = rating_elem.get_text(strip=True) if rating_elem else "N/A"

            date_elem = item.select_one("span.date")
            watched_date = date_elem.get_text(strip=True) if date_elem else ""

            movie_info = self.fetch_movie_detail(movie_id)

            return {
                "douban_id": movie_id,
                "douban_url": douban_url,
                "name": title_elem.select_one("span.title").get_text(strip=True) if title_elem.select_one("span.title") else "",
                "rating": rating,
                "watched_date": watched_date,
                **movie_info,
            }
        except Exception as e:
            logger.error(f"解析电影条目失败: {e}")
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
