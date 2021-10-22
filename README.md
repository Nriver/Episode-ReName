# Episode-ReName

电视剧/番剧自动化重命名工具. 本工具可以对大部分资源进行重命名处理. 主要是给Emby, Jellyfin等播放器使用, 也可以配合和tmm削刮器使用. 

请注意！需要重命名的文件必须在类似 `Season 1`, `s1` 的目录中才会被处理. 


# 使用场景1-右键菜单

右键菜单快速重命名
1. 从[Release](https://github.com/Nriver/Episode-ReName/releases)直接下载最新的exe程序
2. 修改 右键菜单 添加.reg 的exe路径并导入注册表
3. 找到要重命名的文件/文件夹, 右键点击"自动剧集命名". 
注：可以多选进行批量操作. win10多选超过15个, 右键菜单会消失, 可以运行`win10 右键多文件限制修改.reg`将限制修改成999个. 

# 使用场景2-结合qbitorrent下载

可以在qbittorrent 中进行设置, 实现下载完成后自动重命名
1. 选项—>BitTorrent—>做种限制—>做种0分钟—>暂停或删除做种
2. 选项—>下载—>完成时运行外部程序—>命令行
```
D:\Test\EpisodeReName.exe "%D" 15
```

参数说明：1.工具所在路径；2.保存路径="%D"；3.延时执行=秒


# 使用场景3-命令行

可以直接传入文件路径, 注意有空格的路径加双引号
```
D:\Test\EpisodeReName.exe "D:\我的番剧\XXX\Season 1"
```

可以传入第二个参数, 作为重命名的延迟. 这个参数主要是配合qbitorrent使用, 避免qb锁定文件导致重命名失败. 一般停止做种15秒后在操作能确保文件被释放. 
```
D:\Test\EpisodeReName.exe "D:\我的番剧\XXX\Season 1" 15
```

# 脚本编译成可执行程序

如果你想自己将python脚本打包成exe, 需要python3运行环境.
安装[pyinstaller](https://github.com/pyinstaller/pyinstaller)模块. 
可以使用
```
pip3 install -r requirements.txt
```
命令来安装相关模块

将脚本打包成可执行程序
```
pyinstaller -F EpisodeReName.py
```

将脚本打包成可执行程序 (不带启动黑框)
```
pyinstaller -F -w EpisodeReName.py
```

# 强制的规范元数据结构

1. 剧季文件夹：Season1 / Season 1 / s1 / S1
2. 媒体源文件：SxxExx (.mkv / .mp4 等常见视频格式)
3. 剧集元数据：SxxExx.nfo / SxxEPxx.nfo
4. 外置字幕源：SxxExx.zh (.ass / .ssa / .srt)
5. 剧集缩略图：SxxExx-thumb (.jpg / .png)
6. 剧季元数据：season.nfo

# 工具主要功能和处理逻辑

1. 对剧季命名以外的文件夹无效
2. 根据保存的剧季目录命名集号
3. 删除规范以外的多余元数据
4. 下载完成后尝试命名并加.new后缀
5. 删除可命名的同名文件达到换源目的
6. 去除文件命名后的.new后缀名
7. 如果4步命名成功则继续执行5, 6
8. 如果第4步命名不成功则终止后续操作

# 主要文件说明

EpisodeReName.py
重命名工具主程序

make_exe.bat
将python脚本打包成exe, 依赖[pyinstaller](https://github.com/pyinstaller/pyinstaller)模块

# 多季番剧tmdb集数适配

对于有多季的番剧, 比如鬼灭之刃28集, 在tmdb里没有第28集, 而是第2季第2集, 要正确削刮需要从S02E28改成S02E02. 

这时候可以在`Season XX`文件夹中添加一个`all.txt`文件, 里面写上一个数字, 会在自动重命名的时候减掉这个数字. 比如上面的鬼灭之刃就需要在`all.txt`填入26, 自动重命名就会把S02E28改成S02E02, 这样就能正常削刮了.


