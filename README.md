# 📦 批量解壓縮工具（Batch Unzipper GUI）

這是一個使用 Python tkinter 開發的圖形介面應用程式，支援批量解壓縮 `.zip`、`.7z`、`.rar` 壓縮檔，提供三種不同的解壓選項，操作簡單直覺。

---

## 🧩 功能特色

- ✅ 支援 `.zip`, `.7z`, `.rar` 壓縮格式
- ✅ 圖形介面簡單易用，無需命令列操作
- ✅ 三種解壓模式可選：
  1. 解壓到壓縮檔同層資料夾
  2. 解壓到指定資料夾（保留結構）
  3. 扁平化解壓（所有檔案集中，自動編號）
- ✅ 解壓過程顯示進度與日誌訊息

---

## 🛠 安裝方式

1️⃣ 建議使用 Python 3.9 或以上版本。

2️⃣ 安裝相依套件（`py7zr` 和 `rarfile`）：

```bash
pip install -r requirements.txt

3️⃣ 安裝 unrar（僅限需要解壓 .rar 檔案時）：

Windows：下載 UnRAR for Windows，並將 UnRAR.exe 加入環境變數

macOS：

bash
複製
編輯
brew install unrar
Linux（Ubuntu/Debian）：

bash
複製
編輯
sudo apt install unrar
🚀 執行程式
在終端機或命令提示字元執行以下指令：

bash
複製
編輯
python main.py
啟動後會出現 GUI 視窗，請選擇來源資料夾、設定解壓選項並點擊「開始解壓縮」。