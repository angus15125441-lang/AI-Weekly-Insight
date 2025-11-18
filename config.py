"""
AI×Design Newsletter Generator - Configuration
配置管理模块
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# API Configuration
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
CLAUDE_MODEL = os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-20250514')
API_TIMEOUT = int(os.getenv('API_TIMEOUT', '60'))
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))

# Feature Flags
USE_AI_ANALYSIS = os.getenv('USE_AI_ANALYSIS', 'true').lower() == 'true'
USE_MOCK_DATA = os.getenv('USE_MOCK_DATA', 'false').lower() == 'true'

# 如果没有 API Key，自动启用 Mock 模式
if not ANTHROPIC_API_KEY:
    USE_MOCK_DATA = True
    USE_AI_ANALYSIS = False

# Content Fetching
MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', '10000'))
FETCH_TIMEOUT = int(os.getenv('FETCH_TIMEOUT', '30'))
USER_AGENT = os.getenv('USER_AGENT', 'Mozilla/5.0 (compatible; AI-Design-Newsletter-Bot/1.0)')

# Database
DATABASE_PATH = PROJECT_ROOT / os.getenv('DATABASE_PATH', 'data/links.db')

# Output Settings
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / os.getenv('DEFAULT_OUTPUT_DIR', 'output')
DEFAULT_FORMAT = os.getenv('DEFAULT_FORMAT', 'markdown')

# Directories
PROMPTS_DIR = PROJECT_ROOT / 'prompts'
TEMPLATES_DIR = PROJECT_ROOT / 'templates'
DATA_DIR = PROJECT_ROOT / 'data'
OUTPUT_DIR = PROJECT_ROOT / 'output'
EXAMPLES_DIR = PROJECT_ROOT / 'examples'

# Social Media
TWITTER_HANDLE = os.getenv('TWITTER_HANDLE', '@AIDesignWeekly')
WECHAT_NAME = os.getenv('WECHAT_NAME', 'AI×Design周报')
XIAOHONGSHU_ID = os.getenv('XIAOHONGSHU_ID', '')

# Categories Configuration
CATEGORIES = [
    {
        "id": "tools",
        "name": "Tools & Products",
        "icon": "🛠️",
        "description": "新发布的 AI 设计工具和产品"
    },
    {
        "id": "tutorials",
        "name": "Tutorials & Guides",
        "icon": "📚",
        "description": "实用的教程和操作指南"
    },
    {
        "id": "trends",
        "name": "Design Trends",
        "icon": "🎨",
        "description": "行业趋势和案例分析"
    },
    {
        "id": "insights",
        "name": "Insights & Thoughts",
        "icon": "💡",
        "description": "深度文章和观点"
    },
    {
        "id": "research",
        "name": "Research & Tech",
        "icon": "🔬",
        "description": "技术论文和研究成果"
    },
    {
        "id": "videos",
        "name": "Videos & Demos",
        "icon": "🎬",
        "description": "视频教程和产品演示"
    },
    {
        "id": "news",
        "name": "News & Updates",
        "icon": "📰",
        "description": "行业新闻和产品更新"
    }
]

# Category ID to Name mapping
CATEGORY_MAP = {cat['id']: cat for cat in CATEGORIES}

def get_category_info(category_id):
    """获取分类信息"""
    return CATEGORY_MAP.get(category_id, {
        "id": category_id,
        "name": category_id.title(),
        "icon": "📌",
        "description": ""
    })

def ensure_directories():
    """确保必要的目录存在"""
    directories = [
        DATA_DIR,
        DATA_DIR / 'cache',
        DATA_DIR / 'imports',
        OUTPUT_DIR,
        PROMPTS_DIR / 'custom',
        TEMPLATES_DIR / 'custom',
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

    # 创建 .gitkeep 文件
    gitkeep_dirs = [
        DATA_DIR / 'cache',
        DATA_DIR / 'imports',
        OUTPUT_DIR,
        PROMPTS_DIR / 'custom',
        TEMPLATES_DIR / 'custom',
    ]
    for directory in gitkeep_dirs:
        gitkeep_file = directory / '.gitkeep'
        if not gitkeep_file.exists():
            gitkeep_file.touch()

def check_api_key():
    """检查 API Key 是否配置"""
    return bool(ANTHROPIC_API_KEY and ANTHROPIC_API_KEY != 'your_api_key_here')

def get_mode_info():
    """获取当前运行模式信息"""
    has_api_key = check_api_key()

    if has_api_key and USE_AI_ANALYSIS:
        return {
            'mode': 'AI',
            'description': 'AI 分析模式（使用 Claude API）',
            'color': 'green'
        }
    elif USE_MOCK_DATA:
        return {
            'mode': 'MOCK',
            'description': '模拟数据模式（演示用）',
            'color': 'yellow'
        }
    else:
        return {
            'mode': 'MANUAL',
            'description': '手动模式（无 AI 分析）',
            'color': 'blue'
        }
