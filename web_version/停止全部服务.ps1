# 遥感样本制作工具 - 停止全部服务 (PowerShell 版本)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  遥感样本制作工具 - 停止服务" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 停止后端服务
Write-Host "[1/2] 查找并停止后端服务..." -ForegroundColor Yellow
$backendProcesses = Get-Process cmd -ErrorAction SilentlyContinue | Where-Object {
    $_.MainWindowTitle -like "*RemoteSensing-后端*" -or
    $_.MainWindowTitle -like "*遥感样本制作工具 - 后端*"
}

if ($backendProcesses) {
    Write-Host "[信息] 发现后端服务窗口" -ForegroundColor Cyan
    $backendProcesses | ForEach-Object {
        Write-Host "  - 停止进程: $($_.Id)" -ForegroundColor Gray
        Stop-Process -Id $_.Id -Force
    }
    Write-Host "[成功] 后端服务已停止" -ForegroundColor Green
} else {
    Write-Host "[信息] 未发现运行中的后端服务" -ForegroundColor Gray
}
Write-Host ""

# 停止前端服务
Write-Host "[2/2] 查找并停止前端服务..." -ForegroundColor Yellow
$frontendProcesses = Get-Process cmd -ErrorAction SilentlyContinue | Where-Object {
    $_.MainWindowTitle -like "*RemoteSensing-前端*" -or
    $_.MainWindowTitle -like "*遥感样本制作工具 - 前端*"
}

if ($frontendProcesses) {
    Write-Host "[信息] 发现前端服务窗口" -ForegroundColor Cyan
    $frontendProcesses | ForEach-Object {
        Write-Host "  - 停止进程: $($_.Id)" -ForegroundColor Gray
        Stop-Process -Id $_.Id -Force
    }
    Write-Host "[成功] 前端服务已停止" -ForegroundColor Green
} else {
    Write-Host "[信息] 未发现运行中的前端服务" -ForegroundColor Gray
}
Write-Host ""

# 检查并清理 Python 进程
Write-Host "[检查] 清理可能残留的 Python 进程..." -ForegroundColor Yellow
$pythonProcesses = Get-Process python -ErrorAction SilentlyContinue

if ($pythonProcesses) {
    Write-Host "[警告] 发现 Python 进程正在运行" -ForegroundColor Yellow
    Write-Host ""
    $pythonProcesses | Format-Table Id, ProcessName, CPU, WorkingSet -AutoSize
    Write-Host ""
    $killPython = Read-Host "是否要关闭所有 Python 进程? (y/n)"
    
    if ($killPython -eq "y" -or $killPython -eq "Y") {
        $pythonProcesses | ForEach-Object {
            Write-Host "  - 停止进程: $($_.Id)" -ForegroundColor Gray
            Stop-Process -Id $_.Id -Force
        }
        Write-Host "[成功] 所有 Python 进程已关闭" -ForegroundColor Green
    } else {
        Write-Host "[信息] 保留 Python 进程" -ForegroundColor Gray
    }
} else {
    Write-Host "[成功] 无残留 Python 进程" -ForegroundColor Green
}
Write-Host ""

# 检查并清理 Node.js 进程
Write-Host "[检查] 清理可能残留的 Node.js 进程..." -ForegroundColor Yellow
$nodeProcesses = Get-Process node -ErrorAction SilentlyContinue

if ($nodeProcesses) {
    Write-Host "[警告] 发现 Node.js 进程正在运行" -ForegroundColor Yellow
    Write-Host ""
    $nodeProcesses | Format-Table Id, ProcessName, CPU, WorkingSet -AutoSize
    Write-Host ""
    $killNode = Read-Host "是否要关闭所有 Node.js 进程? (y/n)"
    
    if ($killNode -eq "y" -or $killNode -eq "Y") {
        $nodeProcesses | ForEach-Object {
            Write-Host "  - 停止进程: $($_.Id)" -ForegroundColor Gray
            Stop-Process -Id $_.Id -Force
        }
        Write-Host "[成功] 所有 Node.js 进程已关闭" -ForegroundColor Green
    } else {
        Write-Host "[信息] 保留 Node.js 进程" -ForegroundColor Gray
    }
} else {
    Write-Host "[成功] 无残留 Node.js 进程" -ForegroundColor Green
}
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  停止服务完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Read-Host "按回车键退出"