@echo off
chcp 65001 >nul
title Rime AI 智能输入法 - 一键启动懒人包
color 0F

cd /d "%~dp0"

echo ================================================================
echo    🚀 Rime AI 智能输入法 - 一键启动懒人包
echo    小狼毫 · 万象拼音 · TypeSafe Jev AI · macOS 暗黑胶囊
echo ================================================================
echo.

:: 1. 检查 Python 环境
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] 未检测到系统 Python 环境，请先安装 Python 3.10+ 并勾选 Add to PATH。
    echo.
    pause
    exit /b 1
)

:: 2. 后台启动 Jev AI 桥接服务
echo [*] 正在检查并启动 Jev AI 决策服务...
start "JevAI Bridge" /b python run_bridge.py >nul 2>&1

:: 3. 检查并唤醒小狼毫 WeaselServer
if exist "C:\Program Files\Rime\weasel-0.17.4\WeaselServer.exe" (
    tasklist /FI "IMAGENAME eq WeaselServer.exe" 2>nul | find /I /N "WeaselServer.exe">nul
    if "%ERRORLEVEL%"=="1" (
        echo [*] 正在启动小狼毫输入法服务...
        start "WeaselServer" /b "C:\Program Files\Rime\weasel-0.17.4\WeaselServer.exe"
    )
)

:: 4. 启动图形化设置控制中心并自动打开浏览器
echo [*] 正在启动交互设置控制中心...
start "Rime Settings WebUI" python settings_panel\app.py

echo.
echo ================================================================
echo    ✓ 服务已全部就绪！设置面板已在默认浏览器中打开。
echo.
echo    [1] 重新打开设置控制中心
echo    [2] 一键编译并部署到系统
echo    [3] 一键下载 400MB 语法模型
echo    [4] 一键注入 macOS 胶囊托盘图标
echo    [Q] 退出本窗口 (后台服务保持运行)
echo ================================================================
echo.

:menu
set /p opt="请输入选项编号 [默认1]: "
if "%opt%"=="" set opt=1
if /i "%opt%"=="1" (
    start http://127.0.0.1:18888
    goto menu
)
if /i "%opt%"=="2" (
    echo.
    echo [*] 正在部署配置到系统输入法...
    python tools\deploy.py
    echo.
    goto menu
)
if /i "%opt%"=="3" (
    echo.
    echo [*] 正在下载 400MB 语法模型...
    python tools\download_model.py
    echo.
    goto menu
)
if /i "%opt%"=="4" (
    echo.
    echo [*] 正在注入 macOS 胶囊托盘图标...
    python tools\patch_icons.py
    echo.
    goto menu
)
if /i "%opt%"=="q" exit /b 0

goto menu
