"""
AI×Design Newsletter Generator - Content Fetcher
网页内容抓取模块
"""

import requests
from bs4 import BeautifulSoup
from readability import Document
import html2text
from typing import Dict, Optional
from urllib.parse import urlparse
import time
import config


class ContentFetcher:
    """网页内容抓取器"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.USER_AGENT
        })
        self.timeout = config.FETCH_TIMEOUT
        self.max_retries = config.MAX_RETRIES

    def fetch_url(self, url: str) -> Dict[str, any]:
        """
        抓取 URL 内容

        Args:
            url: 目标 URL

        Returns:
            包含标题、描述、内容等的字典
        """
        result = {
            'success': False,
            'url': url,
            'title': '',
            'description': '',
            'content': '',
            'author': '',
            'published_date': '',
            'source': '',
            'error': None
        }

        try:
            # 获取网页源码
            html = self._fetch_html(url)
            if not html:
                result['error'] = '无法获取网页内容'
                return result

            # 解析域名作为来源
            parsed_url = urlparse(url)
            result['source'] = parsed_url.netloc

            # 使用 BeautifulSoup 解析
            soup = BeautifulSoup(html, 'lxml')

            # 提取元数据
            result['title'] = self._extract_title(soup)
            result['description'] = self._extract_description(soup)
            result['author'] = self._extract_author(soup)
            result['published_date'] = self._extract_date(soup)

            # 提取正文内容（使用 Readability）
            result['content'] = self._extract_content(html, url)

            result['success'] = True

        except Exception as e:
            result['error'] = str(e)

        return result

    def _fetch_html(self, url: str) -> Optional[str]:
        """获取网页 HTML"""
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                response.encoding = response.apparent_encoding  # 自动检测编码
                return response.text
            except requests.RequestException as e:
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                    continue
                else:
                    return None
        return None

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取标题"""
        # 优先顺序：og:title > twitter:title > h1 > title
        title = None

        # Open Graph
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            title = og_title['content']

        # Twitter Card
        if not title:
            twitter_title = soup.find('meta', attrs={'name': 'twitter:title'})
            if twitter_title and twitter_title.get('content'):
                title = twitter_title['content']

        # H1
        if not title:
            h1 = soup.find('h1')
            if h1:
                title = h1.get_text(strip=True)

        # Title tag
        if not title:
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text(strip=True)

        return title or 'Untitled'

    def _extract_description(self, soup: BeautifulSoup) -> str:
        """提取描述"""
        # 优先顺序：og:description > twitter:description > meta description
        description = None

        # Open Graph
        og_desc = soup.find('meta', property='og:description')
        if og_desc and og_desc.get('content'):
            description = og_desc['content']

        # Twitter Card
        if not description:
            twitter_desc = soup.find('meta', attrs={'name': 'twitter:description'})
            if twitter_desc and twitter_desc.get('content'):
                description = twitter_desc['content']

        # Meta description
        if not description:
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                description = meta_desc['content']

        return description or ''

    def _extract_author(self, soup: BeautifulSoup) -> str:
        """提取作者"""
        author = None

        # 常见的作者标签
        author_selectors = [
            ('meta', {'name': 'author'}),
            ('meta', {'property': 'article:author'}),
            ('meta', {'name': 'twitter:creator'}),
            ('span', {'class': 'author'}),
            ('a', {'rel': 'author'}),
        ]

        for tag, attrs in author_selectors:
            element = soup.find(tag, attrs)
            if element:
                if tag == 'meta':
                    author = element.get('content')
                else:
                    author = element.get_text(strip=True)
                if author:
                    break

        return author or ''

    def _extract_date(self, soup: BeautifulSoup) -> str:
        """提取发布日期"""
        date = None

        # 常见的日期标签
        date_selectors = [
            ('meta', {'property': 'article:published_time'}),
            ('meta', {'name': 'pubdate'}),
            ('meta', {'name': 'publishdate'}),
            ('time', {'datetime': True}),
        ]

        for tag, attrs in date_selectors:
            element = soup.find(tag, attrs)
            if element:
                if tag == 'meta':
                    date = element.get('content')
                elif tag == 'time':
                    date = element.get('datetime') or element.get_text(strip=True)
                if date:
                    break

        return date or ''

    def _extract_content(self, html: str, url: str) -> str:
        """提取正文内容"""
        try:
            # 使用 Readability 提取主要内容
            doc = Document(html)
            content_html = doc.summary()

            # 转换为纯文本
            h2t = html2text.HTML2Text()
            h2t.ignore_links = False
            h2t.ignore_images = True
            h2t.ignore_emphasis = False
            h2t.body_width = 0  # 不自动换行

            content_text = h2t.handle(content_html)

            # 限制长度
            if len(content_text) > config.MAX_CONTENT_LENGTH:
                content_text = content_text[:config.MAX_CONTENT_LENGTH] + '...'

            return content_text.strip()

        except Exception as e:
            return ''

    def fetch_multiple(self, urls: list) -> Dict[str, Dict]:
        """
        批量抓取多个 URL

        Args:
            urls: URL 列表

        Returns:
            URL 到结果的映射
        """
        results = {}
        for url in urls:
            print(f"抓取: {url}")
            results[url] = self.fetch_url(url)
            time.sleep(1)  # 避免请求过快
        return results


def fetch_url(url: str) -> Dict:
    """便捷函数：抓取单个 URL"""
    fetcher = ContentFetcher()
    return fetcher.fetch_url(url)
