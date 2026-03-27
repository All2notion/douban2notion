# douban2notion

将豆瓣观影记录同步至 Notion 画廊数据库的自动化工具。

## 功能特性

- 从豆瓣获取用户的观影记录
- 同步至 Notion 数据库，支持画廊视图展示
- 自动抓取电影海报并设为页面封面
- 支持 GitHub Actions 定时同步
- 增量同步，自动跳过未变化的数据

## 前提条件

- GitHub 账号
- Notion 账号
- 豆瓣账号

## 快速开始

### 步骤 1 - Fork 仓库

点击 GitHub 仓库右上角 **Fork** 按钮。

### 步骤 2 - 配置 Secrets

仓库 **Settings** → **Secrets and variables** → **Actions** → **New repository secret**：

| Secret 名称 | 说明 |
|-----------|------|
| `NOTION_API_KEY` | Notion Integration Token |
| `NOTION_DATABASE_ID` | Notion 数据库 ID |
| `DOUBAN_USER_ID` | 豆瓣用户 ID |
| `DOUBAN_COOKIES` | 豆瓣登录 Cookie |

### 步骤 3 - 创建 Notion 数据库

1. 在 Notion 创建新页面，选择 **Table** 视图
2. 添加以下属性：

| 属性名 | 类型 |
|-------|------|
| 电影名称 | 标题 |
| 导演 | 富文本 |
| 编剧 | 富文本 |
| 主演 | 富文本 |
| 类型 | 多选 |
| 制片国家/地区 | 富文本 |
| 语言 | 富文本 |
| 上映日期 | 富文本 |
| 片长 | 富文本 |
| IMDb | URL |
| 豆瓣评分 | 数字 |
| 观影日期 | 日期 |
| 豆瓣链接 | URL |
| 海报URL | URL |

3. 点击右上角 `...` → **Add connections** → 选择你的 Integration

### 步骤 4 - 获取数据库 ID

打开数据库页面，从 URL 复制 Database ID：

```
https://notion.so/username/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx?v=...
```

### 步骤 5 - 创建 Notion Integration

1. 访问 [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. 点击 **New integration**
3. 填写名称，选择工作区
4. 点击 **Submit**，复制 API Key

### 步骤 6 - 获取豆瓣配置

**用户 ID**：登录豆瓣，进入个人主页，URL 中 `people/` 后面的数字。

**Cookie**：
1. 浏览器登录 [豆瓣](https://www.douban.com)
2. 按 F12 → **Network** 标签
3. 刷新页面，点击任意请求
4. 在 **Request Headers** 中复制 `Cookie`

### 步骤 7 - 触发同步

1. 进入 **Actions** 页面
2. 选择 **Sync Douban Movies to Notion**
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
| 海报 | 自动设为页面封面 |

## 自动同步

默认每天凌晨 2:00 自动执行。修改时间编辑 `.github/workflows/sync.yml`：

```yaml
schedule:
  - cron: "0 2 * * *"  # 每天凌晨2点
```

## 项目结构

```
douban2notion/
├── .github/workflows/
│   └── sync.yml          # GitHub Actions 工作流
├── src/
│   ├── douban.py         # 豆瓣数据抓取
│   └── notion_sync.py    # Notion 同步
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
