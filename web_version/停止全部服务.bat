@echo off
chcp 65001 >nul
title 遥感样本制作工具 - 停止全部服务

echo ========================================
echo   遥感样本制作工具 - 停止服务
echo ========================================
echo.

echo [1/2] 查找并停止后端服务...
tasklist /FI "WINDOWTITLE eq RemoteSensing-后端*" 2>nul | find /I "cmd.exe" >nul
if not errorlevel 1 (
    echo [信息] 发现后端服务窗口
    taskkill /FI "WINDOWTITLE eq RemoteSensing-后端*" /F >nul 2>&1
    echo [成功] 后端服务已停止
) else (
    echo [信息] 未发现运行中的后端服务
)
echo.

echo [2/2] 查找并停止前端服务...
tasklist /FI "WINDOWTITLE eq RemoteSensing-前端*" 2>nul | find /I "cmd.exe" >nul
if not errorlevel 1 (
    echo [信息] 发现前端服务窗口
    taskkill /FI "WINDOWTITLE eq RemoteSensing-前端*" /F >nul 2>&1
    echo [成功] 前端服务已停止
) else (
    echo [信息] 未发现运行中的前端服务
)
echo.

echo [检查] 清理可能残留的 Python 进程...
tasklist /FI "IMAGENAME eq python.exe" 2>nul | find /I "python.exe" >nul
if not errorlevel 1 (
    echo [警告] 发现 Python 进程正在运行
    echo [提示] 如果确认这些进程是本项目的，请手动关闭
    echo.
    tasklist /FI "IMAGENAME eq python.exe" /FO TABLE
    echo.
    set /p KILL_PYTHON="是否要关闭所有 Python 进程? (y/n): "
    if /i "%KILL_PYTHON%"=="y" (
        taskkill /IM python.exe /F >nul 2>&1
        echo [成功] 所有 Python 进程已关闭
    )
) else (
    echo [成功] 无残留 Python 进程
)
echo.

echo [检查] 清理可能残留的 Node.js 进程...
tasklist /FI "IMAGENAME eq node.exe" 2>nul | find /I "node.exe" >nul
if not errorlevel 1 (
    echo [警告] 发现 Node.js 进程正在运行
    echo [提示] 如果确认这些进程是本项目的，请手动关闭
    echo.
    tasklist /FI "IMAGENAME eq node.exe" /FO TABLE
    echo.
    set /p KILL_NODE="是否要关闭所有 Node.js 进程? (y/n): "
    if /i "%KILL_NODE%"=="y" (
        taskkill /IM node.exe /F >nul 2>&1
        echo [成功] 所有 Node.js 进程已关闭
    )
) else (
    echo [成功] 无残留 Node.js 进程
)
echo.

echo ========================================
echo   停止服务完成！
echo ========================================
echo.
pause