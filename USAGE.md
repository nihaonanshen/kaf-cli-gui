# 使用说明

## 1. 启动
- 双击 kaf-cli-gui/kaf-cli-gui.exe。
- 整个 kaf-cli-gui 文件夹不能删（exe 依赖同目录 _internal）。
- 程序自动在同目录或上一级目录找 kaf-cli.exe。

## 2. 基本流程（全程鼠标）
1. **① 文件**：点“浏览…”选 TXT。书名留空默认用 TXT 文件名，作者默认 YSTYLE；“格式”选 all/epub/azw3/mobi。
2. **② 章节识别**：默认自动识别“第X章/第X卷”式标题，识别不准才填“章节正则”；“排除”“卷规则”已预填默认值，留空 = 用 kaf-cli 内置默认。
3. **③ 样式**：Nook 墨水屏 + KoReader 强烈建议点“嵌入字体：浏览…”选中文字体（.ttf/.otf），避免缺字/错字；标题对齐默认居中。
4. **④ 封面**：默认「Orly 封面·本地排版」（需联网），书名自动缩字号不会截断；也可换本地图片或用服务端字体模式。
5. 点“▶ 开始转换”，下方日志实时显示 kaf-cli 输出；完成后 epub/azw3/mobi 生成在 **TXT 所在目录**，可点“打开所在文件夹”。

## 3. 常见问题
- 无封面 → ④区选封面（本地图或 Orly）。
- KoReader 缺字/乱码 → ③区嵌入中文字体。
- 目录出现悬挂项 → “未知章节名”改成合适词（如“引子”）后重转。
- Orly 长书名截断 → 用默认的本地排版模式（服务端字体模式无解）。

## 4. 源码与重新打包
- 源码：kaf_gui.py（Python + tkinter，运行时额外依赖 Pillow）。
- 打包命令：python -m PyInstaller --clean -y --onedir --windowed --name kaf-cli-gui kaf_gui.py
