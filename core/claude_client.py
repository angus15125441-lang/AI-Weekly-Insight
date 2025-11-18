"""
AI×Design Newsletter Generator - Claude API Client
Claude API 客户端模块（支持模拟模式）
"""

import json
import random
from typing import Dict, List, Optional
from pathlib import Path
import config


class ClaudeClient:
    """Claude API 客户端（支持真实和模拟两种模式）"""

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化客户端

        Args:
            api_key: Claude API Key（如果为空则使用配置或模拟模式）
        """
        self.api_key = api_key or config.ANTHROPIC_API_KEY
        self.model = config.CLAUDE_MODEL
        self.use_mock = config.USE_MOCK_DATA or not self.api_key

        if not self.use_mock:
            try:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=self.api_key)
            except Exception as e:
                print(f"⚠️  Claude API 初始化失败，切换到模拟模式: {e}")
                self.use_mock = True

    def analyze_content(self, title: str, url: str, content: str,
                        source: str = '') -> Dict:
        """
        分析内容

        Args:
            title: 标题
            url: URL
            content: 内容
            source: 来源

        Returns:
            分析结果字典
        """
        if self.use_mock:
            return self._mock_analyze_content(title, url, content, source)
        else:
            return self._real_analyze_content(title, url, content, source)

    def _real_analyze_content(self, title: str, url: str,
                               content: str, source: str) -> Dict:
        """真实的 API 调用"""
        try:
            # 加载提示词模版
            prompt_file = config.PROMPTS_DIR / 'analyze_content.txt'
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt_template = f.read()

            # 填充提示词
            prompt = prompt_template.format(
                title=title,
                url=url,
                source=source,
                content=content[:5000]  # 限制长度
            )

            # 调用 API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # 解析响应
            result_text = response.content[0].text

            # 提取 JSON（可能包含在代码块中）
            if '```json' in result_text:
                result_text = result_text.split('```json')[1].split('```')[0]
            elif '```' in result_text:
                result_text = result_text.split('```')[1].split('```')[0]

            analysis = json.loads(result_text.strip())

            return {
                'success': True,
                'analysis': analysis,
                'tokens_used': response.usage.input_tokens + response.usage.output_tokens,
                'mode': 'AI'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'mode': 'AI'
            }

    def _mock_analyze_content(self, title: str, url: str,
                              content: str, source: str) -> Dict:
        """模拟模式（返回示例数据）"""
        # 基于标题和内容关键词智能推断分类
        title_lower = (title or '').lower()
        content_lower = (content or '').lower()

        # 智能分类推断
        category = 'insights'  # 默认
        tags = []
        rating = 3  # 默认

        # 工具和产品
        if any(kw in title_lower + content_lower for kw in
               ['midjourney', 'stable diffusion', 'dalle', 'figma', 'tool', 'plugin', '插件', '工具']):
            category = 'tools'
            tags = ['AI工具', 'AIGC']
            rating = 4

        # 教程
        elif any(kw in title_lower for kw in
                 ['tutorial', 'guide', 'how to', '教程', '指南', '入门']):
            category = 'tutorials'
            tags = ['教程', '学习']
            rating = 4

        # 趋势
        elif any(kw in title_lower + content_lower for kw in
                 ['trend', 'future', '趋势', '未来', '展望', '2024', '2025']):
            category = 'trends'
            tags = ['设计趋势', '行业洞察']
            rating = 4

        # 研究
        elif any(kw in title_lower + content_lower for kw in
                 ['research', 'paper', 'study', '研究', '论文']):
            category = 'research'
            tags = ['研究', '技术']
            rating = 3

        # 视频
        elif any(kw in title_lower + url for kw in
                 ['youtube', 'video', 'bilibili', '视频']):
            category = 'videos'
            tags = ['视频', '教程']
            rating = 3

        # 新闻
        elif any(kw in title_lower for kw in
                 ['update', 'release', 'launch', '发布', '更新', '新功能']):
            category = 'news'
            tags = ['产品更新', '新闻']
            rating = 4

        # 添加通用标签
        if 'midjourney' in title_lower + content_lower:
            tags.append('Midjourney')
        if 'ai' in title_lower + content_lower or 'artificial intelligence' in content_lower:
            tags.append('AI')
        if 'design' in title_lower + content_lower or '设计' in title_lower + content_lower:
            tags.append('设计')
        if 'prompt' in title_lower + content_lower or '提示词' in title_lower + content_lower:
            tags.append('提示词工程')

        # 确保至少有3个标签
        if len(tags) < 3:
            generic_tags = ['AI×Design', '创意', '工具应用']
            tags.extend([t for t in generic_tags if t not in tags])

        tags = tags[:5]  # 最多5个

        # 生成摘要
        summary = f"本文介绍了{title[:30]}的相关内容，"
        if category == 'tools':
            summary += "展示了AI设计工具的最新发展和实用功能。"
        elif category == 'tutorials':
            summary += "提供了详细的操作指南和实践技巧。"
        elif category == 'trends':
            summary += "分析了当前行业趋势和未来发展方向。"
        elif category == 'research':
            summary += "探讨了相关技术研究和学术成果。"
        elif category == 'videos':
            summary += "通过视频形式直观展示了具体应用。"
        elif category == 'news':
            summary += "报道了最新的产品更新和行业动态。"
        else:
            summary += "分享了有价值的见解和思考。"

        # 生成亮点
        highlights = [
            f"{title[:40]}的核心价值在于其创新性和实用性",
            f"内容涵盖了{category_names.get(category, '相关领域')}的关键要点",
            f"适合关注{', '.join(tags[:2])}的设计师和创作者"
        ]

        analysis = {
            'summary': summary,
            'content_type': category_types.get(category, '深度分析'),
            'category': category,
            'tags': tags,
            'rating': rating,
            'highlights': highlights
        }

        return {
            'success': True,
            'analysis': analysis,
            'tokens_used': 0,
            'mode': 'MOCK',
            'note': '⚠️  当前为模拟模式，配置 API Key 后可使用真实 AI 分析'
        }

    def generate_newsletter(self, links: List[Dict], date_range: str = '') -> Dict:
        """
        生成周报

        Args:
            links: 链接列表
            date_range: 日期范围

        Returns:
            生成结果
        """
        if self.use_mock:
            return self._mock_generate_newsletter(links, date_range)
        else:
            return self._real_generate_newsletter(links, date_range)

    def _real_generate_newsletter(self, links: List[Dict], date_range: str) -> Dict:
        """真实的周报生成"""
        try:
            # 准备内容列表
            content_items = []
            categories = set()

            for link in links:
                analysis = link.get('analysis_result')
                if isinstance(analysis, str):
                    analysis = json.loads(analysis)

                item = {
                    'title': link.get('title', 'Untitled'),
                    'url': link.get('url', ''),
                    'summary': analysis.get('summary', '') if analysis else link.get('description', ''),
                    'category': analysis.get('category', 'insights') if analysis else 'insights',
                    'tags': analysis.get('tags', []) if analysis else [],
                    'rating': analysis.get('rating', 3) if analysis else 3
                }
                content_items.append(item)
                categories.add(item['category'])

            # 加载提示词
            prompt_file = config.PROMPTS_DIR / 'generate_newsletter.txt'
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt_template = f.read()

            prompt = prompt_template.format(
                content_list=json.dumps(content_items, ensure_ascii=False, indent=2),
                date_range=date_range,
                total_links=len(links),
                categories=', '.join(categories)
            )

            # 调用 API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            newsletter_content = response.content[0].text

            return {
                'success': True,
                'content': newsletter_content,
                'tokens_used': response.usage.input_tokens + response.usage.output_tokens,
                'mode': 'AI'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'mode': 'AI'
            }

    def _mock_generate_newsletter(self, links: List[Dict], date_range: str) -> Dict:
        """模拟周报生成（使用模版）"""
        # 这个方法会在后面的generator.py中实现更完整的逻辑
        return {
            'success': True,
            'content': '# 周报内容（模拟模式）\n\n将由 generator.py 生成完整内容',
            'tokens_used': 0,
            'mode': 'MOCK',
            'note': '⚠️  当前为模拟模式，使用模版生成。配置 API Key 后可使用 AI 生成更智能的周报'
        }


# 辅助映射
category_names = {
    'tools': '工具与产品',
    'tutorials': '教程与指南',
    'trends': '设计趋势',
    'insights': '洞察与思考',
    'research': '研究与技术',
    'videos': '视频与演示',
    'news': '新闻与更新'
}

category_types = {
    'tools': '工具发布',
    'tutorials': '实用教程',
    'trends': '趋势分析',
    'insights': '深度洞察',
    'research': '研究论文',
    'videos': '视频演示',
    'news': '产品更新'
}
