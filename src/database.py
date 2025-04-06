import sqlite3
import json
from datetime import datetime
import logging
import os
from typing import Optional, List, Dict, Union
from contextlib import contextmanager
from config import SETTLEMENTS

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), 'weather_bot.db')
        self.conn = None
        self.create_tables()
        self.backup_dir = "backups"
        
        # Create backup directory if it doesn't exist
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

    @contextmanager
    def get_connection(self):
        """Get database connection using context manager"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            yield conn
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def execute_query(self, query: str, params: tuple = None, fetch_all: bool = False) -> Optional[List[tuple]]:
        """Execute SQL query with error handling"""
        with self.get_connection() as conn:
            try:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                if fetch_all:
                    result = cursor.fetchall()
                else:
                    result = cursor.fetchone()
                    
                conn.commit()
                return result
            except sqlite3.Error as e:
                logger.error(f"Query execution error: {e}")
                conn.rollback()
                raise

    def create_backup(self):
        """Create database backup"""
        try:
            backup_file = os.path.join(
                self.backup_dir, 
                f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            )
            with self.get_connection() as conn:
                with open(backup_file, 'wb') as f:
                    for line in conn.iterdump():
                        f.write(f'{line}\n'.encode('utf-8'))
            logger.info(f"Database backup created: {backup_file}")
        except Exception as e:
            logger.error(f"Backup creation error: {e}")

    def create_tables(self):
        """Initialize database"""
        try:
            self.execute_query('''CREATE TABLE IF NOT EXISTS user_settings
                                (user_id INTEGER PRIMARY KEY,
                                 settlement TEXT,
                                 notifications TEXT,
                                 last_notification TIMESTAMP)''')
            logger.info("Database successfully initialized")
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            raise

    def validate_settlement(self, settlement: str) -> bool:
        """Validate settlement name"""
        return settlement in SETTLEMENTS

    def save_user_settlement(self, user_id: int, settlement: str):
        """Save user's selected settlement"""
        if not isinstance(user_id, int):
            raise ValueError("user_id must be an integer")
        if not self.validate_settlement(settlement):
            raise ValueError("Invalid settlement name")
            
        self.execute_query(
            'INSERT OR REPLACE INTO user_settings (user_id, settlement) VALUES (?, ?)',
            (user_id, settlement)
        )

    def get_user_settlement(self, user_id: int) -> Optional[str]:
        """Get user's selected settlement"""
        if not isinstance(user_id, int):
            raise ValueError("user_id must be an integer")
            
        result = self.execute_query(
            'SELECT settlement FROM user_settings WHERE user_id = ?',
            (user_id,)
        )
        return result[0] if result else None

    def validate_notification_times(self, times: List[str]) -> bool:
        """Validate notification times"""
        try:
            for time in times:
                hours, minutes = map(int, time.split(':'))
                if not (0 <= hours <= 23 and 0 <= minutes <= 59):
                    return False
            return True
        except ValueError:
            return False

    def save_user_notifications(self, user_id: int, notification_times: List[str]):
        """Save user's notification settings"""
        if not isinstance(user_id, int):
            raise ValueError("user_id must be an integer")
        if not self.validate_notification_times(notification_times):
            raise ValueError("Invalid notification time format")
            
        self.execute_query(
            'INSERT OR REPLACE INTO user_settings (user_id, notifications) VALUES (?, ?)',
            (user_id, json.dumps(notification_times))
        )

    def get_user_notifications(self, user_id: int) -> List[str]:
        """Get user's notification settings"""
        if not isinstance(user_id, int):
            raise ValueError("user_id must be an integer")
            
        result = self.execute_query(
            'SELECT notifications FROM user_settings WHERE user_id = ?',
            (user_id,)
        )
        return json.loads(result[0]) if result and result[0] else []

    def update_last_notification(self, user_id: int):
        """Update last notification time"""
        if not isinstance(user_id, int):
            raise ValueError("user_id must be an integer")
            
        self.execute_query(
            'UPDATE user_settings SET last_notification = ? WHERE user_id = ?',
            (datetime.now().isoformat(), user_id)
        )

    def get_users_for_notification(self, current_time: str) -> List[Dict[str, Union[int, str]]]:
        """Get list of users for notification"""
        if not self.validate_notification_times([current_time]):
            raise ValueError("Invalid time format")
            
        rows = self.execute_query(
            'SELECT user_id, settlement, notifications FROM user_settings WHERE notifications IS NOT NULL',
            fetch_all=True
        )
        
        users = []
        for row in rows:
            user_id, settlement, notifications = row
            notification_times = json.loads(notifications) if notifications else []
            if current_time in notification_times:
                users.append({"user_id": user_id, "settlement": settlement})
        return users

    def export_user_settings(self, user_id: int) -> Dict:
        """Export user settings"""
        if not isinstance(user_id, int):
            raise ValueError("user_id must be an integer")
            
        result = self.execute_query(
            'SELECT * FROM user_settings WHERE user_id = ?',
            (user_id,)
        )
        if result:
            return {
                "user_id": result[0],
                "settlement": result[1],
                "notifications": json.loads(result[2]) if result[2] else [],
                "last_notification": result[3]
            }
        return None

    def import_user_settings(self, settings: Dict):
        """Import user settings"""
        if not isinstance(settings.get("user_id"), int):
            raise ValueError("user_id must be an integer")
        if not self.validate_settlement(settings.get("settlement", "")):
            raise ValueError("Invalid settlement name")
        if not self.validate_notification_times(settings.get("notifications", [])):
            raise ValueError("Invalid notification time format")
            
        self.execute_query(
            '''INSERT OR REPLACE INTO user_settings 
               (user_id, settlement, notifications, last_notification)
               VALUES (?, ?, ?, ?)''',
            (
                settings["user_id"],
                settings["settlement"],
                json.dumps(settings["notifications"]),
                settings.get("last_notification")
            )
        ) 