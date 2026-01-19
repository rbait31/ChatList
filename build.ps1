Write-Host "Установка зависимостей..." -ForegroundColor Green
pip install -r requirements.txt

Write-Host ""
Write-Host "Получение версии приложения..." -ForegroundColor Green
$version = python -c "from version import __version__; print(__version__)"
$appName = "ChatList-$version"

Write-Host ""
Write-Host "Создание исполняемого файла..." -ForegroundColor Green
pyinstaller --onefile --windowed --name $appName main.py

Write-Host ""
Write-Host "Готово! Исполняемый файл находится в папке dist\$appName.exe" -ForegroundColor Green
Read-Host "Нажмите Enter для выхода"
