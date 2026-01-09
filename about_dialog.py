"""
Диалог "О программе".
Выводит краткую информацию о программе ChatList.
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QDialogButtonBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon


class AboutDialog(QDialog):
    """Диалог 'О программе'."""
    
    def __init__(self, parent=None):
        """
        Инициализация диалога.
        
        Args:
            parent: Родительское окно
        """
        super().__init__(parent)
        self.setWindowTitle("О программе")
        self.setMinimumSize(500, 400)
        self.setModal(True)
        
        self.init_ui()
    
    def init_ui(self):
        """Инициализация интерфейса."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Заголовок
        title_label = QLabel("ChatList")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Версия
        version_label = QLabel("Версия 1.0.0")
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)
        
        layout.addSpacing(20)
        
        # Описание программы
        description = QTextEdit()
        description.setReadOnly(True)
        description.setPlainText(
            "ChatList — это приложение для сравнения ответов различных нейросетей.\n\n"
            "Основные возможности:\n"
            "• Отправка одного промта в несколько AI-моделей одновременно\n"
            "• Сравнение ответов в удобной таблице\n"
            "• Сохранение лучших результатов в базу данных\n"
            "• Управление промтами и моделями\n"
            "• Улучшение промтов с помощью AI-ассистента\n"
            "• Экспорт результатов в Markdown и JSON\n"
            "• Настройка темы и размера шрифта\n\n"
            "Технологии:\n"
            "• Python 3.11+\n"
            "• PyQt5 для графического интерфейса\n"
            "• SQLite для хранения данных\n"
            "• Поддержка OpenAI, DeepSeek, Groq, OpenRouter API\n\n"
            "Разработано для удобного сравнения ответов различных AI-моделей."
        )
        description.setMinimumHeight(250)
        layout.addWidget(description)
        
        layout.addSpacing(10)
        
        # Копирайт
        copyright_label = QLabel("© 2024 ChatList. Все права защищены.")
        copyright_label.setAlignment(Qt.AlignCenter)
        copyright_label.setStyleSheet("color: gray;")
        layout.addWidget(copyright_label)
        
        layout.addStretch()
        
        # Кнопка закрытия
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)
    
    def accept(self):
        """Обработчик нажатия OK."""
        self.close()
