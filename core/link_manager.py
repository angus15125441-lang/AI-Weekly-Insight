"""
AI×Design Newsletter Generator - Link Manager
链接管理模块
"""

import json
import csv
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from storage.database import Database
import config


class LinkManager:
    """链接管理器"""

    def __init__(self):
        self.db = Database()

    def add_link(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        添加链接

        Args:
            url: 链接 URL
            **kwargs: 其他字段（title, category, tags, notes等）

        Returns:
            添加结果
        """
        with self.db as db:
            # 检查是否已存在
            existing = db.get_link_by_url(url)
            if existing:
                return {
                    'success': False,
                    'message': f'链接已存在 (ID: {existing["id"]})',
                    'link_id': existing['id'],
                    'link': existing
                }

            # 添加新链接
            link_id = db.add_link(url, **kwargs)
            link = db.get_link(link_id)

            return {
                'success': True,
                'message': '链接添加成功',
                'link_id': link_id,
                'link': link
            }

    def import_from_file(self, file_path: str, format: str = 'txt') -> Dict[str, Any]:
        """
        从文件导入链接

        Args:
            file_path: 文件路径
            format: 文件格式 (txt, csv, json)

        Returns:
            导入结果统计
        """
        file_path = Path(file_path)
        if not file_path.exists():
            return {'success': False, 'message': f'文件不存在: {file_path}'}

        results = {
            'success': True,
            'total': 0,
            'added': 0,
            'skipped': 0,
            'errors': []
        }

        try:
            if format == 'txt':
                results.update(self._import_from_txt(file_path))
            elif format == 'csv':
                results.update(self._import_from_csv(file_path))
            elif format == 'json':
                results.update(self._import_from_json(file_path))
            else:
                return {'success': False, 'message': f'不支持的格式: {format}'}

        except Exception as e:
            return {'success': False, 'message': f'导入失败: {str(e)}'}

        return results

    def _import_from_txt(self, file_path: Path) -> Dict[str, Any]:
        """从 TXT 文件导入"""
        results = {'total': 0, 'added': 0, 'skipped': 0, 'errors': []}

        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                # 跳过空行和注释
                if not line or line.startswith('#'):
                    continue

                results['total'] += 1
                url = line.split()[0]  # 取第一个词作为 URL

                try:
                    result = self.add_link(url)
                    if result['success']:
                        results['added'] += 1
                    else:
                        results['skipped'] += 1
                except Exception as e:
                    results['errors'].append(f'Line {line_num}: {str(e)}')

        return results

    def _import_from_csv(self, file_path: Path) -> Dict[str, Any]:
        """从 CSV 文件导入"""
        results = {'total': 0, 'added': 0, 'skipped': 0, 'errors': []}

        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row_num, row in enumerate(reader, 2):  # 从第2行开始（第1行是标题）
                if not row.get('url'):
                    continue

                results['total'] += 1
                url = row['url']

                # 准备其他字段
                kwargs = {}
                for key in ['title', 'category', 'notes', 'author', 'source']:
                    if row.get(key):
                        kwargs[key] = row[key]

                # 处理 tags
                if row.get('tags'):
                    kwargs['tags'] = [t.strip() for t in row['tags'].split(',')]

                try:
                    result = self.add_link(url, **kwargs)
                    if result['success']:
                        results['added'] += 1
                    else:
                        results['skipped'] += 1
                except Exception as e:
                    results['errors'].append(f'Row {row_num}: {str(e)}')

        return results

    def _import_from_json(self, file_path: Path) -> Dict[str, Any]:
        """从 JSON 文件导入"""
        results = {'total': 0, 'added': 0, 'skipped': 0, 'errors': []}

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        links = data if isinstance(data, list) else data.get('links', [])

        for idx, item in enumerate(links, 1):
            if not item.get('url'):
                continue

            results['total'] += 1
            url = item['url']

            # 准备其他字段
            kwargs = {k: v for k, v in item.items() if k != 'url'}

            try:
                result = self.add_link(url, **kwargs)
                if result['success']:
                    results['added'] += 1
                else:
                    results['skipped'] += 1
            except Exception as e:
                results['errors'].append(f'Item {idx}: {str(e)}')

        return results

    def get_link(self, link_id: int) -> Optional[Dict]:
        """获取链接详情"""
        with self.db as db:
            link = db.get_link(link_id)
            if link and link.get('tags'):
                try:
                    link['tags'] = json.loads(link['tags'])
                except:
                    pass
            if link and link.get('analysis_result'):
                try:
                    link['analysis_result'] = json.loads(link['analysis_result'])
                except:
                    pass
            return link

    def update_link(self, link_id: int, **kwargs) -> bool:
        """更新链接"""
        with self.db as db:
            return db.update_link(link_id, **kwargs)

    def delete_link(self, link_id: int) -> bool:
        """删除链接"""
        with self.db as db:
            return db.delete_link(link_id)

    def list_links(self, category: Optional[str] = None,
                   status: Optional[str] = None,
                   limit: Optional[int] = None) -> List[Dict]:
        """列出链接"""
        with self.db as db:
            links = db.list_links(category=category, status=status, limit=limit)
            # 解析 JSON 字段
            for link in links:
                if link.get('tags'):
                    try:
                        link['tags'] = json.loads(link['tags'])
                    except:
                        link['tags'] = []
                if link.get('analysis_result'):
                    try:
                        link['analysis_result'] = json.loads(link['analysis_result'])
                    except:
                        pass
            return links

    def search_links(self, keyword: str) -> List[Dict]:
        """搜索链接"""
        with self.db as db:
            return db.search_links(keyword)

    def get_links_by_date_range(self, start_date: str = None, end_date: str = None) -> List[Dict]:
        """
        获取日期范围内的链接

        Args:
            start_date: 开始日期 (YYYY-MM-DD) 或 'this-week', 'last-week'
            end_date: 结束日期 (YYYY-MM-DD)
        """
        # 处理特殊日期范围
        if start_date == 'this-week':
            today = datetime.now()
            start = today - timedelta(days=today.weekday())
            start_date = start.strftime('%Y-%m-%d')
            end_date = today.strftime('%Y-%m-%d')
        elif start_date == 'last-week':
            today = datetime.now()
            start = today - timedelta(days=today.weekday() + 7)
            end = start + timedelta(days=6)
            start_date = start.strftime('%Y-%m-%d')
            end_date = end.strftime('%Y-%m-%d')

        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')

        with self.db as db:
            links = db.get_links_by_date_range(start_date, end_date)
            # 解析 JSON 字段
            for link in links:
                if link.get('tags'):
                    try:
                        link['tags'] = json.loads(link['tags'])
                    except:
                        link['tags'] = []
            return links

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.db as db:
            return db.get_stats()

    def export_links(self, output_path: str, format: str = 'csv',
                     category: Optional[str] = None) -> bool:
        """
        导出链接

        Args:
            output_path: 输出文件路径
            format: 导出格式 (csv, json)
            category: 过滤分类（可选）
        """
        links = self.list_links(category=category)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            if format == 'csv':
                self._export_to_csv(links, output_path)
            elif format == 'json':
                self._export_to_json(links, output_path)
            else:
                return False
            return True
        except Exception as e:
            print(f"导出失败: {e}")
            return False

    def _export_to_csv(self, links: List[Dict], output_path: Path):
        """导出为 CSV"""
        fieldnames = ['id', 'url', 'title', 'category', 'tags', 'rating',
                      'added_at', 'status', 'description']

        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()

            for link in links:
                # 将 tags 转为字符串
                if isinstance(link.get('tags'), list):
                    link['tags'] = ', '.join(link['tags'])
                writer.writerow({k: link.get(k, '') for k in fieldnames})

    def _export_to_json(self, links: List[Dict], output_path: Path):
        """导出为 JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({'links': links, 'exported_at': datetime.now().isoformat()},
                      f, indent=2, ensure_ascii=False)
