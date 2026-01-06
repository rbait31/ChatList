"""
Главный модуль приложения ChatList.
Реализует интерфейс для отправки промтов в нейросети и сравнения ответов.
"""
import sys
from datetime import datetime
from typing import List, Dict, Optional
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLineEdit, QComboBox, QTableWidget,
    QTableWidgetItem, QCheckBox, QLabel, QMessageBox, QHeaderView,
    QSplitter
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

from db import Database
from models import ModelManager


class RequestThread(QThread):
    """Поток для асинхронной отправки запросов к API."""
    
    finished = pyqtSignal(list)  # Сигнал с результатами
    
    def __init__(self, model_manager: ModelManager, prompt: str):
        """
        Инициализация потока.
        
        Args:
            model_manager: Менеджер моделей
            prompt: Текст промта
        """
        super().__init__()
        self.model_manager = model_manager
        self.prompt = prompt
    
    def run(self):
        """Выполнение запросов в отдельном потоке."""
        results = self.model_manager.send_to_all_models(self.prompt)
        self.finished.emit(results)


class MainWindow(QMainWindow):
    """Главное окно приложения."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ChatList - Сравнение ответов нейросетей")
        self.setGeometry(100, 100, 1400, 900)
        
        # Инициализация БД и менеджера моделей
        self.db = Database()
        self.model_manager = ModelManager(self.db)
        
        # Временное хранилище результатов (в памяти)
        self.temp_results: List[Dict] = []
        self.current_prompt_id: Optional[int] = None
        
        # Поток для запросов
        self.request_thread: Optional[RequestThread] = None
        
        self.init_ui()
        self.load_saved_prompts()
    
    def init_ui(self):
        """Инициализация интерфейса."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Создаем сплиттер для разделения на секции
        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter)
        
        # ========== Верхняя панель: Ввод промта ==========
        prompt_panel = QWidget()
        prompt_layout = QVBoxLayout()
        prompt_panel.setLayout(prompt_layout)
        
        # Заголовок
        prompt_label = QLabel("Промт:")
        prompt_label.setFont(QFont("Arial", 10, QFont.Bold))
        prompt_layout.addWidget(prompt_label)
        
        # Текстовое поле для промта
        self.prompt_text = QTextEdit()
        self.prompt_text.setPlaceholderText("Введите ваш промт здесь...")
        self.prompt_text.setMinimumHeight(100)
        prompt_layout.addWidget(self.prompt_text)
        
        # Строка с тегами и выбором сохраненного промта
        prompt_controls = QHBoxLayout()
        
        # Выбор сохраненного промта
        saved_prompt_label = QLabel("Сохраненный промт:")
        prompt_controls.addWidget(saved_prompt_label)
        
        self.saved_prompts_combo = QComboBox()
        self.saved_prompts_combo.setMinimumWidth(200)
        self.saved_prompts_combo.currentIndexChanged.connect(self.on_prompt_selected)
        prompt_controls.addWidget(self.saved_prompts_combo)
        
        prompt_controls.addStretch()
        
        # Поле для тегов
        tags_label = QLabel("Теги:")
        prompt_controls.addWidget(tags_label)
        
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("python, api, test")
        self.tags_input.setMinimumWidth(200)
        prompt_controls.addWidget(self.tags_input)
        
        prompt_layout.addLayout(prompt_controls)
        
        # Кнопка отправки
        send_button = QPushButton("Отправить запрос")
        send_button.setMinimumHeight(35)
        send_button.clicked.connect(self.send_prompt)
        prompt_layout.addWidget(send_button)
        
        splitter.addWidget(prompt_panel)
        
        # ========== Средняя панель: Таблица результатов ==========
        results_panel = QWidget()
        results_layout = QVBoxLayout()
        results_panel.setLayout(results_layout)
        
        results_label = QLabel("Результаты:")
        results_label.setFont(QFont("Arial", 10, QFont.Bold))
        results_layout.addWidget(results_label)
        
        # Таблица результатов
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(["Выбрано", "Модель", "Ответ"])
        
        # Настройка колонок
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Чекбокс
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Модель
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # Ответ
        
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        results_layout.addWidget(self.results_table)
        
        splitter.addWidget(results_panel)
        
        # Устанавливаем пропорции сплиттера
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        
        # ========== Нижняя панель: Управление ==========
        control_panel = QWidget()
        control_layout = QHBoxLayout()
        control_panel.setLayout(control_layout)
        
        # Кнопка сохранения
        self.save_button = QPushButton("Сохранить выбранные")
        self.save_button.setMinimumHeight(35)
        self.save_button.clicked.connect(self.save_selected_results)
        self.save_button.setEnabled(False)
        control_layout.addWidget(self.save_button)
        
        # Кнопка очистки
        clear_button = QPushButton("Очистить результаты")
        clear_button.setMinimumHeight(35)
        clear_button.clicked.connect(self.clear_results)
        control_layout.addWidget(clear_button)
        
        # Кнопка нового запроса
        new_request_button = QPushButton("Новый запрос")
        new_request_button.setMinimumHeight(35)
        new_request_button.clicked.connect(self.new_request)
        control_layout.addWidget(new_request_button)
        
        control_layout.addStretch()
        
        # Статус
        self.status_label = QLabel("Готов к работе")
        control_layout.addWidget(self.status_label)
        
        main_layout.addWidget(control_panel)
    
    def load_saved_prompts(self):
        """Загрузить список сохраненных промтов в ComboBox."""
        self.saved_prompts_combo.clear()
        self.saved_prompts_combo.addItem("-- Выберите промт --", None)
        
        prompts = self.db.get_prompts(order_by="date DESC")
        for prompt in prompts:
            # Формируем отображаемый текст
            date_str = prompt['date'][:10] if prompt['date'] else ""
            tags_str = f" [{prompt['tags']}]" if prompt['tags'] else ""
            display_text = f"{date_str}{tags_str}: {prompt['prompt'][:50]}..."
            self.saved_prompts_combo.addItem(display_text, prompt['id'])
    
    def on_prompt_selected(self, index: int):
        """Обработчик выбора сохраненного промта."""
        prompt_id = self.saved_prompts_combo.itemData(index)
        if prompt_id:
            prompt = self.db.get_prompt(prompt_id)
            if prompt:
                self.prompt_text.setPlainText(prompt['prompt'])
                self.tags_input.setText(prompt['tags'] or "")
    
    def send_prompt(self):
        """Отправить промт во все активные модели."""
        prompt_text = self.prompt_text.toPlainText().strip()
        
        if not prompt_text:
            QMessageBox.warning(self, "Ошибка", "Введите промт перед отправкой!")
            return
        
        # Проверяем наличие активных моделей
        active_models = self.model_manager.get_active_models()
        if not active_models:
            QMessageBox.warning(
                self, 
                "Ошибка", 
                "Нет активных моделей! Добавьте модели в настройках."
            )
            return
        
        # Очищаем предыдущие результаты
        self.clear_results()
        
        # Сохраняем промт в БД (если новый)
        tags = self.tags_input.text().strip() or None
        self.current_prompt_id = self.db.create_prompt(prompt_text, tags)
        
        # Обновляем статус
        self.status_label.setText(f"Отправка запроса в {len(active_models)} моделей...")
        self.save_button.setEnabled(False)
        
        # Отправляем запросы в отдельном потоке
        self.request_thread = RequestThread(self.model_manager, prompt_text)
        self.request_thread.finished.connect(self.on_requests_finished)
        self.request_thread.start()
    
    def on_requests_finished(self, results: List[Dict]):
        """Обработчик завершения запросов."""
        self.temp_results = results
        self.update_results_table()
        
        # Подсчитываем успешные запросы
        successful = sum(1 for r in results if r.get('success', False))
        total = len(results)
        
        self.status_label.setText(
            f"Готово: {successful} из {total} запросов успешны"
        )
        self.save_button.setEnabled(True)
    
    def update_results_table(self):
        """Обновить таблицу результатов."""
        self.results_table.setRowCount(len(self.temp_results))
        
        for row, result in enumerate(self.temp_results):
            # Чекбокс
            checkbox = QCheckBox()
            checkbox.setChecked(False)
            self.results_table.setCellWidget(row, 0, checkbox)
            
            # Название модели
            model_name = result.get('model_name', 'Unknown')
            model_item = QTableWidgetItem(model_name)
            model_item.setFlags(model_item.flags() & ~Qt.ItemIsEditable)
            self.results_table.setItem(row, 1, model_item)
            
            # Ответ или ошибка
            if result.get('success', False):
                response_text = result.get('response', '')
            else:
                error_text = result.get('error', 'Неизвестная ошибка')
                response_text = f"❌ Ошибка: {error_text}"
            
            response_item = QTableWidgetItem(response_text)
            response_item.setFlags(response_item.flags() & ~Qt.ItemIsEditable)
            # Перенос текста
            response_item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
            self.results_table.setItem(row, 2, response_item)
            
            # Устанавливаем высоту строки
            self.results_table.setRowHeight(row, 100)
        
        # Автоматически подгоняем ширину колонки модели
        self.results_table.resizeColumnToContents(1)
    
    def save_selected_results(self):
        """Сохранить выбранные результаты в БД."""
        if not self.current_prompt_id:
            QMessageBox.warning(self, "Ошибка", "Нет активного промта для сохранения!")
            return
        
        selected_results = []
        
        for row in range(self.results_table.rowCount()):
            checkbox = self.results_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                result = self.temp_results[row]
                if result.get('success', False):
                    selected_results.append({
                        'prompt_id': self.current_prompt_id,
                        'model_id': result['model_id'],
                        'response': result['response'],
                        'selected': 1
                    })
        
        if not selected_results:
            QMessageBox.information(self, "Информация", "Не выбрано ни одного результата для сохранения!")
            return
        
        # Сохраняем в БД
        try:
            self.db.save_results(selected_results)
            QMessageBox.information(
                self, 
                "Успех", 
                f"Сохранено {len(selected_results)} результатов!"
            )
            
            # Очищаем результаты
            self.clear_results()
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Ошибка", 
                f"Ошибка при сохранении: {str(e)}"
            )
    
    def clear_results(self):
        """Очистить таблицу результатов."""
        self.temp_results = []
        self.results_table.setRowCount(0)
        self.save_button.setEnabled(False)
        self.status_label.setText("Готов к работе")
    
    def new_request(self):
        """Начать новый запрос (очистить все поля)."""
        self.prompt_text.clear()
        self.tags_input.clear()
        self.clear_results()
        self.current_prompt_id = None
        self.saved_prompts_combo.setCurrentIndex(0)
        self.status_label.setText("Готов к работе")
    
    def closeEvent(self, event):
        """Обработчик закрытия окна."""
        # Останавливаем поток запросов, если он запущен
        if self.request_thread and self.request_thread.isRunning():
            self.request_thread.terminate()
            self.request_thread.wait()
        
        # Закрываем БД
        if self.db:
            self.db.close()
        
        event.accept()


def main():
    """Главная функция приложения."""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Современный стиль интерфейса
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
