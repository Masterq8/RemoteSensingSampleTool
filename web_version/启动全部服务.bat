@echo off
chcp 65001 >nul
title 遥感样本制作工具 - 启动全部服务

echo ========================================
echo   遥感样本制作工具 - 启动中
echo ========================================
echo.

:: 检查 Python 是否可用
echo [检查] Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python！请确保 Python 已安装并添加到 PATH
    echo        推荐路径: C:\Python27\ArcGIS10.4\python.exe
    pause
    exit /b 1
)
echo [成功] Python 环境正常
echo.

:: 检查 Node.js 是否可用
echo [检查] Node.js 环境...
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Node.js！请安装 Node.js 18 或更高版本
    pause
    exit /b 1
)
echo [成功] Node.js 环境正常
echo.

:: 进入前端目录
cd /d "%~dp0vue-app"

:: 检查并安装前端依赖
echo [1/3] 检查前端依赖...
if not exist "node_modules\" (
    echo [信息] 未找到 node_modules，正在安装依赖...
    call npm install
    if errorlevel 1 (
        echo [错误] 前端依赖安装失败！
        pause
        exit /b 1
    )
    echo [成功] 前端依赖安装完成
) else (
    echo [成功] 前端依赖已存在
)
echo.

:: 启动后端服务（在新窗口中）
echo [2/3] 启动后端服务 (端口 8000) ...
start "RemoteSensing-后端" cmd /c "cd /d "%~dp0" && title 遥感样本制作工具 - 后端服务 && echo. && echo ======================================== && echo   遥感样本制作工具 - 后端服务 && echo ======================================== && echo. && echo 服务地址: http://localhost:8000 && echo API文档: http://localhost:8000/docs && echo. && echo 按 Ctrl+C 停止服务 && echo. && python main.py && pause"

:: 等待后端服务启动
echo [等待] 后端服务启动中...
timeout /t 3 /nobreak >nul

:: 检查后端服务是否启动成功
echo [检查] 后端服务状态...
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:8000/docs' -Method GET -TimeoutSec 5 -UseBasicParsing; Write-Host '[成功] 后端服务已启动' } catch { Write-Host '[警告] 后端服务可能未完全启动，但将继续启动前端' }"
echo.

:: 启动前端服务
echo [3/3] 启动前端服务 (端口 5173) ...
start "RemoteSensing-前端" cmd /c "cd /d "%~dp0vue-app" && title 遥感样本制作工具 - 前端服务 && echo. && echo ======================================== && echo   遥感样本制作工具 - 前端服务 && echo ======================================== && echo. && echo 服务地址: http://localhost:5173 && echo. && echo 按 Ctrl+C 停止服务 && echo. && npm run dev && pause"

:: 等待前端服务启动
echo [等待] 前端服务启动中...
timeout /t 3 /nobreak >nul

:: 检查前端服务是否启动成功
echo [检查] 前端服务状态...
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:5173' -Method GET -TimeoutSec 5 -UseBasicParsing; Write-Host '[成功] 前端服务已启动' } catch { Write-Host '[警告] 前端服务可能未完全启动' }"
echo.

echo ========================================
echo   服务启动完成！
echo ========================================
echo.
echo 前端地址: http://localhost:5173
echo 后端地址: http://localhost:8000
echo API文档:  http://localhost:8000/docs
echo.
echo 提示:
echo   - 两个服务已在独立窗口中运行
echo   - 如需停止服务，请关闭对应的服务窗口
echo   - 或使用 "停止全部服务.bat" 批处理文件
echo.
pause