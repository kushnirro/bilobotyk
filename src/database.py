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
        
        # Створюємо директорію для бекапів якщо її немає
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

    @contextmanager
    def get_connection(self):
        """Отримати з'єднання з базою даних використовуючи контекстний менеджер"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            yield conn
        except sqlite3.Error as e:
            logger.error(f"Помилка підключення до бази даних: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def execute_query(self, query: str, params: tuple = None, fetch_all: bool = False) -> Optional[List[tuple]]:
        """Виконати SQL запит з обробкою помилок"""
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
                logger.error(f"Помилка виконання запиту: {e}")
                conn.rollback()
                raise

    def create_backup(self):
        """Створити резервну копію бази даних"""
        try:
            backup_file = os.path.join(
                self.backup_dir, 
                f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            )
            with self.get_connection() as conn:
                with open(backup_file, 'wb') as f:
                    for line in conn.iterdump():
                        f.write(f'{line}\n'.encode('utf-8'))
            logger.info(f"Створено резервну копію бази даних: {backup_file}")
        except Exception as e:
            logger.error(f"Помилка створення резервної копії: {e}")

    def create_tables(self):
        """Ініціалізація бази даних"""
        try:
            self.execute_query('''CREATE TABLE IF NOT EXISTS user_settings
                                (user_id INTEGER PRIMARY KEY,
                                 settlement TEXT,
                                 notifications TEXT,
                                 last_notification TIMESTAMP)''')
            logger.info("База даних успішно ініціалізована")
        except sqlite3.Error as e:
            logger.error(f"Помилка ініціалізації бази даних: {e}")
            raise

    def validate_settlement(self, settlement: str) -> bool:
        """Перевірка валідності назви населеного пункту"""
        return settlement in SETTLEMENTS

    def save_user_settlement(self, user_id: int, settlement: str):
        """Зберегти вибраний населений пункт користувача"""
        if not isinstance(user_id, int):
            raise ValueError("user_id повинен бути цілим числом")
        if not self.validate_settlement(settlement):
            raise ValueError("Невірна назва населеного пункту")
            
        self.execute_query(
            'INSERT OR REPLACE INTO user_settings (user_id, settlement) VALUES (?, ?)',
            (user_id, settlement)
        )

    def get_user_settlement(self, user_id: int) -> Optional[str]:
        """Отримати вибраний населений пункт користувача"""
        if not isinstance(user_id, int):
            raise ValueError("user_id повинен бути цілим числом")
            
        result = self.execute_query(
            'SELECT settlement FROM user_settings WHERE user_id = ?',
            (user_id,)
        )
        return result[0] if result else None

    def validate_notification_times(self, times: List[str]) -> bool:
        """Перевірка валідності часу сповіщень"""
        try:
            for time in times:
                hours, minutes = map(int, time.split(':'))
                if not (0 <= hours <= 23 and 0 <= minutes <= 59):
                    return False
            return True
        except ValueError:
            return False

    def save_user_notifications(self, user_id: int, notification_times: List[str]):
        """Зберегти налаштування сповіщень користувача"""
        if not isinstance(user_id, int):
            raise ValueError("user_id повинен бути цілим числом")
        if not self.validate_notification_times(notification_times):
            raise ValueError("Невірний формат часу сповіщень")
            
        self.execute_query(
            'INSERT OR REPLACE INTO user_settings (user_id, notifications) VALUES (?, ?)',
            (user_id, json.dumps(notification_times))
        )

    def get_user_notifications(self, user_id: int) -> List[str]:
        """Отримати налаштування сповіщень користувача"""
        if not isinstance(user_id, int):
            raise ValueError("user_id повинен бути цілим числом")
            
        result = self.execute_query(
            'SELECT notifications FROM user_settings WHERE user_id = ?',
            (user_id,)
        )
        return json.loads(result[0]) if result and result[0] else []

    def update_last_notification(self, user_id: int):
        """Оновити час останнього сповіщення"""
        if not isinstance(user_id, int):
            raise ValueError("user_id повинен бути цілим числом")
            
        self.execute_query(
            'UPDATE user_settings SET last_notification = ? WHERE user_id = ?',
            (datetime.now().isoformat(), user_id)
        )

    def get_users_for_notification(self, current_time: str) -> List[Dict[str, Union[int, str]]]:
        """Отримати список користувачів для сповіщення"""
        if not self.validate_notification_times([current_time]):
            raise ValueError("Невірний формат часу")
            
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
        """Експорт налаштувань користувача"""
        if not isinstance(user_id, int):
            raise ValueError("user_id повинен бути цілим числом")
            
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
        """Імпорт налаштувань користувача"""
        if not isinstance(settings.get("user_id"), int):
            raise ValueError("user_id повинен бути цілим числом")
        if not self.validate_settlement(settings.get("settlement", "")):
            raise ValueError("Невірна назва населеного пункту")
        if not self.validate_notification_times(settings.get("notifications", [])):
            raise ValueError("Невірний формат часу сповіщень")
            
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