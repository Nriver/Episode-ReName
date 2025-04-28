rmdir /s /q __pycache__
del EpisodeReName.exe
rem pyinstaller -F -w -i logo.ico EpisodeReName.py
pyinstaller -F -i logo.ico EpisodeReName.py
move dist\EpisodeReName.exe EpisodeReName.exe
del EpisodeReName.spec
rmdir /s /q __pycache__
rmdir /s /q build
rmdir /s /q dist
rem pause()