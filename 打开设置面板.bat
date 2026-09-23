@echo off
chcp 65001 >nul
title Rime AI 设置控制面板
cd /d "%~dp0"

echo ========================================================
echo   Rime AI 智能输入法 - 设置控制面板
echo ========================================================
echo.
echo [*] 正在启动本地交互设置中心并打开浏览器...
python settings_panel\app.py
pause
