"""
AI×Design Newsletter Generator - Newsletter Generator
周报生成引擎
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from jinja2 import Environment, FileSystemLoader, Template
from collections import defaultdict
import config


class NewsletterGenerator:
    """周报生成器"""

    def __init__(self):
        """初始化生成器"""
        # 设置 Jinja2 环境
        self.env = Environment(
            loader=FileSystemLoader(str(config.TEMPLATES_DIR)),
            trim_blocks=True,
            lstrip_blocks=True
        )

    def generate(self, links: List[Dict], output_path: str = None,
                 format: str = 'markdown', date_range: str = '',
                 title: str = None) -> Dict:
        """
        生成周报

        Args:
            links: 链接列表
            output_path: 输出路径
            format: 输出格式 (markdown/html/wechat)
            date_range: 日期范围
            title: 周报标题

        Returns:
            生成结果
        """
        # 准备数据
        data = self._prepare_data(links, date_range, title)

        # 选择模版
        template_name = f'{format}.jinja2'
        try:
            template = self.env.get_template(template_name)
        except Exception as e:
            return {
                'success': False,
                'error': f'模版文件不存在: {template_name}'
            }

        # 渲染
        try:
            content = template.render(**data)
        except Exception as e:
            import traceback
            return {
                'success': False,
                'error': f'渲染失败: {str(e)}',
                'traceback': traceback.format_exc()
            }

        # 输出
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)

        return {
            'success': True,
            'content': content,
            'output_path': output_path,
            'format': format
        }

    def _prepare_data(self, links: List[Dict], date_range: str = '',
                      title: str = None) -> Dict:
        """准备模版数据"""
        # 按分类组织链接
        categories_dict = defaultdict(list)

        for link in links:
            # 解析分析结果
            analysis = link.get('analysis_result')
            if isinstance(analysis, str):
                try:
                    analysis = json.loads(analysis)
                except:
                    analysis = {}

            # 解析tags
            tags = link.get('tags')
            if isinstance(tags, str):
                try:
                    tags = json.loads(tags)
                except:
                    tags = []

            # 确定分类
            category = analysis.get('category') if analysis else link.get('category')
            if not category:
                category = 'insights'  # 默认分类

            # 构造条目
            item = {
                'id': link.get('id'),
                'title': link.get('title', 'Untitled'),
                'url': link.get('url', ''),
                'summary': analysis.get('summary') if analysis else link.get('description', ''),
                'tags': analysis.get('tags') if analysis else (tags or []),
                'rating': analysis.get('rating', 3) if analysis else link.get('rating', 3),
                'highlights': analysis.get('highlights', []) if analysis else [],
                'added_at': link.get('added_at', '')
            }

            categories_dict[category].append(item)

        # 构造分类列表
        categories = []
        for cat_id, items in categories_dict.items():
            cat_info = config.get_category_info(cat_id)
            categories.append({
                'id': cat_id,
                'name': cat_info['name'],
                'icon': cat_info['icon'],
                'description': cat_info['description'],
                'content_items': items  # 使用 content_items 而不是 items 避免与 dict.items() 冲突
            })

        # 按预设顺序排序
        cat_order = [cat['id'] for cat in config.CATEGORIES]
        categories.sort(key=lambda x: cat_order.index(x['id']) if x['id'] in cat_order else 999)

        # 提取精选（评分>=4的内容）
        highlights = []
        for cat in categories:
            for item in cat['content_items']:
                if item['rating'] >= 4:
                    highlights.append({
                        **item,
                        'category': cat['name']
                    })

        # 按评分排序并取前5个
        highlights.sort(key=lambda x: x['rating'], reverse=True)
        highlights = highlights[:5]

        # 生成标题
        if not title:
            today = datetime.now()
            if date_range:
                title = f"AI × Design Weekly - {date_range}"
            else:
                title = f"AI × Design Weekly - {today.strftime('%Y-%m-%d')}"

        # 生成导语
        total_links = len(links)
        main_topics = list(set([cat['name'] for cat in categories[:3]]))
        intro = f"本周共收录 {total_links} 篇优质内容，涵盖{' '.join(main_topics)}等多个领域。"

        # 生成编者按（简单版）
        editor_notes = self._generate_editor_notes(categories, highlights)

        return {
            'title': title,
            'date': date_range or datetime.now().strftime('%Y-%m-%d'),
            'intro': intro,
            'total_links': total_links,
            'categories': categories,
            'highlights': highlights,
            'main_topics': main_topics,
            'recommendation_score': min(5, max(3, int(sum(h['rating'] for h in highlights) / len(highlights)) if highlights else 3)),
            'editor_notes': editor_notes,
            'subscription_info': self._get_subscription_info(),
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    def _generate_editor_notes(self, categories: List[Dict], highlights: List[Dict]) -> str:
        """生成编者按（简单版）"""
        if not highlights:
            return "本周内容质量上乘，值得深入阅读。"

        # 统计主要话题
        all_tags = []
        for cat in categories:
            for item in cat['content_items']:
                all_tags.extend(item.get('tags', []))

        # 找出高频标签
        from collections import Counter
        tag_counts = Counter(all_tags)
        top_tags = [tag for tag, count in tag_counts.most_common(3)]

        notes = f"本周AI×Design领域热点聚焦在{', '.join(top_tags)}等方向。"

        if len(highlights) >= 3:
            notes += f"特别推荐关注本周精选的{len(highlights)}篇内容，它们代表了当前最值得关注的趋势和工具。"

        return notes

    def _get_subscription_info(self) -> str:
        """获取订阅信息"""
        return f"""
📮 **订阅方式**
- GitHub: 关注本项目获取最新周报
- Twitter: {config.TWITTER_HANDLE}

💬 **反馈与建议**
欢迎通过 Issue 或 Pull Request 参与贡献！
        """.strip()

    def generate_multiple_formats(self, links: List[Dict], output_dir: str,
                                   formats: List[str] = None,
                                   date_range: str = '', title: str = None) -> Dict:
        """
        生成多种格式

        Args:
            links: 链接列表
            output_dir: 输出目录
            formats: 格式列表（默认全部）
            date_range: 日期范围
            title: 标题

        Returns:
            生成结果
        """
        if not formats:
            formats = ['markdown', 'html', 'wechat']

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        results = {}
        for fmt in formats:
            filename = f'newsletter.{fmt}' if fmt != 'wechat' else 'newsletter_wechat.html'
            file_path = output_path / filename

            result = self.generate(
                links=links,
                output_path=str(file_path),
                format=fmt,
                date_range=date_range,
                title=title
            )

            results[fmt] = result

        return {
            'success': all(r.get('success') for r in results.values()),
            'results': results
        }
