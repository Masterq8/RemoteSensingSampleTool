@echo off
chcp 65001 >nul
title 遥感样本制作工具 - 一键启动

setlocal enabledelayedexpansion

echo ========================================
echo    遥感样本制作工具 - 一键启动
echo ========================================
echo.

REM 步骤1: 检查 Python 环境
echo [步骤1/5] 检查 Python 环境...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "delims=" %%i in ('python --version 2^>^&1') do set "pythonVersion=%%i"
    echo         [成功] !pythonVersion!
) else (
    echo.
    echo         [错误] 未找到 Python！
    echo                请安装 Python 并添加到系统 PATH
    echo.
    pause
    exit /b 1
)

REM 步骤2: 检查 Node.js 环境
echo [步骤2/5] 检查 Node.js 环境...
node --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "delims=" %%i in ('node --version 2^>^&1') do set "nodeVersion=%%i"
    echo         [成功] Node.js !nodeVersion!
) else (
    echo.
    echo         [错误] 未找到 Node.js！
    echo                请安装 Node.js 18+
    echo.
    pause
    exit /b 1
)

REM 设置路径
set "scriptPath=%~dp0"
set "vueAppPath=%scriptPath%vue-app"

REM 步骤3: 检查前端依赖
echo [步骤3/5] 检查前端依赖...
if exist "%vueAppPath%\node_modules" (
    echo         [成功] 前端依赖已存在
) else (
    echo         [信息] 正在安装前端依赖...
    cd /d "%vueAppPath%"
    npm install
    if %errorlevel% equ 0 (
        echo         [成功] 前端依赖安装完成
    ) else (
        echo.
        echo         [错误] 前端依赖安装失败！
        echo.
        pause
        exit /b 1
    )
)

REM 步骤4: 检查并释放端口
echo [步骤4/5] 检查端口占用...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000"') do (
    echo         [信息] 端口 8000 被占用，正在释放...
    taskkill /PID %%a /F >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173"') do (
    echo         [信息] 端口 5173 被占用，正在释放...
    taskkill /PID %%a /F >nul 2>&1
)
echo         [成功] 端口检查完成

REM 步骤5: 启动服务
echo [步骤5/5] 启动服务...
echo.

REM 启动后端服务
echo         启动后端服务...
start "遥感样本制作工具 - 后端服务" cmd /k "cd /d ""%scriptPath%"" && chcp 65001 >nul && python main.py"

REM 等待后端启动
timeout /t 2 /nobreak >nul

REM 启动前端服务
echo         启动前端服务...
start "遥感样本制作工具 - 前端服务" cmd /k "cd /d ""%vueAppPath%"" && chcp 65001 >nul && npm run dev"

REM 等待前端启动
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo    服务启动完成！
echo ========================================
echo.
echo 前端地址: http://localhost:5173
echo 后端地址: http://localhost:8000
echo API文档:  http://localhost:8000/docs
echo.
echo 提示:
echo   - 两个服务已在独立窗口中运行
echo   - 如需停止服务，请关闭对应的服务窗口
echo   - 或使用 '停止全部服务.bat' 脚本
echo.

echo         正在打开浏览器...
start http://localhost:5173

echo.
echo 按任意键关闭此窗口（服务将继续运行）...
pause >nul