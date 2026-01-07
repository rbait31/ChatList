"""
Диалог для просмотра сохраненных результатов.
Позволяет просматривать, фильтровать и удалять сохраненные результаты.
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QLineEdit, QLabel,
    QComboBox, QWidget, QTextEdit
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont
from datetime import datetime
from db import Database


class ViewResultsDialog(QDialog):
    """Диалог для просмотра сохраненных результатов."""
    
    def __init__(self, db: Database, parent=None):
        """
        Инициализация диалога.
        
        Args:
            db: Экземпляр класса Database
            parent: Родительское окно
        """
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Просмотр сохраненных результатов")
        self.setMinimumSize(1000, 700)
        
        self.init_ui()
        self.load_results()
    
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
        
        # Первая строка фильтров
        filter_row1 = QHBoxLayout()
        
        # Поиск по тексту ответа
        search_label = QLabel("Поиск:")
        filter_row1.addWidget(search_label)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по тексту ответа...")
        self.search_input.textChanged.connect(self.apply_filters)
        filter_row1.addWidget(self.search_input)
        
        # Фильтр по промту
        prompt_label = QLabel("Промт:")
        filter_row1.addWidget(prompt_label)
        self.prompt_combo = QComboBox()
        self.prompt_combo.addItem("Все промты", None)
        self.prompt_combo.currentIndexChanged.connect(self.apply_filters)
        filter_row1.addWidget(self.prompt_combo)
        
        filter_layout.addLayout(filter_row1)
        
        # Вторая строка фильтров
        filter_row2 = QHBoxLayout()
        
        # Фильтр по модели
        model_label = QLabel("Модель:")
        filter_row2.addWidget(model_label)
        self.model_combo = QComboBox()
        self.model_combo.addItem("Все модели", None)
        self.model_combo.currentIndexChanged.connect(self.apply_filters)
        filter_row2.addWidget(self.model_combo)
        
        # Кнопка очистки фильтров
        clear_filters_button = QPushButton("Очистить фильтры")
        clear_filters_button.clicked.connect(self.clear_filters)
        filter_row2.addWidget(clear_filters_button)
        
        filter_row2.addStretch()
        
        filter_layout.addLayout(filter_row2)
        
        layout.addWidget(filter_panel)
        
        # Таблица результатов
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels([
            "Дата", "Промт", "Модель", "Ответ", "Действия"
        ])
        
        # Настройка колонок
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Дата
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Промт
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Модель
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Ответ
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Действия
        
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.setSortingEnabled(True)
        self.results_table.setWordWrap(True)  # Перенос текста в ячейках
        # Обработчик двойного клика для просмотра полного ответа
        self.results_table.itemDoubleClicked.connect(self.view_full_response)
        layout.addWidget(self.results_table)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        
        refresh_button = QPushButton("Обновить")
        refresh_button.clicked.connect(self.load_results)
        buttons_layout.addWidget(refresh_button)
        
        buttons_layout.addStretch()
        
        delete_button = QPushButton("Удалить выбранные")
        delete_button.clicked.connect(self.delete_selected)
        buttons_layout.addWidget(delete_button)
        
        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.accept)
        buttons_layout.addWidget(close_button)
        
        layout.addLayout(buttons_layout)
        
        # Загружаем списки для фильтров
        self.load_filter_lists()
    
    def load_filter_lists(self):
        """Загрузить списки промтов и моделей для фильтров."""
        # Загружаем промты
        prompts = self.db.get_prompts(order_by="date DESC")
        for prompt in prompts:
            date_str = prompt['date'][:10] if prompt['date'] else ""
            display_text = f"{date_str}: {prompt['prompt'][:50]}..."
            self.prompt_combo.addItem(display_text, prompt['id'])
        
        # Загружаем модели
        models = self.db.get_models(order_by="name ASC")
        for model in models:
            self.model_combo.addItem(model['name'], model['id'])
    
    def load_results(self):
        """Загрузить все результаты из БД."""
        self.all_results = self.db.get_results(order_by="created_at DESC")
        
        # Загружаем информацию о промтах и моделях
        self.prompts_dict = {}
        prompts = self.db.get_prompts()
        for prompt in prompts:
            self.prompts_dict[prompt['id']] = prompt
        
        self.models_dict = {}
        models = self.db.get_models()
        for model in models:
            self.models_dict[model['id']] = model
        
        self.apply_filters()
    
    def apply_filters(self):
        """Применить фильтры к результатам."""
        filtered_results = self.all_results.copy()
        
        # Фильтр по поиску
        search_text = self.search_input.text().strip().lower()
        if search_text:
            filtered_results = [
                r for r in filtered_results
                if search_text in r['response'].lower()
            ]
        
        # Фильтр по промту
        prompt_id = self.prompt_combo.currentData()
        if prompt_id:
            filtered_results = [
                r for r in filtered_results
                if r['prompt_id'] == prompt_id
            ]
        
        # Фильтр по модели
        model_id = self.model_combo.currentData()
        if model_id:
            filtered_results = [
                r for r in filtered_results
                if r['model_id'] == model_id
            ]
        
        # Обновляем таблицу
        self.update_table(filtered_results)
    
    def update_table(self, results):
        """Обновить таблицу результатов."""
        self.results_table.setRowCount(len(results))
        
        for row, result in enumerate(results):
            # Дата
            date_str = result['created_at']
            if date_str:
                try:
                    dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                    date_display = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    date_display = date_str[:10]
            else:
                date_display = "N/A"
            
            date_item = QTableWidgetItem(date_display)
            date_item.setData(Qt.UserRole, result['id'])  # Сохраняем ID
            date_item.setFlags(date_item.flags() & ~Qt.ItemIsEditable)
            self.results_table.setItem(row, 0, date_item)
            
            # Промт
            prompt_id = result['prompt_id']
            prompt_text = "N/A"
            if prompt_id in self.prompts_dict:
                prompt = self.prompts_dict[prompt_id]
                prompt_text = prompt['prompt'][:80] + "..." if len(prompt['prompt']) > 80 else prompt['prompt']
            
            prompt_item = QTableWidgetItem(prompt_text)
            prompt_item.setFlags(prompt_item.flags() & ~Qt.ItemIsEditable)
            self.results_table.setItem(row, 1, prompt_item)
            
            # Модель
            model_id = result['model_id']
            model_name = "Unknown"
            if model_id in self.models_dict:
                model_name = self.models_dict[model_id]['name']
            
            model_item = QTableWidgetItem(model_name)
            model_item.setFlags(model_item.flags() & ~Qt.ItemIsEditable)
            self.results_table.setItem(row, 2, model_item)
            
            # Ответ (полный текст)
            response_text = result['response']
            response_item = QTableWidgetItem(response_text)
            response_item.setFlags(response_item.flags() & ~Qt.ItemIsEditable)
            response_item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
            # Сохраняем полный текст в пользовательских данных для просмотра
            response_item.setData(Qt.UserRole + 1, response_text)
            self.results_table.setItem(row, 3, response_item)
            
            # Добавляем обработчик двойного клика для просмотра полного текста
            self.results_table.item(row, 3).setToolTip("Двойной клик для просмотра полного текста")
            
            # Кнопка удаления
            delete_button = QPushButton("🗑️")
            delete_button.setMaximumWidth(30)
            delete_button.clicked.connect(
                lambda checked, r_id=result['id']: self.delete_result(r_id)
            )
            self.results_table.setCellWidget(row, 4, delete_button)
            
            # Устанавливаем высоту строки (больше для лучшего отображения текста)
            # Высота будет автоматически подстраиваться при включенном переносе текста
            self.results_table.setRowHeight(row, 100)
        
        # Автоматически подгоняем ширину колонок
        self.results_table.resizeColumnToContents(0)
        self.results_table.resizeColumnToContents(1)
        self.results_table.resizeColumnToContents(2)
    
    def clear_filters(self):
        """Очистить все фильтры."""
        self.search_input.clear()
        self.prompt_combo.setCurrentIndex(0)
        self.model_combo.setCurrentIndex(0)
        self.apply_filters()
    
    def delete_result(self, result_id: int):
        """Удалить один результат."""
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Вы уверены, что хотите удалить этот результат?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.db.delete_result(result_id)
                QMessageBox.information(self, "Успех", "Результат успешно удален!")
                self.load_results()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении: {str(e)}")
    
    def delete_selected(self):
        """Удалить выбранные результаты."""
        selected_rows = set()
        for item in self.results_table.selectedItems():
            selected_rows.add(item.row())
        
        if not selected_rows:
            QMessageBox.warning(self, "Ошибка", "Не выбрано ни одного результата!")
            return
        
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Вы уверены, что хотите удалить {len(selected_rows)} результатов?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            deleted_count = 0
            for row in selected_rows:
                result_id_item = self.results_table.item(row, 0)
                if result_id_item:
                    result_id = result_id_item.data(Qt.UserRole)
                    try:
                        self.db.delete_result(result_id)
                        deleted_count += 1
                    except Exception as e:
                        QMessageBox.warning(
                            self,
                            "Ошибка",
                            f"Ошибка при удалении результата ID {result_id}: {str(e)}"
                        )
            
            if deleted_count > 0:
                QMessageBox.information(
                    self,
                    "Успех",
                    f"Удалено {deleted_count} результатов!"
                )
                self.load_results()
    
    def view_full_response(self, item):
        """Просмотр полного текста ответа в отдельном окне."""
        # Проверяем, что клик был по колонке "Ответ" (индекс 3)
        if item.column() == 3:
            full_text = item.data(Qt.UserRole + 1) or item.text()
            
            # Создаем диалог для отображения полного текста
            dialog = QDialog(self)
            dialog.setWindowTitle("Полный текст ответа")
            dialog.setMinimumSize(700, 500)
            
            layout = QVBoxLayout()
            dialog.setLayout(layout)
            
            # Метка с информацией
            info_label = QLabel(f"Ответ модели: {self.results_table.item(item.row(), 2).text()}")
            info_label.setFont(QFont("Arial", 10, QFont.Bold))
            layout.addWidget(info_label)
            
            # Текстовое поле с полным ответом
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setPlainText(full_text)
            text_edit.setFont(QFont("Consolas", 10))  # Моноширинный шрифт для читаемости
            layout.addWidget(text_edit)
            
            # Кнопка закрытия
            button_layout = QHBoxLayout()
            button_layout.addStretch()
            close_button = QPushButton("Закрыть")
            close_button.clicked.connect(dialog.accept)
            button_layout.addWidget(close_button)
            layout.addLayout(button_layout)
            
            dialog.exec_()

