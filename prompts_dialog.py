"""
Диалог для управления промтами.
Позволяет просматривать, создавать, редактировать и удалять промты.
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QLineEdit, QLabel,
    QComboBox, QWidget, QTextEdit, QFormLayout, QGroupBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from datetime import datetime
from db import Database


class PromptsDialog(QDialog):
    """Диалог для управления промтами."""
    
    def __init__(self, db: Database, parent=None):
        """
        Инициализация диалога.
        
        Args:
            db: Экземпляр класса Database
            parent: Родительское окно
        """
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Управление промтами")
        self.setMinimumSize(900, 700)
        
        self.init_ui()
        self.load_prompts()
    
    def init_ui(self):
        """Инициализация интерфейса."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Панель фильтров
        filter_panel = QWidget()
        filter_layout = QVBoxLayout()
        filter_panel.setLayout(filter_layout)
        
        # Заголовок фильтров
        filter_label = QLabel("Фильтры:")
        filter_label.setFont(QFont("Arial", 10, QFont.Bold))
        filter_layout.addWidget(filter_label)
        
        # Строка фильтров
        filter_row = QHBoxLayout()
        
        # Поиск по тексту промта
        search_label = QLabel("Поиск:")
        filter_row.addWidget(search_label)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по тексту промта...")
        self.search_input.textChanged.connect(self.apply_filters)
        filter_row.addWidget(self.search_input)
        
        # Фильтр по тегам
        tags_label = QLabel("Теги:")
        filter_row.addWidget(tags_label)
        self.tags_filter_input = QLineEdit()
        self.tags_filter_input.setPlaceholderText("Фильтр по тегам...")
        self.tags_filter_input.textChanged.connect(self.apply_filters)
        filter_row.addWidget(self.tags_filter_input)
        
        # Кнопка очистки фильтров
        clear_filters_button = QPushButton("Очистить фильтры")
        clear_filters_button.clicked.connect(self.clear_filters)
        filter_row.addWidget(clear_filters_button)
        
        filter_row.addStretch()
        
        filter_layout.addLayout(filter_row)
        layout.addWidget(filter_panel)
        
        # Таблица промтов
        self.prompts_table = QTableWidget()
        self.prompts_table.setColumnCount(4)
        self.prompts_table.setHorizontalHeaderLabels([
            "Дата", "Промт", "Теги", "Действия"
        ])
        
        # Настройка колонок
        header = self.prompts_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Дата
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Промт
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Теги
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Действия
        
        self.prompts_table.setAlternatingRowColors(True)
        self.prompts_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.prompts_table.setSortingEnabled(True)
        self.prompts_table.setWordWrap(True)
        layout.addWidget(self.prompts_table)
        
        # Кнопки CRUD
        crud_layout = QHBoxLayout()
        
        create_button = QPushButton("➕ Создать")
        create_button.clicked.connect(self.create_prompt)
        crud_layout.addWidget(create_button)
        
        read_button = QPushButton("👁 Просмотр")
        read_button.clicked.connect(self.read_prompt)
        crud_layout.addWidget(read_button)
        
        update_button = QPushButton("✏️ Редактировать")
        update_button.clicked.connect(self.update_prompt)
        crud_layout.addWidget(update_button)
        
        delete_button = QPushButton("🗑️ Удалить")
        delete_button.clicked.connect(self.delete_prompt)
        crud_layout.addWidget(delete_button)
        
        refresh_button = QPushButton("🔄 Обновить")
        refresh_button.clicked.connect(self.load_prompts)
        crud_layout.addWidget(refresh_button)
        
        crud_layout.addStretch()
        
        layout.addLayout(crud_layout)
        
        # Кнопка закрытия
        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
    
    def load_prompts(self):
        """Загрузить список промтов из БД."""
        self.all_prompts = self.db.get_prompts(order_by="date DESC")
        self.apply_filters()
    
    def apply_filters(self):
        """Применить фильтры к промтам."""
        filtered_prompts = self.all_prompts.copy()
        
        # Фильтр по поиску
        search_text = self.search_input.text().strip().lower()
        if search_text:
            filtered_prompts = [
                p for p in filtered_prompts
                if search_text in p['prompt'].lower()
            ]
        
        # Фильтр по тегам
        tags_filter = self.tags_filter_input.text().strip().lower()
        if tags_filter:
            filtered_prompts = [
                p for p in filtered_prompts
                if p.get('tags') and tags_filter in p['tags'].lower()
            ]
        
        # Обновляем таблицу
        self.update_table(filtered_prompts)
    
    def update_table(self, prompts):
        """Обновить таблицу промтов."""
        self.prompts_table.setRowCount(len(prompts))
        
        for row, prompt in enumerate(prompts):
            # Дата
            date_str = prompt['date']
            if date_str:
                try:
                    dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                    date_display = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    date_display = date_str[:10]
            else:
                date_display = "N/A"
            
            date_item = QTableWidgetItem(date_display)
            date_item.setData(Qt.UserRole, prompt['id'])  # Сохраняем ID
            date_item.setFlags(date_item.flags() & ~Qt.ItemIsEditable)
            self.prompts_table.setItem(row, 0, date_item)
            
            # Промт (обрезаем для отображения)
            prompt_text = prompt['prompt'][:100] + "..." if len(prompt['prompt']) > 100 else prompt['prompt']
            prompt_item = QTableWidgetItem(prompt_text)
            prompt_item.setFlags(prompt_item.flags() & ~Qt.ItemIsEditable)
            prompt_item.setData(Qt.UserRole + 1, prompt['prompt'])  # Сохраняем полный текст
            prompt_item.setToolTip("Двойной клик для просмотра полного текста")
            self.prompts_table.setItem(row, 1, prompt_item)
            
            # Теги
            tags_item = QTableWidgetItem(prompt.get('tags', '') or '')
            tags_item.setFlags(tags_item.flags() & ~Qt.ItemIsEditable)
            self.prompts_table.setItem(row, 2, tags_item)
            
            # Кнопка удаления
            delete_button = QPushButton("🗑️")
            delete_button.setMaximumWidth(30)
            delete_button.clicked.connect(
                lambda checked, p_id=prompt['id']: self.delete_prompt_by_id(p_id)
            )
            self.prompts_table.setCellWidget(row, 3, delete_button)
            
            # Устанавливаем высоту строки
            self.prompts_table.setRowHeight(row, 60)
        
        # Автоматически подгоняем ширину колонок
        self.prompts_table.resizeColumnToContents(0)
        self.prompts_table.resizeColumnToContents(2)
        
        # Обработчик двойного клика для просмотра полного промта
        self.prompts_table.itemDoubleClicked.connect(self.view_full_prompt)
    
    def view_full_prompt(self, item):
        """Просмотр полного текста промта."""
        if item.column() == 1:  # Колонка "Промт"
            full_text = item.data(Qt.UserRole + 1) or item.text()
            
            dialog = QDialog(self)
            dialog.setWindowTitle("Полный текст промта")
            dialog.setMinimumSize(700, 500)
            
            layout = QVBoxLayout()
            dialog.setLayout(layout)
            
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setPlainText(full_text)
            text_edit.setFont(QFont("Consolas", 10))
            layout.addWidget(text_edit)
            
            close_button = QPushButton("Закрыть")
            close_button.clicked.connect(dialog.accept)
            layout.addWidget(close_button)
            
            dialog.exec_()
    
    def clear_filters(self):
        """Очистить все фильтры."""
        self.search_input.clear()
        self.tags_filter_input.clear()
        self.apply_filters()
    
    def get_selected_prompt_id(self) -> Optional[int]:
        """Получить ID выбранного промта."""
        selected_rows = self.prompts_table.selectionModel().selectedRows()
        if not selected_rows:
            return None
        
        row = selected_rows[0].row()
        date_item = self.prompts_table.item(row, 0)
        if date_item:
            return date_item.data(Qt.UserRole)
        return None
    
    def create_prompt(self):
        """Создать новый промт."""
        dialog = PromptEditDialog(self, None)
        if dialog.exec_() == QDialog.Accepted:
            prompt_text, tags = dialog.get_data()
            try:
                self.db.create_prompt(prompt_text, tags)
                QMessageBox.information(self, "Успех", "Промт успешно создан!")
                self.load_prompts()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при создании промта: {str(e)}")
    
    def read_prompt(self):
        """Просмотреть промт."""
        prompt_id = self.get_selected_prompt_id()
        if not prompt_id:
            QMessageBox.warning(self, "Ошибка", "Выберите промт для просмотра!")
            return
        
        prompt = self.db.get_prompt(prompt_id)
        if not prompt:
            QMessageBox.warning(self, "Ошибка", "Промт не найден!")
            return
        
        dialog = PromptViewDialog(self, prompt)
        dialog.exec_()
    
    def update_prompt(self):
        """Редактировать промт."""
        prompt_id = self.get_selected_prompt_id()
        if not prompt_id:
            QMessageBox.warning(self, "Ошибка", "Выберите промт для редактирования!")
            return
        
        prompt = self.db.get_prompt(prompt_id)
        if not prompt:
            QMessageBox.warning(self, "Ошибка", "Промт не найден!")
            return
        
        dialog = PromptEditDialog(self, prompt)
        if dialog.exec_() == QDialog.Accepted:
            prompt_text, tags = dialog.get_data()
            try:
                self.db.update_prompt(prompt_id, prompt=prompt_text, tags=tags)
                QMessageBox.information(self, "Успех", "Промт успешно обновлен!")
                self.load_prompts()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при обновлении промта: {str(e)}")
    
    def delete_prompt(self):
        """Удалить выбранный промт."""
        prompt_id = self.get_selected_prompt_id()
        if not prompt_id:
            QMessageBox.warning(self, "Ошибка", "Выберите промт для удаления!")
            return
        
        self.delete_prompt_by_id(prompt_id)
    
    def delete_prompt_by_id(self, prompt_id: int):
        """Удалить промт по ID."""
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Вы уверены, что хотите удалить этот промт?\n\n"
            "Внимание: Все связанные результаты также будут удалены!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.db.delete_prompt(prompt_id)
                QMessageBox.information(self, "Успех", "Промт успешно удален!")
                self.load_prompts()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении промта: {str(e)}")


class PromptViewDialog(QDialog):
    """Диалог для просмотра промта."""
    
    def __init__(self, parent, prompt: Dict):
        super().__init__(parent)
        self.setWindowTitle("Просмотр промта")
        self.setMinimumWidth(700)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Дата
        date_label = QLabel(f"Дата: {prompt.get('date', 'N/A')}")
        date_label.setFont(QFont("Arial", 9))
        layout.addWidget(date_label)
        
        # Промт
        prompt_label = QLabel("Промт:")
        prompt_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(prompt_label)
        
        prompt_text = QTextEdit()
        prompt_text.setReadOnly(True)
        prompt_text.setPlainText(prompt.get('prompt', ''))
        prompt_text.setFont(QFont("Consolas", 10))
        layout.addWidget(prompt_text)
        
        # Теги
        tags_label = QLabel("Теги:")
        tags_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(tags_label)
        
        tags_text = QLineEdit()
        tags_text.setReadOnly(True)
        tags_text.setText(prompt.get('tags', '') or '')
        layout.addWidget(tags_text)
        
        # Кнопка закрытия
        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)


class PromptEditDialog(QDialog):
    """Диалог для создания/редактирования промта."""
    
    def __init__(self, parent, prompt: Optional[Dict] = None):
        super().__init__(parent)
        self.prompt = prompt
        self.is_edit = prompt is not None
        
        self.setWindowTitle("Редактировать промт" if self.is_edit else "Создать промт")
        self.setMinimumWidth(600)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Промт
        prompt_label = QLabel("Промт: *")
        prompt_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(prompt_label)
        
        self.prompt_text = QTextEdit()
        self.prompt_text.setPlaceholderText("Введите текст промта...")
        if self.is_edit and prompt:
            self.prompt_text.setPlainText(prompt.get('prompt', ''))
        self.prompt_text.setMinimumHeight(150)
        layout.addWidget(self.prompt_text)
        
        # Теги
        tags_label = QLabel("Теги:")
        tags_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(tags_label)
        
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("python, api, test (через запятую)")
        if self.is_edit and prompt:
            self.tags_input.setText(prompt.get('tags', '') or '')
        layout.addWidget(self.tags_input)
        
        # Кнопки
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self.validate_and_accept)
        button_layout.addWidget(save_button)
        
        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
    
    def validate_and_accept(self):
        """Валидация и принятие диалога."""
        prompt_text = self.prompt_text.toPlainText().strip()
        
        if not prompt_text:
            QMessageBox.warning(self, "Ошибка", "Промт не может быть пустым!")
            return
        
        self.accept()
    
    def get_data(self):
        """
        Получить данные из диалога.
        
        Returns:
            Кортеж (prompt, tags)
        """
        prompt_text = self.prompt_text.toPlainText().strip()
        tags = self.tags_input.text().strip() or None
        return prompt_text, tags

