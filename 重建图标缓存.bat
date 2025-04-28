@echo off
title 重建图标缓存

:: 提示用户关闭explorer.exe
echo.
echo 如果图标没有更新，可以尝试重建图标缓存。
echo 该过程需要先关闭 "Explorer.exe" 进程。
echo 按任意键继续…
echo.
pause >nul

:: 结束 Explorer 进程
echo 正在关闭 Explorer 进程...
taskkill /f /im explorer.exe >nul 2>&1
if %errorlevel% neq 0 (
    echo 无法结束 Explorer 进程，可能它已经关闭。
) else (
    echo Explorer 进程已成功关闭。
)

:: 删除图标缓存文件（仅在文件存在时删除）
echo 正在删除图标缓存文件...
set iconCachePath=%localappdata%\Microsoft\Windows\Explorer
if exist "%iconCachePath%\iconcache.db" (
    del /a /f /q "%iconCachePath%\iconcache.db"
    echo iconcache.db 文件已删除。
) else (
    echo 没有找到 iconcache.db 文件。
)

for %%F in (%iconCachePath%\thumbcache_*.db) do (
    if exist "%%F" (
        del /a /f /q "%%F"
        echo 已删除 %%F 文件。
    ) else (
        echo 没有找到 thumbcache 文件。
    )
)

:: 启动 Explorer 进程
echo 正在重新启动 Explorer 进程...
start explorer.exe

:: 完成提示
echo.
echo 图标缓存已成功重建！请稍等片刻，图标将自动更新。
timeout /t 5 /nobreak >nul

pause >nul