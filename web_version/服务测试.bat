@echo off
chcp 65001 >nul
title 遥感样本制作工具 - 服务测试

echo ========================================
echo   遥感样本制作工具 - 服务测试
echo ========================================
echo.

:: 测试后端服务
echo [1/2] 测试后端服务 (http://localhost:8000)...
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:8000/docs' -Method GET -TimeoutSec 5 -UseBasicParsing; Write-Host '[成功] 后端服务正常响应'; Write-Host '状态码:' $response.StatusCode } catch { Write-Host '[失败] 后端服务无响应'; Write-Host '错误信息:' $_.Exception.Message }"
echo.

:: 测试前端服务
echo [2/2] 测试前端服务 (http://localhost:5173)...
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:5173' -Method GET -TimeoutSec 5 -UseBasicParsing; Write-Host '[成功] 前端服务正常响应'; Write-Host '状态码:' $response.StatusCode } catch { Write-Host '[失败] 前端服务无响应'; Write-Host '错误信息:' $_.Exception.Message }"
echo.

:: 测试 API 端点
echo [3/3] 测试 API 端点...
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:8000/api/tasks' -Method GET -TimeoutSec 5 -UseBasicParsing; Write-Host '[成功] API 端点正常响应'; Write-Host '状态码:' $response.StatusCode } catch { Write-Host '[失败] API 端点无响应'; Write-Host '错误信息:' $_.Exception.Message }"
echo.

echo ========================================
echo   测试完成
echo ========================================
echo.
echo 访问地址:
echo   前端: http://localhost:5173
echo   后端: http://localhost:8000
echo   API文档: http://localhost:8000/docs
echo.
pause