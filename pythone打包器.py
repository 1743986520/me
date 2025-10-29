import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
import subprocess
import sys
import platform
import tempfile
import shutil
from pathlib import Path

class PythonPackager:
    def __init__(self, root):
        self.root = root
        self.root.title("Python 檔案打包器")
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        
        # 變數初始化
        self.script_path = tk.StringVar()
        self.output_name = tk.StringVar(value="我的應用程式")
        self.with_console = tk.BooleanVar(value=True)  # True = .py (有終端), False = .pyw (無終端)
        self.icon_path = tk.StringVar()
        self.target_system = tk.StringVar(value="current")  # current, windows, linux, mac
        
        self.required_packages = []
        
        self.create_widgets()
        
    def create_widgets(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置網格權重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 選擇 Python 檔案
        ttk.Label(main_frame, text="選擇 Python 檔案:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.script_path, width=50).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        ttk.Button(main_frame, text="瀏覽", command=self.browse_script).grid(row=0, column=2, padx=5, pady=5)
        
        # 輸出檔案名稱
        ttk.Label(main_frame, text="輸出檔案名稱:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.output_name, width=50).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # 終端選項
        ttk.Label(main_frame, text="終端選項:").grid(row=2, column=0, sticky=tk.W, pady=5)
        console_frame = ttk.Frame(main_frame)
        console_frame.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)
        ttk.Radiobutton(console_frame, text="有終端 (.py)", variable=self.with_console, value=True).pack(side=tk.LEFT)
        ttk.Radiobutton(console_frame, text="無終端 (.pyw)", variable=self.with_console, value=False).pack(side=tk.LEFT)
        
        # 選擇圖標
        ttk.Label(main_frame, text="應用程式圖標:").grid(row=3, column=0, sticky=tk.W, pady=5)
        icon_frame = ttk.Frame(main_frame)
        icon_frame.grid(row=3, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        ttk.Entry(icon_frame, textvariable=self.icon_path, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(icon_frame, text="瀏覽", command=self.browse_icon).pack(side=tk.RIGHT, padx=5)
        
        # 目標系統
        ttk.Label(main_frame, text="目標系統:").grid(row=4, column=0, sticky=tk.W, pady=5)
        system_frame = ttk.Frame(main_frame)
        system_frame.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=5)
        systems = [("當前系統", "current"), ("Windows", "windows"), ("Linux", "linux"), ("macOS", "mac")]
        for i, (text, value) in enumerate(systems):
            ttk.Radiobutton(system_frame, text=text, variable=self.target_system, value=value).grid(row=0, column=i, padx=5)
        
        # 偵測依賴按鈕
        ttk.Button(main_frame, text="自動偵測所需庫", command=self.detect_dependencies).grid(row=5, column=0, columnspan=3, pady=10)
        
        # 依賴列表
        ttk.Label(main_frame, text="檢測到的依賴庫:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.dependencies_frame = ttk.Frame(main_frame)
        self.dependencies_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # 創建樹狀視圖顯示依賴
        columns = ("package", "version")
        self.dependencies_tree = ttk.Treeview(self.dependencies_frame, columns=columns, show="headings", height=8)
        self.dependencies_tree.heading("package", text="套件名稱")
        self.dependencies_tree.heading("version", text="版本")
        self.dependencies_tree.column("package", width=200)
        self.dependencies_tree.column("version", width=100)
        
        # 添加滾動條
        scrollbar = ttk.Scrollbar(self.dependencies_frame, orient=tk.VERTICAL, command=self.dependencies_tree.yview)
        self.dependencies_tree.configure(yscrollcommand=scrollbar.set)
        
        self.dependencies_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 配置依賴框架的網格權重
        self.dependencies_frame.columnconfigure(0, weight=1)
        self.dependencies_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(7, weight=1)
        
        # 添加/刪除依賴按鈕
        dependency_buttons_frame = ttk.Frame(main_frame)
        dependency_buttons_frame.grid(row=8, column=0, columnspan=3, pady=5)
        ttk.Button(dependency_buttons_frame, text="添加依賴", command=self.add_dependency).pack(side=tk.LEFT, padx=5)
        ttk.Button(dependency_buttons_frame, text="刪除選中", command=self.remove_dependency).pack(side=tk.LEFT, padx=5)
        
        # 打包按鈕
        ttk.Button(main_frame, text="開始打包", command=self.package).grid(row=9, column=0, columnspan=3, pady=20)
        
        # 狀態欄
        self.status_var = tk.StringVar(value="準備就緒")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=10, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
    
    def browse_script(self):
        filename = filedialog.askopenfilename(
            title="選擇 Python 檔案",
            filetypes=[("Python 檔案", "*.py *.pyw"), ("所有檔案", "*.*")]
        )
        if filename:
            self.script_path.set(filename)
            # 自動設置輸出名稱
            base_name = os.path.splitext(os.path.basename(filename))[0]
            self.output_name.set(base_name)
    
    def browse_icon(self):
        filename = filedialog.askopenfilename(
            title="選擇圖標檔案",
            filetypes=[("圖標檔案", "*.ico *.icns *.png"), ("所有檔案", "*.*")]
        )
        if filename:
            self.icon_path.set(filename)
    
    def detect_dependencies(self):
        if not self.script_path.get():
            messagebox.showerror("錯誤", "請先選擇 Python 檔案")
            return
        
        self.status_var.set("正在偵測依賴庫...")
        self.root.update()
        
        try:
            # 使用 pipreqs 來偵測依賴 (如果已安裝)
            temp_dir = tempfile.mkdtemp()
            script_dir = os.path.dirname(self.script_path.get())
            
            # 嘗試使用 pipreqs
            try:
                subprocess.run([
                    sys.executable, "-m", "pipreqs.pipreqs", 
                    script_dir, 
                    "--savepath", os.path.join(temp_dir, "requirements.txt"),
                    "--mode", "no-pin"
                ], check=True, capture_output=True)
                
                req_file = os.path.join(temp_dir, "requirements.txt")
                if os.path.exists(req_file):
                    with open(req_file, 'r') as f:
                        requirements = f.readlines()
                    
                    # 解析依賴
                    self.required_packages = []
                    for req in requirements:
                        req = req.strip()
                        if req and not req.startswith('#'):
                            # 移除版本號
                            package = req.split('==')[0].split('>=')[0].split('<=')[0]
                            self.required_packages.append(package)
                    
                    self.update_dependencies_tree()
                    self.status_var.set(f"偵測到 {len(self.required_packages)} 個依賴庫")
                    return
            except:
                pass  # pipreqs 不可用，嘗試其他方法
            
            # 備用方法：分析導入語句
            self.required_packages = self.analyze_imports(self.script_path.get())
            self.update_dependencies_tree()
            self.status_var.set(f"偵測到 {len(self.required_packages)} 個依賴庫")
            
        except Exception as e:
            messagebox.showerror("錯誤", f"偵測依賴時發生錯誤: {str(e)}")
            self.status_var.set("依賴偵測失敗")
        finally:
            # 清理臨時目錄
            if 'temp_dir' in locals() and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def analyze_imports(self, script_path):
        """分析 Python 檔案中的導入語句來偵測依賴"""
        standard_libs = {
            'os', 'sys', 'math', 'datetime', 'json', 're', 'collections', 
            'itertools', 'functools', 'threading', 'multiprocessing', 'subprocess',
            'tkinter', 'time', 'random', 'string', 'argparse', 'logging'
        }
        
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 簡單的導入語句解析
            imports = set()
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('import '):
                    # 處理 import module1, module2
                    modules = line[7:].split(',')
                    for module in modules:
                        module = module.strip().split(' ')[0].split('.')[0]
                        if module and module not in standard_libs:
                            imports.add(module)
                elif line.startswith('from '):
                    # 處理 from module import something
                    parts = line[5:].split(' import ')
                    if len(parts) > 1:
                        module = parts[0].strip().split(' ')[0].split('.')[0]
                        if module and module not in standard_libs:
                            imports.add(module)
            
            return list(imports)
        except Exception as e:
            messagebox.showerror("錯誤", f"分析導入語句時發生錯誤: {str(e)}")
            return []
    
    def update_dependencies_tree(self):
        # 清空樹狀視圖
        for item in self.dependencies_tree.get_children():
            self.dependencies_tree.delete(item)
        
        # 添加檢測到的依賴
        for package in self.required_packages:
            self.dependencies_tree.insert("", tk.END, values=(package, "自動檢測"))
    
    def add_dependency(self):
        package = simpledialog.askstring("添加依賴", "輸入套件名稱:")
        if package:
            self.required_packages.append(package)
            self.update_dependencies_tree()
    
    def remove_dependency(self):
        selected = self.dependencies_tree.selection()
        if selected:
            for item in selected:
                package = self.dependencies_tree.item(item)['values'][0]
                if package in self.required_packages:
                    self.required_packages.remove(package)
            self.update_dependencies_tree()
    
    def package(self):
        if not self.script_path.get():
            messagebox.showerror("錯誤", "請先選擇 Python 檔案")
            return
        
        if not self.output_name.get():
            messagebox.showerror("錯誤", "請輸入輸出檔案名稱")
            return
        
        # 選擇輸出目錄
        output_dir = filedialog.askdirectory(title="選擇輸出目錄")
        if not output_dir:
            return
        
        self.status_var.set("正在打包...")
        self.root.update()
        
        try:
            # 創建臨時目錄
            temp_dir = tempfile.mkdtemp()
            
            # 複製原始檔案
            script_ext = ".py" if self.with_console.get() else ".pyw"
            shutil.copy2(self.script_path.get(), os.path.join(temp_dir, f"main{script_ext}"))
            
            # 創建 requirements.txt
            if self.required_packages:
                with open(os.path.join(temp_dir, "requirements.txt"), 'w') as f:
                    for package in self.required_packages:
                        f.write(f"{package}\n")
            
            # 根據目標系統選擇 PyInstaller 選項
            pyinstaller_cmd = [sys.executable, "-m", "PyInstaller"]
            
            # 基本選項
            pyinstaller_cmd.extend([
                "--onefile",  # 打包成單一檔案
                "--distpath", output_dir,  # 輸出目錄
                "--workpath", os.path.join(temp_dir, "build"),  # 工作目錄
                "--specpath", temp_dir,  # spec 檔案目錄
            ])
            
            # 添加圖標
            if self.icon_path.get():
                pyinstaller_cmd.extend(["--icon", self.icon_path.get()])
            
            # 根據終端選項添加 --noconsole
            if not self.with_console.get():
                pyinstaller_cmd.append("--noconsole")
            
            # 根據目標系統添加選項
            target_system = self.target_system.get()
            if target_system != "current":
                # 注意：這需要相應的 Python 環境
                if target_system == "windows":
                    pyinstaller_cmd.append("--osx-bundle-identifier")
                    pyinstaller_cmd.append("com.example.app")
                # 其他系統特定的選項可以在此添加
            
            # 添加主檔案
            pyinstaller_cmd.append(os.path.join(temp_dir, f"main{script_ext}"))
            
            # 添加隱藏導入 (對於某些庫可能需要)
            for package in self.required_packages:
                pyinstaller_cmd.extend(["--hidden-import", package])
            
            # 執行 PyInstaller
            self.status_var.set("正在執行 PyInstaller...")
            result = subprocess.run(pyinstaller_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.status_var.set("打包完成!")
                messagebox.showinfo("成功", f"應用程式已成功打包到:\n{output_dir}")
            else:
                self.status_var.set("打包失敗")
                # 顯示錯誤訊息
                error_msg = result.stderr if result.stderr else result.stdout
                messagebox.showerror("錯誤", f"打包過程中發生錯誤:\n{error_msg}")
                
        except Exception as e:
            self.status_var.set("打包失敗")
            messagebox.showerror("錯誤", f"打包過程中發生錯誤: {str(e)}")
        finally:
            # 清理臨時目錄
            if 'temp_dir' in locals() and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

def main():
    # 檢查必要的庫
    try:
        import PyInstaller
    except ImportError:
        response = messagebox.askyesno(
            "缺少依賴", 
            "打包需要 PyInstaller 庫，是否現在安裝？"
        )
        if response:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
                messagebox.showinfo("成功", "PyInstaller 安裝成功!")
            except subprocess.CalledProcessError:
                messagebox.showerror("錯誤", "PyInstaller 安裝失敗，請手動安裝。")
                return
    
    root = tk.Tk()
    app = PythonPackager(root)
    root.mainloop()

if __name__ == "__main__":
    main()