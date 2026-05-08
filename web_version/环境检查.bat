@echo off
chcp 65001 >nul
title 遥感样本制作工具 - 环境检查

echo ========================================
echo   遥感样本制作工具 - 环境检查
echo ========================================
echo.

:: 检查 Python
echo [1/8] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python！
    echo.
    echo 解决方案:
    echo   1. 安装 Python 2.7
    echo   2. 或使用 ArcGIS 自带的 Python (通常位于 C:\Python27\ArcGIS10.4\)
    echo   3. 将 Python 添加到系统 PATH 环境变量
    echo.
    set PYTHON_OK=0
) else (
    for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo [成功] %PYTHON_VERSION%
    echo.
    echo Python 路径:
    where python
    echo.
    set PYTHON_OK=1
)

:: 检查 ArcPy
if %PYTHON_OK%==1 (
    echo [2/8] 检查 ArcPy 模块...
    python -c "import arcpy; print('ArcPy version:', arcpy.GetInstallInfo()['Version'])" >nul 2>&1
    if errorlevel 1 (
        echo [错误] 未找到 ArcPy 模块！
        echo.
        echo 解决方案:
        echo   1. 确保已安装 ArcGIS Desktop (10.x) 或 ArcGIS Pro
        echo   2. ArcPy 随 ArcGIS 安装，无需单独安装
        echo   3. 确保使用 ArcGIS 自带的 Python 环境
        echo.
        set ARCPY_OK=0
    ) else (
        python -c "import arcpy; print('[成功] ArcPy version:', arcpy.GetInstallInfo()['Version'])"
        echo.
        set ARCPY_OK=1
    )
)

:: 检查 Node.js
echo [3/8] 检查 Node.js 环境...
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Node.js！
    echo.
    echo 解决方案:
    echo   1. 下载并安装 Node.js (推荐 18.x 或 20.x)
    echo   2. 访问: https://nodejs.org/
    echo   3. 安装时勾选 "Add to PATH" 选项
    echo.
    set NODE_OK=0
) else (
    for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
    echo [成功] Node.js %NODE_VERSION%
    echo.
    echo Node.js 路径:
    where node
    echo.
    set NODE_OK=1
)

:: 检查 npm
if %NODE_OK%==1 (
    echo [4/8] 检查 npm (Node Package Manager)...
    npm --version >nul 2>&1
    if errorlevel 1 (
        echo [错误] 未找到 npm！
        echo.
        echo 解决方案:
        echo   1. 重新安装 Node.js，npm 会随 Node.js 一起安装
        echo   2. 确保安装时没有取消 npm 组件
        echo.
        set NPM_OK=0
    ) else (
        for /f "tokens=*" %%i in ('npm --version') do set NPM_VERSION=%%i
        echo [成功] npm %NPM_VERSION%
        echo.
        set NPM_OK=1
    )
)

:: 检查端口占用
echo [5/8] 检查端口占用情况...
netstat -ano | findstr ":8000" >nul 2>&1
if not errorlevel 1 (
    echo [警告] 端口 8000 (后端) 已被占用！
    echo.
    netstat -ano | findstr ":8000"
    echo.
    echo 解决方案:
    echo   1. 关闭占用端口的程序
    echo   2. 或使用 "停止全部服务.bat" 停止之前的服务
    echo.
) else (
    echo [成功] 端口 8000 可用
)

netstat -ano | findstr ":5173" >nul 2>&1
if not errorlevel 1 (
    echo [警告] 端口 5173 (前端) 已被占用！
    echo.
    netstat -ano | findstr ":5173"
    echo.
    echo 解决方案:
    echo   1. 关闭占用端口的程序
    echo   2. 或使用 "停止全部服务.bat" 停止之前的服务
    echo.
) else (
    echo [成功] 端口 5173 可用
)
echo.

:: 检查前端依赖
echo [6/8] 检查前端依赖...
if exist "%~dp0vue-app\node_modules\" (
    echo [成功] node_modules 目录存在
    echo.
    set DEPS_OK=1
) else (
    echo [警告] node_modules 目录不存在！
    echo.
    echo 解决方案:
    echo   1. 运行 "启动全部服务.bat" 会自动安装依赖
    echo   2. 或手动运行: cd vue-app ^&^& npm install
    echo.
    set DEPS_OK=0
)

:: 检查 Python 依赖
echo [7/8] 检查 Python 依赖...
if exist "%~dp0requirements.txt" (
    echo [信息] 发现 requirements.txt 文件
    echo.
    echo 内容:
    type "%~dp0requirements.txt"
    echo.
    echo 提示: 如需安装依赖，运行: pip install -r requirements.txt
) else (
    echo [警告] 未找到 requirements.txt 文件
)
echo.

:: 检查文件权限
echo [8/8] 检查文件权限...
if exist "%~dp0main.py" (
    echo [成功] main.py 存在且可访问
) else (
    echo [错误] main.py 不存在或无访问权限！
)

if exist "%~dp0processor.py" (
    echo [成功] processor.py 存在且可访问
) else (
    echo [错误] processor.py 不存在或无访问权限！
)

if exist "%~dp0vue-app\src\App.vue" (
    echo [成功] App.vue 存在且可访问
) else (
    echo [错误] App.vue 不存在或无访问权限！
)
echo.

:: 总结
echo ========================================
echo   检查结果总结
echo ========================================
echo.

if %PYTHON_OK%==1 (
    echo [✓] Python 环境
) else (
    echo [✗] Python 环境 (必须修复)
)

if %ARCPY_OK%==1 (
    echo [✓] ArcPy 模块
) else (
    echo [✗] ArcPy 模块 (必须修复)
)

if %NODE_OK%==1 (
    echo [✓] Node.js 环境
) else (
    echo [✗] Node.js 环境 (必须修复)
)

if %NPM_OK%==1 (
    echo [✓] npm 工具
) else (
    echo [✗] npm 工具 (必须修复)
)

if %DEPS_OK%==1 (
    echo [✓] 前端依赖
) else (
    echo [✗] 前端依赖 (首次运行会自动安装)
)
echo.

if %PYTHON_OK%==1 if %ARCPY_OK%==1 if %NODE_OK%==1 if %NPM_OK%==1 (
    echo ========================================
    echo   环境检查通过！可以启动服务
    echo ========================================
    echo.
    echo 下一步:
    echo   1. 运行 "启动全部服务.bat"
    echo   2. 或分别运行 "启动前端.bat" 和 "启动后端.bat"
    echo.
) else (
    echo ========================================
    echo   环境检查未通过！请修复上述错误
    echo ========================================
    echo.
    echo 请根据上面的错误提示进行修复
    echo.
)

pause