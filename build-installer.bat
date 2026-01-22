@echo off
echo Получение версии приложения...
for /f "delims=" %%i in ('python -c "from version import __version__; print(__version__)"') do set VERSION=%%i
set APPNAME=ChatList-%VERSION%

echo Версия приложения: %VERSION%

REM Проверяем наличие собранного exe файла
if not exist "dist\%APPNAME%.exe" (
    echo Ошибка: Файл dist\%APPNAME%.exe не найден!
    echo Сначала выполните сборку приложения (build.bat)
    pause
    exit /b 1
)

REM Проверяем наличие Inno Setup Compiler
set INNO_PATH=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe
if not exist "%INNO_PATH%" (
    set INNO_PATH=%ProgramFiles%\Inno Setup 6\ISCC.exe
    if not exist "%INNO_PATH%" (
        echo Ошибка: Inno Setup Compiler не найден!
        echo Установите Inno Setup 6 из https://jrsoftware.org/isdl.php
        pause
        exit /b 1
    )
)

echo.
echo Создание инсталлятора...

REM Обновляем setup.iss с версией
powershell -Command "(Get-Content setup.iss -Raw -Encoding UTF8) -replace '#define AppVersion \".*\"', '#define AppVersion \"%VERSION%\"' -replace 'OutputBaseFilename=ChatList-Setup-.*', 'OutputBaseFilename=ChatList-Setup-%VERSION%' -replace 'Source: \"dist\\\\ChatList-.*\.exe\"', 'Source: \"dist\ChatList-%VERSION%.exe\"' | Out-File -FilePath setup_temp.iss -Encoding UTF8"

REM Запускаем компилятор Inno Setup
"%INNO_PATH%" setup_temp.iss

REM Удаляем временный файл
if exist setup_temp.iss del setup_temp.iss

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Готово! Инсталлятор создан в папке installer\ChatList-Setup-%VERSION%.exe
) else (
    echo.
    echo Ошибка при создании инсталлятора!
)

pause

