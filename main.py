import os
import threading
import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext, messagebox
import zipfile
import py7zr
import rarfile
import shutil

class BatchUnzipperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("批量解壓縮工具")
        self.root.geometry("750x530")
        self.selected_folder = tk.StringVar()
        self.out_folder = tk.StringVar()
        self.progress_var = tk.DoubleVar()
        self.log_lines = []

        self.extract_to_same = tk.BooleanVar(value=True)
        self.extract_to_custom = tk.BooleanVar(value=False)
        self.extract_flat_all = tk.BooleanVar(value=False)

        self.setup_widgets()

    def setup_widgets(self):
        frm = ttk.Frame(self.root)
        frm.pack(fill="x", padx=10, pady=10)
        ttk.Label(frm, text="來源資料夾：").pack(side="left")
        ttk.Entry(frm, textvariable=self.selected_folder, width=40).pack(side="left", padx=5)
        ttk.Button(frm, text="瀏覽...", command=self.select_folder).pack(side="left")

        opt_frame = ttk.LabelFrame(self.root, text="解壓選項", padding=(10, 5))
        opt_frame.pack(fill="x", padx=10, pady=5)
        ttk.Checkbutton(opt_frame, text="解壓到壓縮檔同層資料夾", variable=self.extract_to_same).pack(anchor="w")
        ttk.Checkbutton(opt_frame, text="解壓到指定資料夾（保留結構）", variable=self.extract_to_custom).pack(anchor="w")
        ttk.Checkbutton(opt_frame, text="全部扁平化解壓到指定資料夾（檔名自動編號）", variable=self.extract_flat_all).pack(anchor="w")

        out_frame = ttk.Frame(opt_frame)
        out_frame.pack(fill="x", pady=2)
        ttk.Label(out_frame, text="指定輸出資料夾：").pack(side="left")
        ttk.Entry(out_frame, textvariable=self.out_folder, width=35).pack(side="left", padx=5)
        ttk.Button(out_frame, text="選擇...", command=self.select_out_folder).pack(side="left")

        ttk.Button(self.root, text="開始解壓縮", command=self.start_unzip).pack(pady=10)
        self.progress = ttk.Progressbar(self.root, variable=self.progress_var, maximum=100)
        self.progress.pack(fill="x", padx=10)
        self.log_text = scrolledtext.ScrolledText(self.root, height=20, state="disabled", font=("Consolas", 10))
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.selected_folder.set(folder)

    def select_out_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.out_folder.set(folder)

    def log(self, msg):
        self.log_lines.append(msg)
        self.log_text.config(state="normal")
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")
        print(msg)

    def start_unzip(self):
        folder = self.selected_folder.get()
        if not folder or not os.path.isdir(folder):
            messagebox.showwarning("請選擇資料夾", "請選擇有效的來源資料夾")
            return
        if not (self.extract_to_same.get() or self.extract_to_custom.get() or self.extract_flat_all.get()):
            messagebox.showwarning("請選擇解壓選項", "請至少勾選一個解壓選項")
            return
        if (self.extract_to_custom.get() or self.extract_flat_all.get()):
            out_folder = self.out_folder.get()
            if not out_folder or not os.path.isdir(out_folder):
                messagebox.showwarning("請選擇輸出資料夾", "請選擇有效的指定輸出資料夾")
                return
        self.progress_var.set(0)
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, "end")
        self.log_text.config(state="disabled")
        threading.Thread(target=self.unzip_all, args=(folder,), daemon=True).start()

    def unzip_all(self, folder):
        compress_exts = (".zip", ".rar", ".7z")
        filelist = []
        for root, dirs, files in os.walk(folder):
            for f in files:
                if f.lower().endswith(compress_exts):
                    filelist.append(os.path.join(root, f))
        total = len(filelist)
        if total == 0:
            self.log("找不到任何壓縮檔。")
            return
        self.log(f"共發現 {total} 個壓縮檔，開始解壓縮...")

        # 累計全扁平化的檔案編號
        flat_index = 1
        flat_dst = self.out_folder.get() if self.extract_flat_all.get() else None

        for idx, f in enumerate(filelist, 1):
            self.log(f"\n[{idx}/{total}] 處理壓縮檔：{f}")
            try:
                parent_name = os.path.basename(os.path.dirname(f))
                # 1. 解壓到壓縮檔同層
                if self.extract_to_same.get():
                    out_dir = f + "_unzip"
                    self.log(f"→ 解壓到同層資料夾：{out_dir}")
                    self._extract_with_prefix(f, out_dir, parent_name)
                # 2. 解壓到指定資料夾（保留結構）
                if self.extract_to_custom.get():
                    base = os.path.splitext(os.path.basename(f))[0]
                    out_dir = os.path.join(self.out_folder.get(), base)
                    os.makedirs(out_dir, exist_ok=True)
                    self.log(f"→ 解壓到指定資料夾：{out_dir}")
                    self._extract_with_prefix(f, out_dir, parent_name)
                # 3. 扁平化解壓到指定資料夾
                if self.extract_flat_all.get():
                    self.log(f"→ 扁平化解壓到：{flat_dst}，檔名自動編號")
                    flat_index = self._extract_flat_and_number(f, flat_dst, flat_index)
            except Exception as e:
                self.log(f"× 失敗：{f}，錯誤：{e}")
            self.progress_var.set(idx / total * 100)
            self.root.update()
        self.log("\n全部解壓縮完成！")

    def _extract_with_prefix(self, src, dst, prefix):
        if src.lower().endswith(".zip"):
            with zipfile.ZipFile(src, 'r') as zf:
                for member in zf.namelist():
                    if member.endswith('/'):
                        os.makedirs(os.path.join(dst, member), exist_ok=True)
                        continue
                    new_name = f"{prefix}_{os.path.basename(member)}"
                    new_name = self._get_unique_name(dst, new_name)
                    with zf.open(member) as source, open(os.path.join(dst, new_name), 'wb') as target:
                        data = source.read()
                        target.write(data)
                    self.log(f"  - 解壓: {member} → {new_name} ({len(data)} bytes)")
        elif src.lower().endswith(".7z"):
            with py7zr.SevenZipFile(src, mode='r') as zf:
                for member in zf.getnames():
                    if member.endswith('/'):
                        os.makedirs(os.path.join(dst, member), exist_ok=True)
                        continue
                    new_name = f"{prefix}_{os.path.basename(member)}"
                    new_name = self._get_unique_name(dst, new_name)
                    zf.extract(targets=[member], path=dst)
                    orig_path = os.path.join(dst, member)
                    if os.path.exists(orig_path):
                        os.rename(orig_path, os.path.join(dst, new_name))
                        size = os.path.getsize(os.path.join(dst, new_name))
                        self.log(f"  - 解壓: {member} → {new_name} ({size} bytes)")
        elif src.lower().endswith(".rar"):
            with rarfile.RarFile(src, 'r') as rf:
                for member in rf.infolist():
                    if member.isdir():
                        continue
                    new_name = f"{prefix}_{os.path.basename(member.filename)}"
                    new_name = self._get_unique_name(dst, new_name)
                    with rf.open(member) as source, open(os.path.join(dst, new_name), 'wb') as target:
                        data = source.read()
                        target.write(data)
                    self.log(f"  - 解壓: {member.filename} → {new_name} ({len(data)} bytes)")

    def _extract_flat_and_number(self, src, dst, start_index):
        idx = start_index
        if src.lower().endswith(".zip"):
            with zipfile.ZipFile(src, 'r') as zf:
                files = [f for f in zf.namelist() if not f.endswith('/')]
                for file in files:
                    ext = os.path.splitext(file)[1]
                    new_name = f"{idx}{ext}"
                    target_path = os.path.join(dst, new_name)
                    # 避免同名
                    while os.path.exists(target_path):
                        idx += 1
                        new_name = f"{idx}{ext}"
                        target_path = os.path.join(dst, new_name)
                    with zf.open(file) as source, open(target_path, 'wb') as target:
                        data = source.read()
                        target.write(data)
                    self.log(f"  - 扁平化: {file} → {new_name} ({len(data)} bytes)")
                    idx += 1
        elif src.lower().endswith(".7z"):
            with py7zr.SevenZipFile(src, mode='r') as zf:
                files = [f for f in zf.getnames() if not f.endswith('/')]
                for file in files:
                    ext = os.path.splitext(file)[1]
                    new_name = f"{idx}{ext}"
                    target_path = os.path.join(dst, new_name)
                    while os.path.exists(target_path):
                        idx += 1
                        new_name = f"{idx}{ext}"
                        target_path = os.path.join(dst, new_name)
                    zf.extract(targets=[file], path=dst)
                    orig_path = os.path.join(dst, file)
                    if os.path.exists(orig_path):
                        shutil.move(orig_path, target_path)
                        size = os.path.getsize(target_path)
                        self.log(f"  - 扁平化: {file} → {new_name} ({size} bytes)")
                    idx += 1
        elif src.lower().endswith(".rar"):
            with rarfile.RarFile(src, 'r') as rf:
                files = [f for f in rf.infolist() if not f.isdir()]
                for member in files:
                    ext = os.path.splitext(member.filename)[1]
                    new_name = f"{idx}{ext}"
                    target_path = os.path.join(dst, new_name)
                    while os.path.exists(target_path):
                        idx += 1
                        new_name = f"{idx}{ext}"
                        target_path = os.path.join(dst, new_name)
                    with rf.open(member) as source, open(target_path, 'wb') as target:
                        data = source.read()
                        target.write(data)
                    self.log(f"  - 扁平化: {member.filename} → {new_name} ({len(data)} bytes)")
                    idx += 1
        return idx

    def _get_unique_name(self, folder, filename):
        name, ext = os.path.splitext(filename)
        counter = 1
        candidate = filename
        while os.path.exists(os.path.join(folder, candidate)):
            candidate = f"{name}_{counter}{ext}"
            counter += 1
        return candidate

if __name__ == "__main__":
    root = tk.Tk()
    app = BatchUnzipperGUI(root)
    root.mainloop()
