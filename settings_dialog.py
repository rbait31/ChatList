"""
Диалог настроек приложения.
Позволяет выбрать тему и размер шрифта.
"""
import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QSpinBox, QGroupBox, QDialogButtonBox
)
from PyQt5.QtCore import Qt
from db import Database

logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
    """Диалог настроек приложения."""
    
    def __init__(self, db: Database, parent=None):
        """
        Инициализация диалога настроек.
        
        Args:
            db: Экземпляр базы данных
            parent: Родительское окно
        """
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Настройки")
        self.setMinimumSize(400, 250)
        self.setModal(True)
        
        self.init_ui()
        self.load_settings()
    
    def init_ui(self):
        """Инициализация интерфейса."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Группа выбора темы
        theme_group = QGroupBox("Тема интерфейса")
        theme_layout = QVBoxLayout()
        theme_group.setLayout(theme_layout)
        
        theme_label = QLabel("Выберите тему:")
        theme_layout.addWidget(theme_label)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Светлая", "light")
        self.theme_combo.addItem("Темная", "dark")
        theme_layout.addWidget(self.theme_combo)
        
        layout.addWidget(theme_group)
        
        # Группа размера шрифта
        font_group = QGroupBox("Размер шрифта")
        font_layout = QVBoxLayout()
        font_group.setLayout(font_layout)
        
        font_label = QLabel("Размер шрифта (8-20):")
        font_layout.addWidget(font_label)
        
        font_size_layout = QHBoxLayout()
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setMinimum(8)
        self.font_size_spin.setMaximum(20)
        self.font_size_spin.setValue(10)
        self.font_size_spin.setSuffix(" pt")
        font_size_layout.addWidget(self.font_size_spin)
        font_size_layout.addStretch()
        
        font_layout.addLayout(font_size_layout)
        
        layout.addWidget(font_group)
        
        layout.addStretch()
        
        # Кнопки диалога
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def load_settings(self):
        """Загрузить настройки из базы данных."""
        try:
            # Загружаем тему
            theme = self.db.get_setting("theme", "light")
            index = self.theme_combo.findData(theme)
            if index >= 0:
                self.theme_combo.setCurrentIndex(index)
            else:
                self.theme_combo.setCurrentIndex(0)  # По умолчанию светлая
            
            # Загружаем размер шрифта
            font_size = self.db.get_setting("font_size", "10")
            try:
                font_size_int = int(font_size)
                if 8 <= font_size_int <= 20:
                    self.font_size_spin.setValue(font_size_int)
            except ValueError:
                self.font_size_spin.setValue(10)  # По умолчанию 10
        except Exception as e:
            logger.error(f"Ошибка при загрузке настроек: {str(e)}")
    
    def save_settings(self):
        """Сохранить настройки в базу данных."""
        try:
            # Сохраняем тему
            theme = self.theme_combo.currentData()
            self.db.set_setting("theme", theme)
            
            # Сохраняем размер шрифта
            font_size = str(self.font_size_spin.value())
            self.db.set_setting("font_size", font_size)
            
            logger.info(f"Настройки сохранены: theme={theme}, font_size={font_size}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении настроек: {str(e)}")
            return False
    
    def accept(self):
        """Обработчик нажатия OK."""
        if self.save_settings():
            super().accept()
    
    def get_theme(self) -> str:
        """
        Получить выбранную тему.
        
        Returns:
            Название темы ("light" или "dark")
        """
        return self.theme_combo.currentData()
    
    def get_font_size(self) -> int:
        """
        Получить выбранный размер шрифта.
        
        Returns:
            Размер шрифта
        """
        return self.font_size_spin.value()
