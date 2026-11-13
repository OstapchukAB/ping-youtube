import tkinter as tk
from tkinter import ttk
import requests
import winreg
import threading
import subprocess
import os
import psutil
import time

# --- НАСТРОЙКИ ---
# Укажите полный путь к v2rayN.exe на вашем компьютере

DESCTOP_PATH = os.path.join(os.environ['USERPROFILE'], 'Desktop')
V2RAYN_PATH = DESCTOP_PATH + r"\v2rayN-windows-64-With-Core\v2rayN-windows-64\v2rayN.exe"  # <-- ИЗМЕНИТЕ ЭТОТ ПУТЬ
# -----------------

class VPNCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Проверка VPN / YouTube + v2rayN")
        self.root.geometry("500x420")
        self.root.resizable(False, False)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # --- Рамка управления v2rayN ---
        v2ray_frame = tk.LabelFrame(root, text="Управление v2rayN", font=("Arial", 10, "bold"))
        v2ray_frame.pack(pady=10, padx=10, fill="x")

        self.v2ray_status_label = tk.Label(v2ray_frame, text="Статус: Проверка...", font=("Arial", 10))
        self.v2ray_status_label.pack(pady=5)

        btn_frame = tk.Frame(v2ray_frame)
        btn_frame.pack(pady=5)

        self.btn_start_v2ray = tk.Button(btn_frame, text="Запустить v2rayN", command=self.start_v2ray, 
                                         bg="#2196F3", fg="white", font=("Arial", 10), width=18)
        self.btn_start_v2ray.pack(side="left", padx=5)

        self.btn_stop_v2ray = tk.Button(btn_frame, text="Выключить v2rayN", command=self.stop_v2ray, 
                                        bg="#f44336", fg="white", font=("Arial", 10), width=18, state="disabled")
        self.btn_stop_v2ray.pack(side="left", padx=5)

        # --- Заголовок проверки доступа ---
        tk.Label(root, text="Статус доступа", font=("Arial", 14, "bold")).pack(pady=(10, 0))

        # --- Фрейм для индикаторов ---
        frame = tk.Frame(root)
        frame.pack(pady=10)

        # YouTube
        self.youtube_flag = tk.Label(frame, text="●", font=("Arial", 24), fg="gray")
        self.youtube_flag.grid(row=0, column=0, padx=10)
        tk.Label(frame, text="YouTube", font=("Arial", 12)).grid(row=0, column=1, sticky="w")

        # VPN / Прокси
        self.vpn_flag = tk.Label(frame, text="●", font=("Arial", 24), fg="gray")
        self.vpn_flag.grid(row=1, column=0, padx=10, pady=10)
        tk.Label(frame, text="VPN / Прокси", font=("Arial", 12)).grid(row=1, column=1, sticky="w")

        # Страна
        self.country_label = tk.Label(root, text="Страна: —", font=("Arial", 12))
        self.country_label.pack(pady=5)

        # Кнопка проверки
        self.check_button = tk.Button(root, text="Проверить доступ", command=self.start_check, 
                                      font=("Arial", 12), bg="#4CAF50", fg="white")
        self.check_button.pack(pady=15)

        # Статусная строка
        self.status_label = tk.Label(root, text="Готово к работе", font=("Arial", 9), fg="gray")
        self.status_label.pack(side="bottom", pady=5)

        # Проверить статус v2rayN при запуске
        self.update_v2ray_ui()

    def on_close(self):
        """Закрываем ТОЛЬКО GUI. v2rayN намеренно не трогаем — он остаётся работать в трее."""
        # Никаких terminate()/kill() для v2rayN здесь быть не должно.
        self.root.destroy()
    
    # --- Логика управления v2rayN ---
    def is_v2rayn_running(self):
        """Проверяет, запущен ли процесс v2rayN.exe."""
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] and proc.info['name'].lower() == 'v2rayn.exe':
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False

    def update_v2ray_ui(self):
        """Обновляет статус и кнопки в зависимости от того, запущен ли v2rayN."""
        if self.is_v2rayn_running():
            self.v2ray_status_label.config(text="Статус: Работает (в трее)", fg="green")
            self.btn_start_v2ray.config(state="disabled")
            self.btn_stop_v2ray.config(state="normal")
        else:
            self.v2ray_status_label.config(text="Статус: Не запущен", fg="red")
            self.btn_start_v2ray.config(state="normal")
            self.btn_stop_v2ray.config(state="disabled")

    def start_v2ray(self):
        """Запускает v2rayN в свернутом виде (в трей)."""
        if self.is_v2rayn_running():
            self.update_v2ray_ui()
            return

        if not os.path.exists(V2RAYN_PATH):
            self.status_label.config(text=f"Ошибка: v2rayN.exe не найден по пути {V2RAYN_PATH}")
            return

        try:
            DETACHED_PROCESS = 0x00000008
            CREATE_NEW_PROCESS_GROUP = 0x00000200
            
            # Запускаем с параметром --tray для старта в трее
            subprocess.Popen(
            [V2RAYN_PATH, "--tray"],
            creationflags= DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
        )

            self.status_label.config(text="Запуск v2rayN...")
            # Даем программе немного времени на инициализацию
            self.root.after(2000, self.update_v2ray_ui)
        except Exception as e:
            self.status_label.config(text=f"Ошибка запуска: {e}")

    def stop_v2ray(self):
        """Завершает процесс v2rayN."""
        if not self.is_v2rayn_running():
            self.update_v2ray_ui()
            return

        self.status_label.config(text="Выключение v2rayN...")
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] and proc.info['name'].lower() == 'v2rayn.exe':
                    proc.terminate()  # Мягкое завершение
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Даем время на завершение и обновляем интерфейс
        self.root.after(1500, self.update_v2ray_ui)

    # --- Логика проверки доступа (без изменений) ---
    def get_system_proxy(self):
        """Читает настройки системного прокси из реестра Windows."""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                 r"Software\Microsoft\Windows\CurrentVersion\Internet Settings")
            proxy_enable, _ = winreg.QueryValueEx(key, "ProxyEnable")
            if proxy_enable == 1:
                proxy_server, _ = winreg.QueryValueEx(key, "ProxyServer")
                winreg.CloseKey(key)
                if "=" in proxy_server:
                    parts = proxy_server.split(";")
                    for part in parts:
                        if part.startswith("https="):
                            return part.split("=")[1]
                    return parts[0].split("=")[1]
                return proxy_server
            winreg.CloseKey(key)
        except Exception:
            pass
        return None

    def check_youtube(self, proxies):
        try:
            response = requests.get("https://www.youtube.com/", proxies=proxies, timeout=10, allow_redirects=True)
            return response.status_code == 200
        except Exception:
            return False

    def get_country(self, proxies):
        try:
            response = requests.get("https://ipinfo.io/json", proxies=proxies, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("country", "??")
        except Exception:
            pass
        return None

    def update_ui(self, youtube_ok, vpn_ok, country):
        self.youtube_flag.config(fg="green" if youtube_ok else "red")
        self.vpn_flag.config(fg="green" if vpn_ok else "red")
        self.country_label.config(text=f"Страна: {country}" if country else "Страна: —")

    def start_check(self):
        self.check_button.config(state="disabled")
        self.status_label.config(text="Проверка...")
        threading.Thread(target=self.run_check, daemon=True).start()

    def run_check(self):
        proxy = self.get_system_proxy()
        proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"} if proxy else None
        
        if proxy:
            self.root.after(0, lambda: self.status_label.config(text=f"Прокси: {proxy}"))
        else:
            self.root.after(0, lambda: self.status_label.config(text="Прокси не обнаружен"))

        youtube_ok = self.check_youtube(proxies)
        vpn_ok = youtube_ok and (proxy is not None)
        country = self.get_country(proxies)

        self.root.after(0, self.update_ui, youtube_ok, vpn_ok, country)
        self.root.after(0, lambda: self.check_button.config(state="normal"))
        self.root.after(0, lambda: self.status_label.config(text="Проверка завершена"))

if __name__ == "__main__":
    root = tk.Tk()
    app = VPNCheckerApp(root)
    root.mainloop()