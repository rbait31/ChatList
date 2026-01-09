"""
Главный модуль приложения ChatList.
Реализует интерфейс для отправки промтов в нейросети и сравнения ответов.
"""
import sys
import logging
import traceback
from datetime import datetime
from typing import List, Dict, Optional
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLineEdit, QComboBox, QTableWidget,
    QTableWidgetItem, QCheckBox, QLabel, QMessageBox, QHeaderView,
    QSplitter, QMenuBar, QMenu, QFileDialog, QDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon

from db import Database
from models import ModelManager
from model_settings_dialog import ModelSettingsDialog
from view_results_dialog import ViewResultsDialog
from prompts_dialog import PromptsDialog
from prompt_improver import PromptImprover
from prompt_improver_dialog import PromptImproverDialog


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
        self.logger = logging.getLogger(__name__)
        self.setWindowTitle("ChatList - Сравнение ответов нейросетей")
        self.setGeometry(100, 100, 1400, 900)
        
        # Устанавливаем иконку приложения
        try:
            icon = QIcon("app.ico")
            if not icon.isNull():
                self.setWindowIcon(icon)
                self.logger.info("Иконка приложения загружена успешно")
            else:
                self.logger.warning("Не удалось загрузить иконку app.ico")
        except Exception as e:
            self.logger.warning(f"Ошибка при загрузке иконки: {str(e)}")
        
        try:
            # Инициализация БД и менеджера моделей
            self.db = Database()
            self.model_manager = ModelManager(self.db)
            self.prompt_improver = PromptImprover(self.model_manager)
            self.logger.info("Инициализация приложения завершена успешно")
        except Exception as e:
            self.logger.error(f"Ошибка при инициализации: {str(e)}\n{traceback.format_exc()}")
            QMessageBox.critical(
                None,
                "Ошибка инициализации",
                f"Не удалось инициализировать приложение:\n{str(e)}\n\n"
                f"Проверьте файл chatlist.log для подробностей."
            )
            raise
        
        # Временное хранилище результатов (в памяти)
        self.temp_results: List[Dict] = []
        self.current_prompt_id: Optional[int] = None
        
        # Поток для запросов
        self.request_thread: Optional[RequestThread] = None
        
        self.init_ui()
        self.load_saved_prompts()
    
    def init_ui(self):
        """Инициализация интерфейса."""
        # Создаем меню
        self.create_menu()
        
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
        
        # Поиск по промтам
        search_label = QLabel("Поиск:")
        prompt_controls.addWidget(search_label)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по тексту...")
        self.search_input.setMinimumWidth(150)
        self.search_input.textChanged.connect(self.on_search_changed)
        prompt_controls.addWidget(self.search_input)
        
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
        
        # Кнопки управления промтом
        prompt_buttons_layout = QHBoxLayout()
        
        # Кнопка улучшения промта
        improve_button = QPushButton("✨ Улучшить промт")
        improve_button.setMinimumHeight(35)
        improve_button.clicked.connect(self.improve_prompt)
        prompt_buttons_layout.addWidget(improve_button)
        
        prompt_buttons_layout.addStretch()
        
        # Кнопка отправки
        send_button = QPushButton("Отправить запрос")
        send_button.setMinimumHeight(35)
        send_button.clicked.connect(self.send_prompt)
        prompt_buttons_layout.addWidget(send_button)
        
        prompt_layout.addLayout(prompt_buttons_layout)
        
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
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["Выбрано", "Модель", "Ответ", "Действия"])
        
        # Настройка колонок
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Чекбокс
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Модель
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # Ответ
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Действия
        
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.results_table.setSortingEnabled(True)  # Включаем сортировку
        self.results_table.setWordWrap(True)  # Включаем перенос текста
        # Обработчик двойного клика для просмотра полного текста
        self.results_table.itemDoubleClicked.connect(self.view_full_response_main)
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
        
        # Кнопка просмотра результатов
        view_results_button = QPushButton("Просмотр результатов")
        view_results_button.setMinimumHeight(35)
        view_results_button.clicked.connect(self.view_saved_results)
        control_layout.addWidget(view_results_button)
        
        # Кнопка экспорта
        export_button = QPushButton("Экспорт")
        export_button.setMinimumHeight(35)
        export_button.clicked.connect(self.export_results)
        control_layout.addWidget(export_button)
        
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
    
    def improve_prompt(self):
        """Открыть диалог улучшения промта."""
        current_prompt = self.prompt_text.toPlainText().strip()
        
        if not current_prompt:
            reply = QMessageBox.question(
                self,
                "Пустой промт",
                "Поле промта пусто. Хотите создать новый промт с помощью AI-ассистента?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
            current_prompt = "Создай промт для..."  # Базовый промт для создания
        
        # Проверяем наличие активных моделей
        active_models = self.model_manager.get_active_models()
        if not active_models:
            QMessageBox.warning(
                self,
                "Ошибка",
                "Нет активных моделей для улучшения промта!\n"
                "Добавьте модели через меню 'Настройки' → 'Управление моделями'."
            )
            return
        
        try:
            dialog = PromptImproverDialog(self.prompt_improver, current_prompt, self)
            if dialog.exec_() == QDialog.Accepted:
                improved_prompt = dialog.get_selected_prompt()
                if improved_prompt:
                    self.prompt_text.setPlainText(improved_prompt)
                    QMessageBox.information(
                        self,
                        "Успех",
                        "Улучшенный промт подставлен в поле ввода!"
                    )
        except Exception as e:
            self.logger.error(f"Ошибка при открытии диалога улучшения: {str(e)}")
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось открыть диалог улучшения промта:\n{str(e)}"
            )
    
    def send_prompt(self):
        """Отправить промт во все активные модели."""
        prompt_text = self.prompt_text.toPlainText().strip()
        
        if not prompt_text:
            QMessageBox.warning(self, "Ошибка", "Введите промт перед отправкой!")
            return
        
        # Проверяем наличие активных моделей
        try:
            active_models = self.model_manager.get_active_models()
            if not active_models:
                error_msg = (
                    "Нет активных моделей!\n\n"
                    "Добавьте модели через меню:\n"
                    "Настройки → Управление моделями\n\n"
                    "Убедитесь, что:\n"
                    "1. Модель добавлена в базу данных\n"
                    "2. У модели установлен флаг 'Активна'\n"
                    "3. В файле .env указан правильный API-ключ"
                )
                self.logger.warning("Попытка отправить запрос без активных моделей")
                QMessageBox.warning(self, "Ошибка", error_msg)
                return
        except Exception as e:
            error_msg = f"Ошибка при получении списка моделей: {str(e)}"
            self.logger.error(error_msg)
            QMessageBox.critical(self, "Ошибка", error_msg)
            return
        
        # Очищаем предыдущие результаты
        self.clear_results()
        
        # Сохраняем промт в БД (если новый)
        try:
            tags = self.tags_input.text().strip() or None
            self.current_prompt_id = self.db.create_prompt(prompt_text, tags)
        except Exception as e:
            QMessageBox.warning(
                self,
                "Ошибка БД",
                f"Не удалось сохранить промт в БД: {str(e)}\nПродолжаем без сохранения..."
            )
            self.current_prompt_id = None
        
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
        failed = total - successful
        
        status_text = f"Готово: {successful} из {total} запросов успешны"
        if failed > 0:
            status_text += f" ({failed} ошибок)"
        
        self.status_label.setText(status_text)
        self.save_button.setEnabled(True)
        
        # Показываем предупреждение, если все запросы неудачны
        if successful == 0 and total > 0:
            # Собираем все ошибки для подробного сообщения
            errors = []
            for r in results:
                if r.get('error'):
                    model_name = r.get('model_name', 'Unknown')
                    error = r.get('error', 'Неизвестная ошибка')
                    errors.append(f"• {model_name}: {error}")
            
            error_details = "\n".join(errors[:5])  # Показываем первые 5 ошибок
            if len(errors) > 5:
                error_details += f"\n... и еще {len(errors) - 5} ошибок"
            
            error_msg = (
                "Все запросы завершились с ошибками!\n\n"
                "Детали ошибок:\n" + error_details + "\n\n"
                "Проверьте:\n"
                "1. Правильность API-ключей в файле .env\n"
                "2. Наличие интернет-соединения\n"
                "3. Доступность выбранных моделей\n"
                "4. Настройки моделей (API URL, имя переменной окружения)"
            )
            self.logger.error(f"Все запросы завершились с ошибками: {errors}")
            QMessageBox.warning(self, "Внимание", error_msg)
    
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
            # Сохраняем полный текст для просмотра
            response_item.setData(Qt.UserRole + 1, response_text)
            self.results_table.setItem(row, 2, response_item)
            
            # Кнопка "Открыть" для просмотра в Markdown
            open_button = QPushButton("Открыть")
            open_button.setMaximumWidth(80)
            open_button.clicked.connect(
                lambda checked, r=row: self.open_markdown_viewer(r)
            )
            self.results_table.setCellWidget(row, 3, open_button)
            
            # Автоматически рассчитываем высоту строки на основе длины текста
            # Базовое значение: примерно 20 пикселей на строку текста
            lines_count = len(response_text.split('\n'))
            # Если одна строка, считаем примерное количество строк с учетом переноса
            if lines_count == 1:
                # Примерно 60 символов на строку в ячейке
                estimated_lines = max(1, len(response_text) // 60)
            else:
                estimated_lines = lines_count
            
            # Минимальная высота 60, максимальная 400 пикселей
            row_height = min(max(60, estimated_lines * 25 + 20), 400)
            self.results_table.setRowHeight(row, row_height)
            
            # Добавляем подсказку
            response_item.setToolTip("Двойной клик для просмотра полного текста")
        
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
    
    def create_menu(self):
        """Создать меню приложения."""
        menubar = self.menuBar()
        
        # Меню "Настройки"
        settings_menu = menubar.addMenu("Настройки")
        
        model_settings_action = settings_menu.addAction("Управление моделями")
        model_settings_action.triggered.connect(self.open_model_settings)
        
        # Меню "Данные"
        data_menu = menubar.addMenu("Данные")
        
        view_prompts_action = data_menu.addAction("Управление промтами")
        view_prompts_action.triggered.connect(self.view_prompts)
        
        view_results_action = data_menu.addAction("Просмотр сохраненных результатов")
        view_results_action.triggered.connect(self.view_saved_results)
        
        # Меню "Файл"
        file_menu = menubar.addMenu("Файл")
        
        export_action = file_menu.addAction("Экспорт результатов")
        export_action.triggered.connect(self.export_results)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("Выход")
        exit_action.triggered.connect(self.close)
    
    def open_model_settings(self):
        """Открыть диалог управления моделями."""
        dialog = ModelSettingsDialog(self.db, self)
        if dialog.exec_() == QDialog.Accepted:
            # Обновляем менеджер моделей после изменений
            self.model_manager.refresh_clients()
            QMessageBox.information(self, "Успех", "Настройки моделей обновлены!")
    
    def view_prompts(self):
        """Открыть диалог управления промтами."""
        dialog = PromptsDialog(self.db, self)
        if dialog.exec_() == QDialog.Accepted:
            # Обновляем список промтов в ComboBox
            self.load_saved_prompts()
    
    def view_saved_results(self):
        """Открыть диалог просмотра сохраненных результатов."""
        dialog = ViewResultsDialog(self.db, self)
        dialog.exec_()
    
    def open_markdown_viewer(self, row: int):
        """Открыть ответ нейросети в форматированном Markdown."""
        if row >= len(self.temp_results):
            return
        
        result = self.temp_results[row]
        
        # Получаем текст ответа
        if result.get('success', False):
            markdown_text = result.get('response', '')
        else:
            error_text = result.get('error', 'Неизвестная ошибка')
            markdown_text = f"## Ошибка\n\n{error_text}"
        
        # Получаем название модели
        model_name = result.get('model_name', 'Unknown')
        
        # Конвертируем Markdown в HTML
        try:
            import markdown
            html_content = markdown.markdown(
                markdown_text,
                extensions=['extra', 'codehilite', 'nl2br', 'sane_lists']
            )
        except ImportError:
            # Если markdown не установлен, используем простой HTML
            html_content = markdown_text.replace('\n', '<br>')
            QMessageBox.warning(
                self,
                "Предупреждение",
                "Библиотека markdown не установлена. Установите её командой:\npip install markdown"
            )
        except Exception as e:
            # Если ошибка конвертации, показываем как обычный текст
            html_content = f"<pre>{markdown_text}</pre>"
            self.logger.warning(f"Ошибка конвертации Markdown: {str(e)}")
        
        # Создаем диалог для отображения Markdown
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Ответ модели: {model_name}")
        dialog.setMinimumSize(900, 700)
        
        layout = QVBoxLayout()
        dialog.setLayout(layout)
        
        # Метка с информацией
        info_label = QLabel(f"Ответ модели: {model_name}")
        info_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(info_label)
        
        # Текстовое поле с форматированным Markdown
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        # Устанавливаем HTML контент
        text_edit.setHtml(f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: 'Segoe UI', Arial, sans-serif;
                    font-size: 11pt;
                    line-height: 1.6;
                    padding: 10px;
                }}
                h1, h2, h3, h4, h5, h6 {{
                    color: #2c3e50;
                    margin-top: 20px;
                    margin-bottom: 10px;
                }}
                code {{
                    background-color: #f4f4f4;
                    padding: 2px 5px;
                    border-radius: 3px;
                    font-family: 'Consolas', 'Courier New', monospace;
                }}
                pre {{
                    background-color: #f4f4f4;
                    padding: 10px;
                    border-radius: 5px;
                    overflow-x: auto;
                }}
                pre code {{
                    background-color: transparent;
                    padding: 0;
                }}
                ul, ol {{
                    margin-left: 20px;
                }}
                blockquote {{
                    border-left: 4px solid #ddd;
                    margin-left: 0;
                    padding-left: 20px;
                    color: #666;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin: 10px 0;
                }}
                table th, table td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }}
                table th {{
                    background-color: #f2f2f2;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """)
        layout.addWidget(text_edit)
        
        # Кнопки управления
        button_layout = QHBoxLayout()
        
        # Кнопка копирования
        copy_button = QPushButton("Копировать текст")
        copy_button.clicked.connect(lambda: self.copy_to_clipboard(markdown_text, text_edit))
        button_layout.addWidget(copy_button)
        
        button_layout.addStretch()
        
        # Кнопка закрытия
        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(dialog.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        dialog.exec_()
    
    def copy_to_clipboard(self, text: str, text_edit: QTextEdit):
        """Копировать текст в буфер обмена."""
        from PyQt5.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QMessageBox.information(self, "Успех", "Текст скопирован в буфер обмена!")
    
    def view_full_response_main(self, item):
        """Просмотр полного текста ответа в отдельном окне (из главной таблицы)."""
        # Проверяем, что клик был по колонке "Ответ" (индекс 2)
        if item.column() == 2:
            full_text = item.data(Qt.UserRole + 1) or item.text()
            
            # Получаем название модели из той же строки
            model_item = self.results_table.item(item.row(), 1)
            model_name = model_item.text() if model_item else "Unknown"
            
            # Создаем диалог для отображения полного текста
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Полный текст ответа - {model_name}")
            dialog.setMinimumSize(800, 600)
            
            layout = QVBoxLayout()
            dialog.setLayout(layout)
            
            # Метка с информацией
            info_label = QLabel(f"Ответ модели: {model_name}")
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
    
    def on_search_changed(self, text: str):
        """Обработчик изменения текста поиска."""
        search_text = text.strip()
        if search_text:
            prompts = self.db.get_prompts(search=search_text)
        else:
            prompts = self.db.get_prompts()
        
        # Обновляем ComboBox
        self.saved_prompts_combo.clear()
        self.saved_prompts_combo.addItem("-- Выберите промт --", None)
        
        for prompt in prompts:
            date_str = prompt['date'][:10] if prompt['date'] else ""
            tags_str = f" [{prompt['tags']}]" if prompt['tags'] else ""
            display_text = f"{date_str}{tags_str}: {prompt['prompt'][:50]}..."
            self.saved_prompts_combo.addItem(display_text, prompt['id'])
    
    def export_results(self):
        """Экспортировать результаты в файл."""
        if not self.temp_results:
            QMessageBox.warning(self, "Ошибка", "Нет результатов для экспорта!")
            return
        
        # Выбираем формат
        format_dialog = QMessageBox(self)
        format_dialog.setWindowTitle("Выбор формата экспорта")
        format_dialog.setText("Выберите формат экспорта:")
        md_button = format_dialog.addButton("Markdown", QMessageBox.AcceptRole)
        json_button = format_dialog.addButton("JSON", QMessageBox.AcceptRole)
        cancel_button = format_dialog.addButton("Отмена", QMessageBox.RejectRole)
        format_dialog.exec_()
        
        if format_dialog.clickedButton() == cancel_button:
            return
        
        # Выбираем файл для сохранения
        if format_dialog.clickedButton() == md_button:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Сохранить как Markdown", "", "Markdown Files (*.md);;All Files (*)"
            )
            if file_path:
                self.export_to_markdown(file_path)
        elif format_dialog.clickedButton() == json_button:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Сохранить как JSON", "", "JSON Files (*.json);;All Files (*)"
            )
            if file_path:
                self.export_to_json(file_path)
    
    def export_to_markdown(self, file_path: str):
        """Экспортировать результаты в Markdown."""
        try:
            prompt_text = self.prompt_text.toPlainText()
            tags = self.tags_input.text()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("# Результаты сравнения нейросетей\n\n")
                f.write(f"**Промт:** {prompt_text}\n\n")
                if tags:
                    f.write(f"**Теги:** {tags}\n\n")
                f.write(f"**Дата:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("---\n\n")
                
                for i, result in enumerate(self.temp_results, 1):
                    model_name = result.get('model_name', 'Unknown')
                    f.write(f"## {i}. {model_name}\n\n")
                    
                    if result.get('success', False):
                        response = result.get('response', '')
                        f.write(f"{response}\n\n")
                    else:
                        error = result.get('error', 'Неизвестная ошибка')
                        f.write(f"❌ **Ошибка:** {error}\n\n")
                    
                    f.write("---\n\n")
            
            QMessageBox.information(self, "Успех", f"Результаты экспортированы в {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при экспорте: {str(e)}")
    
    def export_to_json(self, file_path: str):
        """Экспортировать результаты в JSON."""
        import json
        try:
            prompt_text = self.prompt_text.toPlainText()
            tags = self.tags_input.text()
            
            export_data = {
                "prompt": prompt_text,
                "tags": tags,
                "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "results": []
            }
            
            for result in self.temp_results:
                export_data["results"].append({
                    "model_id": result.get('model_id'),
                    "model_name": result.get('model_name'),
                    "success": result.get('success', False),
                    "response": result.get('response', ''),
                    "error": result.get('error')
                })
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            QMessageBox.information(self, "Успех", f"Результаты экспортированы в {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при экспорте: {str(e)}")
    
    def closeEvent(self, event):
        """Обработчик закрытия окна."""
        try:
            # Останавливаем поток запросов, если он запущен
            if self.request_thread and self.request_thread.isRunning():
                self.logger.info("Остановка потока запросов...")
                self.request_thread.terminate()
                self.request_thread.wait()
            
            # Закрываем БД
            if self.db:
                self.db.close()
                self.logger.info("База данных закрыта")
            
            self.logger.info("Приложение закрыто")
            event.accept()
        except Exception as e:
            self.logger.error(f"Ошибка при закрытии приложения: {str(e)}\n{traceback.format_exc()}")
            event.accept()  # Все равно закрываем


def main():
    """Главная функция приложения."""
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('chatlist.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger = logging.getLogger(__name__)
    
    try:
        app = QApplication(sys.argv)
        app.setStyle('Fusion')  # Современный стиль интерфейса
        
        # Устанавливаем иконку для приложения (отображается в панели задач)
        try:
            app_icon = QIcon("app.ico")
            if not app_icon.isNull():
                app.setWindowIcon(app_icon)
                logger.info("Иконка приложения установлена")
        except Exception as e:
            logger.warning(f"Не удалось установить иконку приложения: {str(e)}")
        
        window = MainWindow()
        window.show()
        
        logger.info("Приложение ChatList запущено успешно")
        sys.exit(app.exec_())
    except Exception as e:
        error_msg = f"Критическая ошибка при запуске приложения: {str(e)}\n{traceback.format_exc()}"
        logger.critical(error_msg)
        print(f"\n{'='*60}")
        print("КРИТИЧЕСКАЯ ОШИБКА!")
        print(f"{'='*60}")
        print(error_msg)
        print(f"{'='*60}\n")
        input("Нажмите Enter для выхода...")
        sys.exit(1)


if __name__ == "__main__":
    main()
