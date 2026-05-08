@echo off
chcp 65001 >nul
title 遥感样本制作工具 - 全部服务

echo ========================================
echo   遥感样本制作工具 - 启动中
echo ========================================
echo.

cd /d "%~dp0vue-app"
echo [1/2] 安装前端依赖...
call npm install
if errorlevel 1 (
    echo 前端依赖安装失败！
    pause
    exit /b 1
)

echo.
echo [2/2] 启动前端开发服务器 (端口 5173) ...
start "Vue前端" cmd /c "npm run dev"

cd /d "%~dp0"
echo.
echo 启动后端服务 (端口 8000) ...
echo.
python main.py

pause
