# 部署指南

本文档提供使用 GitHub Actions 部署 douban2notion 的完整步骤。

---

## 准备工作

### 所需账号

- **GitHub 账号**：用于 Fork 仓库和配置 Actions
- **Notion 账号**：用于创建 Integration 和数据库
- **豆瓣账号**：用于获取观影记录

---

## 步骤 1 - Fork 仓库

点击 GitHub 仓库右上角 **Fork** 按钮。

---

## 步骤 2 - 配置 Secrets

仓库 **Settings** → **Secrets and variables** → **Actions** → **New repository secret**：

| Secret 名称 | 说明 |
|-----------|------|
| `NOTION_API_KEY` | Notion Integration Token |
| `NOTION_DATABASE_ID` | Notion 数据库 ID |
| `DOUBAN_USER_ID` | 豆瓣用户 ID |
| `DOUBAN_COOKIES` | 豆瓣登录 Cookie |

---

## 步骤 3 - 创建 Notion Integration

1. 访问 [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. 点击 **New integration**
3. 填写名称（如 `douban2notion`），选择工作区
4. 点击 **Submit**，复制 API Key

---

## 步骤 4 - 创建 Notion 数据库

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

---

## 步骤 5 - 获取数据库 ID

打开数据库页面，从 URL 复制 Database ID：

```
https://notion.so/username/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx?v=...
```

---

## 步骤 6 - 获取豆瓣用户 ID

1. 登录豆瓣，点击头像进入个人主页
2. URL 中 `people/` 后面的数字即用户 ID

示例：`https://www.douban.com/people/123456789/` → 用户 ID：`123456789`

---

## 步骤 7 - 获取豆瓣 Cookie

1. 浏览器登录 [豆瓣](https://www.douban.com)
2. 按 F12 打开开发者工具
3. 切换到 **Network** 标签
4. 刷新页面或访问任意豆瓣页面
5. 点击任意请求（如 `www.douban.com`）
6. 在 **Request Headers** 中找到 `Cookie` 字段
7. 复制完整 Cookie 字符串

**注意**：
- Cookie 有效期约一周，过期后需重新获取
- 请勿泄露 Cookie 信息

---

## 步骤 8 - 触发同步

1. 进入仓库 **Actions** 页面
2. 选择 **Sync Douban Movies to Notion** 工作流
3. 点击 **Run workflow** → **Run workflow**

---

## 设置自动同步

默认每天凌晨 2:00（UTC）自动执行。

修改时间编辑 `.github/workflows/sync.yml`：

```yaml
schedule:
  - cron: "0 2 * * *"  # 每天凌晨2点
```

常用 cron 表达式：

| 表达式 | 说明 |
|-------|------|
| `0 2 * * *` | 每天凌晨 2 点 |
| `0 3 * * 0` | 每周日凌晨 3 点 |
| `0 */6 * * *` | 每 6 小时 |
| `0 9,21 * * *` | 每天 9 点和 21 点 |

---

## 设置 Notion 画廊视图

同步成功后，按以下步骤设置画廊视图：

1. 打开 Notion 数据库
2. 左上角点击视图切换器
3. 选择 **Gallery** 画廊视图
4. 点击 **Properties** 设置封面
5. 选择 **海报URL** 或 **Cover** 作为封面来源
6. 调整卡片大小和布局

---

## 常见问题

### Q1: 403 Forbidden / 418 I'm a teapot

豆瓣反爬机制触发。检查 Cookie 是否有效，等待一段时间后重试。

### Q2: Notion API error

确认 `NOTION_API_KEY` 正确，Integration 已连接数据库。

### Q3: Cookie 过期

豆瓣 Cookie 约一周失效。更新 GitHub Secret 中的 `DOUBAN_COOKIES`。

### Q4: 封面不显示

确认海报 URL 可公开访问，格式为 JPEG/PNG。

### Q5: 如何过滤电影

在 `src/notion_sync.py` 的 `_sync_single_movie` 方法中添加条件判断。

---

## 数据安全

- GitHub Secrets 不出现在代码仓库中
- 请勿泄露你的凭证信息
