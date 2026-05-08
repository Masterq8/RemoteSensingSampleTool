@echo off
chcp 65001 >nul
title 环境测试工具

echo ========================================
echo        环境测试工具
echo ========================================
echo.

echo 1. 检查当前目录:
echo    %cd%
echo.

echo 2. 检查 Python:
python --version
if %errorlevel% equ 0 (
    echo    [成功] Python 已安装
) else (
    echo    [失败] Python 未找到
)
echo.

echo 3. 检查 Node.js:
node --version
if %errorlevel% equ 0 (
    echo    [成功] Node.js 已安装
) else (
    echo    [失败] Node.js 未找到
)
echo.

echo 4. 检查 npm:
npm --version
if %errorlevel% equ 0 (
    echo    [成功] npm 已安装
) else (
    echo    [失败] npm 未找到
)
echo.

echo 5. 检查脚本路径:
echo    脚本目录: %~dp0
if exist "%~dp0main.py" (
    echo    [成功] main.py 存在
) else (
    echo    [失败] main.py 不存在
)
echo.

echo 6. 检查前端目录:
if exist "%~dp0vue-app\package.json" (
    echo    [成功] vue-app/package.json 存在
) else (
    echo    [失败] vue-app/package.json 不存在
)
echo.

echo ========================================
echo 测试完成！
echo ========================================
echo.
echo 如果有任何 [失败]，请先安装对应的软件。
echo.
pause