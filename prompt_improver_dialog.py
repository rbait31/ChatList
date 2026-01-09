"""
Диалог для улучшения промтов с помощью AI.
Позволяет улучшить промт, получить альтернативные варианты и адаптировать под разные типы задач.
"""
import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLabel,
    QComboBox, QMessageBox, QTabWidget, QWidget, QGroupBox, QFrame
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
from typing import Optional
from prompt_improver import PromptImprover

logger = logging.getLogger(__name__)


class ImprovePromptThread(QThread):
    """Поток для асинхронного улучшения промта."""
    
    finished = pyqtSignal(dict)  # Сигнал с результатами
    
    def __init__(self, improver: PromptImprover, prompt: str, model_name: Optional[str] = None):
        """
        Инициализация потока.
        
        Args:
            improver: Экземпляр PromptImprover
            prompt: Текст промта для улучшения
            model_name: Название модели для улучшения
        """
        super().__init__()
        self.improver = improver
        self.prompt = prompt
        self.model_name = model_name
    
    def run(self):
        """Выполнение улучшения в отдельном потоке."""
        result = self.improver.improve_prompt(self.prompt, self.model_name)
        self.finished.emit(result)


class PromptImproverDialog(QDialog):
    """Диалог для улучшения промтов."""
    
    def __init__(self, improver: PromptImprover, original_prompt: str, parent=None):
        """
        Инициализация диалога.
        
        Args:
            improver: Экземпляр PromptImprover
            original_prompt: Исходный промт для улучшения
            parent: Родительское окно
        """
        super().__init__(parent)
        self.improver = improver
        self.original_prompt = original_prompt
        self.selected_prompt = None  # Выбранный промт для использования
        
        self.setWindowTitle("Улучшение промта")
        self.setMinimumSize(900, 700)
        
        # Поток для улучшения
        self.improve_thread: Optional[ImprovePromptThread] = None
        
        self.init_ui()
    
    def init_ui(self):
        """Инициализация интерфейса."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Исходный промт
        original_group = QGroupBox("Исходный промт")
        original_layout = QVBoxLayout()
        original_group.setLayout(original_layout)
        
        self.original_text = QTextEdit()
        self.original_text.setReadOnly(True)
        self.original_text.setPlainText(self.original_prompt)
        self.original_text.setMaximumHeight(100)
        original_layout.addWidget(self.original_text)
        
        layout.addWidget(original_group)
        
        # Индикатор загрузки (скрыт по умолчанию)
        self.loading_label = QLabel("⏳ Обработка промта, пожалуйста подождите...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setStyleSheet("color: blue; font-weight: bold; padding: 10px;")
        self.loading_label.setVisible(False)
        layout.addWidget(self.loading_label)
        
        # Выбор модели
        model_layout = QHBoxLayout()
        model_label = QLabel("Модель для улучшения:")
        model_layout.addWidget(model_label)
        
        self.model_combo = QComboBox()
        # Загружаем активные модели
        active_models = self.improver.model_manager.get_active_models()
        for model in active_models:
            self.model_combo.addItem(model['name'], model['name'])
        
        if not active_models:
            self.model_combo.addItem("Нет активных моделей", None)
            self.model_combo.setEnabled(False)
        
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch()
        
        # Кнопка улучшения
        self.improve_button = QPushButton("✨ Улучшить промт")
        self.improve_button.setMinimumHeight(35)
        self.improve_button.clicked.connect(self.start_improvement)
        model_layout.addWidget(self.improve_button)
        
        layout.addLayout(model_layout)
        
        # Вкладки с результатами
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Вкладка: Улучшенная версия
        self.improved_tab = QWidget()
        improved_layout = QVBoxLayout()
        self.improved_tab.setLayout(improved_layout)
        
        improved_label = QLabel("Улучшенная версия:")
        improved_label.setFont(QFont("Arial", 10, QFont.Bold))
        improved_layout.addWidget(improved_label)
        
        self.improved_text = QTextEdit()
        self.improved_text.setReadOnly(True)
        self.improved_text.setPlaceholderText("Нажмите 'Улучшить промт' для получения улучшенной версии...")
        improved_layout.addWidget(self.improved_text)
        
        use_improved_button = QPushButton("✅ Использовать эту версию")
        use_improved_button.clicked.connect(lambda: self.use_prompt(self.improved_text.toPlainText()))
        improved_layout.addWidget(use_improved_button)
        
        self.tabs.addTab(self.improved_tab, "Улучшенная версия")
        
        # Вкладка: Альтернативные варианты
        self.alternatives_tab = QWidget()
        alternatives_layout = QVBoxLayout()
        self.alternatives_tab.setLayout(alternatives_layout)
        
        alternatives_label = QLabel("Альтернативные варианты (2-3 варианта):")
        alternatives_label.setFont(QFont("Arial", 10, QFont.Bold))
        alternatives_layout.addWidget(alternatives_label)
        
        self.alternatives_widget = QWidget()
        self.alternatives_layout = QVBoxLayout()
        self.alternatives_widget.setLayout(self.alternatives_layout)
        alternatives_layout.addWidget(self.alternatives_widget)
        
        self.tabs.addTab(self.alternatives_tab, "Альтернативы")
        
        # Вкладка: Адаптации
        self.adaptations_tab = QWidget()
        adaptations_layout = QVBoxLayout()
        self.adaptations_tab.setLayout(adaptations_layout)
        
        adaptations_label = QLabel("Адаптация под типы задач:")
        adaptations_label.setFont(QFont("Arial", 10, QFont.Bold))
        adaptations_layout.addWidget(adaptations_label)
        
        # Адаптация под код
        code_group = QGroupBox("Для программирования (код)")
        code_layout = QVBoxLayout()
        code_group.setLayout(code_layout)
        
        self.code_text = QTextEdit()
        self.code_text.setReadOnly(True)
        self.code_text.setPlaceholderText("Адаптированная версия для работы с кодом...")
        self.code_text.setMaximumHeight(150)
        code_layout.addWidget(self.code_text)
        
        use_code_button = QPushButton("✅ Использовать версию для кода")
        use_code_button.clicked.connect(lambda: self.use_prompt(self.code_text.toPlainText()))
        code_layout.addWidget(use_code_button)
        
        adaptations_layout.addWidget(code_group)
        
        # Адаптация под анализ
        analysis_group = QGroupBox("Для анализа данных")
        analysis_layout = QVBoxLayout()
        analysis_group.setLayout(analysis_layout)
        
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        self.analysis_text.setPlaceholderText("Адаптированная версия для аналитических задач...")
        self.analysis_text.setMaximumHeight(150)
        analysis_layout.addWidget(self.analysis_text)
        
        use_analysis_button = QPushButton("✅ Использовать версию для анализа")
        use_analysis_button.clicked.connect(lambda: self.use_prompt(self.analysis_text.toPlainText()))
        analysis_layout.addWidget(use_analysis_button)
        
        adaptations_layout.addWidget(analysis_group)
        
        # Адаптация под креатив
        creative_group = QGroupBox("Для творческих задач")
        creative_layout = QVBoxLayout()
        creative_group.setLayout(creative_layout)
        
        self.creative_text = QTextEdit()
        self.creative_text.setReadOnly(True)
        self.creative_text.setPlaceholderText("Адаптированная версия для творческих задач...")
        self.creative_text.setMaximumHeight(150)
        creative_layout.addWidget(self.creative_text)
        
        use_creative_button = QPushButton("✅ Использовать версию для креатива")
        use_creative_button.clicked.connect(lambda: self.use_prompt(self.creative_text.toPlainText()))
        creative_layout.addWidget(use_creative_button)
        
        adaptations_layout.addWidget(creative_group)
        
        adaptations_layout.addStretch()
        
        self.tabs.addTab(self.adaptations_tab, "Адаптации")
        
        # Кнопки диалога
        button_layout = QHBoxLayout()
        
        copy_button = QPushButton("📋 Копировать исходный")
        copy_button.clicked.connect(lambda: self.copy_to_clipboard(self.original_prompt))
        button_layout.addWidget(copy_button)
        
        button_layout.addStretch()
        
        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        ok_button = QPushButton("Использовать выбранный")
        ok_button.clicked.connect(self.accept_selected)
        button_layout.addWidget(ok_button)
        
        layout.addLayout(button_layout)
    
    def start_improvement(self):
        """Начать процесс улучшения промта."""
        model_name = self.model_combo.currentData()
        
        if not model_name:
            QMessageBox.warning(self, "Ошибка", "Выберите модель для улучшения!")
            return
        
        # Очищаем предыдущие результаты
        self.improved_text.clear()
        self.improved_text.setPlaceholderText("Улучшение промта...")
        
        # Очищаем альтернативы
        for i in reversed(range(self.alternatives_layout.count())):
            self.alternatives_layout.itemAt(i).widget().setParent(None)
        
        self.code_text.clear()
        self.analysis_text.clear()
        self.creative_text.clear()
        
        # Блокируем кнопку и показываем индикатор
        self.improve_button.setEnabled(False)
        self.improve_button.setText("⏳ Обработка...")
        self.loading_label.setVisible(True)
        
        # Запускаем улучшение в отдельном потоке
        self.improve_thread = ImprovePromptThread(self.improver, self.original_prompt, model_name)
        self.improve_thread.finished.connect(self.on_improvement_finished)
        self.improve_thread.start()
    
    def on_improvement_finished(self, result: dict):
        """Обработчик завершения улучшения."""
        self.improve_button.setEnabled(True)
        self.improve_button.setText("✨ Улучшить промт")
        self.loading_label.setVisible(False)
        
        if not result.get('success'):
            error = result.get('error', 'Неизвестная ошибка')
            QMessageBox.critical(self, "Ошибка", f"Не удалось улучшить промт:\n{error}")
            self.improved_text.setPlaceholderText("Ошибка при улучшении промта")
            return
        
        # Отображаем улучшенную версию
        improved = result.get('improved', '')
        if improved:
            self.improved_text.setPlainText(improved)
        else:
            self.improved_text.setPlaceholderText("Не удалось получить улучшенную версию")
        
        # Отображаем альтернативы
        alternatives = result.get('alternatives', [])
        if alternatives:
            for idx, alt in enumerate(alternatives, 1):
                alt_group = QGroupBox(f"Вариант {idx}")
                alt_layout = QVBoxLayout()
                alt_group.setLayout(alt_layout)
                
                alt_text = QTextEdit()
                alt_text.setReadOnly(True)
                alt_text.setPlainText(alt)
                alt_text.setMaximumHeight(100)
                alt_layout.addWidget(alt_text)
                
                use_alt_button = QPushButton(f"✅ Использовать вариант {idx}")
                use_alt_button.clicked.connect(lambda checked, text=alt: self.use_prompt(text))
                alt_layout.addWidget(use_alt_button)
                
                self.alternatives_layout.addWidget(alt_group)
        else:
            no_alt_label = QLabel("Альтернативные варианты не найдены")
            no_alt_label.setStyleSheet("color: gray;")
            self.alternatives_layout.addWidget(no_alt_label)
        
        # Отображаем адаптации
        code_version = result.get('code_version', '')
        if code_version:
            self.code_text.setPlainText(code_version)
        
        analysis_version = result.get('analysis_version', '')
        if analysis_version:
            self.analysis_text.setPlainText(analysis_version)
        
        creative_version = result.get('creative_version', '')
        if creative_version:
            self.creative_text.setPlainText(creative_version)
        
        QMessageBox.information(self, "Успех", "Промт успешно улучшен!")
    
    def use_prompt(self, prompt_text: str):
        """Выбрать промт для использования."""
        if not prompt_text or not prompt_text.strip():
            QMessageBox.warning(self, "Ошибка", "Выбранный промт пуст!")
            return
        
        self.selected_prompt = prompt_text.strip()
        QMessageBox.information(
            self,
            "Выбрано",
            "Промт выбран для использования.\nНажмите 'Использовать выбранный' для применения."
        )
    
    def accept_selected(self):
        """Принять диалог с выбранным промтом."""
        # Если не выбран конкретный вариант, используем улучшенный
        if not self.selected_prompt:
            self.selected_prompt = self.improved_text.toPlainText().strip()
        
        if not self.selected_prompt:
            QMessageBox.warning(self, "Ошибка", "Выберите вариант промта для использования!")
            return
        
        self.accept()
    
    def copy_to_clipboard(self, text: str):
        """Скопировать текст в буфер обмена."""
        from PyQt5.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QMessageBox.information(self, "Успех", "Текст скопирован в буфер обмена!")
    
    def get_selected_prompt(self) -> Optional[str]:
        """
        Получить выбранный промт.
        
        Returns:
            Выбранный промт или None
        """
        return self.selected_prompt if self.selected_prompt else None
    
    def closeEvent(self, event):
        """Обработчик закрытия окна."""
        # Останавливаем поток, если он запущен
        if self.improve_thread and self.improve_thread.isRunning():
            self.improve_thread.terminate()
            self.improve_thread.wait()
        event.accept()

