# Схема базы данных ChatList

## Общая информация

База данных: **SQLite**  
Файл БД: `chatlist.db` (создается автоматически при первом запуске)

## Таблицы

### 1. Таблица `prompts` (Промты)

Хранит все введенные пользователем промты.

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Уникальный идентификатор промта |
| `date` | TEXT | NOT NULL | Дата и время создания промта (ISO формат: YYYY-MM-DD HH:MM:SS) |
| `prompt` | TEXT | NOT NULL | Текст промта |
| `tags` | TEXT | NULL | Теги через запятую (например: "python, api, test") |

**Индексы:**
- `idx_prompts_date` на поле `date` (для быстрой сортировки)
- `idx_prompts_tags` на поле `tags` (для поиска по тегам)

**Пример записи:**
```sql
id: 1
date: "2024-01-15 14:30:00"
prompt: "Напиши функцию на Python для сортировки списка"
tags: "python, алгоритм, сортировка"
```

---

### 2. Таблица `models` (Нейросети)

Хранит конфигурацию доступных нейросетей и их API-настройки.

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Уникальный идентификатор модели |
| `name` | TEXT | NOT NULL UNIQUE | Название модели (например: "GPT-4", "DeepSeek Chat") |
| `api_url` | TEXT | NOT NULL | URL API-эндпоинта модели |
| `api_id` | TEXT | NOT NULL | Имя переменной окружения с API-ключом (например: "OPENAI_API_KEY") |
| `is_active` | INTEGER | NOT NULL DEFAULT 1 | Флаг активности (1 - активна, 0 - неактивна) |

**Индексы:**
- `idx_models_name` на поле `name` (уникальность)
- `idx_models_active` на поле `is_active` (для быстрого поиска активных)

**Пример записи:**
```sql
id: 1
name: "GPT-4"
api_url: "https://api.openai.com/v1/chat/completions"
api_id: "OPENAI_API_KEY"
is_active: 1
```

**Примечание:** Сами API-ключи хранятся в файле `.env` в корне проекта. В таблице хранится только имя переменной окружения.

---

### 3. Таблица `results` (Результаты)

Хранит сохраненные пользователем ответы от нейросетей.

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Уникальный идентификатор результата |
| `prompt_id` | INTEGER | NOT NULL | Ссылка на промт (FOREIGN KEY → prompts.id) |
| `model_id` | INTEGER | NOT NULL | Ссылка на модель (FOREIGN KEY → models.id) |
| `response` | TEXT | NOT NULL | Текст ответа от нейросети |
| `selected` | INTEGER | NOT NULL DEFAULT 0 | Флаг выбора пользователем (1 - выбран, 0 - не выбран) |
| `created_at` | TEXT | NOT NULL | Дата и время создания результата (ISO формат) |

**Индексы:**
- `idx_results_prompt_id` на поле `prompt_id` (для быстрого поиска по промту)
- `idx_results_model_id` на поле `model_id` (для быстрого поиска по модели)
- `idx_results_created_at` на поле `created_at` (для сортировки)

**Внешние ключи:**
- `prompt_id` → `prompts.id` ON DELETE CASCADE
- `model_id` → `models.id` ON DELETE SET NULL

**Пример записи:**
```sql
id: 1
prompt_id: 1
model_id: 1
response: "Вот функция для сортировки списка:\ndef sort_list(lst):\n    return sorted(lst)"
selected: 1
created_at: "2024-01-15 14:31:00"
```

---

### 4. Таблица `settings` (Настройки)

Хранит настройки приложения в формате ключ-значение.

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Уникальный идентификатор настройки |
| `key` | TEXT | NOT NULL UNIQUE | Ключ настройки |
| `value` | TEXT | NULL | Значение настройки (JSON-строка для сложных значений) |

**Индексы:**
- `idx_settings_key` на поле `key` (уникальность и быстрый поиск)

**Примеры записей:**
```sql
id: 1
key: "export_path"
value: "C:\Users\Username\Documents\ChatList\exports"

id: 2
key: "request_timeout"
value: "30"

id: 3
key: "window_geometry"
value: "{\"width\": 1200, \"height\": 800, \"x\": 100, \"y\": 100}"
```

**Стандартные ключи настроек:**
- `export_path` - путь для экспорта файлов по умолчанию
- `request_timeout` - таймаут запросов к API (секунды)
- `window_geometry` - размер и позиция окна (JSON)
- `last_prompt_id` - ID последнего использованного промта

---

## Диаграмма связей

```
prompts (1) ──< (N) results
                    │
                    │
models (1) ────────< (N) results

settings (независимая таблица)
```

## SQL-скрипт создания таблиц

```sql
-- Таблица промтов
CREATE TABLE IF NOT EXISTS prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    prompt TEXT NOT NULL,
    tags TEXT
);

CREATE INDEX IF NOT EXISTS idx_prompts_date ON prompts(date);
CREATE INDEX IF NOT EXISTS idx_prompts_tags ON prompts(tags);

-- Таблица моделей
CREATE TABLE IF NOT EXISTS models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    api_url TEXT NOT NULL,
    api_id TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_models_name ON models(name);
CREATE INDEX IF NOT EXISTS idx_models_active ON models(is_active);

-- Таблица результатов
CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_id INTEGER NOT NULL,
    model_id INTEGER NOT NULL,
    response TEXT NOT NULL,
    selected INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (prompt_id) REFERENCES prompts(id) ON DELETE CASCADE,
    FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_results_prompt_id ON results(prompt_id);
CREATE INDEX IF NOT EXISTS idx_results_model_id ON results(model_id);
CREATE INDEX IF NOT EXISTS idx_results_created_at ON results(created_at);

-- Таблица настроек
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    value TEXT
);

CREATE INDEX IF NOT EXISTS idx_settings_key ON settings(key);
```

## Примечания по реализации

1. **Даты и время:** Используется формат ISO 8601 (TEXT) для простоты. При необходимости можно использовать функции SQLite для работы с датами.

2. **Логические значения:** Используется INTEGER (0/1) вместо BOOLEAN, так как SQLite не имеет типа BOOLEAN.

3. **Внешние ключи:** Включены для целостности данных. При удалении промта автоматически удаляются связанные результаты (CASCADE). При удалении модели связанные результаты сохраняются, но model_id становится NULL (SET NULL).

4. **API-ключи:** Хранятся в `.env` файле. Формат:
   ```
   OPENAI_API_KEY=sk-...
   DEEPSEEK_API_KEY=sk-...
   GROQ_API_KEY=gsk_...
   ```

5. **Расширяемость:** Схема позволяет легко добавлять новые поля в таблицы без изменения структуры БД (ALTER TABLE).

