import tkinter as tk
from tkinter import simpledialog, messagebox
import re
import webbrowser
import threading
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
import keyboard
import sys
import json
import os
from datetime import datetime
import time

class IPClipboardOpener:
    def __init__(self):
        self.hotkey_enabled = [True]
        self.current_hotkey = ['f9']
        self.config_file = 'ip_opener_config.json'
        self.icon = None  # Referência para o ícone da tray
        self.load_config()
        self.hotkey_listener_thread = None
        self.setup_hotkey_listener()
        
    def load_config(self):
        """Carrega configurações salvas"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.hotkey_enabled[0] = config.get('hotkey_enabled', True)
                    self.current_hotkey[0] = config.get('current_hotkey', 'f9')
            except:
                pass
    
    def save_config(self):
        """Salva configurações"""
        config = {
            'hotkey_enabled': self.hotkey_enabled[0],
            'current_hotkey': self.current_hotkey[0]
        }
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except:
            pass

    def get_ip_from_clipboard(self):
        root = tk.Tk()
        root.withdraw()
        try:
            ip = root.clipboard_get().strip()
        except tk.TclError:
            ip = ""
        root.destroy()
        return ip

    def show_tray_notification(self, title, message, is_error=False):
        """Mostra notificação através do ícone da tray"""
        if self.icon:
            try:
                # Usa a notificação nativa do sistema através do pystray
                self.icon.notify(message, title)
            except:
                # Fallback: apenas imprime no console se a notificação falhar
                print(f"{title}: {message}")

    def open_links(self):
        ip = self.get_ip_from_clipboard()
        # Regex para validar IP (4 grupos de 1-3 dígitos separados por pontos)
        ip_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
        
        if re.match(ip_pattern, ip):
            try:
                webbrowser.open(f'http://{ip}')
                webbrowser.open(f'https://{ip}')
                webbrowser.open(f'http://{ip}:8081')
                webbrowser.open(f'https://{ip}:8081')
                return True
            except Exception as e:
                self.show_tray_notification("Erro", f"Erro ao abrir links: {str(e)}", True)
                return False
        else:
            return False

    def open_single_link(self, protocol, port=None):
        """Abre um link específico"""
        ip = self.get_ip_from_clipboard()
        # Regex para validar IP
        ip_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
        
        if re.match(ip_pattern, ip):
            try:
                if port:
                    url = f'{protocol}://{ip}:{port}'
                else:
                    url = f'{protocol}://{ip}'
                webbrowser.open(url)
                return True
            except Exception as e:
                self.show_tray_notification("Erro", f"Erro ao abrir link: {str(e)}", True)
                return False
        else:
            self.show_tray_notification("Erro", "A área de transferência não contém um IP válido.", True)
            return False

    def show_error(self, message):
        """Mostra mensagem de erro - apenas para casos onde realmente precisamos de modal"""
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Erro", message)
        root.destroy()

    def show_info(self, message):
        """Mostra mensagem de informação - apenas para casos onde realmente precisamos de modal"""
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo("Informação", message)
        root.destroy()

    def on_hotkey(self):
        """Função chamada quando o hotkey é pressionado - agora completamente silenciosa"""
        if self.hotkey_enabled[0]:
            success = self.open_links()
            if not success:
                # Em vez de mostrar uma janela modal, usa notificação silenciosa
                ip = self.get_ip_from_clipboard()
                if not ip:
                    self.show_tray_notification("Erro", "Área de transferência vazia", True)
                else:
                    self.show_tray_notification("Erro", f"IP inválido: '{ip}'", True)

    def setup_hotkey_listener(self):
        """Configura o listener do hotkey"""
        if self.hotkey_listener_thread and self.hotkey_listener_thread.is_alive():
            keyboard.unhook_all()
        
        def hotkey_listener():
            try:
                keyboard.add_hotkey(self.current_hotkey[0], self.on_hotkey)
                keyboard.wait()
            except:
                pass

        self.hotkey_listener_thread = threading.Thread(target=hotkey_listener, daemon=True)
        self.hotkey_listener_thread.start()

    def format_key_name(self, key):
        """Formata o nome da tecla para exibição"""
        key_mappings = {
            'space': 'ESPAÇO',
            'enter': 'ENTER',
            'tab': 'TAB',
            'backspace': 'BACKSPACE',
            'delete': 'DELETE',
            'insert': 'INSERT',
            'home': 'HOME',
            'end': 'END',
            'page up': 'PAGE UP',
            'page down': 'PAGE DOWN',
            'up': '↑',
            'down': '↓',
            'left': '←',
            'right': '→',
            'caps lock': 'CAPS LOCK',
            'shift': 'SHIFT',
            'ctrl': 'CTRL',
            'alt': 'ALT',
            'esc': 'ESC'
        }
        
        # Processa combinações de teclas
        if '+' in key:
            parts = key.split('+')
            formatted_parts = []
            for part in parts:
                part = part.strip().lower()
                formatted_parts.append(key_mappings.get(part, part.upper()))
            return '+'.join(formatted_parts)
        else:
            return key_mappings.get(key.lower(), key.upper())

    def capture_new_hotkey(self):
        """Captura uma nova tecla pressionada pelo usuário"""
        captured_key = [None]
        capture_active = [True]
        
        def on_key_event(event):
            if not capture_active[0]:
                return
                
            if event.event_type == keyboard.KEY_DOWN:
                key_name = event.name
                
                # Verifica se são teclas modificadoras sendo pressionadas
                modifiers = []
                if keyboard.is_pressed('ctrl'):
                    modifiers.append('ctrl')
                if keyboard.is_pressed('alt'):
                    modifiers.append('alt')
                if keyboard.is_pressed('shift'):
                    modifiers.append('shift')
                
                # Remove modificadores da tecla principal se necessário
                if key_name in ['ctrl', 'alt', 'shift']:
                    return
                
                # Constrói a combinação de teclas
                if modifiers:
                    captured_key[0] = '+'.join(modifiers + [key_name])
                else:
                    captured_key[0] = key_name
                
                capture_active[0] = False
                return False  # Para parar o hook
        
        return captured_key, capture_active, on_key_event

    def change_hotkey(self, icon, item):
        """Permite trocar a tecla de ativação com sistema de pressionar tecla"""
        # Para temporariamente o hotkey atual
        keyboard.unhook_all()
        
        # Cria janela de instrução
        root = tk.Tk()
        root.title("Trocar Tecla de Ativação")
        root.geometry("400x200")
        root.resizable(False, False)
        
        # Centraliza a janela
        root.eval('tk::PlaceWindow %s center' % root.winfo_pathname(root.winfo_id()))
        
        # Variáveis de controle
        status_var = tk.StringVar()
        status_var.set("Pressione a nova tecla de ativação...")
        
        # Interface
        frame = tk.Frame(root, padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text="Trocar Tecla de Ativação", font=("Arial", 12, "bold")).pack(pady=(0, 10))
        tk.Label(frame, text=f"Tecla atual: {self.format_key_name(self.current_hotkey[0])}", font=("Arial", 10)).pack(pady=(0, 20))
        
        status_label = tk.Label(frame, textvariable=status_var, font=("Arial", 10))
        status_label.pack(pady=(0, 10))
        
        tk.Label(frame, text="Exemplos: F9, Ctrl+Shift+O, Alt+I", font=("Arial", 8), fg="gray").pack(pady=(0, 20))
        
        # Botões
        button_frame = tk.Frame(frame)
        button_frame.pack()
        
        cancel_button = tk.Button(button_frame, text="Cancelar", command=root.destroy)
        cancel_button.pack(side=tk.LEFT, padx=(0, 10))
        
        def finish_capture():
            root.destroy()
        
        confirm_button = tk.Button(button_frame, text="Confirmar", command=finish_capture, state=tk.DISABLED)
        confirm_button.pack(side=tk.LEFT)
        
        # Sistema de captura
        captured_key, capture_active, on_key_event = self.capture_new_hotkey()
        
        def check_capture():
            if captured_key[0] and capture_active[0] == False:
                try:
                    # Testa se a tecla é válida
                    keyboard.add_hotkey(captured_key[0], lambda: None)
                    keyboard.remove_hotkey(captured_key[0])
                    
                    formatted_key = self.format_key_name(captured_key[0])
                    status_var.set(f"Nova tecla: {formatted_key}")
                    confirm_button.config(state=tk.NORMAL)
                    
                    def apply_change():
                        self.current_hotkey[0] = captured_key[0]
                        self.save_config()
                        self.setup_hotkey_listener()
                        self.show_info(f"Tecla de ativação alterada para: {formatted_key}")
                        icon.update_menu()
                        root.destroy()
                    
                    confirm_button.config(command=apply_change)
                    
                except Exception as e:
                    status_var.set(f"Tecla inválida: {captured_key[0]}")
                    captured_key[0] = None
                    capture_active[0] = True
                    keyboard.hook(on_key_event)
            
            if capture_active[0]:
                root.after(100, check_capture)
        
        # Inicia captura
        keyboard.hook(on_key_event)
        root.after(100, check_capture)
        
        # Cleanup ao fechar
        def on_closing():
            keyboard.unhook_all()
            self.setup_hotkey_listener()  # Restaura o hotkey original
            root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()

    def test_clipboard(self, icon, item):
        """Testa se o clipboard contém um IP válido"""
        ip = self.get_ip_from_clipboard()
        ip_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
        
        if re.match(ip_pattern, ip):
            self.show_tray_notification("Teste", f"IP válido: {ip}")
        else:
            self.show_tray_notification("Teste", f"IP inválido: '{ip}'", True)

    def show_about(self, icon, item):
        """Mostra informações sobre o programa"""
        info = f"""IP Clipboard Opener v2.2

Tecla de ativação: {self.format_key_name(self.current_hotkey[0])}
Status: {'Ativado' if self.hotkey_enabled[0] else 'Desativado'}

Funcionalidades:
• Abre automaticamente links HTTP/HTTPS
• Suporte para porta 8081
• Sistema de captura de tecla intuitivo
• Menu de contexto expandido
• Notificações silenciosas via system tray

Desenvolvido para automação de acesso a IPs."""
        self.show_info(info)

    def create_image(self):
        # Cria um ícone mais elaborado
        image = Image.new('RGB', (64, 64), color=(255, 255, 255))
        d = ImageDraw.Draw(image)
        
        # Fundo circular
        d.ellipse((4, 4, 60, 60), fill=(30, 144, 255))
        
        # Símbolo de rede (quadrados conectados)
        d.rectangle((20, 20, 28, 28), fill=(255, 255, 255))
        d.rectangle((36, 20, 44, 28), fill=(255, 255, 255))
        d.rectangle((20, 36, 28, 44), fill=(255, 255, 255))
        d.rectangle((36, 36, 44, 44), fill=(255, 255, 255))
        
        # Linhas conectoras
        d.line((28, 24, 36, 24), fill=(255, 255, 255), width=2)
        d.line((24, 28, 24, 36), fill=(255, 255, 255), width=2)
        d.line((40, 28, 40, 36), fill=(255, 255, 255), width=2)
        d.line((28, 40, 36, 40), fill=(255, 255, 255), width=2)
        
        return image

    def toggle_hotkey(self, icon, item):
        self.hotkey_enabled[0] = not self.hotkey_enabled[0]
        self.save_config()
        icon.update_menu()

    def quit_app(self, icon, item):
        keyboard.unhook_all()
        icon.stop()
        sys.exit()

    def open_all_links_manual(self, icon, item):
        """Abre todos os links manualmente via menu"""
        success = self.open_links()
        if not success:
            ip = self.get_ip_from_clipboard()
            if not ip:
                self.show_tray_notification("Erro", "Área de transferência vazia", True)
            else:
                self.show_tray_notification("Erro", f"IP inválido: '{ip}'", True)

    def get_menu(self):
        return (
            # Status e controle principal
            item(
                f'Status: {"Ativado" if self.hotkey_enabled[0] else "Desativado"}',
                self.toggle_hotkey,
                checked=lambda item: self.hotkey_enabled[0]
            ),
            item(f'Tecla atual: {self.format_key_name(self.current_hotkey[0])}', self.change_hotkey),
            
            # Separador
            pystray.Menu.SEPARATOR,
            
            # Ações rápidas
            item('Abrir todos os links', self.open_all_links_manual),
            item('Testar clipboard', self.test_clipboard),
            
            # Submenu para links individuais
            item('Abrir link específico', pystray.Menu(
                item('HTTP', lambda i, it: self.open_single_link('http')),
                item('HTTPS', lambda i, it: self.open_single_link('https')),
                item('HTTP:8081', lambda i, it: self.open_single_link('http', '8081')),
                item('HTTPS:8081', lambda i, it: self.open_single_link('https', '8081'))
            )),
            
            # Separador
            pystray.Menu.SEPARATOR,
            
            # Configurações e informações
            item('Trocar tecla de ativação', self.change_hotkey),
            item('Sobre', self.show_about),
            
            # Separador
            pystray.Menu.SEPARATOR,
            
            # Sair
            item('Sair', self.quit_app)
        )

    def run(self):
        self.icon = pystray.Icon(
            "IP Tray", 
            self.create_image(), 
            "IP Clipboard Opener", 
            menu=pystray.Menu(*self.get_menu())
        )
        self.icon.run()

def main():
    app = IPClipboardOpener()
    app.run()

if __name__ == "__main__":
    main()
