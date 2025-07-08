import tkinter as tk
import re
import webbrowser
import threading
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
import keyboard
import sys

# Variável de controle do atalho
hotkey_enabled = [True]  # Usar lista para mutabilidade em threads

def get_ip_from_clipboard():
    root = tk.Tk()
    root.withdraw()
    try:
        ip = root.clipboard_get().strip()
    except tk.TclError:
        ip = ""
    root.destroy()
    return ip

def open_links():
    ip = get_ip_from_clipboard()
    if re.match(r'^\d{1,3}(\.\d{1,3}){3}$', ip):
        webbrowser.open(f'http://{ip}')
        webbrowser.open(f'https://{ip}')
        webbrowser.open(f'http://{ip}:8081')
        webbrowser.open(f'https://{ip}:8081')
    else:
        print("A área de transferência não contém um IP válido.")

def on_hotkey():
    if hotkey_enabled[0]:
        open_links()

def hotkey_listener():
    keyboard.add_hotkey('f9', on_hotkey)
    keyboard.wait()  # Mantém o listener ativo

def create_image():
    # Cria um ícone simples (círculo azul)
    image = Image.new('RGB', (64, 64), color=(255, 255, 255))
    d = ImageDraw.Draw(image)
    d.ellipse((16, 16, 48, 48), fill=(30, 144, 255))
    return image

def toggle_hotkey(icon, item):
    hotkey_enabled[0] = not hotkey_enabled[0]
    icon.update_menu()

def quit_app(icon, item):
    icon.stop()
    sys.exit()

def main():
    # Thread para o listener do hotkey
    threading.Thread(target=hotkey_listener, daemon=True).start()

    # Menu da bandeja
    def get_menu():
        return (
            item(
                'Ativar F9' if not hotkey_enabled[0] else 'Desativar F9',
                toggle_hotkey,
                checked=lambda item: hotkey_enabled[0]
            ),
            item('Sair', quit_app)
        )

    icon = pystray.Icon("IP Tray", create_image(), "IP Clipboard Opener", menu=pystray.Menu(*get_menu()))
    icon.run()

if __name__ == "__main__":
    main()
