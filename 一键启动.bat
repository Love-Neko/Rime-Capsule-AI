@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Rime AI 智能输入法 - 一键启动懒人包

echo ================================================================
echo    Rime AI 智能输入法 - 一键启动懒人包
echo    小狼毫 · 万象拼音 · TypeSafe Jev AI · macOS 暗黑胶囊
echo ================================================================
echo.

rem 1. 检查 Python 环境
python --version >nul 2>&1
if errorlevel 1 (
    echo [!] 未检测到系统 Python 环境，请先安装 Python 3.10+ 并勾选 Add to PATH。
    echo.
    pause
    exit /b 1
)

rem 2. 后台启动 Jev AI 本地决策服务
echo [*] 正在检查并启动 Jev AI 本地决策服务...
start "JevAI Bridge" /b python run_bridge.py >nul 2>&1

rem 3. 检查并唤醒小狼毫 WeaselServer
if exist "C:\Program Files\Rime\weasel-0.17.4\WeaselServer.exe" (
    tasklist /FI "IMAGENAME eq WeaselServer.exe" 2>nul | find /I /N "WeaselServer.exe" >nul
    if errorlevel 1 (
        echo [*] 正在启动小狼毫输入法服务...
        start "" /b "C:\Program Files\Rime\weasel-0.17.4\WeaselServer.exe"
    )
)

rem 4. 启动图形化设置控制中心并在浏览器中自动打开
echo [*] 正在启动交互设置控制中心并自动打开浏览器...
echo.
python settings_panel\app.py
pause
