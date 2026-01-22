# Инструкция по настройке GitHub Pages

## Проблема: 404 Not Found

Если вы видите ошибку 404 на `rbait31.github.io/ChatList/`, это означает, что GitHub Pages не настроен или файлы находятся не в том месте.

## Решение

### Вариант 1: Использование папки `docs/` (рекомендуется)

1. **Убедитесь, что файл `docs/index.html` существует**
   - Файл уже создан: `docs/index.html`

2. **Настройте GitHub Pages:**
   - Перейдите в репозиторий на GitHub
   - Откройте **Settings** → **Pages**
   - В разделе **Source** выберите:
     - **Branch:** `main` (или `master`)
     - **Folder:** `/docs`
   - Нажмите **Save**

3. **Подождите несколько минут**
   - GitHub может занять 1-5 минут для публикации сайта
   - Обновите страницу через несколько минут

4. **Проверьте URL:**
   - Сайт будет доступен по адресу: `https://rbait31.github.io/ChatList/`

### Вариант 2: Использование ветки `gh-pages`

Если вариант 1 не работает, создайте отдельную ветку:

```powershell
# Создайте ветку gh-pages
git checkout -b gh-pages

# Скопируйте index.html в корень
Copy-Item docs\index.html index.html

# Закоммитьте изменения
git add index.html
git commit -m "Add GitHub Pages index.html"
git push origin gh-pages

# Вернитесь в основную ветку
git checkout main
```

Затем в настройках GitHub Pages выберите:
- **Branch:** `gh-pages`
- **Folder:** `/ (root)`

### Вариант 3: Использование корня репозитория

Если хотите использовать корень репозитория:

```powershell
# Скопируйте index.html в корень
Copy-Item docs\index.html index.html

# Закоммитьте изменения
git add index.html
git commit -m "Add GitHub Pages index.html to root"
git push
```

Затем в настройках GitHub Pages выберите:
- **Branch:** `main`
- **Folder:** `/ (root)`

## Проверка настройки

После настройки проверьте:

1. **Settings → Pages** должен показывать:
   - ✅ "Your site is published at https://rbait31.github.io/ChatList/"

2. **Подождите 1-5 минут** после сохранения настроек

3. **Проверьте URL:**
   - Откройте: https://rbait31.github.io/ChatList/
   - Должен отображаться лендинг, а не 404

## Устранение проблем

### Если все еще видите 404:

1. **Проверьте, что файл закоммичен:**
   ```powershell
   git status
   git add docs/index.html
   git commit -m "Add GitHub Pages"
   git push
   ```

2. **Проверьте имя файла:**
   - Должен быть точно `index.html` (с маленькой буквы)
   - Должен находиться в `docs/` или корне

3. **Проверьте настройки репозитория:**
   - Settings → Pages → Source должен быть настроен
   - Branch должен существовать

4. **Подождите дольше:**
   - Иногда GitHub Pages может занять до 10 минут

5. **Очистите кеш браузера:**
   - Нажмите Ctrl+F5 для жесткой перезагрузки

## Обновление лендинга

При каждом обновлении версии:

1. Обновите версию в `docs/index.html`:
   ```html
   <div class="version-badge">Версия 1.0.1</div>
   ```

2. Обновите ссылки на последний релиз (если нужно)

3. Закоммитьте изменения:
   ```powershell
   git add docs/index.html
   git commit -m "Update landing page for version 1.0.1"
   git push
   ```

## Полезные ссылки

- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [Troubleshooting GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/troubleshooting-github-pages)

