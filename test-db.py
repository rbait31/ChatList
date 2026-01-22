"""
Тестовая программа для просмотра и редактирования SQLite баз данных.
Позволяет просматривать таблицы, данные с пагинацией и выполнять CRUD операции.
"""
import sys
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QFileDialog, QLabel, QLineEdit, QDialog,
    QFormLayout, QTextEdit, QSpinBox, QComboBox, QGroupBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from typing import List, Dict, Optional, Any


class DatabaseViewer(QMainWindow):
    """Главное окно просмотра базы данных."""
    
    def __init__(self):
        super().__init__()
        self.db_path = None
        self.conn = None
        self.current_table = None
        self.current_page = 1
        self.page_size = 50
        self.total_rows = 0
        
        self.setWindowTitle("SQLite Database Viewer")
        self.setGeometry(100, 100, 1200, 800)
        
        self.init_ui()
    
    def init_ui(self):
        """Инициализация интерфейса."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Панель выбора файла
        file_panel = QWidget()
        file_layout = QHBoxLayout()
        file_panel.setLayout(file_layout)
        
        self.file_label = QLabel("Файл не выбран")
        self.file_label.setFont(QFont("Arial", 10))
        file_layout.addWidget(self.file_label)
        
        open_file_button = QPushButton("Выбрать файл БД")
        open_file_button.clicked.connect(self.open_database)
        file_layout.addWidget(open_file_button)
        
        layout.addWidget(file_panel)
        
        # Список таблиц
        tables_group = QGroupBox("Таблицы базы данных")
        tables_layout = QVBoxLayout()
        tables_group.setLayout(tables_layout)
        
        self.tables_list = QTableWidget()
        self.tables_list.setColumnCount(2)
        self.tables_list.setHorizontalHeaderLabels(["Название таблицы", "Действия"])
        self.tables_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tables_list.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tables_list.setSelectionBehavior(QTableWidget.SelectRows)
        tables_layout.addWidget(self.tables_list)
        
        layout.addWidget(tables_group)
        
        # Панель данных таблицы
        data_group = QGroupBox("Данные таблицы")
        data_layout = QVBoxLayout()
        data_group.setLayout(data_layout)
        
        # Информация о таблице
        info_layout = QHBoxLayout()
        self.table_info_label = QLabel("Выберите таблицу для просмотра")
        info_layout.addWidget(self.table_info_label)
        
        # Пагинация
        pagination_layout = QHBoxLayout()
        pagination_layout.addStretch()
        
        self.page_info_label = QLabel("")
        pagination_layout.addWidget(self.page_info_label)
        
        prev_button = QPushButton("◀ Предыдущая")
        prev_button.clicked.connect(self.prev_page)
        pagination_layout.addWidget(prev_button)
        
        self.page_spin = QSpinBox()
        self.page_spin.setMinimum(1)
        self.page_spin.setMaximum(1)
        self.page_spin.valueChanged.connect(self.go_to_page)
        pagination_layout.addWidget(self.page_spin)
        
        page_size_label = QLabel("из")
        pagination_layout.addWidget(page_size_label)
        
        self.total_pages_label = QLabel("1")
        pagination_layout.addWidget(self.total_pages_label)
        
        next_button = QPushButton("Следующая ▶")
        next_button.clicked.connect(self.next_page)
        pagination_layout.addWidget(next_button)
        
        pagination_layout.addStretch()
        
        info_layout.addLayout(pagination_layout)
        data_layout.addLayout(info_layout)
        
        # Таблица данных
        self.data_table = QTableWidget()
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.data_table.setEditTriggers(QTableWidget.NoEditTriggers)  # Редактирование через диалог
        data_layout.addWidget(self.data_table)
        
        # Кнопки CRUD
        crud_layout = QHBoxLayout()
        
        create_button = QPushButton("➕ Создать")
        create_button.clicked.connect(self.create_record)
        crud_layout.addWidget(create_button)
        
        read_button = QPushButton("👁 Просмотр")
        read_button.clicked.connect(self.read_record)
        crud_layout.addWidget(read_button)
        
        update_button = QPushButton("✏️ Редактировать")
        update_button.clicked.connect(self.update_record)
        crud_layout.addWidget(update_button)
        
        delete_button = QPushButton("🗑️ Удалить")
        delete_button.clicked.connect(self.delete_record)
        crud_layout.addWidget(delete_button)
        
        refresh_button = QPushButton("🔄 Обновить")
        refresh_button.clicked.connect(self.refresh_table)
        crud_layout.addWidget(refresh_button)
        
        crud_layout.addStretch()
        
        data_layout.addLayout(crud_layout)
        
        layout.addWidget(data_group)
    
    def open_database(self):
        """Открыть файл базы данных."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл базы данных SQLite",
            "",
            "SQLite Database (*.db *.sqlite *.sqlite3);;All Files (*)"
        )
        
        if file_path:
            try:
                if self.conn:
                    self.conn.close()
                
                self.db_path = file_path
                self.conn = sqlite3.connect(file_path)
                self.conn.row_factory = sqlite3.Row
                
                self.file_label.setText(f"Файл: {file_path}")
                self.load_tables()
                
                QMessageBox.information(self, "Успех", "База данных успешно открыта!")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось открыть базу данных:\n{str(e)}")
    
    def load_tables(self):
        """Загрузить список таблиц."""
        if not self.conn:
            return
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            tables = cursor.fetchall()
            
            self.tables_list.setRowCount(len(tables))
            
            for row, (table_name,) in enumerate(tables):
                # Название таблицы
                name_item = QTableWidgetItem(table_name)
                name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
                self.tables_list.setItem(row, 0, name_item)
                
                # Кнопка "Открыть"
                open_button = QPushButton("Открыть")
                open_button.clicked.connect(
                    lambda checked, t=table_name: self.open_table(t)
                )
                self.tables_list.setCellWidget(row, 1, open_button)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке таблиц:\n{str(e)}")
    
    def open_table(self, table_name: str):
        """Открыть таблицу для просмотра."""
        self.current_table = table_name
        self.current_page = 1
        self.load_table_data()
    
    def load_table_data(self):
        """Загрузить данные таблицы с пагинацией."""
        if not self.conn or not self.current_table:
            return
        
        try:
            cursor = self.conn.cursor()
            
            # Получаем структуру таблицы
            cursor.execute(f"PRAGMA table_info({self.current_table})")
            columns_info = cursor.fetchall()
            column_names = [col[1] for col in columns_info]
            
            # Подсчитываем общее количество строк
            cursor.execute(f"SELECT COUNT(*) FROM {self.current_table}")
            self.total_rows = cursor.fetchone()[0]
            
            # Вычисляем пагинацию
            total_pages = max(1, (self.total_rows + self.page_size - 1) // self.page_size)
            self.page_spin.setMaximum(total_pages)
            self.total_pages_label.setText(str(total_pages))
            self.page_spin.setValue(self.current_page)
            
            # Загружаем данные для текущей страницы
            offset = (self.current_page - 1) * self.page_size
            cursor.execute(f"SELECT * FROM {self.current_table} LIMIT ? OFFSET ?", 
                          (self.page_size, offset))
            rows = cursor.fetchall()
            
            # Настраиваем таблицу
            self.data_table.setColumnCount(len(column_names))
            self.data_table.setHorizontalHeaderLabels(column_names)
            self.data_table.setRowCount(len(rows))
            
            # Заполняем данные
            for row_idx, row in enumerate(rows):
                for col_idx, value in enumerate(row):
                    item = QTableWidgetItem(str(value) if value is not None else "NULL")
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    # Сохраняем исходное значение для редактирования
                    item.setData(Qt.UserRole, value)
                    self.data_table.setItem(row_idx, col_idx, item)
            
            # Автоматически подгоняем ширину колонок
            self.data_table.resizeColumnsToContents()
            
            # Обновляем информацию
            start_row = offset + 1
            end_row = min(offset + len(rows), self.total_rows)
            self.table_info_label.setText(
                f"Таблица: {self.current_table} | "
                f"Всего записей: {self.total_rows} | "
                f"Показано: {start_row}-{end_row}"
            )
            self.page_info_label.setText(
                f"Страница {self.current_page} из {total_pages}"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при загрузке данных:\n{str(e)}")
    
    def prev_page(self):
        """Перейти на предыдущую страницу."""
        if self.current_page > 1:
            self.current_page -= 1
            self.load_table_data()
    
    def next_page(self):
        """Перейти на следующую страницу."""
        total_pages = max(1, (self.total_rows + self.page_size - 1) // self.page_size)
        if self.current_page < total_pages:
            self.current_page += 1
            self.load_table_data()
    
    def go_to_page(self, page: int):
        """Перейти на указанную страницу."""
        self.current_page = page
        self.load_table_data()
    
    def refresh_table(self):
        """Обновить данные таблицы."""
        if self.current_table:
            self.load_table_data()
    
    def get_selected_row_data(self) -> Optional[Dict[str, Any]]:
        """Получить данные выбранной строки."""
        selected_rows = self.data_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Ошибка", "Выберите строку для редактирования!")
            return None
        
        row = selected_rows[0].row()
        data = {}
        for col in range(self.data_table.columnCount()):
            header = self.data_table.horizontalHeaderItem(col).text()
            item = self.data_table.item(row, col)
            if item:
                data[header] = item.data(Qt.UserRole)
        
        return data
    
    def create_record(self):
        """Создать новую запись."""
        if not self.current_table:
            QMessageBox.warning(self, "Ошибка", "Выберите таблицу!")
            return
        
        dialog = RecordEditDialog(self, self.conn, self.current_table, None)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_table()
    
    def read_record(self):
        """Просмотреть запись."""
        row_data = self.get_selected_row_data()
        if not row_data:
            return
        
        dialog = RecordViewDialog(self, row_data)
        dialog.exec_()
    
    def update_record(self):
        """Редактировать запись."""
        if not self.current_table:
            QMessageBox.warning(self, "Ошибка", "Выберите таблицу!")
            return
        
        row_data = self.get_selected_row_data()
        if not row_data:
            return
        
        dialog = RecordEditDialog(self, self.conn, self.current_table, row_data)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_table()
    
    def delete_record(self):
        """Удалить запись."""
        if not self.current_table:
            QMessageBox.warning(self, "Ошибка", "Выберите таблицу!")
            return
        
        row_data = self.get_selected_row_data()
        if not row_data:
            return
        
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Вы уверены, что хотите удалить эту запись?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                cursor = self.conn.cursor()
                
                # Получаем PRIMARY KEY
                cursor.execute(f"PRAGMA table_info({self.current_table})")
                columns_info = cursor.fetchall()
                pk_column = None
                for col in columns_info:
                    if col[5]:  # pk flag
                        pk_column = col[1]
                        break
                
                if not pk_column:
                    QMessageBox.warning(self, "Ошибка", "Не найден PRIMARY KEY для удаления!")
                    return
                
                pk_value = row_data[pk_column]
                cursor.execute(f"DELETE FROM {self.current_table} WHERE {pk_column} = ?", (pk_value,))
                self.conn.commit()
                
                QMessageBox.information(self, "Успех", "Запись успешно удалена!")
                self.refresh_table()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении:\n{str(e)}")
    
    def closeEvent(self, event):
        """Закрытие приложения."""
        if self.conn:
            self.conn.close()
        event.accept()


class RecordViewDialog(QDialog):
    """Диалог для просмотра записи."""
    
    def __init__(self, parent, row_data: Dict[str, Any]):
        super().__init__(parent)
        self.setWindowTitle("Просмотр записи")
        self.setMinimumWidth(600)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Отображаем данные
        for key, value in row_data.items():
            form_layout = QHBoxLayout()
            label = QLabel(f"{key}:")
            label.setFont(QFont("Arial", 9, QFont.Bold))
            form_layout.addWidget(label)
            
            value_label = QLabel(str(value) if value is not None else "NULL")
            value_label.setWordWrap(True)
            form_layout.addWidget(value_label)
            
            layout.addLayout(form_layout)
        
        # Кнопка закрытия
        button = QPushButton("Закрыть")
        button.clicked.connect(self.accept)
        layout.addWidget(button)


class RecordEditDialog(QDialog):
    """Диалог для создания/редактирования записи."""
    
    def __init__(self, parent, conn: sqlite3.Connection, table_name: str, 
                 row_data: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.conn = conn
        self.table_name = table_name
        self.row_data = row_data
        self.is_edit = row_data is not None
        
        self.setWindowTitle("Редактировать запись" if self.is_edit else "Создать запись")
        self.setMinimumWidth(500)
        
        self.init_ui()
    
    def init_ui(self):
        """Инициализация интерфейса."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Получаем структуру таблицы
        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA table_info({self.table_name})")
        columns_info = cursor.fetchall()
        
        self.fields = {}
        form_layout = QFormLayout()
        
        for col in columns_info:
            col_name = col[1]
            col_type = col[2]
            is_pk = col[5]  # PRIMARY KEY flag
            is_not_null = col[3]  # NOT NULL flag
            
            # Пропускаем PRIMARY KEY при редактировании
            if self.is_edit and is_pk:
                continue
            
            label_text = col_name
            if is_not_null:
                label_text += " *"
            
            # Создаем поле ввода
            if "TEXT" in col_type.upper():
                field = QTextEdit()
                field.setMaximumHeight(100)
                if self.is_edit and col_name in self.row_data:
                    field.setPlainText(str(self.row_data[col_name]) if self.row_data[col_name] is not None else "")
            else:
                field = QLineEdit()
                if self.is_edit and col_name in self.row_data:
                    field.setText(str(self.row_data[col_name]) if self.row_data[col_name] is not None else "")
            
            form_layout.addRow(label_text, field)
            self.fields[col_name] = (field, is_pk, is_not_null)
        
        layout.addLayout(form_layout)
        
        # Кнопки
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self.save_record)
        button_layout.addWidget(save_button)
        
        cancel_button = QPushButton("Отмена")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
    
    def save_record(self):
        """Сохранить запись."""
        try:
            cursor = self.conn.cursor()
            
            if self.is_edit:
                # Обновление существующей записи
                pk_column = None
                for col_name, (field, is_pk, _) in self.fields.items():
                    if is_pk:
                        pk_column = col_name
                        break
                
                if not pk_column:
                    # Ищем PK в исходных данных
                    cursor.execute(f"PRAGMA table_info({self.table_name})")
                    columns_info = cursor.fetchall()
                    for col in columns_info:
                        if col[5]:  # pk flag
                            pk_column = col[1]
                            break
                
                if not pk_column:
                    QMessageBox.warning(self, "Ошибка", "Не найден PRIMARY KEY!")
                    return
                
                pk_value = self.row_data[pk_column]
                set_clauses = []
                values = []
                
                for col_name, (field, is_pk, _) in self.fields.items():
                    if not is_pk:
                        if isinstance(field, QTextEdit):
                            value = field.toPlainText()
                        else:
                            value = field.text()
                        set_clauses.append(f"{col_name} = ?")
                        values.append(value if value else None)
                
                values.append(pk_value)
                query = f"UPDATE {self.table_name} SET {', '.join(set_clauses)} WHERE {pk_column} = ?"
                cursor.execute(query, values)
            else:
                # Создание новой записи
                columns = []
                values = []
                placeholders = []
                
                for col_name, (field, is_pk, is_not_null) in self.fields.items():
                    if isinstance(field, QTextEdit):
                        value = field.toPlainText()
                    else:
                        value = field.text()
                    
                    if is_not_null and not value:
                        QMessageBox.warning(self, "Ошибка", f"Поле '{col_name}' обязательно для заполнения!")
                        return
                    
                    columns.append(col_name)
                    placeholders.append("?")
                    values.append(value if value else None)
                
                query = f"INSERT INTO {self.table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
                cursor.execute(query, values)
            
            self.conn.commit()
            QMessageBox.information(self, "Успех", "Запись успешно сохранена!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении:\n{str(e)}")


def main():
    """Главная функция."""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = DatabaseViewer()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

