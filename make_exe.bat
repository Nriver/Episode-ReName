rmdir /s /q __pycache__
del EpisodeReName.exe
pyinstaller -F -w EpisodeReName.py
move dist\EpisodeReName.exe EpisodeReName.exe
del EpisodeReName.spec
rmdir /s /q __pycache__
rmdir /s /q build
rmdir /s /q dist
rem pause()