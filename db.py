"""
Модуль для работы с базой данных SQLite.
Инкапсулирует все операции с БД.
"""
import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple


class Database:
    """Класс для работы с базой данных SQLite."""
    
    def __init__(self, db_path: str = "chatlist.db"):
        """
        Инициализация подключения к БД.
        
        Args:
            db_path: Путь к файлу базы данных
        """
        self.db_path = db_path
        self.conn = None
        self.init_db()
    
    def get_connection(self):
        """Получить соединение с БД."""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def init_db(self):
        """Инициализация БД и создание таблиц."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Таблица промтов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                prompt TEXT NOT NULL,
                tags TEXT
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_prompts_date ON prompts(date)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_prompts_tags ON prompts(tags)
        """)
        
        # Таблица моделей
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                api_url TEXT NOT NULL,
                api_id TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_models_name ON models(name)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_models_active ON models(is_active)
        """)
        
        # Таблица результатов
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt_id INTEGER NOT NULL,
                model_id INTEGER NOT NULL,
                response TEXT NOT NULL,
                selected INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (prompt_id) REFERENCES prompts(id) ON DELETE CASCADE,
                FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE SET NULL
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_results_prompt_id ON results(prompt_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_results_model_id ON results(model_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_results_created_at ON results(created_at)
        """)
        
        # Таблица настроек
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL UNIQUE,
                value TEXT
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_settings_key ON settings(key)
        """)
        
        conn.commit()
    
    # ========== Методы для работы с промтами ==========
    
    def create_prompt(self, prompt: str, tags: Optional[str] = None) -> int:
        """
        Создать новый промт.
        
        Args:
            prompt: Текст промта
            tags: Теги через запятую
            
        Returns:
            ID созданного промта
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO prompts (date, prompt, tags) VALUES (?, ?, ?)",
            (date, prompt, tags)
        )
        conn.commit()
        return cursor.lastrowid
    
    def get_prompts(self, search: Optional[str] = None, 
                    tags: Optional[str] = None,
                    order_by: str = "date DESC") -> List[Dict]:
        """
        Получить список промтов.
        
        Args:
            search: Поиск по тексту промта
            tags: Фильтр по тегам
            order_by: Поле и направление сортировки
            
        Returns:
            Список словарей с данными промтов
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM prompts WHERE 1=1"
        params = []
        
        if search:
            query += " AND prompt LIKE ?"
            params.append(f"%{search}%")
        
        if tags:
            query += " AND tags LIKE ?"
            params.append(f"%{tags}%")
        
        query += f" ORDER BY {order_by}"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_prompt(self, prompt_id: int) -> Optional[Dict]:
        """
        Получить промт по ID.
        
        Args:
            prompt_id: ID промта
            
        Returns:
            Словарь с данными промта или None
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM prompts WHERE id = ?", (prompt_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def update_prompt(self, prompt_id: int, prompt: Optional[str] = None,
                     tags: Optional[str] = None) -> bool:
        """
        Обновить промт.
        
        Args:
            prompt_id: ID промта
            prompt: Новый текст промта
            tags: Новые теги
            
        Returns:
            True если обновление успешно
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if prompt is not None:
            updates.append("prompt = ?")
            params.append(prompt)
        
        if tags is not None:
            updates.append("tags = ?")
            params.append(tags)
        
        if not updates:
            return False
        
        params.append(prompt_id)
        query = f"UPDATE prompts SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
        return cursor.rowcount > 0
    
    def delete_prompt(self, prompt_id: int) -> bool:
        """
        Удалить промт.
        
        Args:
            prompt_id: ID промта
            
        Returns:
            True если удаление успешно
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM prompts WHERE id = ?", (prompt_id,))
        conn.commit()
        return cursor.rowcount > 0
    
    # ========== Методы для работы с моделями ==========
    
    def create_model(self, name: str, api_url: str, api_id: str,
                    is_active: int = 1) -> int:
        """
        Создать новую модель.
        
        Args:
            name: Название модели
            api_url: URL API-эндпоинта
            api_id: Имя переменной окружения с API-ключом
            is_active: Флаг активности (1 - активна, 0 - неактивна)
            
        Returns:
            ID созданной модели
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO models (name, api_url, api_id, is_active) VALUES (?, ?, ?, ?)",
            (name, api_url, api_id, is_active)
        )
        conn.commit()
        return cursor.lastrowid
    
    def get_models(self, search: Optional[str] = None,
                  order_by: str = "name ASC") -> List[Dict]:
        """
        Получить список всех моделей.
        
        Args:
            search: Поиск по названию
            order_by: Поле и направление сортировки
            
        Returns:
            Список словарей с данными моделей
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM models WHERE 1=1"
        params = []
        
        if search:
            query += " AND name LIKE ?"
            params.append(f"%{search}%")
        
        query += f" ORDER BY {order_by}"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_active_models(self) -> List[Dict]:
        """
        Получить список активных моделей.
        
        Returns:
            Список словарей с данными активных моделей
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM models WHERE is_active = 1 ORDER BY name ASC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_model(self, model_id: int) -> Optional[Dict]:
        """
        Получить модель по ID.
        
        Args:
            model_id: ID модели
            
        Returns:
            Словарь с данными модели или None
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM models WHERE id = ?", (model_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def update_model(self, model_id: int, name: Optional[str] = None,
                    api_url: Optional[str] = None, api_id: Optional[str] = None,
                    is_active: Optional[int] = None) -> bool:
        """
        Обновить модель.
        
        Args:
            model_id: ID модели
            name: Новое название
            api_url: Новый URL
            api_id: Новое имя переменной окружения
            is_active: Новый флаг активности
            
        Returns:
            True если обновление успешно
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        
        if api_url is not None:
            updates.append("api_url = ?")
            params.append(api_url)
        
        if api_id is not None:
            updates.append("api_id = ?")
            params.append(api_id)
        
        if is_active is not None:
            updates.append("is_active = ?")
            params.append(is_active)
        
        if not updates:
            return False
        
        params.append(model_id)
        query = f"UPDATE models SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
        return cursor.rowcount > 0
    
    def delete_model(self, model_id: int) -> bool:
        """
        Удалить модель.
        
        Args:
            model_id: ID модели
            
        Returns:
            True если удаление успешно
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM models WHERE id = ?", (model_id,))
        conn.commit()
        return cursor.rowcount > 0
    
    # ========== Методы для работы с результатами ==========
    
    def save_results(self, results: List[Dict]) -> List[int]:
        """
        Сохранить результаты в БД.
        
        Args:
            results: Список словарей с ключами:
                - prompt_id: ID промта
                - model_id: ID модели
                - response: Текст ответа
                - selected: Флаг выбора (1 или 0)
                
        Returns:
            Список ID созданных записей
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ids = []
        
        for result in results:
            cursor.execute(
                """INSERT INTO results (prompt_id, model_id, response, selected, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (result['prompt_id'], result['model_id'], result['response'],
                 result.get('selected', 0), created_at)
            )
            ids.append(cursor.lastrowid)
        
        conn.commit()
        return ids
    
    def get_results(self, prompt_id: Optional[int] = None,
                   model_id: Optional[int] = None,
                   selected_only: bool = False,
                   order_by: str = "created_at DESC") -> List[Dict]:
        """
        Получить результаты.
        
        Args:
            prompt_id: Фильтр по ID промта
            model_id: Фильтр по ID модели
            selected_only: Только выбранные результаты
            order_by: Поле и направление сортировки
            
        Returns:
            Список словарей с данными результатов
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM results WHERE 1=1"
        params = []
        
        if prompt_id:
            query += " AND prompt_id = ?"
            params.append(prompt_id)
        
        if model_id:
            query += " AND model_id = ?"
            params.append(model_id)
        
        if selected_only:
            query += " AND selected = 1"
        
        query += f" ORDER BY {order_by}"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def delete_result(self, result_id: int) -> bool:
        """
        Удалить результат.
        
        Args:
            result_id: ID результата
            
        Returns:
            True если удаление успешно
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM results WHERE id = ?", (result_id,))
        conn.commit()
        return cursor.rowcount > 0
    
    # ========== Методы для работы с настройками ==========
    
    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Получить значение настройки.
        
        Args:
            key: Ключ настройки
            default: Значение по умолчанию
            
        Returns:
            Значение настройки или default
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row['value'] if row and row['value'] else default
    
    def set_setting(self, key: str, value: str) -> bool:
        """
        Установить значение настройки.
        
        Args:
            key: Ключ настройки
            value: Значение настройки
            
        Returns:
            True если установка успешна
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value)
        )
        conn.commit()
        return True
    
    def close(self):
        """Закрыть соединение с БД."""
        if self.conn:
            self.conn.close()
            self.conn = None

