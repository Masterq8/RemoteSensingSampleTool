@echo off
chcp 65001 >nul
title 遥感样本制作工具 - 后端

cd /d "%~dp0"
echo.
echo ========================================
echo   遥感样本制作工具 - 后端服务
echo ========================================
echo.
echo Python 路径: C:\Python27\ArcGIS10.4\python.exe
echo 服务地址: http://localhost:8000
echo API文档: http://localhost:8000/docs
echo.
echo 按 Ctrl+C 停止服务
echo.

python main.py

pause
