import tkinter as tk
from tkinter import ttk
import requests
import winreg
import threading
from datetime import datetime

class VPNCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Проверка VPN / YouTube")
        self.root.geometry("450x340")
        self.root.resizable(False, False)

        # Заголовок
        title_label = tk.Label(root, text="Статус доступа", font=("Arial", 14, "bold"))
        title_label.pack(pady=10)

        # Фрейм для индикаторов
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
        
        # Время последней проверки
        self.time_label = tk.Label(root, text="Последняя проверка: —",
                           font=("Arial", 10), fg="#333")
        self.time_label.pack(pady=(0, 5))

        # Кнопка проверки
        self.check_button = tk.Button(root, text="Проверить", command=self.start_check, 
                                      font=("Arial", 12), bg="#4CAF50", fg="white")
        self.check_button.pack(pady=15)

        # Статусная строка
        self.status_label = tk.Label(root, text="Нажмите «Проверить»", font=("Arial", 9), fg="gray")
        self.status_label.pack(side="bottom", pady=5)

    def get_system_proxy(self):
        """Читает настройки системного прокси из реестра Windows."""
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                                 r"Software\Microsoft\Windows\CurrentVersion\Internet Settings")
            proxy_enable, _ = winreg.QueryValueEx(key, "ProxyEnable")
            if proxy_enable == 1:
                proxy_server, _ = winreg.QueryValueEx(key, "ProxyServer")
                winreg.CloseKey(key)
                # Формат может быть "host:port" или "http=host:port;https=host:port"
                if "=" in proxy_server:
                    # Извлекаем https-прокси, если есть
                    parts = proxy_server.split(";")
                    for part in parts:
                        if part.startswith("https="):
                            return part.split("=")[1]
                    # Если https не найден, берём первый
                    return parts[0].split("=")[1]
                return proxy_server
            winreg.CloseKey(key)
        except Exception:
            pass
        return None

    def check_youtube(self, proxies):
        """Проверяет доступность YouTube."""
        try:
            # Используем системный прокси, если он есть
            response = requests.get("https://www.youtube.com/", 
                                    proxies=proxies, 
                                    timeout=10, 
                                    allow_redirects=True)
            return response.status_code == 200
        except Exception:
            return False

    def get_country(self, proxies):
        """Определяет страну через прокси (или напрямую)."""
        try:
            # ipinfo.io возвращает JSON с полем "country"
            response = requests.get("https://ipinfo.io/json", 
                                    proxies=proxies, 
                                    timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("country", "??")
        except Exception:
            pass
        return None

    def update_ui(self, youtube_ok, vpn_ok, country, check_time):
        """Обновляет индикаторы на форме."""
        # YouTube
        if youtube_ok:
            self.youtube_flag.config(fg="green")
        else:
            self.youtube_flag.config(fg="red")

        self.time_label.config(text=f"Последняя проверка: {check_time}")

        # VPN
        if vpn_ok:
            self.vpn_flag.config(fg="green")
        else:
            self.vpn_flag.config(fg="red")

        # Страна
        if country:
            self.country_label.config(text=f"Страна: {country}")
        else:
            self.country_label.config(text="Страна: —")

    def start_check(self):
        """Запускает проверку в отдельном потоке, чтобы не блокировать GUI."""
        self.check_button.config(state="disabled")
        self.status_label.config(text="Проверка...")
        thread = threading.Thread(target=self.run_check)
        thread.daemon = True
        thread.start()

    def run_check(self):
        """Выполняет все проверки."""
        check_time = datetime.now().strftime("%H:%M:%S")

        proxy = self.get_system_proxy()
        proxies = None
        if proxy:
            proxies = {
                "http": f"http://{proxy}",
                "https": f"http://{proxy}"
            }
            self.root.after(0, lambda: self.status_label.config(text=f"Используется прокси: {proxy}"))
        else:
            self.root.after(0, lambda: self.status_label.config(text="Системный прокси не обнаружен"))

        # Проверка YouTube
        youtube_ok = self.check_youtube(proxies)

        # Проверка VPN: если YouTube доступен и прокси используется, считаем VPN рабочим.
        # (Можно также сравнить IP, но для простоты достаточно доступности YouTube через прокси)
        vpn_ok = youtube_ok and (proxy is not None)

        # Определение страны (через прокси, если он есть)
        country = self.get_country(proxies)

        # Обновляем интерфейс в основном потоке
        self.root.after(0, self.update_ui, youtube_ok, vpn_ok, country, check_time)
        self.root.after(0, lambda: self.check_button.config(state="normal"))
        self.root.after(0, lambda: self.status_label.config(text="Готово"))

if __name__ == "__main__":
    root = tk.Tk()
    app = VPNCheckerApp(root)
    root.mainloop()