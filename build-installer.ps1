# Скрипт для сборки инсталлятора ChatList с помощью Inno Setup
# Использует версию из version.py

Write-Host "Получение версии приложения..." -ForegroundColor Green
$version = python -c "from version import __version__; print(__version__)"
$appName = "ChatList-$version"

Write-Host "Версия приложения: $version" -ForegroundColor Cyan

# Проверяем наличие собранного exe файла
$exePath = "dist\$appName.exe"
if (-not (Test-Path $exePath)) {
    Write-Host "Ошибка: Файл $exePath не найден!" -ForegroundColor Red
    Write-Host "Сначала выполните сборку приложения (build.ps1)" -ForegroundColor Yellow
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

# Проверяем наличие Inno Setup Compiler
$innoSetupPath = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $innoSetupPath)) {
    $innoSetupPath = "${env:ProgramFiles}\Inno Setup 6\ISCC.exe"
    if (-not (Test-Path $innoSetupPath)) {
        Write-Host "Ошибка: Inno Setup Compiler не найден!" -ForegroundColor Red
        Write-Host "Установите Inno Setup 6 из https://jrsoftware.org/isdl.php" -ForegroundColor Yellow
        Read-Host "Нажмите Enter для выхода"
        exit 1
    }
}

Write-Host ""
Write-Host "Создание инсталлятора..." -ForegroundColor Green

# Обновляем имя exe файла в setup.iss (если нужно)
# Используем параметры компилятора для передачи версии
$setupIssPath = "setup.iss"
if (-not (Test-Path $setupIssPath)) {
    Write-Host "Ошибка: Файл setup.iss не найден!" -ForegroundColor Red
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

# Создаем временный setup.iss с подставленной версией
$setupContent = Get-Content $setupIssPath -Raw -Encoding UTF8
$setupContent = $setupContent -replace '#define AppVersion ".*"', "#define AppVersion `"$version`""
$setupContent = $setupContent -replace 'OutputBaseFilename=ChatList-Setup-.*', "OutputBaseFilename=ChatList-Setup-$version"
$setupContent = $setupContent -replace 'Source: "dist\\ChatList-\{.*\}.exe"', "Source: `"dist\$appName.exe`""

$tempSetupIss = "setup_temp.iss"
$setupContent | Out-File -FilePath $tempSetupIss -Encoding UTF8

# Запускаем компилятор Inno Setup
Write-Host "Запуск компилятора Inno Setup..." -ForegroundColor Cyan
& $innoSetupPath $tempSetupIss

# Удаляем временный файл
if (Test-Path $tempSetupIss) {
    Remove-Item $tempSetupIss
}

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Готово! Инсталлятор создан в папке installer\ChatList-Setup-$version.exe" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Ошибка при создании инсталлятора!" -ForegroundColor Red
}

Read-Host "Нажмите Enter для выхода"
