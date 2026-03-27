import logging
from typing import List, Dict, Optional
from notion_client import Client
from notion_client.errors import APIResponseError

logger = logging.getLogger(__name__)


class NotionSyncer:
    MOVIE_PROPERTIES = {
        "电影名称": {"type": "title"},
        "导演": {"type": "rich_text"},
        "编剧": {"type": "rich_text"},
        "主演": {"type": "rich_text"},
        "类型": {"type": "multi_select"},
        "制片国家/地区": {"type": "rich_text"},
        "语言": {"type": "rich_text"},
        "上映日期": {"type": "rich_text"},
        "片长": {"type": "rich_text"},
        "IMDb": {"type": "url"},
        "豆瓣评分": {"type": "number"},
        "观影日期": {"type": "date"},
        "豆瓣链接": {"type": "url"},
        "海报URL": {"type": "url"},
        "豆瓣ID": {"type": "rich_text"},
    }

    def __init__(self, api_key: str, database_id: str = None, parent_page_id: str = None):
        self.client = Client(auth=api_key)
        
        def clean_id(id_str: str) -> str:
            if not id_str:
                return ""
            id_str = id_str.strip()
            id_str = id_str.replace('"', '').replace("'", "")
            if id_str and len(id_str) >= 32:
                if '-' not in id_str:
                    id_str = f"{id_str[:8]}-{id_str[8:12]}-{id_str[12:16]}-{id_str[16:20]}-{id_str[20:]}"
            return id_str
        
        database_id = clean_id(database_id)
        parent_page_id = clean_id(parent_page_id)
        
        self.parent_page_id = parent_page_id
        
        if database_id:
            self.database_id = database_id
            logger.info(f"使用数据库ID: {database_id}")
            if not self._validate_database():
                logger.warning("数据库属性不匹配，可能需要重新创建")
        elif parent_page_id:
            logger.info(f"使用父页面ID: {parent_page_id}")
            self.database_id = self.create_database(parent_page_id)
        else:
            raise ValueError("必须提供 database_id 或 parent_page_id")

    def _validate_database(self) -> bool:
        try:
            db = self.client.databases.retrieve(database_id=self.database_id)
            props = db.get("properties", {})
            required = {"电影名称", "导演", "编剧", "主演", "类型", "豆瓣ID"}
            existing = set(props.keys())
            missing = required - existing
            if missing:
                logger.warning(f"数据库缺少属性: {missing}")
                return False
            return True
        except APIResponseError as e:
            logger.error(f"验证数据库失败: {e}")
            return False

    def create_database(self, parent_page_id: str) -> str:
        properties = {
            "电影名称": {"title": {}},
            "导演": {"rich_text": {}},
            "编剧": {"rich_text": {}},
            "主演": {"rich_text": {}},
            "类型": {"multi_select": {"options": []}},
            "制片国家/地区": {"rich_text": {}},
            "语言": {"rich_text": {}},
            "上映日期": {"rich_text": {}},
            "片长": {"rich_text": {}},
            "IMDb": {"url": {}},
            "豆瓣评分": {"number": {"format": "number"}},
            "观影日期": {"date": {}},
            "豆瓣链接": {"url": {}},
            "海报URL": {"url": {}},
            "豆瓣ID": {"rich_text": {}},
        }

        try:
            database = self.client.databases.create(
                parent={"type": "page_id", "page_id": parent_page_id},
                title=[{"type": "text", "text": {"content": "豆瓣电影收藏"}}],
                properties=properties,
            )
            logger.info(f"数据库创建成功: {database['id']}")
            return database["id"]
        except APIResponseError as e:
            logger.error(f"创建数据库失败: {e}")
            raise

    def get_existing_movies(self) -> Dict[str, Dict]:
        existing = {}
        try:
            results = self.client.databases.query(database_id=self.database_id)
            for page in results.get("results", []):
                props = page.get("properties", {})
                name = self._get_title(props)
                douban_id = self._get_rich_text(props, "豆瓣ID")
                
                if douban_id:
                    existing[douban_id] = {
                        "id": page["id"],
                        "name": name,
                        "rating": props.get("豆瓣评分", {}).get("number"),
                        "watched_date": props.get("观影日期", {}).get("date", {}).get("start"),
                    }
        except APIResponseError as e:
            logger.error(f"查询已有电影失败: {e}")
        return existing

    def _get_rich_text(self, props: Dict, prop_name: str) -> str:
        prop = props.get(prop_name, {})
        if prop.get("type") == "rich_text":
            rt_list = prop.get("rich_text", [])
            if rt_list:
                return rt_list[0].get("text", {}).get("content", "")
        return ""

    def sync_movies(self, movies: List[Dict], existing: Dict[str, Dict]) -> Dict[str, int]:
        stats = {"created": 0, "updated": 0, "skipped": 0, "errors": 0}

        for movie in movies:
            try:
                result = self._sync_single_movie(movie, existing)
                if result == "created":
                    stats["created"] += 1
                elif result == "updated":
                    stats["updated"] += 1
                else:
                    stats["skipped"] += 1
            except Exception as e:
                logger.error(f"同步电影失败 {movie.get('name', 'Unknown')}: {e}")
                stats["errors"] += 1

        return stats

    def _sync_single_movie(self, movie: Dict, existing: Dict[str, Dict]) -> str:
        douban_id = movie.get("douban_id")
        name = movie.get("name", "Unknown")

        if douban_id and douban_id in existing:
            existing_movie = existing[douban_id]
            if self._is_unchanged(movie, existing_movie):
                logger.debug(f"跳过已有电影: {name}")
                return "skipped"

            self._update_movie_page(existing_movie["id"], movie)
            logger.info(f"更新电影: {name}")
            return "updated"
        else:
            self._create_movie_page(movie)
            logger.info(f"创建电影: {name}")
            return "created"

    def _is_unchanged(self, movie: Dict, existing_movie: Dict) -> bool:
        movie_rating = movie.get("rating")
        existing_rating = existing_movie.get("rating")
        
        movie_date = movie.get("watched_date")
        existing_date = existing_movie.get("watched_date")
        
        return movie_rating == existing_rating and movie_date == existing_date

    def _create_movie_page(self, movie: Dict):
        properties = self._build_properties(movie)
        icon_url = movie.get("poster_url")

        page_data = {
            "parent": {"database_id": self.database_id},
            "properties": properties,
        }

        if icon_url:
            try:
                page_data["icon"] = {"type": "external", "external": {"url": icon_url}}
                page_data["cover"] = {"type": "external", "external": {"url": icon_url}}
            except Exception:
                pass

        try:
            self.client.pages.create(**page_data)
        except APIResponseError as e:
            logger.error(f"创建页面失败: {e}")
            raise

    def _update_movie_page(self, page_id: str, movie: Dict):
        properties = self._build_properties(movie)
        icon_url = movie.get("poster_url")

        update_data = {"page_id": page_id, "properties": properties}

        if icon_url:
            try:
                update_data["icon"] = {"type": "external", "external": {"url": icon_url}}
                update_data["cover"] = {"type": "external", "external": {"url": icon_url}}
            except Exception:
                pass

        try:
            self.client.pages.update(**update_data)
        except APIResponseError as e:
            logger.error(f"更新页面失败: {e}")
            raise

    def _build_properties(self, movie: Dict) -> Dict:
        properties = {}

        properties["电影名称"] = {"title": [{"text": {"content": movie.get("name", "Unknown")}}]}

        def rich_text(value):
            return [{"text": {"content": value}}] if value else []

        properties["导演"] = {"rich_text": rich_text(movie.get("directors", ""))}
        properties["编剧"] = {"rich_text": rich_text(movie.get("screenwriters", ""))}
        properties["主演"] = {"rich_text": rich_text(movie.get("actors", ""))}

        genres = movie.get("genres", "")
        genre_list = [g.strip() for g in genres.split("/") if g.strip()]
        properties["类型"] = {"multi_select": [{"name": g} for g in genre_list]}

        properties["制片国家/地区"] = {"rich_text": rich_text(movie.get("countries", ""))}
        properties["语言"] = {"rich_text": rich_text(movie.get("languages", ""))}
        properties["上映日期"] = {"rich_text": rich_text(movie.get("release_date", ""))}
        properties["片长"] = {"rich_text": rich_text(movie.get("duration", ""))}

        properties["IMDb"] = {"url": movie.get("IMDb", "")} if movie.get("IMDb") else {"url": None}

        rating_value = movie.get("douban_rating", "")
        try:
            properties["豆瓣评分"] = {"number": float(rating_value)} if rating_value and rating_value != "N/A" else {"number": None}
        except (ValueError, TypeError):
            properties["豆瓣评分"] = {"number": None}

        watched_date = movie.get("watched_date", "")
        if watched_date:
            properties["观影日期"] = {"date": {"start": watched_date[:10]}}
        else:
            properties["观影日期"] = {"date": None}

        properties["豆瓣链接"] = {"url": movie.get("douban_url", "")} if movie.get("douban_url") else {"url": None}
        properties["海报URL"] = {"url": movie.get("poster_url", "")} if movie.get("poster_url") else {"url": None}
        
        douban_id = movie.get("douban_id", "")
        properties["豆瓣ID"] = {"rich_text": rich_text(douban_id)}

        return properties

    def _get_title(self, props: Dict) -> str:
        title_prop = props.get("电影名称", {})
        if title_prop.get("type") == "title":
            title_list = title_prop.get("title", [])
            if title_list:
                return title_list[0].get("text", {}).get("content", "")
        return ""
