# 遥感样本制作工具 - 启动全部服务 (PowerShell 版本)
# 修复版：添加更好的错误处理和调试信息

# 设置错误处理
$ErrorActionPreference = "Continue"

# 检查 PowerShell 执行策略
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  遥感样本制作工具 - 启动中" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[检查] PowerShell 执行策略..." -ForegroundColor Yellow
$executionPolicy = Get-ExecutionPolicy
if ($executionPolicy -eq "Restricted") {
    Write-Host "[警告] 当前执行策略为 Restricted，可能无法运行脚本" -ForegroundColor Yellow
    Write-Host "[提示] 请以管理员身份运行 PowerShell 并执行以下命令：" -ForegroundColor Yellow
    Write-Host "       Set-ExecutionPolicy RemoteSigned" -ForegroundColor White
    Write-Host ""
}
Write-Host "[成功] 执行策略: $executionPolicy" -ForegroundColor Green
Write-Host ""

# 检查 Python
Write-Host "[检查] Python 环境..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[成功] $pythonVersion" -ForegroundColor Green
    Write-Host ""
    $pythonOk = $true
} catch {
    Write-Host "[错误] 未找到 Python！" -ForegroundColor Red
    Write-Host "       错误详情: $_" -ForegroundColor Red
    Write-Host "       请确保 Python 已安装并添加到 PATH" -ForegroundColor Red
    Write-Host "       推荐路径: C:\Python27\ArcGIS10.4\python.exe" -ForegroundColor Red
    Write-Host ""
    Read-Host "按回车键退出"
    exit 1
}

# 检查 Node.js
Write-Host "[检查] Node.js 环境..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    Write-Host "[成功] Node.js $nodeVersion" -ForegroundColor Green
    Write-Host ""
    $nodeOk = $true
} catch {
    Write-Host "[错误] 未找到 Node.js！" -ForegroundColor Red
    Write-Host "       错误详情: $_" -ForegroundColor Red
    Write-Host "       请安装 Node.js 18 或更高版本" -ForegroundColor Red
    Write-Host ""
    Read-Host "按回车键退出"
    exit 1
}

# 获取脚本路径
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$vueAppPath = Join-Path $scriptPath "vue-app"

Write-Host "[信息] 脚本路径: $scriptPath" -ForegroundColor Gray
Write-Host "[信息] 前端路径: $vueAppPath" -ForegroundColor Gray
Write-Host ""

# 进入前端目录
try {
    Set-Location $vueAppPath
    Write-Host "[成功] 切换到前端目录" -ForegroundColor Green
} catch {
    Write-Host "[错误] 无法切换到前端目录: $vueAppPath" -ForegroundColor Red
    Write-Host "       错误详情: $_" -ForegroundColor Red
    Write-Host ""
    Read-Host "按回车键退出"
    exit 1
}

# 检查并安装前端依赖
Write-Host "[1/3] 检查前端依赖..." -ForegroundColor Yellow
if (!(Test-Path "node_modules")) {
    Write-Host "[信息] 未找到 node_modules，正在安装依赖..." -ForegroundColor Cyan
    try {
        npm install
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[错误] 前端依赖安装失败！" -ForegroundColor Red
            Write-Host "       错误码: $LASTEXITCODE" -ForegroundColor Red
            Write-Host ""
            Read-Host "按回车键退出"
            exit 1
        }
        Write-Host "[成功] 前端依赖安装完成" -ForegroundColor Green
    } catch {
        Write-Host "[错误] 安装依赖时发生异常: $_" -ForegroundColor Red
        Write-Host ""
        Read-Host "按回车键退出"
        exit 1
    }
} else {
    Write-Host "[成功] 前端依赖已存在" -ForegroundColor Green
}
Write-Host ""

# 启动后端服务
Write-Host "[2/3] 启动后端服务 (端口 8000)..." -ForegroundColor Yellow
$backendScript = @"
chcp 65001 >`$null
cd /d "$scriptPath"
title 遥感样本制作工具 - 后端服务
echo.
echo ========================================
echo   遥感样本制作工具 - 后端服务
echo ========================================
echo.
echo 服务地址: http://localhost:8000
echo API文档: http://localhost:8000/docs
echo.
echo 按 Ctrl+C 停止服务
echo.
python main.py
pause
"@

try {
    Start-Process cmd.exe -ArgumentList "/c", $backendScript -WindowStyle Normal
    Write-Host "[成功] 后端服务已启动" -ForegroundColor Green
} catch {
    Write-Host "[错误] 无法启动后端服务: $_" -ForegroundColor Red
    Write-Host ""
    Read-Host "按回车键退出"
    exit 1
}

# 等待后端服务启动
Write-Host "[等待] 后端服务启动中..." -ForegroundColor Cyan
Start-Sleep -Seconds 3

# 检查后端服务
Write-Host "[检查] 后端服务状态..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/docs" -Method GET -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
    Write-Host "[成功] 后端服务已启动" -ForegroundColor Green
} catch {
    Write-Host "[警告] 后端服务可能未完全启动，但将继续启动前端" -ForegroundColor Yellow
    Write-Host "       错误详情: $_" -ForegroundColor Gray
}
Write-Host ""

# 启动前端服务
Write-Host "[3/3] 启动前端服务 (端口 5173)..." -ForegroundColor Yellow
$frontendScript = @"
chcp 65001 >`$null
cd /d "$vueAppPath"
title 遥感样本制作工具 - 前端服务
echo.
echo ========================================
echo   遥感样本制作工具 - 前端服务
echo ========================================
echo.
echo 服务地址: http://localhost:5173
echo.
echo 按 Ctrl+C 停止服务
echo.
npm run dev
pause
"@

try {
    Start-Process cmd.exe -ArgumentList "/c", $frontendScript -WindowStyle Normal
    Write-Host "[成功] 前端服务已启动" -ForegroundColor Green
} catch {
    Write-Host "[错误] 无法启动前端服务: $_" -ForegroundColor Red
    Write-Host ""
    Read-Host "按回车键退出"
    exit 1
}

# 等待前端服务启动
Write-Host "[等待] 前端服务启动中..." -ForegroundColor Cyan
Start-Sleep -Seconds 3

# 检查前端服务
Write-Host "[检查] 前端服务状态..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5173" -Method GET -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
    Write-Host "[成功] 前端服务已启动" -ForegroundColor Green
} catch {
    Write-Host "[警告] 前端服务可能未完全启动" -ForegroundColor Yellow
    Write-Host "       错误详情: $_" -ForegroundColor Gray
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  服务启动完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "前端地址: http://localhost:5173" -ForegroundColor White
Write-Host "后端地址: http://localhost:8000" -ForegroundColor White
Write-Host "API文档:  http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "提示:" -ForegroundColor Cyan
Write-Host "  - 两个服务已在独立窗口中运行" -ForegroundColor White
Write-Host "  - 如需停止服务，请关闭对应的服务窗口" -ForegroundColor White
Write-Host "  - 或使用 '停止全部服务.ps1' 脚本" -ForegroundColor White
Write-Host ""

# 自动打开浏览器
try {
    Start-Process "http://localhost:5173"
    Write-Host "[信息] 已自动打开浏览器" -ForegroundColor Green
} catch {
    Write-Host "[提示] 请手动打开浏览器访问 http://localhost:5173" -ForegroundColor Yellow
}

Write-Host ""
Read-Host "按回车键关闭此窗口（服务将继续运行）"