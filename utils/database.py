"""
历史记录数据库管理
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from config import DATABASE_DIR


class HistoryDB:
    """历史记录数据库"""
    
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = DATABASE_DIR / "history.db"
        
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.init_database()
    
    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建历史记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prediction_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                model_path TEXT NOT NULL,
                source_path TEXT NOT NULL,
                source_type TEXT NOT NULL,
                result_path TEXT,
                parameters TEXT,
                success INTEGER NOT NULL,
                error_message TEXT,
                inference_time REAL,
                num_detections INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_record(self, record_data):
        """添加记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO prediction_history 
            (timestamp, model_path, source_path, source_type, result_path, 
             parameters, success, error_message, inference_time, num_detections)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            record_data.get('timestamp', datetime.now().isoformat()),
            record_data.get('model_path', ''),
            record_data.get('source_path', ''),
            record_data.get('source_type', ''),
            record_data.get('result_path', ''),
            json.dumps(record_data.get('parameters', {})),
            1 if record_data.get('success', True) else 0,
            record_data.get('error_message', ''),
            record_data.get('inference_time', 0.0),
            record_data.get('num_detections', 0)
        ))
        
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return record_id
    
    def get_all_records(self, limit=100, offset=0):
        """获取所有记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM prediction_history
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))
        
        columns = [desc[0] for desc in cursor.description]
        records = []
        
        for row in cursor.fetchall():
            record = dict(zip(columns, row))
            # 解析参数
            if record['parameters']:
                record['parameters'] = json.loads(record['parameters'])
            records.append(record)
        
        conn.close()
        return records
    
    def get_record(self, record_id):
        """获取单条记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM prediction_history WHERE id = ?
        ''', (record_id,))
        
        row = cursor.fetchone()
        if row:
            columns = [desc[0] for desc in cursor.description]
            record = dict(zip(columns, row))
            if record['parameters']:
                record['parameters'] = json.loads(record['parameters'])
        else:
            record = None
        
        conn.close()
        return record
    
    def search_records(self, keyword, limit=100):
        """搜索记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM prediction_history
            WHERE source_path LIKE ? OR model_path LIKE ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (f'%{keyword}%', f'%{keyword}%', limit))
        
        columns = [desc[0] for desc in cursor.description]
        records = []
        
        for row in cursor.fetchall():
            record = dict(zip(columns, row))
            if record['parameters']:
                record['parameters'] = json.loads(record['parameters'])
            records.append(record)
        
        conn.close()
        return records
    
    def delete_record(self, record_id):
        """删除记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM prediction_history WHERE id = ?
        ''', (record_id,))
        
        conn.commit()
        conn.close()
    
    def clear_all(self):
        """清空所有记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM prediction_history')
        
        conn.commit()
        conn.close()
    
    def get_statistics(self):
        """获取统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 总记录数
            cursor.execute('SELECT COUNT(*) FROM prediction_history')
            total = cursor.fetchone()[0]
            
            # 成功数
            cursor.execute('SELECT COUNT(*) FROM prediction_history WHERE success = 1')
            success = cursor.fetchone()[0]
            
            # 平均推理时间
            cursor.execute('SELECT AVG(inference_time) FROM prediction_history WHERE success = 1')
            avg_time = cursor.fetchone()[0] or 0.0
            
            # 总检测数
            cursor.execute('SELECT SUM(num_detections) FROM prediction_history WHERE success = 1')
            total_detections = cursor.fetchone()[0] or 0
            
            stats = {
                'total': total,
                'success': success,
                'failed': total - success,
                'avg_inference_time': avg_time,
                'total_detections': total_detections
            }
            
            return stats
            
        except Exception as e:
            # 静默处理错误，返回默认值
            return {
                'total': 0,
                'success': 0,
                'failed': 0,
                'avg_inference_time': 0.0,
                'total_detections': 0
            }
        finally:
            conn.close()
