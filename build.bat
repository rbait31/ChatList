@echo off
echo Установка зависимостей...
pip install -r requirements.txt

echo.
echo Получение версии приложения...
for /f "delims=" %%i in ('python -c "from version import __version__; print(__version__)"') do set VERSION=%%i
set APPNAME=ChatList-%VERSION%

echo.
echo Создание исполняемого файла...
pyinstaller --onefile --windowed --name "%APPNAME%" main.py

echo.
echo Готово! Исполняемый файл находится в папке dist\%APPNAME%.exe
pause
