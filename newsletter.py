#!/usr/bin/env python
"""
AI×Design Newsletter Generator
AI×设计周报生成器 - 命令行工具

Usage:
    python newsletter.py --help
"""

import click
import json
import sys
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

import config
from storage.database import Database, init_db
from core.link_manager import LinkManager
from core.fetcher import ContentFetcher
from core.claude_client import ClaudeClient
from core.generator import NewsletterGenerator


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """
    AI×Design Newsletter Generator

    AI×设计周报生成器 - 自动化处理收藏链接，生成高质量周报
    """
    # 确保目录存在
    config.ensure_directories()


# ===== 初始化命令 =====

@cli.command()
def init():
    """初始化数据库"""
    click.echo("🚀 初始化数据库...")

    try:
        init_db()
        click.echo("✅ 数据库初始化成功！")
        click.echo(f"📁 数据库路径: {config.DATABASE_PATH}")

        # 显示当前模式
        mode_info = config.get_mode_info()
        click.echo(f"\n当前运行模式: {mode_info['mode']} - {mode_info['description']}")

        if mode_info['mode'] == 'MOCK':
            click.echo("\n💡 提示: 配置 Claude API Key 后可启用 AI 分析功能")
            click.echo("   使用命令: python newsletter.py config set-api-key")

    except Exception as e:
        click.echo(f"❌ 初始化失败: {e}", err=True)
        sys.exit(1)


# ===== 配置命令 =====

@cli.group()
def config_cmd():
    """配置管理"""
    pass


@config_cmd.command('set-api-key')
@click.option('--key', prompt='请输入 Claude API Key', hide_input=True,
              help='Claude API Key')
def set_api_key(key):
    """设置 Claude API Key"""
    env_file = config.PROJECT_ROOT / '.env'

    # 读取现有配置
    lines = []
    if env_file.exists():
        with open(env_file, 'r') as f:
            lines = f.readlines()

    # 更新或添加 API Key
    updated = False
    for i, line in enumerate(lines):
        if line.startswith('ANTHROPIC_API_KEY='):
            lines[i] = f'ANTHROPIC_API_KEY={key}\n'
            updated = True
            break

    if not updated:
        lines.append(f'ANTHROPIC_API_KEY={key}\n')

    # 写入文件
    with open(env_file, 'w') as f:
        f.writelines(lines)

    click.echo("✅ API Key 已保存")
    click.echo("💡 请重新运行命令以使用 AI 功能")


@config_cmd.command('show')
def show_config():
    """显示当前配置"""
    mode_info = config.get_mode_info()

    click.echo("=== 当前配置 ===")
    click.echo(f"运行模式: {mode_info['mode']} - {mode_info['description']}")
    click.echo(f"数据库路径: {config.DATABASE_PATH}")
    click.echo(f"输出目录: {config.OUTPUT_DIR}")
    click.echo(f"Claude 模型: {config.CLAUDE_MODEL}")

    if config.check_api_key():
        click.echo("✅ Claude API Key: 已配置")
    else:
        click.echo("❌ Claude API Key: 未配置")


# ===== 链接管理命令 =====

@cli.group()
def links():
    """链接管理"""
    pass


@links.command('add')
@click.option('--url', required=True, help='链接 URL')
@click.option('--title', help='标题')
@click.option('--category', help='分类')
@click.option('--tags', help='标签（逗号分隔）')
@click.option('--notes', help='备注')
@click.option('--fetch/--no-fetch', default=True, help='是否自动抓取内容')
def add_link(url, title, category, tags, notes, fetch):
    """添加单个链接"""
    manager = LinkManager()

    kwargs = {}
    if title:
        kwargs['title'] = title
    if category:
        kwargs['category'] = category
    if tags:
        kwargs['tags'] = [t.strip() for t in tags.split(',')]
    if notes:
        kwargs['notes'] = notes

    # 如果启用抓取且没有提供标题
    if fetch and not title:
        click.echo(f"📡 抓取内容: {url}")
        fetcher = ContentFetcher()
        result = fetcher.fetch_url(url)

        if result['success']:
            kwargs['title'] = result['title']
            kwargs['description'] = result['description']
            kwargs['content'] = result['content']
            kwargs['author'] = result['author']
            kwargs['source'] = result['source']
            click.echo(f"✅ 内容抓取成功: {result['title']}")
        else:
            click.echo(f"⚠️  内容抓取失败: {result.get('error')}")

    # 添加链接
    result = manager.add_link(url, **kwargs)

    if result['success']:
        click.echo(f"✅ 链接添加成功 (ID: {result['link_id']})")
    else:
        click.echo(f"ℹ️  {result['message']}")


@links.command('list')
@click.option('--category', help='按分类筛选')
@click.option('--status', help='按状态筛选 (pending/analyzed/published)')
@click.option('--limit', type=int, default=20, help='显示数量')
def list_links(category, status, limit):
    """列出链接"""
    manager = LinkManager()
    links_list = manager.list_links(category=category, status=status, limit=limit)

    if not links_list:
        click.echo("📭 暂无链接")
        return

    click.echo(f"\n共找到 {len(links_list)} 条链接:\n")

    for link in links_list:
        click.echo(f"[{link['id']}] {link['title'] or 'Untitled'}")
        click.echo(f"    URL: {link['url']}")
        if link.get('category'):
            click.echo(f"    分类: {link['category']}")
        if link.get('rating'):
            click.echo(f"    评分: {'⭐' * link['rating']}")
        click.echo(f"    添加时间: {link['added_at']}")
        click.echo("")


@links.command('stats')
def links_stats():
    """显示统计信息"""
    manager = LinkManager()
    stats = manager.get_stats()

    click.echo("\n=== 链接库统计 ===\n")
    click.echo(f"📊 总链接数: {stats['total']}")

    if stats.get('by_status'):
        click.echo("\n按状态:")
        for status, count in stats['by_status'].items():
            click.echo(f"  {status}: {count}")

    if stats.get('by_category'):
        click.echo("\n按分类:")
        for cat, count in stats['by_category'].items():
            cat_info = config.get_category_info(cat)
            click.echo(f"  {cat_info['icon']} {cat_info['name']}: {count}")


@links.command('export')
@click.option('--output', required=True, help='输出文件路径')
@click.option('--format', type=click.Choice(['csv', 'json']), default='csv',
              help='导出格式')
@click.option('--category', help='按分类筛选')
def export_links(output, format, category):
    """导出链接"""
    manager = LinkManager()

    click.echo(f"📤 导出链接到: {output}")
    success = manager.export_links(output, format=format, category=category)

    if success:
        click.echo("✅ 导出成功")
    else:
        click.echo("❌ 导出失败")


# ===== 导入命令 =====

@cli.command('import')
@click.option('--file', 'file_path', required=True, help='文件路径')
@click.option('--format', type=click.Choice(['txt', 'csv', 'json']), default='txt',
              help='文件格式')
def import_links(file_path, format):
    """从文件导入链接"""
    manager = LinkManager()

    click.echo(f"📥 从文件导入: {file_path}")
    result = manager.import_from_file(file_path, format=format)

    if result['success']:
        click.echo(f"\n✅ 导入完成:")
        click.echo(f"   总计: {result['total']} 条")
        click.echo(f"   新增: {result['added']} 条")
        click.echo(f"   跳过: {result['skipped']} 条")

        if result.get('errors'):
            click.echo(f"\n⚠️  错误 ({len(result['errors'])}):")
            for error in result['errors'][:5]:  # 只显示前5个
                click.echo(f"   {error}")
    else:
        click.echo(f"❌ 导入失败: {result['message']}")


# ===== 分析命令 =====

@cli.command('analyze')
@click.option('--url', help='分析单个 URL')
@click.option('--link-id', type=int, help='分析指定 ID 的链接')
@click.option('--batch', is_flag=True, help='批量分析所有未分析的链接')
@click.option('--date-range', help='分析日期范围内的链接 (this-week/last-week)')
def analyze(url, link_id, batch, date_range):
    """AI 分析内容"""
    manager = LinkManager()
    client = ClaudeClient()

    mode_info = config.get_mode_info()
    click.echo(f"🤖 分析模式: {mode_info['mode']} - {mode_info['description']}\n")

    links_to_analyze = []

    if url:
        # 分析单个 URL
        link = manager.get_link_by_url(url) if hasattr(manager, 'get_link_by_url') else None
        if link:
            links_to_analyze = [link]
        else:
            click.echo(f"❌ 未找到链接: {url}")
            return
    elif link_id:
        # 分析指定 ID
        link = manager.get_link(link_id)
        if link:
            links_to_analyze = [link]
        else:
            click.echo(f"❌ 未找到 ID: {link_id}")
            return
    elif date_range:
        # 分析日期范围
        links_to_analyze = manager.get_links_by_date_range(date_range)
    elif batch:
        # 批量分析
        links_to_analyze = manager.list_links(status='pending')
    else:
        click.echo("❌ 请指定 --url, --link-id, --batch 或 --date-range")
        return

    if not links_to_analyze:
        click.echo("📭 没有需要分析的链接")
        return

    click.echo(f"📊 准备分析 {len(links_to_analyze)} 条链接\n")

    success_count = 0
    fail_count = 0

    with tqdm(total=len(links_to_analyze), desc="分析进度") as pbar:
        for link in links_to_analyze:
            try:
                # 分析内容
                result = client.analyze_content(
                    title=link.get('title', ''),
                    url=link.get('url', ''),
                    content=link.get('content', '') or link.get('description', ''),
                    source=link.get('source', '')
                )

                if result['success']:
                    # 更新数据库
                    analysis = result['analysis']
                    manager.update_link(
                        link['id'],
                        analysis_result=json.dumps(analysis, ensure_ascii=False),
                        category=analysis.get('category'),
                        rating=analysis.get('rating'),
                        status='analyzed',
                        analyzed_at=datetime.now().isoformat()
                    )
                    success_count += 1
                else:
                    fail_count += 1

            except Exception as e:
                fail_count += 1

            pbar.update(1)

    click.echo(f"\n✅ 分析完成:")
    click.echo(f"   成功: {success_count}")
    click.echo(f"   失败: {fail_count}")

    if mode_info['mode'] == 'MOCK':
        click.echo(f"\n💡 提示: 当前使用模拟模式，配置 API Key 可获得真实 AI 分析")


# ===== 生成命令 =====

@cli.command('generate')
@click.option('--output', help='输出文件路径')
@click.option('--format', type=click.Choice(['markdown', 'html', 'wechat']),
              default='markdown', help='输出格式')
@click.option('--date-range', help='日期范围 (this-week/last-week/YYYY-MM-DD to YYYY-MM-DD)')
@click.option('--title', help='周报标题')
@click.option('--category', help='只包含指定分类')
def generate(output, format, date_range, title, category):
    """生成周报"""
    manager = LinkManager()
    generator = NewsletterGenerator()

    # 获取链接
    if date_range:
        if ' to ' in date_range:
            start, end = date_range.split(' to ')
            links = manager.get_links_by_date_range(start.strip(), end.strip())
        else:
            links = manager.get_links_by_date_range(date_range)
    else:
        links = manager.list_links(category=category, status='analyzed')

    if not links:
        click.echo("📭 没有可用的链接，请先添加并分析链接")
        return

    click.echo(f"📝 生成周报 ({format} 格式)...")
    click.echo(f"   使用 {len(links)} 条链接\n")

    # 设置默认输出路径
    if not output:
        timestamp = datetime.now().strftime('%Y-%m-%d')
        ext = 'html' if format in ['html', 'wechat'] else 'md'
        output = config.OUTPUT_DIR / f'newsletter_{timestamp}.{ext}'

    # 生成
    result = generator.generate(
        links=links,
        output_path=output,
        format=format,
        date_range=date_range or '',
        title=title
    )

    if result['success']:
        click.echo(f"✅ 周报生成成功!")
        click.echo(f"📄 输出文件: {result['output_path']}")

        # 显示预览
        if click.confirm('\n是否显示预览？', default=False):
            click.echo("\n" + "="*60)
            click.echo(result['content'][:500] + "...")
            click.echo("="*60)
    else:
        click.echo(f"❌ 生成失败: {result.get('error')}")


@cli.command('quick-generate')
@click.option('--import-file', 'import_file', help='要导入的文件路径')
@click.option('--output-dir', help='输出目录')
@click.option('--formats', default='markdown', help='输出格式（逗号分隔）')
def quick_generate(import_file, output_dir, formats):
    """快速生成（导入 → 分析 → 生成）"""
    click.echo("🚀 快速生成模式\n")

    # Step 1: 导入
    if import_file:
        ctx = click.get_current_context()
        ctx.invoke(import_links, file_path=import_file, format='txt')
        click.echo("")

    # Step 2: 分析
    click.echo("📊 开始分析...")
    ctx = click.get_current_context()
    ctx.invoke(analyze, batch=True, url=None, link_id=None, date_range=None)
    click.echo("")

    # Step 3: 生成
    click.echo("📝 开始生成周报...\n")

    if not output_dir:
        timestamp = datetime.now().strftime('%Y-%m-%d')
        output_dir = config.OUTPUT_DIR / f'weekly_{timestamp}'

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    format_list = [f.strip() for f in formats.split(',')]

    for fmt in format_list:
        ext = 'html' if fmt in ['html', 'wechat'] else 'md'
        filename = f'newsletter.{ext}' if fmt != 'wechat' else 'newsletter_wechat.html'
        output_file = output_path / filename

        ctx.invoke(generate, output=str(output_file), format=fmt,
                   date_range='this-week', title=None, category=None)

    click.echo(f"\n✅ 所有格式已生成到: {output_dir}")


if __name__ == '__main__':
    cli()
