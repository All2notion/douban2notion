# douban2notion

将豆瓣观影记录同步至 Notion 画廊数据库的自动化工具。

## 功能特性

- 从豆瓣获取用户的观影记录（看过的电影）
- 自动创建 Notion 数据库，无需手动配置属性
- 基于豆瓣ID的精确重复检测，避免重名电影混淆
- 支持 GitHub Actions 定时自动同步
- 增量同步，自动跳过未变化的数据
- 自动抓取电影海报并设为 Notion 页面封面

## 前提条件

- GitHub 账号
- Notion 账号
- 豆瓣账号

## 快速开始

### 1. Fork 仓库

点击 GitHub 仓库右上角 **Fork** 按钮。

### 2. 配置 GitHub Secrets

仓库 **Settings** → **Secrets and variables** → **Actions** → **New repository secret**：

| Secret 名称 | 说明 | 必填 |
|-----------|------|------|
| `NOTION_API_KEY` | Notion Integration Token | 是 |
| `NOTION_PARENT_PAGE_ID` | Notion父页面ID（用于自动创建数据库） | 二选一 |
| `NOTION_DATABASE_ID` | 已有Notion数据库ID | 二选一 |
| `DOUBAN_USER_ID` | 豆瓣用户ID或用户名 | 是 |
| `DOUBAN_COOKIES` | 豆瓣登录Cookie | 是 |

**注意**：
- 如果提供 `NOTION_PARENT_PAGE_ID`，程序会自动创建数据库
- 如果提供 `NOTION_DATABASE_ID`，程序会使用现有数据库

### 3. 创建 Notion Integration

1. 访问 [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. 点击 **New integration**
3. 填写名称（如 `douban2notion`），选择工作区
4. 点击 **Submit**，复制 API Key

### 4. 获取 Notion 父页面ID（用于自动创建数据库）

1. 在 Notion 创建一个新页面（将用于存放数据库）
2. 打开页面，从 URL 复制页面 ID
3. 点击右上角 `...` → **Add connections** → 选择你的 Integration

### 5. 获取豆瓣Cookie

1. 浏览器登录 [豆瓣](https://www.douban.com)
2. 按 F12 打开开发者工具
3. 切换到 **Network** 标签
4. 刷新页面，点击任意请求
5. 在 **Request Headers** 中找到 `Cookie`
6. 复制完整 Cookie 字符串

### 6. 触发同步

1. 进入仓库 **Actions** 页面
2. 选择 **Sync Douban Movies to Notion** 工作流
3. 点击 **Run workflow** → **Run workflow**

## 同步字段

| 豆瓣字段 | Notion 属性类型 |
|---------|----------------|
| 电影名称 | 标题 |
| 导演 / 编剧 / 主演 | 富文本 |
| 类型 | 多选 |
| 制片国家/地区 / 语言 / 上映日期 / 片长 | 富文本 |
| IMDb / 豆瓣链接 | URL |
| 豆瓣评分 | 数字 |
| 观影日期 | 日期 |
| 豆瓣ID | 富文本（用于去重） |
| 海报 | 自动设为页面封面 |

## 自动同步

默认每天凌晨 2:00（UTC）自动执行。修改时间编辑 `.github/workflows/sync.yml`：

```yaml
schedule:
  - cron: "0 2 * * *"  # 每天凌晨2点
```

## 本地开发

```bash
git clone https://github.com/YOUR_USERNAME/douban2notion.git
cd douban2notion
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 填写配置
python main.py
```

## 项目结构

```
douban2notion/
├── .github/workflows/
│   └── sync.yml          # GitHub Actions 工作流
├── src/
│   ├── douban.py         # 豆瓣数据抓取
│   └── notion_sync.py    # Notion 同步（支持自动创建数据库）
├── docs/
│   └── DEPLOYMENT.md     # 详细部署指南
├── config.py             # 配置管理
├── main.py               # 程序入口
├── requirements.txt      # 依赖列表
└── .env.example          # 环境变量模板
```

## 详细文档

- [部署指南](docs/DEPLOYMENT.md) - 完整部署步骤

## License

[GPL-3.0](LICENSE)
