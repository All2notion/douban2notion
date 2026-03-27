import os
import sys
import logging
from config import NOTION_API_KEY, NOTION_DATABASE_ID, NOTION_PARENT_PAGE_ID, DOUBAN_USER_ID, DOUBAN_COOKIES, MAX_PAGES, ENABLE_LOGGING
from src import DoubanScraper, NotionSyncer


def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def validate_config():
    missing = []
    if not NOTION_API_KEY:
        missing.append("NOTION_API_KEY")
    if not DOUBAN_USER_ID:
        missing.append("DOUBAN_USER_ID")
    if not (NOTION_DATABASE_ID or NOTION_PARENT_PAGE_ID):
        missing.append("NOTION_DATABASE_ID 或 NOTION_PARENT_PAGE_ID")

    if missing:
        raise ValueError(f"缺少必需的环境变量: {', '.join(missing)}")


def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("=" * 50)
    logger.info("豆瓣电影 → Notion 同步程序启动")
    logger.info("=" * 50)

    try:
        validate_config()
    except ValueError as e:
        logger.error(f"配置验证失败: {e}")
        logger.info("请确保已设置环境变量，或复制 .env.example 为 .env 并填写配置")
        sys.exit(1)

    logger.info("正在从豆瓣获取观影记录...")
    scraper = DoubanScraper(user_id=DOUBAN_USER_ID, cookies=DOUBAN_COOKIES, delay=1.0)

    try:
        movies = scraper.fetch_watched_movies(max_pages=1)
        movies = movies[:10]
        logger.info(f"共获取 {len(movies)} 部电影")
    except Exception as e:
        logger.error(f"获取豆瓣数据失败: {e}")
        sys.exit(1)

    if not movies:
        logger.warning("未获取到任何电影数据")
        sys.exit(0)

    logger.info("正在初始化 Notion 同步...")
    try:
        syncer = NotionSyncer(
            api_key=NOTION_API_KEY,
            database_id=NOTION_DATABASE_ID,
            parent_page_id=NOTION_PARENT_PAGE_ID
        )
    except Exception as e:
        logger.error(f"初始化 NotionSyncer 失败: {e}")
        sys.exit(1)

    logger.info("正在查询 Notion 数据库...")
    existing = syncer.get_existing_movies()
    logger.info(f"Notion 数据库已有 {len(existing)} 部电影")

    logger.info("正在同步数据...")
    stats = syncer.sync_movies(movies, existing)

    logger.info("=" * 50)
    logger.info("同步完成!")
    logger.info(f"  新增: {stats['created']}")
    logger.info(f"  更新: {stats['updated']}")
    logger.info(f"  跳过: {stats['skipped']}")
    logger.info(f"  错误: {stats['errors']}")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
