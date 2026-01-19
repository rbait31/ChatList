"""
Диалог для управления моделями нейросетей.
Позволяет добавлять, редактировать, удалять и включать/отключать модели.
"""
import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QLineEdit, QLabel,
    QCheckBox, QDialogButtonBox, QWidget
)
from PyQt5.QtCore import Qt
from db import Database
# Импортируем config для автоматической загрузки .env из правильной папки
import config  # noqa: F401


class ModelSettingsDialog(QDialog):
    """Диалог для управления моделями."""
    
    def __init__(self, db: Database, parent=None):
        """
        Инициализация диалога.
        
        Args:
            db: Экземпляр класса Database
            parent: Родительское окно
        """
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Управление моделями")
        self.setMinimumSize(800, 600)
        
        self.init_ui()
        self.load_models()
    
    def init_ui(self):
        """Инициализация интерфейса."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Таблица моделей
        self.models_table = QTableWidget()
        self.models_table.setColumnCount(5)
        self.models_table.setHorizontalHeaderLabels([
            "Активна", "Название", "API URL", "API Key Env", "Действия"
        ])
        
        # Настройка колонок
        header = self.models_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Активна
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Название
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # API URL
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # API Key Env
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Действия
        
        self.models_table.setAlternatingRowColors(True)
        self.models_table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.models_table)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        
        add_button = QPushButton("Добавить модель")
        add_button.clicked.connect(self.add_model)
        buttons_layout.addWidget(add_button)
        
        buttons_layout.addStretch()
        
        refresh_button = QPushButton("Обновить")
        refresh_button.clicked.connect(self.load_models)
        buttons_layout.addWidget(refresh_button)
        
        layout.addLayout(buttons_layout)
        
        # Кнопки диалога
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def load_models(self):
        """Загрузить список моделей из БД."""
        models = self.db.get_models()
        self.models_table.setRowCount(len(models))
        
        for row, model in enumerate(models):
            # Чекбокс активности
            checkbox = QCheckBox()
            checkbox.setChecked(model['is_active'] == 1)
            checkbox.stateChanged.connect(
                lambda state, m_id=model['id']: self.toggle_model_active(m_id, state)
            )
            self.models_table.setCellWidget(row, 0, checkbox)
            
            # Название
            name_item = QTableWidgetItem(model['name'])
            name_item.setData(Qt.UserRole, model['id'])  # Сохраняем ID
            self.models_table.setItem(row, 1, name_item)
            
            # API URL
            url_item = QTableWidgetItem(model['api_url'])
            self.models_table.setItem(row, 2, url_item)
            
            # API Key Env
            api_id_item = QTableWidgetItem(model['api_id'])
            self.models_table.setItem(row, 3, api_id_item)
            
            # Кнопки действий
            actions_widget = QWidget()
            actions_layout = QHBoxLayout()
            actions_layout.setContentsMargins(2, 2, 2, 2)
            actions_widget.setLayout(actions_layout)
            
            edit_button = QPushButton("✏️")
            edit_button.setMaximumWidth(30)
            edit_button.clicked.connect(
                lambda checked, r=row: self.edit_model(r)
            )
            
            delete_button = QPushButton("🗑️")
            delete_button.setMaximumWidth(30)
            delete_button.clicked.connect(
                lambda checked, m_id=model['id']: self.delete_model(m_id)
            )
            
            actions_layout.addWidget(edit_button)
            actions_layout.addWidget(delete_button)
            
            # Устанавливаем виджет с кнопками
            self.models_table.setCellWidget(row, 4, actions_widget)
    
    def toggle_model_active(self, model_id: int, state: int):
        """Переключить активность модели."""
        is_active = 1 if state == Qt.Checked else 0
        self.db.update_model(model_id, is_active=is_active)
    
    def add_model(self):
        """Добавить новую модель."""
        dialog = ModelEditDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            name, api_url, api_id = dialog.get_data()
            try:
                self.db.create_model(name, api_url, api_id, is_active=1)
                self.load_models()
                QMessageBox.information(self, "Успех", "Модель успешно добавлена!")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при добавлении модели: {str(e)}")
    
    def edit_model(self, row: int):
        """Редактировать модель."""
        model_id = self.models_table.item(row, 1).data(Qt.UserRole)
        model = self.db.get_model(model_id)
        
        if not model:
            QMessageBox.warning(self, "Ошибка", "Модель не найдена!")
            return
        
        dialog = ModelEditDialog(self, model)
        if dialog.exec_() == QDialog.Accepted:
            name, api_url, api_id = dialog.get_data()
            try:
                self.db.update_model(model_id, name=name, api_url=api_url, api_id=api_id)
                self.load_models()
                QMessageBox.information(self, "Успех", "Модель успешно обновлена!")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при обновлении модели: {str(e)}")
    
    def delete_model(self, model_id: int):
        """Удалить модель."""
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Вы уверены, что хотите удалить эту модель?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.db.delete_model(model_id)
                self.load_models()
                QMessageBox.information(self, "Успех", "Модель успешно удалена!")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении модели: {str(e)}")


class ModelEditDialog(QDialog):
    """Диалог для добавления/редактирования модели."""
    
    def __init__(self, parent=None, model=None):
        """
        Инициализация диалога.
        
        Args:
            parent: Родительское окно
            model: Словарь с данными модели (для редактирования) или None (для добавления)
        """
        super().__init__(parent)
        self.setWindowTitle("Редактировать модель" if model else "Добавить модель")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Название
        name_label = QLabel("Название модели:")
        layout.addWidget(name_label)
        self.name_input = QLineEdit()
        if model:
            self.name_input.setText(model['name'])
        layout.addWidget(self.name_input)
        
        # API URL
        url_label = QLabel("API URL:")
        layout.addWidget(url_label)
        self.url_input = QLineEdit()
        if model:
            self.url_input.setText(model['api_url'])
        else:
            self.url_input.setPlaceholderText("https://api.example.com/v1/chat/completions")
        layout.addWidget(self.url_input)
        
        # API Key Env
        api_id_label = QLabel("Имя переменной окружения с API-ключом:")
        layout.addWidget(api_id_label)
        self.api_id_input = QLineEdit()
        if model:
            self.api_id_input.setText(model['api_id'])
        else:
            self.api_id_input.setPlaceholderText("OPENAI_API_KEY")
        layout.addWidget(self.api_id_input)
        
        # Кнопка проверки модели
        test_button = QPushButton("Проверить модель")
        test_button.clicked.connect(self.test_model)
        layout.addWidget(test_button)
        
        # Кнопки
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def test_model(self):
        """Проверить модель (API-ключ и возможность создания клиента)."""
        name = self.name_input.text().strip()
        api_url = self.url_input.text().strip()
        api_id = self.api_id_input.text().strip()
        
        # Базовая валидация
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название модели!")
            return
        
        if not api_url:
            QMessageBox.warning(self, "Ошибка", "Введите API URL!")
            return
        
        if not api_id:
            QMessageBox.warning(self, "Ошибка", "Введите имя переменной окружения!")
            return
        
        # Проверяем наличие API-ключа
        api_key = os.getenv(api_id)
        if not api_key:
            QMessageBox.warning(
                self,
                "Ошибка проверки",
                f"API ключ не найден!\n\n"
                f"Переменная окружения '{api_id}' не найдена в файле .env.\n\n"
                f"Проверьте:\n"
                f"1. Файл .env существует в корне проекта\n"
                f"2. В файле .env есть строка: {api_id}=ваш_ключ\n"
                f"3. Ключ не является заглушкой"
            )
            return
        
        # Проверяем, что ключ не заглушка
        placeholders = [
            'sk-your-', 'gsk_your-', 'sk-or-your-', 
            'your-api-key', 'api-key-here'
        ]
        if any(ph in api_key.lower() for ph in placeholders):
            QMessageBox.warning(
                self,
                "Предупреждение",
                f"Обнаружена заглушка вместо реального ключа!\n\n"
                f"Значение переменной '{api_id}' похоже на заглушку.\n"
                f"Замените её на реальный API-ключ в файле .env"
            )
            return
        
        # Пытаемся создать клиент
        try:
            from network import create_api_client
            client = create_api_client(name, api_url, api_id)
            
            QMessageBox.information(
                self,
                "Проверка успешна",
                f"Модель '{name}' проверена успешно!\n\n"
                f"✓ API-ключ найден\n"
                f"✓ Клиент создан успешно\n"
                f"✓ Модель готова к использованию"
            )
        except ValueError as e:
            # Ошибка создания клиента (неизвестный тип модели)
            QMessageBox.warning(
                self,
                "Предупреждение",
                f"Модель может работать, но тип не распознан автоматически.\n\n"
                f"Детали: {str(e)}\n\n"
                f"Проверьте правильность API URL и типа модели."
            )
        except Exception as e:
            error_msg = str(e)
            QMessageBox.critical(
                self,
                "Ошибка проверки",
                f"Не удалось создать клиент для модели!\n\n"
                f"Ошибка: {error_msg}\n\n"
                f"Проверьте:\n"
                f"1. Правильность API URL\n"
                f"2. Правильность API-ключа\n"
                f"3. Тип модели соответствует API"
            )
    
    def validate_and_accept(self):
        """Валидация и принятие диалога."""
        name = self.name_input.text().strip()
        api_url = self.url_input.text().strip()
        api_id = self.api_id_input.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название модели!")
            return
        
        if not api_url:
            QMessageBox.warning(self, "Ошибка", "Введите API URL!")
            return
        
        if not api_id:
            QMessageBox.warning(self, "Ошибка", "Введите имя переменной окружения!")
            return
        
        # Простая валидация URL
        if not (api_url.startswith("http://") or api_url.startswith("https://")):
            QMessageBox.warning(self, "Ошибка", "API URL должен начинаться с http:// или https://")
            return
        
        # Автоматическая проверка модели перед сохранением
        api_key = os.getenv(api_id)
        if not api_key:
            reply = QMessageBox.question(
                self,
                "Предупреждение",
                f"API ключ для переменной '{api_id}' не найден в файле .env.\n\n"
                f"Модель будет сохранена, но не сможет использоваться до добавления ключа.\n\n"
                f"Продолжить сохранение?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        else:
            # Проверяем, что ключ не заглушка
            placeholders = [
                'sk-your-', 'gsk_your-', 'sk-or-your-', 
                'your-api-key', 'api-key-here'
            ]
            if any(ph in api_key.lower() for ph in placeholders):
                reply = QMessageBox.question(
                    self,
                    "Предупреждение",
                    f"Обнаружена заглушка вместо реального API-ключа.\n\n"
                    f"Модель будет сохранена, но не сможет использоваться до замены ключа.\n\n"
                    f"Продолжить сохранение?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
        
        self.accept()
    
    def get_data(self):
        """
        Получить данные из диалога.
        
        Returns:
            Кортеж (name, api_url, api_id)
        """
        return (
            self.name_input.text().strip(),
            self.url_input.text().strip(),
            self.api_id_input.text().strip()
        )

