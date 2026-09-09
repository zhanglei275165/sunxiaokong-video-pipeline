@echo off
chcp 65001 >nul
REM ============================================================
REM  孙小空明末镇魔录 · FastSD CPU 本地生图演示（双击运行）
REM  依赖：已下载的 sd-cli.exe + sd-turbo 权重（在 F:\LugangAI-Source）
REM  推荐：GPU/Vulkan 加速；若电脑无独显，把 vulkan0 改成 cpu
REM ============================================================
cd /d "%~dp0"

set PYTHON=C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe
if not exist "%PYTHON%" set PYTHON=python

echo 正在用 FastSD CPU 底层引擎(sd-cli)生成 6 个关键画面...
echo 显卡后端：vulkan0（若失败请编辑本文件把 vulkan0 改成 cpu）
"%PYTHON%" gen_fastsd_sdcpp.py --demo --backend vulkan0 --threads 8

echo.
echo 生成完成，图片在 img_fastsd\ 目录。
pause
