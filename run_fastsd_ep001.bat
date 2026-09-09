@echo off
chcp 65001 >nul
REM ============================================================
REM  孙小空明末镇魔录第一集 · 本地生图完整生成（122 张连续画面）
REM  双击后自动生成：img_fastsd\ep001_d001.png ~ d122.png
REM  后端：vulkan0（GPU）；若电脑无独显，把 vulkan0 改成 cpu
REM ============================================================
cd /d "%~dp0"

set PYTHON=C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe
if not exist "%PYTHON%" set PYTHON=python

echo 正在生成第一集全部 122 张连续画面（约需几分钟到几十分钟，视显卡而定）...
"%PYTHON%" gen_fastsd_sdcpp.py --ep 001 --backend vulkan0 --threads 8

echo.
echo 生成完成。接下来用 make_ep1_film_dense.py 合成胶卷视频。
pause
