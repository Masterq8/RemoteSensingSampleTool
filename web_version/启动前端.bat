@echo off
chcp 65001 >nul
title 遥感样本制作工具 - 前端

cd /d "%~dp0vue-app"
echo 安装前端依赖...
call npm install
if errorlevel 1 (
    echo 前端依赖安装失败！
    pause
    exit /b 1
)

echo.
echo 启动前端开发服务器 (端口 5173) ...
echo 请访问 http://localhost:5173
echo.
npm run dev

pause
