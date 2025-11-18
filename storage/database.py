"""
AI×Design Newsletter Generator - Database Module
数据库管理模块
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import config


class Database:
    """SQLite 数据库管理类"""

    def __init__(self, db_path: Optional[Path] = None):
        """初始化数据库连接"""
        self.db_path = db_path or config.DATABASE_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self.cursor = None

    def connect(self):
        """连接数据库"""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row  # 允许通过列名访问
        self.cursor = self.conn.cursor()
        return self

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        """上下文管理器入口"""
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()

    def init_database(self):
        """初始化数据库结构"""
        # Links 表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                title TEXT,
                description TEXT,
                content TEXT,
                category TEXT,
                tags TEXT,
                analysis_result TEXT,
                rating INTEGER,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                analyzed_at TIMESTAMP,
                published_date TEXT,
                author TEXT,
                source TEXT,
                status TEXT DEFAULT 'pending',
                notes TEXT
            )
        ''')

        # Newsletters 表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS newsletters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                date_range_start TEXT,
                date_range_end TEXT,
                content TEXT,
                format TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                published BOOLEAN DEFAULT 0,
                metadata TEXT
            )
        ''')

        # Newsletter_Links 关联表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS newsletter_links (
                newsletter_id INTEGER,
                link_id INTEGER,
                FOREIGN KEY (newsletter_id) REFERENCES newsletters(id),
                FOREIGN KEY (link_id) REFERENCES links(id),
                PRIMARY KEY (newsletter_id, link_id)
            )
        ''')

        # API Usage 表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation TEXT,
                tokens_used INTEGER,
                cost REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                model TEXT,
                success BOOLEAN DEFAULT 1
            )
        ''')

        self.conn.commit()
        return True

    # ===== Links 操作 =====

    def add_link(self, url: str, **kwargs) -> int:
        """添加新链接"""
        fields = ['url']
        values = [url]
        placeholders = ['?']

        for key, value in kwargs.items():
            if key in ['title', 'description', 'content', 'category', 'tags',
                       'author', 'source', 'published_date', 'notes']:
                fields.append(key)
                if key == 'tags' and isinstance(value, list):
                    values.append(json.dumps(value))
                else:
                    values.append(value)
                placeholders.append('?')

        query = f'''
            INSERT INTO links ({', '.join(fields)})
            VALUES ({', '.join(placeholders)})
        '''

        try:
            self.cursor.execute(query, values)
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            # URL 已存在
            return self.get_link_by_url(url)['id']

    def get_link(self, link_id: int) -> Optional[Dict]:
        """获取链接详情"""
        self.cursor.execute('SELECT * FROM links WHERE id = ?', (link_id,))
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def get_link_by_url(self, url: str) -> Optional[Dict]:
        """通过URL获取链接"""
        self.cursor.execute('SELECT * FROM links WHERE url = ?', (url,))
        row = self.cursor.fetchone()
        return dict(row) if row else None

    def update_link(self, link_id: int, **kwargs):
        """更新链接信息"""
        updates = []
        values = []

        for key, value in kwargs.items():
            if key == 'tags' and isinstance(value, list):
                updates.append(f'{key} = ?')
                values.append(json.dumps(value))
            else:
                updates.append(f'{key} = ?')
                values.append(value)

        if not updates:
            return False

        values.append(link_id)
        query = f'UPDATE links SET {", ".join(updates)} WHERE id = ?'

        self.cursor.execute(query, values)
        self.conn.commit()
        return True

    def delete_link(self, link_id: int):
        """删除链接"""
        self.cursor.execute('DELETE FROM links WHERE id = ?', (link_id,))
        self.conn.commit()
        return True

    def list_links(self, category: Optional[str] = None,
                   status: Optional[str] = None,
                   limit: Optional[int] = None,
                   offset: int = 0) -> List[Dict]:
        """列出链接"""
        query = 'SELECT * FROM links WHERE 1=1'
        params = []

        if category:
            query += ' AND category = ?'
            params.append(category)

        if status:
            query += ' AND status = ?'
            params.append(status)

        query += ' ORDER BY added_at DESC'

        if limit:
            query += ' LIMIT ? OFFSET ?'
            params.extend([limit, offset])

        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]

    def search_links(self, keyword: str) -> List[Dict]:
        """搜索链接"""
        query = '''
            SELECT * FROM links
            WHERE title LIKE ? OR description LIKE ? OR content LIKE ? OR tags LIKE ?
            ORDER BY added_at DESC
        '''
        pattern = f'%{keyword}%'
        self.cursor.execute(query, (pattern, pattern, pattern, pattern))
        return [dict(row) for row in self.cursor.fetchall()]

    def get_links_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """获取日期范围内的链接"""
        query = '''
            SELECT * FROM links
            WHERE date(added_at) BETWEEN date(?) AND date(?)
            ORDER BY added_at DESC
        '''
        self.cursor.execute(query, (start_date, end_date))
        return [dict(row) for row in self.cursor.fetchall()]

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {}

        # 总数
        self.cursor.execute('SELECT COUNT(*) as total FROM links')
        stats['total'] = self.cursor.fetchone()['total']

        # 按状态统计
        self.cursor.execute('''
            SELECT status, COUNT(*) as count
            FROM links
            GROUP BY status
        ''')
        stats['by_status'] = {row['status']: row['count'] for row in self.cursor.fetchall()}

        # 按分类统计
        self.cursor.execute('''
            SELECT category, COUNT(*) as count
            FROM links
            WHERE category IS NOT NULL
            GROUP BY category
            ORDER BY count DESC
        ''')
        stats['by_category'] = {row['category']: row['count'] for row in self.cursor.fetchall()}

        return stats

    # ===== Newsletters 操作 =====

    def create_newsletter(self, title: str, content: str, format: str = 'markdown', **kwargs) -> int:
        """创建周报"""
        fields = ['title', 'content', 'format']
        values = [title, content, format]
        placeholders = ['?', '?', '?']

        for key in ['date_range_start', 'date_range_end', 'metadata']:
            if key in kwargs:
                fields.append(key)
                if key == 'metadata':
                    values.append(json.dumps(kwargs[key]))
                else:
                    values.append(kwargs[key])
                placeholders.append('?')

        query = f'''
            INSERT INTO newsletters ({', '.join(fields)})
            VALUES ({', '.join(placeholders)})
        '''

        self.cursor.execute(query, values)
        self.conn.commit()
        return self.cursor.lastrowid

    def link_newsletter_to_links(self, newsletter_id: int, link_ids: List[int]):
        """关联周报和链接"""
        for link_id in link_ids:
            self.cursor.execute('''
                INSERT OR IGNORE INTO newsletter_links (newsletter_id, link_id)
                VALUES (?, ?)
            ''', (newsletter_id, link_id))
        self.conn.commit()

    # ===== API Usage 操作 =====

    def log_api_usage(self, operation: str, tokens_used: int = 0,
                      cost: float = 0.0, model: str = '', success: bool = True):
        """记录 API 使用"""
        self.cursor.execute('''
            INSERT INTO api_usage (operation, tokens_used, cost, model, success)
            VALUES (?, ?, ?, ?, ?)
        ''', (operation, tokens_used, cost, model, success))
        self.conn.commit()

    def get_api_usage_stats(self, days: int = 30) -> Dict[str, Any]:
        """获取 API 使用统计"""
        query = '''
            SELECT
                COUNT(*) as total_calls,
                SUM(tokens_used) as total_tokens,
                SUM(cost) as total_cost,
                AVG(tokens_used) as avg_tokens
            FROM api_usage
            WHERE timestamp >= datetime('now', '-' || ? || ' days')
        '''
        self.cursor.execute(query, (days,))
        row = self.cursor.fetchone()
        return dict(row) if row else {}


def init_db():
    """初始化数据库（便捷函数）"""
    with Database() as db:
        db.init_database()
        return True
