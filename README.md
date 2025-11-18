# AI × Design Newsletter Generator

🤖 自动化 AI×Design 周报生成工具，通过 AI 分析和聚合收藏链接，快速生成高质量的行业周报。

## ✨ 功能特性

- ✅ **多种链接导入方式** - 支持 TXT/CSV/JSON 文件导入
- ✅ **智能内容抓取** - 自动提取网页标题、描述、正文内容
- ✅ **AI 内容分析** - 基于 Claude API 的智能分类和摘要（可选）
- ✅ **模拟模式** - 无 API Key 也可使用基础功能
- ✅ **可定制提示词** - 灵活的提示词模版系统
- ✅ **多格式输出** - Markdown / HTML / 微信公众号格式
- ✅ **完整CLI工具** - 类似 Git 的命令行体验
- ✅ **数据管理** - SQLite 数据库，完整的链接库管理

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 初始化数据库

```bash
python newsletter.py init
```

### 3. 配置 Claude API（可选）

```bash
# 交互式配置
python newsletter.py config set-api-key

# 或编辑 .env 文件
cp .env.example .env
# 编辑 .env，添加: ANTHROPIC_API_KEY=your_key_here
```

**没有 API Key？** 不用担心！工具会自动使用模拟模式，提供基础的分析功能。

### 4. 导入链接

```bash
# 从文本文件导入（每行一个URL）
python newsletter.py import --file examples/sample_links.txt

# 从CSV导入（带标题、分类等）
python newsletter.py import --file examples/sample_links.csv --format csv
```

### 5. 分析内容

```bash
# 批量分析所有未分析的链接
python newsletter.py analyze --batch

# 分析本周添加的链接
python newsletter.py analyze --date-range this-week
```

### 6. 生成周报

```bash
# 生成 Markdown 格式周报
python newsletter.py generate --output weekly.md

# 生成多种格式
python newsletter.py generate --output-dir output/ --formats markdown,html,wechat --date-range this-week
```

### 🎯 一键生成（快速模式）

```bash
# 导入 → 分析 → 生成，一步完成
python newsletter.py quick-generate --import-file my_links.txt
```

## 📖 详细使用

### 链接管理

```bash
# 添加单个链接（自动抓取内容）
python newsletter.py links add --url "https://example.com" --category tools

# 列出所有链接
python newsletter.py links list

# 按分类查看
python newsletter.py links list --category tools

# 搜索链接
python newsletter.py links search "Midjourney"

# 导出链接库
python newsletter.py links export --output links.csv --format csv

# 查看统计
python newsletter.py links stats
```

### 内容分析

```bash
# 分析单个URL
python newsletter.py analyze --url "https://example.com"

# 分析指定链接
python newsletter.py analyze --link-id 10

# 批量分析
python newsletter.py analyze --batch
```

### 周报生成

```bash
# 基础生成
python newsletter.py generate

# 指定日期范围
python newsletter.py generate --date-range "2024-11-01 to 2024-11-30"

# 本周内容
python newsletter.py generate --date-range this-week

# 多格式输出
python newsletter.py generate \
  --output-dir output/weekly_2024-11-19 \
  --formats markdown,html,wechat
```

## 📁 项目结构

```
AI-Weekly-Insight/
├── newsletter.py              # CLI 主程序
├── config.py                  # 配置管理
├── core/                      # 核心功能
│   ├── fetcher.py             # 内容抓取
│   ├── claude_client.py       # AI 分析（支持模拟模式）
│   ├── link_manager.py        # 链接管理
│   └── generator.py           # 周报生成
├── storage/                   # 数据存储
│   └── database.py            # SQLite 数据库
├── prompts/                   # AI 提示词模版
│   ├── analyze_content.txt    # 内容分析
│   ├── generate_newsletter.txt# 周报生成
│   └── social_media.txt       # 社交媒体文案
├── templates/                 # 输出模版
│   ├── markdown.jinja2        # Markdown 格式
│   ├── html.jinja2            # HTML 邮件格式
│   └── wechat.jinja2          # 微信公众号格式
└── examples/                  # 示例文件
    ├── sample_links.txt       # 示例链接（TXT）
    ├── sample_links.csv       # 示例链接（CSV）
    └── sample_output.md       # 示例输出
```

## 🎨 输出格式

### Markdown
- 适用：GitHub、Notion、博客
- 特点：纯文本、易编辑、版本控制友好

### HTML
- 适用：邮件订阅、Substack、Mailchimp
- 特点：响应式设计、精美样式

### 微信公众号
- 适用：微信公众号编辑器
- 特点：已排版、可直接复制粘贴

## 💡 核心特性详解

### 1. 智能模拟模式

没有 Claude API Key？没问题！工具会自动使用模拟模式：
- 基于关键词的智能分类
- 自动生成标签和评分
- 完整的周报生成功能

配置 API Key 后可获得更智能的 AI 分析。

### 2. 提示词模版系统

提示词模版支持完全自定义，适应不同的内容策展需求。
可以编辑 `prompts/` 目录下的文件来调整 AI 分析的行为。

### 3. 分类系统

内置7种分类：
- 🛠️ **Tools & Products** - AI 设计工具和产品
- 📚 **Tutorials & Guides** - 实用教程
- 🎨 **Design Trends** - 行业趋势
- 💡 **Insights & Thoughts** - 深度文章
- 🔬 **Research & Tech** - 技术研究
- 🎬 **Videos & Demos** - 视频演示
- 📰 **News & Updates** - 资讯更新

可在 `config.py` 中自定义分类。

## 🔧 配置选项

编辑 `.env` 文件：

```bash
# Claude API
ANTHROPIC_API_KEY=your_key_here
CLAUDE_MODEL=claude-sonnet-4-20250514

# 功能开关
USE_AI_ANALYSIS=true
USE_MOCK_DATA=false  # 设为 true 强制使用模拟模式

# 内容抓取
MAX_CONTENT_LENGTH=10000
FETCH_TIMEOUT=30
```

## 📊 数据存储

使用 SQLite 数据库存储：
- 链接信息和内容
- AI 分析结果
- 生成的周报记录
- API 使用统计

数据库位置：`data/links.db`

## 🎯 典型工作流

### 每周周报流程

```bash
# 周一-周五：随时添加链接
python newsletter.py links add --url "https://..." --fetch

# 周六：批量分析
python newsletter.py analyze --batch

# 周日：生成和发布
python newsletter.py generate \
  --date-range this-week \
  --formats markdown,html,wechat \
  --output-dir output/weekly_$(date +%Y-%m-%d)
```

## ⚙️ 系统要求

- Python 3.8+
- 依赖包见 `requirements.txt`
- （可选）Claude API Key

## 📝 示例输出

查看 `examples/sample_output.md` 了解生成的周报样式。

## 📄 License

MIT License

## 🙏 致谢

本项目使用以下技术：
- [Anthropic Claude](https://anthropic.com) - AI 内容分析
- [Click](https://click.palletsprojects.com/) - CLI 框架
- [Jinja2](https://jinja.palletsprojects.com/) - 模版引擎
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) - 内容提取

---

**快速开始**: `python newsletter.py init && python newsletter.py quick-generate --import-file examples/sample_links.txt`

**获取帮助**: `python newsletter.py --help`
