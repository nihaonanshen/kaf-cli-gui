# -*- coding: utf-8 -*-
"""kaf-cli 图形界面（EasyPub 风格）—— 鼠标可调各项选项的 TXT 转 EPUB/AZW3/MOBI 工具。
仅依赖 Windows 自带 Python 的 tkinter；打包后可独立运行。
"""
import os, sys, queue, subprocess
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

IS_FROZEN = getattr(sys, "frozen", False)
APP_DIR = Path(sys.executable).resolve().parent if IS_FROZEN else Path(__file__).resolve().parent.parent
_cand = [APP_DIR / "kaf-cli.exe", APP_DIR.parent / "kaf-cli.exe"]
KAF_CLI = next((c for c in _cand if c.exists()), _cand[0])

ORLY_COLORS = ["61005e", "70706d", "890029", "c4000e", "6d001d", "6a00bd", "f10000", "0071b1", "f9bc00",
               "2c0077", "ba009a", "009047", "009d9e", "222e85", "bd002e", "009d1a", "75a500"]
ORLY_FONT_CANDIDATES = [r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\msyh.ttc",
                        r"C:\Windows\Fonts\simhei.ttf", r"C:\Windows\Fonts\simsun.ttc"]

LANGS = ["zh", "en", "de", "fr", "it", "es", "ja", "pt", "ru", "nl"]
ALIGNS = ["center", "left", "right"]
DEFAULT_EXCLUDE = "^第[0-9一二三四五六七八九十零〇百千两 ]+(部门|部队|部属|部分|部件|部落|部.*：$)"
DEFAULT_VOLUME = "^第[0-9一二三四五六七八九十零〇百千两 ]+[卷部]"


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.q: "queue.Queue" = queue.Queue()
        self.proc = None
        root.title("kaf-cli 图形界面 — TXT 转 EPUB / AZW3 / MOBI")
        root.minsize(780, 620)

        pad = {"padx": 8, "pady": 6}
        top = ttk.Frame(root)
        top.pack(fill="x", **pad)
        grid = ttk.Frame(root)
        grid.pack(fill="x", **pad)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        self.v = {}
        def var(key, value, kind="s"):
            cls = {"s": tk.StringVar, "i": tk.IntVar, "b": tk.BooleanVar, "d": tk.DoubleVar}[kind]
            self.v[key] = cls(value=value)
            return self.v[key]

        # ---------- 1 文件 ----------
        f1 = ttk.LabelFrame(grid, text="① 文件")
        f1.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=(0, 6))
        var("txt", str(APP_DIR / "示例.txt"))
        var("bookname", "")
        var("author", "YSTYLE")
        var("out", "")
        var("fmt", "all")
        r = 0
        f1.columnconfigure(1, weight=1)
        ttk.Label(f1, text="TXT 文件:").grid(row=r, column=0, sticky="w", padx=6, pady=2)
        ttk.Entry(f1, textvariable=self.v["txt"]).grid(row=r, column=1, sticky="ew", padx=4, pady=2)
        ttk.Button(f1, text="浏览…", width=7, command=lambda: self.pick(self.v["txt"], "txt")).grid(row=r, column=2, padx=6, pady=2)
        r += 1
        ttk.Label(f1, text="书名:").grid(row=r, column=0, sticky="w", padx=6, pady=2)
        e = ttk.Entry(f1, textvariable=self.v["bookname"]); e.insert(0, "")
        e.grid(row=r, column=1, sticky="ew", padx=4, pady=2)
        r += 1
        ttk.Label(f1, text="作者:").grid(row=r, column=0, sticky="w", padx=6, pady=2)
        ttk.Entry(f1, textvariable=self.v["author"]).grid(row=r, column=1, sticky="ew", padx=4, pady=2)
        r += 1
        ttk.Label(f1, text="输出名:").grid(row=r, column=0, sticky="w", padx=6, pady=2)
        ttk.Entry(f1, textvariable=self.v["out"]).grid(row=r, column=1, sticky="ew", padx=4, pady=2)
        r += 1
        ttk.Label(f1, text="格式:").grid(row=r, column=0, sticky="w", padx=6, pady=2)
        ttk.Combobox(f1, textvariable=self.v["fmt"], values=["all", "epub", "azw3", "mobi"], state="readonly", width=14).grid(row=r, column=1, sticky="w", padx=4, pady=2)
        ttk.Label(f1, text="(输出文件生成在 TXT 所在目录)", foreground="#888").grid(row=r + 1, column=1, sticky="w", padx=4)
        r += 2
        ttk.Button(f1, text="打开所在文件夹", command=lambda: self.open_folder()).grid(row=r, column=1, sticky="w", padx=4, pady=2)

        # ---------- 2 章节 ----------
        f2 = ttk.LabelFrame(grid, text="② 章节识别")
        f2.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=(0, 6))
        f2.columnconfigure(1, weight=1)
        var("match", "")
        var("vol", DEFAULT_VOLUME)
        var("excl", DEFAULT_EXCLUDE)
        var("unknow", "章节正文")
        var("max", 35, "i")
        var("sep", False, "b")
        r = 0
        ttk.Label(f2, text="章节正则:").grid(row=r, column=0, sticky="w", padx=6, pady=2)
        ttk.Entry(f2, textvariable=self.v["match"]).grid(row=r, column=1, sticky="ew", padx=4, pady=2)
        r += 1
        ttk.Label(f2, text="卷规则:").grid(row=r, column=0, sticky="w", padx=6, pady=2)
        ttk.Entry(f2, textvariable=self.v["vol"]).grid(row=r, column=1, sticky="ew", padx=4, pady=2)
        r += 1
        ttk.Label(f2, text="排除:").grid(row=r, column=0, sticky="w", padx=6, pady=2)
        ttk.Entry(f2, textvariable=self.v["excl"]).grid(row=r, column=1, sticky="ew", padx=4, pady=2)
        r += 1
        ttk.Label(f2, text="未知章节名:").grid(row=r, column=0, sticky="w", padx=6, pady=2)
        ttk.Entry(f2, textvariable=self.v["unknow"]).grid(row=r, column=1, sticky="ew", padx=4, pady=2)
        r += 1
        ttk.Label(f2, text="标题最大字数:").grid(row=r, column=0, sticky="w", padx=6, pady=2)
        ttk.Spinbox(f2, from_=10, to=80, textvariable=self.v["max"], width=8).grid(row=r, column=1, sticky="w", padx=4, pady=2)
        r += 1
        ttk.Checkbutton(f2, text="章节序号单独一行显示", variable=self.v["sep"]).grid(row=r, column=1, sticky="w", padx=4)
        r += 1
        ttk.Label(f2, text="留空 = 自动识别 / 使用默认值", foreground="#888").grid(row=r, column=1, sticky="w", padx=4)

        # ---------- 3 样式 ----------
        f3 = ttk.LabelFrame(grid, text="③ 样式")
        f3.grid(row=1, column=0, sticky="nsew", padx=(0, 5), pady=(0, 6))
        f3.columnconfigure(1, weight=1)
        var("font", ""); var("css", "")
        var("indent", 2, "i"); var("bottom", "1em"); var("lh", "1.5rem")
        var("align", "center"); var("lang", "zh"); var("tips", True, "b")
        r = 0
        ttk.Label(f3, text="嵌入字体:").grid(row=r, column=0, sticky="w", padx=6, pady=2)
        ttk.Entry(f3, textvariable=self.v["font"]).grid(row=r, column=1, sticky="ew", padx=4, pady=2)
        ttk.Button(f3, text="浏览…", width=7, command=lambda: self.pick(self.v["font"], "font")).grid(row=r, column=2, padx=6, pady=2)
        r += 1
        ttk.Label(f3, text="自定义CSS:").grid(row=r, column=0, sticky="w", padx=6, pady=2)
        ttk.Entry(f3, textvariable=self.v["css"]).grid(row=r, column=1, sticky="ew", padx=4, pady=2)
        ttk.Button(f3, text="浏览…", width=7, command=lambda: self.pick(self.v["css"], "css")).grid(row=r, column=2, padx=6, pady=2)
        r += 1
        ttk.Label(f3, text="段落缩进(字):").grid(row=r, column=0, sticky="w", padx=6, pady=2)
        ttk.Spinbox(f3, from_=0, to=8, textvariable=self.v["indent"], width=8).grid(row=r, column=1, sticky="w", padx=4, pady=2)
        r += 1
        ttk.Label(f3, text="段间距:").grid(row=r, column=0, sticky="w", padx=6, pady=2)
        ttk.Entry(f3, textvariable=self.v["bottom"]).grid(row=r, column=1, sticky="ew", padx=4, pady=2)
        r += 1
        ttk.Label(f3, text="行高:").grid(row=r, column=0, sticky="w", padx=6, pady=2)
        ttk.Entry(f3, textvariable=self.v["lh"]).grid(row=r, column=1, sticky="ew", padx=4, pady=2)
        r += 1
        ttk.Label(f3, text="标题对齐:").grid(row=r, column=0, sticky="w", padx=6, pady=2)
        ttk.Combobox(f3, textvariable=self.v["align"], values=ALIGNS, state="readonly", width=14).grid(row=r, column=1, sticky="w", padx=4, pady=2)
        r += 1
        ttk.Label(f3, text="语言:").grid(row=r, column=0, sticky="w", padx=6, pady=2)
        ttk.Combobox(f3, textvariable=self.v["lang"], values=LANGS, state="readonly", width=14).grid(row=r, column=1, sticky="w", padx=4, pady=2)
        r += 1
        ttk.Checkbutton(f3, text="在书内附加本软件教程页", variable=self.v["tips"]).grid(row=r, column=1, sticky="w", padx=4)

        # ---------- 4 封面 ----------
        f4 = ttk.LabelFrame(grid, text="④ 封面")
        f4.grid(row=1, column=1, sticky="nsew", padx=(5, 0), pady=(0, 6))
        f4.columnconfigure(1, weight=1)
        var("covermode", "orly_local"); var("cover", "cover.png")
        var("orlycolor", ""); var("orlyidx", -1, "i")
        r = 0
        ttk.Radiobutton(f4, text="本地图片", variable=self.v["covermode"], value="local").grid(row=r, column=0, columnspan=3, sticky="w", padx=6, pady=1)
        r += 1
        ttk.Label(f4, text="封面文件:").grid(row=r, column=0, sticky="w", padx=6, pady=2)
        ttk.Entry(f4, textvariable=self.v["cover"]).grid(row=r, column=1, sticky="ew", padx=4, pady=2)
        ttk.Button(f4, text="浏览…", width=7, command=lambda: self.pick(self.v["cover"], "img")).grid(row=r, column=2, padx=6, pady=2)
        r += 1
        ttk.Radiobutton(f4, text="Orly 封面·本地排版（书名自动缩字号，推荐）", variable=self.v["covermode"], value="orly_local").grid(row=r, column=0, columnspan=3, sticky="w", padx=6, pady=1)
        r += 1
        ttk.Radiobutton(f4, text="Orly 封面·服务端字体（原样）", variable=self.v["covermode"], value="orly").grid(row=r, column=0, columnspan=3, sticky="w", padx=6, pady=1)
        r += 1
        ttk.Label(f4, text="Orly 主题色:").grid(row=r, column=0, sticky="w", padx=6, pady=2)
        ttk.Entry(f4, textvariable=self.v["orlycolor"]).grid(row=r, column=1, sticky="ew", padx=4, pady=2)
        ttk.Label(f4, text="(留空随机)", foreground="#888").grid(row=r, column=2, sticky="w", padx=4)
        r += 1
        ttk.Label(f4, text="Orly 动物(0-41):").grid(row=r, column=0, sticky="w", padx=6, pady=2)
        ttk.Spinbox(f4, from_=-1, to=41, textvariable=self.v["orlyidx"], width=8).grid(row=r, column=1, sticky="w", padx=4, pady=2)
        ttk.Label(f4, text="(-1=随机, 图案见 orly.nanmu.me)", foreground="#888").grid(row=r, column=2, sticky="w", padx=4)

        # ---------- 运行区 ----------
        bot = ttk.Frame(root)
        bot.pack(fill="x", **pad)
        self.btn_run = ttk.Button(bot, text="▶ 开始转换", command=self.run)
        self.btn_run.pack(side="left", padx=(2, 8))
        self.status = ttk.Label(bot, text="就绪。kaf-cli: " + ("已找到 " + str(KAF_CLI) if KAF_CLI.exists() else "❌ 未找到（与本工具同目录）"), foreground="#06c" if KAF_CLI.exists() else "#c00")
        self.status.pack(side="left")

        logf = ttk.LabelFrame(root, text="运行日志")
        logf.pack(fill="both", expand=True, **pad)
        self.log = tk.Text(logf, height=10, state="disabled", background="#1e1e1e", foreground="#d4d4d4", font=("Consolas", 9))
        sb = ttk.Scrollbar(logf, command=self.log.yview)
        self.log.configure(yscrollcommand=sb.set)
        self.log.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")
        self.root.after(120, self.poll)

    def pick(self, target, kind):
        opts = {
            "txt": dict(filetypes=[("文本文件", "*.txt")], title="选择 TXT 文件"),
            "font": dict(filetypes=[("字体", "*.ttf *.otf")], title="选择字体"),
            "css": dict(filetypes=[("CSS 文件", "*.css")], title="选择 CSS 文件"),
            "img": dict(filetypes=[("图片", "*.png *.jpg *.jpeg *.gif *.webp")], title="选择封面图片"),
        }[kind]
        p = filedialog.askopenfilename(parent=self.root, **opts)
        if p:
            target.set(p)
            if kind == "txt":
                stem = Path(p).stem
                if not self.v["bookname"].get().strip():
                    self.v["bookname"].set(stem)

    def open_folder(self):
        txt = Path(self.v["txt"].get().strip())
        folder = txt.parent if txt.suffix.lower() == ".txt" else APP_DIR
        try:
            import subprocess as _s
            _s.Popen(["explorer", str(folder)])
        except Exception:
            pass

    def _args(self, cover_override=None):
        a = ["-filename", self.v["txt"].get().strip()]
        bookname = self.v["bookname"].get().strip()
        if bookname:
            a += ["-bookname", bookname]
        a += ["-author", self.v["author"].get().strip() or "YSTYLE"]
        out = self.v["out"].get().strip()
        if out:
            a += ["-out", out]
        a += ["-format", self.v["fmt"].get().strip() or "all"]
        a += ["-lang", self.v["lang"].get() or "zh", "-align", self.v["align"].get() or "center",
              "-max", str(int(self.v["max"].get() or 35)), "-indent", str(int(self.v["indent"].get() or 2))]
        bottom = self.v["bottom"].get().strip()
        if bottom:
            a += ["-bottom", bottom]
        lh = self.v["lh"].get().strip()
        if lh:
            a += ["-line-height", lh]
        unknow = self.v["unknow"].get().strip()
        if unknow:
            a += ["-unknow-title", unknow]
        match = self.v["match"].get().strip()
        if match:
            a += ["-match", match]
        vol = self.v["vol"].get().strip()
        if vol:
            a += ["-volume-match", vol]
        excl = self.v["excl"].get().strip()
        if excl:
            a += ["-exclude", excl]
        font = self.v["font"].get().strip()
        if font:
            a += ["-font", font]
        css = self.v["css"].get().strip()
        if css:
            a += ["-custom-css-file", css]
        if self.v["sep"].get():
            a.append("-separate-chapter-number")
        if self.v["tips"].get():
            a.append("-tips")
        else:
            a.append("-tips=false")
        mode = self.v["covermode"].get()
        if mode == "orly":
            a += ["-cover", "orly"]
            c = self.v["orlycolor"].get().strip()
            if c:
                a += ["-cover-orly-color", c]
            try:
                idx = int(self.v["orlyidx"].get())
            except Exception:
                idx = -1
            if idx >= 0:
                a += ["-cover-orly-idx", str(idx)]
        else:
            if cover_override:
                a += ["-cover", cover_override]
            else:
                cv = self.v["cover"].get().strip()
                if cv:
                    a += ["-cover", cv]
        return a

    def _logmsg(self, s):
        self.log.configure(state="normal")
        self.log.insert("end", s + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _gen_orly_local(self):
        import random, urllib.request, urllib.parse
        txt = Path(self.v["txt"].get().strip())
        base = self.v["out"].get().strip() or self.v["bookname"].get().strip() or txt.stem
        author = self.v["author"].get().strip()
        c = self.v["orlycolor"].get().strip()
        if c.lstrip("#").isdigit():
            i = int(c.lstrip("#"))
            i = random.randrange(0, len(ORLY_COLORS)) if i < 1 else min(i - 1, len(ORLY_COLORS) - 1)
            color_hex = ORLY_COLORS[i]
        else:
            color_hex = (c.lstrip("#") or random.choice(ORLY_COLORS)).lower()
        try:
            idx = int(self.v["orlyidx"].get())
        except Exception:
            idx = -1
        if idx < 0 or idx > 41:
            idx = random.randrange(0, 41)
        self._logmsg("获取 Orly 底图 (颜色=%s 动物=%d)…" % (color_hex, idx))
        q = urllib.parse.urlencode({"title": "", "author": "", "g_loc": "BR", "g_text": "",
                                    "img_id": str(idx), "color": color_hex, "top_text": ""})
        url = "https://orly.nanmu.me/api/generate?" + q
        with urllib.request.urlopen(url, timeout=30) as r:
            data = r.read()
        im = self._compose_orly(data, base, author)
        out_jpg = Path(txt).parent / (base + "_orlycover.jpg")
        im.save(out_jpg, quality=92)
        self._logmsg("Orly 本地封面已生成: " + str(out_jpg))
        return str(out_jpg)

    def _compose_orly(self, data, base, author):
        import io
        from PIL import Image, ImageDraw, ImageFont
        im = Image.open(io.BytesIO(data)).convert("RGB")
        W, H = im.size
        fontpath = self.v["font"].get().strip()
        if not fontpath or not Path(fontpath).is_file():
            fontpath = next((p for p in ORLY_FONT_CANDIDATES if Path(p).is_file()), None)
            if not fontpath:
                raise RuntimeError("未找到可用中文字体（请在③区选择一个字体文件或安装微软雅黑）")
        scale = W / 1000.0
        draw0 = ImageDraw.Draw(im)
        def fit(text, max_w, start, min_sz, step=4):
            sz = start
            f = ImageFont.truetype(fontpath, sz)
            while True:
                bb = draw0.textbbox((0, 0), text, font=f)
                if bb[2] - bb[0] <= max_w or sz <= min_sz:
                    return f, sz
                sz -= step
                f = ImageFont.truetype(fontpath, sz)
        max_w = int(840 * scale)
        f_t, sz_t = fit(base, max_w, int(96 * scale), int(44 * scale))
        lines = [base]
        if draw0.textbbox((0, 0), base, font=f_t)[2] - draw0.textbbox((0, 0), base, font=f_t)[0] > max_w:
            mid = len(base) // 2
            lines = [base[:mid], base[mid:]]
            longest = max(lines, key=len)
            f_t, sz_t = fit(longest, max_w, int(72 * scale), int(32 * scale))
        has_author = bool(author)
        f_a = ImageFont.truetype(fontpath, max(20, int(sz_t * 0.42)))
        x0, x1, y0, y1 = int(50 * scale), int(950 * scale), int(850 * scale), int(1150 * scale)
        ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        od.rounded_rectangle([x0, y0, x1, y1], radius=int(16 * scale), fill=(0, 0, 0, 100))
        im = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")
        draw = ImageDraw.Draw(im)
        line_h = int(sz_t * 1.3)
        gap = int(sz_t * 0.55)
        a_h = int(sz_t * 0.42 * 1.3) if has_author else 0
        total = len(lines) * line_h + (gap + a_h if has_author else 0)
        y = (y0 + y1) / 2 - total / 2
        for l in lines:
            draw.text((W / 2, y + line_h / 2), l, font=f_t, fill=(255, 255, 255), anchor="mm")
            y += line_h
        if has_author:
            y += gap
            draw.text((W / 2, y + a_h / 2), author, font=f_a, fill=(235, 235, 235), anchor="mm")
        return im

    def run(self):
        if self.proc and self.proc.poll() is None:
            messagebox.showinfo("kaf-cli 图形界面", "已有转换任务在运行")
            return
        if not KAF_CLI.exists():
            messagebox.showerror("kaf-cli 图形界面", "未找到 kaf-cli.exe（应与本工具位于同一目录）\n" + str(KAF_CLI))
            return
        txt = self.v["txt"].get().strip()
        if not txt or not Path(txt).is_file():
            messagebox.showerror("kaf-cli 图形界面", "请先选择有效的 TXT 文件")
            return
        cover_override = None
        if self.v["covermode"].get() == "orly_local":
            try:
                cover_override = self._gen_orly_local()
            except Exception as e:
                self._logmsg("Orly 本地封面生成失败: " + str(e))
                messagebox.showerror("kaf-cli 图形界面", "Orly 本地封面生成失败:\n" + str(e))
                return
        args = self._args(cover_override=cover_override)
        self.log.configure(state="normal")
        self.log.insert("end", "\n$ " + KAF_CLI.name + " " + " ".join(f'"{x}"' if " " in x else x for x in args) + "\n")
        self.log.configure(state="disabled")
        self.btn_run.state(["disabled"])
        self.status.config(text="转换中…", foreground="#06c")
        out_dir = str(Path(txt).parent) if Path(txt).is_file() else str(APP_DIR)
        self.proc = subprocess.Popen([str(KAF_CLI)] + args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                     text=True, encoding="utf-8", errors="replace", cwd=out_dir)
        import threading
        threading.Thread(target=self._pump, daemon=True).start()

    def _pump(self):
        p = self.proc
        for line in p.stdout:
            self.q.put(("line", line))
        rc = p.wait()
        self.q.put(("done", rc))

    def poll(self):
        try:
            while True:
                kind, payload = self.q.get_nowait()
                if kind == "line":
                    self.log.configure(state="normal")
                    self.log.insert("end", payload)
                    self.log.see("end")
                    self.log.configure(state="disabled")
                elif kind == "done":
                    self.btn_run.state(["!disabled"])
                    if payload == 0:
                        self.status.config(text="✅ 转换完成（输出在 TXT 所在目录）", foreground="#080")
                    else:
                        self.status.config(text=f"❌ 退出码 {payload}，见日志", foreground="#c00")
        except queue.Empty:
            pass
        self.root.after(120, self.poll)


ERRLOG = APP_DIR / "kaf-gui-error.log"


def main():
    root = tk.Tk()

    def _bgerr(msg):
        try:
            with open(str(ERRLOG), "a", encoding="utf-8") as f:
                f.write("Tcl bgerror: " + str(msg) + "\n\n")
        except Exception:
            pass

    try:
        root.tk.createcommand("bgerror", _bgerr)
    except Exception:
        pass

    import traceback
    try:
        App(root)
    except Exception:
        try:
            with open(str(ERRLOG), "w", encoding="utf-8") as f:
                f.write(traceback.format_exc())
        except Exception:
            pass
        raise
    root.mainloop()


if __name__ == "__main__":
    main()
