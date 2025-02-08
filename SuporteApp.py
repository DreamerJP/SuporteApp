import os
import sys
import tkinter as tk
from tkinter import simpledialog, scrolledtext, filedialog, ttk, messagebox, colorchooser
import json
import pygame
import random
import subprocess
import tempfile
import requests
import time
import shutil

def get_resource_path(relative_path):
    """Obtém caminho correto para recursos tanto em desenvolvimento quanto no executável"""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

# Constantes para cores e caminhos de arquivo
DEFAULT_BG_COLOR = "#FFFFFF"  # Cor de fundo padrão
DARK_BG_COLOR = "#000000"     # Cor de fundo no modo escuro
SEPIA_BG_COLOR = "#F4EBD0"    # Cor de fundo sepia
SEPIA_TEXT_COLOR = "#5A4A42"  # Cor do texto no tema sepia
SEPIA_BUTTON_BG = "#D2B48C"   # Cor de fundo dos botões no tema sepia
SEPIA_BUTTON_FG = "#5A4A42"   # Cor do texto dos botões no tema sepia
DEFAULT_WINDOW_SIZE = "800x600+100+100"
DEFAULT_BG_IMAGE_PATH = "background.png"
LIGHT_THEME_PREVIEW_PATH = get_resource_path("light_theme_preview.png")
DARK_THEME_PREVIEW_PATH = get_resource_path("dark_theme_preview.png")
SEPIA_THEME_PREVIEW_PATH = get_resource_path("sepia_theme_preview.png")
SEPIA_BG_IMAGE_PATH = get_resource_path("sepia_background.png")
CONFIG_FILE = "config.txt"
TEXTS_FILE = "texts.json"
NOTEPAD_FILE = "notepad.json"

def handle_rmtree_error(func, path, exc_info):
    """Manipulador de erros para shutil.rmtree."""
    import stat
    if not os.access(path, os.W_OK):
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise

def cleanup_old_temp_dirs():
    """
    Limpa diretórios temporários antigos (_MEI*) no diretório do executável.
    Executa automaticamente no início do programa.
    """
    try:
        if not getattr(sys, 'frozen', False):
            return

        exe_dir = os.path.dirname(sys.executable)
        current_temp_dir = getattr(sys, '_MEIPASS', None)

        for entry in os.listdir(exe_dir):
            entry_path = os.path.join(exe_dir, entry)
            
            if os.path.isdir(entry_path) and entry.startswith('_MEI') and entry_path != current_temp_dir:
                print(f"[CLEANUP] Tentando excluir: {entry_path}")
                try:
                    shutil.rmtree(entry_path, ignore_errors=True)
                    print(f"[CLEANUP] Diretório excluído: {entry_path}")
                except Exception as e:
                    print(f"[CLEANUP] Erro ao excluir {entry_path}: {str(e)}")

    except Exception as main_error:
        print(f"[CLEANUP] Erro crítico durante a limpeza: {str(main_error)}")

class Updater:
    def __init__(self, current_version):
        self.current_version = current_version
        self.version_url = "https://raw.githubusercontent.com/DreamerJP/SuporteApp/main/version.json"

    def check_for_updates(self):
        try:
            response = requests.get(self.version_url)
            response.raise_for_status()
            version_info = response.json()
            if version_info["version"] > self.current_version:
                return version_info
            return None
        except Exception as e:
            print(f"Erro ao verificar atualizações: {e}")
            return None

    def download_and_install(self, download_url):
        try:
            current_exe = sys.executable
            print(f"[DEBUG] Caminho atual: {current_exe}")

            response = requests.get(download_url)
            response.raise_for_status()
            
            with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as temp_file:
                temp_file.write(response.content)
                new_exe_path = temp_file.name
                print(f"[DEBUG] Novo executável: {new_exe_path}")

            bat_content = self.generate_bat_script(current_exe, new_exe_path)
            bat_path = self.write_and_validate_bat(bat_content, current_exe, new_exe_path)
            
            subprocess.Popen(
                [bat_path],
                shell=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            time.sleep(2)  # Pequena pausa para garantir que o script BAT seja iniciado
            sys.exit(0)
        except Exception as e:
            print(f"Falha crítica na atualização: {str(e)}")
            messagebox.showerror("Erro de Atualização", f"Detalhes: {str(e)}")

    def generate_bat_script(self, old_exe, new_exe):
        """Gera o conteúdo do BAT com caminhos embutidos"""
        old_exe = os.path.normpath(os.path.abspath(old_exe))
        new_exe = os.path.normpath(os.path.abspath(new_exe))
        return f"""@@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: === DADOS EMBUTIDOS ===
set "OLD_EXE={old_exe}"
set "NEW_EXE={new_exe}"

:: === Encerrando processo atual ===
echo Encerrando processo atual...
for %%I in ("%OLD_EXE%") do set "EXE_NAME=%%~nxI"
taskkill /IM "!EXE_NAME!" /F >nul 2>&1

:: === VALIDAÇÃO DOS CAMINHOS ===
if not exist "%OLD_EXE%" (
    echo ERRO: Executável original não encontrado
    echo [DEBUG] Caminho verificado: %OLD_EXE%
    pause
    exit /b 1
)

if not exist "%NEW_EXE%" (
    echo ERRO: Novo executável não encontrado
    echo [DEBUG] Caminho verificado: %NEW_EXE%
    pause
    exit /b 1
)

:: === LÓGICA DE ATUALIZAÇÃO ===
set "MAX_TENTATIVAS=10"
:loop_substituicao
del /F /Q "%OLD_EXE%" >nul 2>&1

if exist "%OLD_EXE%" (
    echo Aguardando liberação do arquivo...
    timeout /t 1 /nobreak >nul
    set /a MAX_TENTATIVAS-=1
    if !MAX_TENTATIVAS! GTR 0 goto loop_substituicao
    
    echo Falha crítica: Não foi possível substituir o arquivo
    pause
    exit /b 1
)

move /Y "%NEW_EXE%" "%OLD_EXE%" >nul || (
    echo ERRO: Falha ao mover novo executável
    pause
    exit /b 1
)

echo Reiniciando aplicação...
start "" "%OLD_EXE%"
exit /b 0
"""

    def write_and_validate_bat(self, content, old_exe, new_exe):
        """Escreve o arquivo BAT e verifica a integridade"""
        old_exe = os.path.normpath(os.path.abspath(old_exe))
        new_exe = os.path.normpath(os.path.abspath(new_exe))
        bat_path = os.path.join(tempfile.gettempdir(), "update_script.bat")
    
        # Escreve com codificação UTF-8 com BOM
        with open(bat_path, "w", encoding="utf-8-sig") as f:
            f.write(content)
    
        # Verificação crítica
        with open(bat_path, "r", encoding="utf-8-sig") as f:
            content_read = f.read()
            if old_exe not in content_read or new_exe not in content_read:
                raise ValueError("Falha na geração do script de atualização")
        
        return bat_path

class ConfigManager:
    """Gerencia o carregamento e salvamento das configurações do aplicativo."""
    def __init__(self):
        self.config_path = os.path.join(os.path.dirname(sys.executable), CONFIG_FILE)
        self.default_config = {
            "bg_image_path": DEFAULT_BG_IMAGE_PATH,
            "sound_enabled": True,
            "dark_mode": False,
            "bg_color": DEFAULT_BG_COLOR,
            "show_edit_buttons": True,
            "window_size_normal": DEFAULT_WINDOW_SIZE,
            "window_size_notepad": "800x800+100+100",
            "notepad_expanded": True,
            "last_bg_image_path": DEFAULT_BG_IMAGE_PATH,
            "last_bg_color": DEFAULT_BG_COLOR
        }
        self.config = self.load_config()

    def load_config(self):
        """Carrega as configurações do arquivo ou retorna as configurações padrão."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as file:
                    config = json.load(file)
                    for key in self.default_config:
                        if key not in config:
                            config[key] = self.default_config[key]
                    return config
            except (json.JSONDecodeError, FileNotFoundError):
                return self.default_config
        return self.default_config

    def save_config(self):
        """Salva as configurações no arquivo."""
        with open(self.config_path, "w") as file:
            json.dump(self.config, file)

class TextManager:
    """Gerencia o carregamento e salvamento dos textos."""
    def __init__(self):
        self.texts_path = os.path.join(os.path.dirname(sys.executable), TEXTS_FILE)
        self.texts = self.load_texts()

    def load_texts(self):
        """Carrega os textos do arquivo ou retorna uma lista padrão."""
        if os.path.exists(self.texts_path):
            try:
                with open(self.texts_path, "r", encoding="utf-8") as file:
                    return json.load(file)
            except (json.JSONDecodeError, FileNotFoundError):
                return [("EXEMPLO", "BOTÃO")]
        return [("EXEMPLO", "BOTÃO")]

    def save_texts(self):
        """Salva os textos no arquivo."""
        with open(self.texts_path, "w", encoding="utf-8") as file:
            json.dump(self.texts, file, ensure_ascii=False, indent=4)

class NotepadManager:
    """Gerencia o bloco de notas."""
    def __init__(self):
        self.notepad_path = os.path.join(os.path.dirname(sys.executable), NOTEPAD_FILE)

    def load_notepad(self):
        """Carrega o conteúdo do bloco de notas."""
        if os.path.exists(self.notepad_path):
            try:
                with open(self.notepad_path, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    return data["text"], data["tags"]
            except (FileNotFoundError, json.JSONDecodeError):
                return "", []
        return "", []

    def save_notepad(self, content, tags):
        """Salva o conteúdo no bloco de notas."""
        data = {
            "text": content,
            "tags": tags
        }
        with open(self.notepad_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

class SupportApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SuporteApp")

        try:
            if getattr(sys, 'frozen', False):  # Verifica se é executável compilado
                # Caminho para o ícone nos recursos temporários do executável
                icon_path = os.path.join(sys._MEIPASS, "ico.ico")
                self.root.iconbitmap(icon_path)
        except Exception as e:
            print(f"Icone não carregado: {e}")
        
        self.current_version = "2.8"
        self.updater = Updater(self.current_version)
        self.check_updates()

        # Inicializa os gerenciadores
        self.config_manager = ConfigManager()
        self.text_manager = TextManager()
        self.notepad_manager = NotepadManager()

        # Carrega as configurações
        self.config = self.config_manager.config
        self.texts = self.text_manager.texts

        # Define a geometria
        initial_size = self.config["window_size_notepad" if self.config["notepad_expanded"] else "window_size_normal"]
        self.root.geometry(initial_size)

        self.setup_ui()
        pygame.mixer.init()
        self.click_sound = None
        self.load_sound()

        # Inicializa pilhas de undo e redo
        self.undo_stack = []
        self.redo_stack = []

    def check_updates(self):
        version_info = self.updater.check_for_updates()
        if version_info:
            if messagebox.askyesno("Atualização Disponível", f"Uma nova versão ({version_info['version']}) está disponível. Deseja atualizar agora?"):
                self.updater.download_and_install(version_info["download_url"])

    def load_sound(self):
        try:
            self.click_sound = pygame.mixer.Sound("click.wav")
        except Exception as e:
            print(f"Erro ao carregar som: {e}")
            self.config["sound_enabled"] = False
            self.sound_menu.entryconfig(0, label="Erro - Som Desativado")

    def setup_ui(self):
        self.root.configure(bg=self.config["bg_color"])
        self.load_bg_image()
        self.create_widgets()
        self.create_menu()
        self.create_notepad_widget()
        self.root.bind("<Configure>", self.save_window_size)
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Configurações de cores com base no modo atual
        if self.config["dark_mode"] == "dark":
            self.style.configure('TButton', font=('Helvetica', 8), padding=3, background='black', foreground='white')
            self.style.map('TButton', 
                background=[('pressed', '#333333'), ('active', '#444444')],
                foreground=[('pressed', 'white'), ('active', 'white')]
            )
        elif self.config["dark_mode"] == "sepia":
            self.style.configure('TButton', font=('Helvetica', 8), padding=3, background=SEPIA_BUTTON_BG, foreground=SEPIA_BUTTON_FG)
            self.style.map('TButton', 
                background=[('pressed', '#C4A484'), ('active', '#B8860B')],
                foreground=[('pressed', SEPIA_TEXT_COLOR), ('active', SEPIA_TEXT_COLOR)]
            )
        else:
            self.style.configure('TButton', font=('Helvetica', 8), padding=3, background='white', foreground='black')
            self.style.map('TButton', 
                background=[('pressed', '#dddddd'), ('active', '#cccccc')],
                foreground=[('pressed', 'black'), ('active', 'black')]
            )

        self.style.configure('TFrame', background=self.config["bg_color"])

    def save_window_size(self, event):
            """Salva o tamanho atual da janela no estado correto."""
            if event.widget == self.root:
                current_geometry = self.root.wm_geometry()
        
                if self.config["notepad_expanded"]:
                    self.config["window_size_notepad"] = current_geometry
                else:
                    self.config["window_size_normal"] = current_geometry
        
                self.config_manager.save_config()
            
    def load_bg_image(self):
        try:
            if self.config["dark_mode"] == "sepia":
                self.bg_image = tk.PhotoImage(file=SEPIA_BG_IMAGE_PATH)
            else:
                self.bg_image = tk.PhotoImage(file=self.config["bg_image_path"])
        except tk.TclError:
            # Exibe mensagem de erro e permite ao usuário selecionar uma nova imagem
            tk.messagebox.showerror("Erro", "Não foi possível carregar a imagem de fundo.")
            new_path = self.select_bg_image()
            self.config["bg_image_path"] = new_path
            self.config_manager.save_config()
            try:
                # Tenta carregar a nova imagem selecionada
                self.bg_image = tk.PhotoImage(file=self.config["bg_image_path"])
            except tk.TclError:
                # Se falhar novamente, usa a imagem padrão e exibe erro
                tk.messagebox.showerror("Erro", "A nova imagem também não pôde ser carregada. Usando imagem padrão.")
                self.config["bg_image_path"] = DEFAULT_BG_IMAGE_PATH
                self.config_manager.save_config()
                try:
                    self.bg_image = tk.PhotoImage(file=self.config["bg_image_path"])
                except tk.TclError:
                    # Se a imagem padrão também não existir, exibe erro e continua sem imagem
                    tk.messagebox.showerror("Erro", "Imagem padrão não encontrada. Verifique o arquivo.")
                    self.bg_image = None

    def select_bg_image(self):
        file_path = filedialog.askopenfilename(
            title="Selecione a imagem de fundo",
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.gif")]
        )
        return file_path if file_path else DEFAULT_BG_IMAGE_PATH

    def create_widgets(self):
        self.canvas = tk.Canvas(self.root, width=self.bg_image.width(), height=self.bg_image.height())
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_image(0, 0, image=self.bg_image, anchor="nw")

        frame = tk.Frame(self.canvas)
        self.canvas.create_window(10, 10, anchor="nw", window=frame)

        self.scrollbar = tk.Scrollbar(frame, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side="right", fill="y")

        button_frame = tk.Frame(frame, bg=self.config["bg_color"])
        button_frame.pack(side="left", fill="both", expand=True)

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.create_buttons(button_frame)

    def create_buttons(self, button_frame):
        column, row = 0, 0
        for idx, (text, resumo) in enumerate(self.texts):
            button = ttk.Button(button_frame, text=resumo, style='TButton', 
                              command=lambda t=text: self.copy_to_clipboard(t))
            button.grid(row=row, column=column, padx=5, pady=5, sticky="nsew")

            edit_button = ttk.Button(button_frame, text="Editar", command=lambda idx=idx: self.open_edit_window(idx))
            if self.config["show_edit_buttons"]:
                edit_button.grid(row=row + 1, column=column, padx=5, pady=5, sticky="nsew")

            row += 2
            if row > 16:
                row = 0
                column += 1

        button_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def copy_to_clipboard(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        if self.config["sound_enabled"] and self.click_sound:
            try:
                # Toca em um novo canal cada vez para permitir sobreposição
                pygame.mixer.find_channel(True).play(self.click_sound)
            except Exception as e:
                print(f"Erro ao reproduzir som: {e}")

    def open_edit_window(self, idx):
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Editar Texto e Nome do Botão")

        # Campo para editar o nome do botão
        tk.Label(edit_window, text="Nome do Botão:").pack(padx=10, pady=(10, 0))
        name_entry = tk.Entry(edit_window, width=50)
        name_entry.pack(padx=10, pady=(0, 10))
        name_entry.insert(tk.END, self.texts[idx][1])  # Preenche com o nome atual do botão

        # Campo para editar o texto do botão
        tk.Label(edit_window, text="Texto do Botão:").pack(padx=10, pady=(10, 0))
        text_box = scrolledtext.ScrolledText(edit_window, wrap=tk.WORD, width=50, height=15)
        text_box.pack(padx=10, pady=(0, 10))
        text_box.insert(tk.END, self.texts[idx][0])  # Preenche com o texto atual do botão

        def save_text():
            new_text = text_box.get("1.0", tk.END).strip()
            new_name = name_entry.get()
            if new_name and new_text:
                self.texts[idx] = (new_text, new_name)  # Atualiza tanto o texto quanto o nome
                self.text_manager.save_texts()
                self.refresh_gui()
                edit_window.destroy()

        ttk.Button(edit_window, text="Salvar", command=save_text).pack(pady=10)

    def create_menu(self):
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        # Menu "Visual"
        self.view_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Visual", menu=self.view_menu)

        # Adiciona a opção "Temas"
        self.view_menu.add_command(label="Temas", command=self.open_theme_selector)

        # Outras opções do menu "Visual"
        self.view_menu.add_command(label="Alterar Plano de Fundo", command=self.change_bg_image)
        self.view_menu.add_command(label="Editar Cor de fundo", command=self.edit_colors)
        self.view_menu.add_command(
            label="Ocultar Botões de Edição" if self.config["show_edit_buttons"] else "Exibir Botões de Edição",
            command=self.toggle_edit_buttons
        )
        self.view_menu.add_command(
            label="Ocultar Bloco de Notas" if self.config["notepad_expanded"] else "Exibir Bloco de Notas",
            command=self.toggle_notepad
        )

        # Menu "Som"
        self.sound_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Som", menu=self.sound_menu)
        self.sound_menu.add_command(
            label="Desativar Som de Clique" if self.config["sound_enabled"] else "Ativar Som de Clique",
            command=self.toggle_sound
        )

        # Menu "Ajuda"
        help_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Ajuda", menu=help_menu)
        help_menu.add_command(label="Sobre", command=self.show_about)

    def open_theme_selector(self):
        """Abre a janela de seleção de temas com preview."""
        theme_window = tk.Toplevel(self.root)
        theme_window.title("Selecionar Tema")
        theme_window.geometry("620x450")

        # Frame para organizar os temas
        theme_frame = tk.Frame(theme_window, bg=self.config["bg_color"])
        theme_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # Configuração do grid para expansão
        theme_frame.grid_columnconfigure(0, weight=1)
        theme_frame.grid_columnconfigure(1, weight=1)
        theme_frame.grid_columnconfigure(2, weight=1)
        theme_frame.grid_rowconfigure(0, weight=1)
        theme_frame.grid_rowconfigure(1, weight=1)

        # Tema Claro
        light_theme_btn = tk.Button(
            theme_frame,
            text="Modo Claro",
            command=lambda: self.apply_theme("light"),
            bg="white", fg="black",
            font=('Helvetica', 12, 'bold'),
            padx=10, pady=10
        )
        light_theme_btn.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Adiciona preview do tema claro
        try:
            light_preview = tk.PhotoImage(file=LIGHT_THEME_PREVIEW_PATH)
            light_preview_label = tk.Label(theme_frame, image=light_preview, bg=self.config["bg_color"])
            light_preview_label.image = light_preview
            light_preview_label.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        except Exception as e:
            print(f"Erro ao carregar miniatura do tema claro: {e}")

        # Tema Escuro
        dark_theme_btn = tk.Button(
            theme_frame,
            text="Modo Escuro",
            command=lambda: self.apply_theme("dark"),
            bg="black", fg="white",
            font=('Helvetica', 12, 'bold'),
            padx=10, pady=10
        )
        dark_theme_btn.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # Adiciona preview do tema escuro
        try:
            dark_preview = tk.PhotoImage(file=DARK_THEME_PREVIEW_PATH)
            dark_preview_label = tk.Label(theme_frame, image=dark_preview, bg=self.config["bg_color"])
            dark_preview_label.image = dark_preview
            dark_preview_label.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        except Exception as e:
            print(f"Erro ao carregar miniatura do tema escuro: {e}")

        # Tema Sepia
        sepia_theme_btn = tk.Button(
            theme_frame,
            text="Modo Sepia",
            command=lambda: self.apply_theme("sepia"),
            bg=SEPIA_BUTTON_BG, fg=SEPIA_BUTTON_FG,
            font=('Helvetica', 12, 'bold'),
            padx=10, pady=10
        )
        sepia_theme_btn.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")

        # Adiciona preview do tema sepia
        try:
            sepia_preview = tk.PhotoImage(file=SEPIA_THEME_PREVIEW_PATH)
            sepia_preview_label = tk.Label(theme_frame, image=sepia_preview, bg=self.config["bg_color"])
            sepia_preview_label.image = sepia_preview
            sepia_preview_label.grid(row=1, column=2, padx=10, pady=10, sticky="nsew")
        except Exception as e:
            print(f"Erro ao carregar miniatura do tema sepia: {e}")

    def apply_theme(self, theme):
        """Aplica o tema selecionado."""
        # Captura o conteúdo e as tags do bloco de notas antes de recriar a interface
        notepad_content = self.notepad_text.get("1.0", tk.END).strip()  # Remove espaços em branco no final
        notepad_tags = self._capture_tags()

        if theme == "light":
            self.config["dark_mode"] = "light"
            self.config["bg_image_path"] = DEFAULT_BG_IMAGE_PATH  # Define o caminho da imagem padrão
            self.config["last_bg_image_path"] = DEFAULT_BG_IMAGE_PATH  # Reseta o último caminho da imagem
            self.config["bg_color"] = DEFAULT_BG_COLOR
        elif theme == "dark":
            self.config["dark_mode"] = "dark"
            self.config["last_bg_image_path"] = self.config["bg_image_path"]  # Salva o caminho atual
            self.config["last_bg_color"] = self.config["bg_color"]
            self.config["bg_image_path"] = "ModoNoturno.png"
            self.config["bg_color"] = DARK_BG_COLOR
        elif theme == "sepia":
            self.config["dark_mode"] = "sepia"
            self.config["last_bg_image_path"] = self.config["bg_image_path"]  # Salva o caminho atual
            self.config["last_bg_color"] = self.config["bg_color"]
            self.config["bg_image_path"] = SEPIA_BG_IMAGE_PATH
            self.config["bg_color"] = SEPIA_BG_COLOR

        self.config_manager.save_config()
        self.refresh_gui()

        # Restaura o conteúdo e as tags do bloco de notas após recriar a interface
        self.notepad_text.delete("1.0", tk.END)  # Limpa o conteúdo atual
        self.notepad_text.insert(tk.END, notepad_content)  # Insere o conteúdo salvo
        for tag in notepad_tags:
            self.notepad_text.tag_add(tag["tag"], tag["start"], tag["end"])  # Restaura as tags
        self.update_button_styles()
        
    def toggle_sound(self):
        self.config["sound_enabled"] = not self.config["sound_enabled"]
        self.sound_menu.entryconfig(0, label="Desativar Som de Clique" if self.config["sound_enabled"] else "Ativar Som de Clique")
        self.config_manager.save_config()

    def toggle_edit_buttons(self):
        self.config["show_edit_buttons"] = not self.config["show_edit_buttons"]
        self.view_menu.entryconfig(2, label="Ocultar Botões de Edição" if self.config["show_edit_buttons"] else "Exibir Botões de Edição")
        self.config_manager.save_config()
        self.refresh_gui()

    def toggle_notepad(self):
        """Alterna a visibilidade do bloco de notas e ajusta a janela."""
        # 1. Salva geometria atual ANTES de mudar o estado
        current_geometry = self.root.wm_geometry()
    
        if self.config["notepad_expanded"]:
            self.config["window_size_notepad"] = current_geometry
        else:
            self.config["window_size_normal"] = current_geometry

        # 2. Alterna o estado
        self.config["notepad_expanded"] = not self.config["notepad_expanded"]
    
        # 3. Aplica nova geometria baseada no novo estado
        if self.config["notepad_expanded"]:
            nova_geometria = self.config["window_size_notepad"]
            self.notepad_frame.pack(fill="both", expand=True)
        else:
            nova_geometria = self.config["window_size_normal"]
            self.notepad_frame.pack_forget()

        # 4. Força redimensionamento imediato
        self.root.geometry(nova_geometria)
        self.root.update_idletasks()
    
        # 5. Atualiza menu e salvar configuração
        self.view_menu.entryconfig(4, label="Ocultar Bloco de Notas" if self.config["notepad_expanded"] else "Exibir Bloco de Notas")
        self.config_manager.save_config()

    def show_about(self):
        """Exibe a janela 'Sobre' com informações do aplicativo."""
        about_window = tk.Toplevel(self.root)
        about_window.title("Sobre")
        about_window.geometry("400x300")  # Aumenta a largura e altura da janela

        # Adiciona informações sobre a versão
        tk.Label(about_window, text="Versão Suporte 2.8\n").pack(padx=20, pady=(20, 5))

        # Nome do desenvolvedor
        nome_label = tk.Label(about_window, text="Paulo Gama", fg="blue", cursor="hand2")
        nome_label.pack(padx=20, pady=(5, 5))
        nome_label.bind("<1>", lambda event: self.start_snake_game(about_window))

        # Email do desenvolvedor
        email_label = tk.Label(about_window, text="DreamerJPMG@gmail.com", fg="green", cursor="hand2")
        email_label.pack(padx=20, pady=(5, 10))
        email_label.bind("<1>", lambda event: self.copy_to_clipboard("DreamerJPMG@gmail.com"))

        # Adiciona informações sobre as tecnologias utilizadas
        tk.Label(about_window, text="Tecnologias utilizadas:").pack(padx=20, pady=(5, 5))

        # Texto com quebra automática
        tecnologias = "Python, Tkinter, Pygame, JSON, Requests, Subprocess, Tempfile, Random, Time, OS, Sys, TTK (Themed Tkinter), ScrolledText, Messagebox, Filedialog, Simpledialog, shutil."
        tk.Label(about_window, text=tecnologias, wraplength=350, justify="left").pack(padx=20, pady=(5, 10))
        
        # Informações sobre o desenvolvimento
        tk.Label(about_window, text="Desenvolvido como um projeto pessoal.").pack(padx=20, pady=(5, 5))

    def start_snake_game(self, about_window):
        about_window.destroy()  # Fecha a janela "Sobre"
        try:
            snake_game = tk.Toplevel(self.root)  # Cria uma nova janela para o jogo
            SnakeGame(snake_game)  # Inicializa o jogo Snake na nova janela
        except Exception as e:
            messagebox.showerror("Erro ao Iniciar o Jogo", f"Ocorreu um erro: {str(e)}")
            print(f"Erro detalhado: {traceback.format_exc()}")

    def adjust_window_geometry(self):
        # Obten a geometria atual da janela
        current_geometry = self.root.geometry()
        width, height, x, y = map(int, current_geometry.replace('x', '+').split('+'))
    
        # Define a nova altura da janela com base no estado do bloco de notas
        if self.config["notepad_expanded"]:
            new_height = height + 200  # Aumenta a altura para acomodar o bloco de notas
        else:
            new_height = height - 200  # Reduz a altura para recolher o bloco de notas
    
        # Aplica a nova geometria
        self.root.geometry(f"{width}x{new_height}+{x}+{y}")

    def change_bg_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.gif")])
        if file_path:
            self.config["bg_image_path"] = file_path
            self.config_manager.save_config()
            self.refresh_gui()

    def edit_colors(self):
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Editar Cores")

        # Frame principal para organização
        main_frame = ttk.Frame(edit_window)
        main_frame.pack(padx=20, pady=20)

        # Frame para a cor de fundo
        bg_frame = ttk.LabelFrame(main_frame, text="Cor de Fundo")
        bg_frame.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        # Label explicativa
        ttk.Label(bg_frame, text="Digite o código hexadecimal ou use o seletor:").grid(row=0, column=0, columnspan=3, pady=5)

        # Entrada para o código hexadecimal
        bg_color_entry = ttk.Entry(bg_frame, width=10)
        bg_color_entry.grid(row=1, column=0, padx=5, pady=5)
        bg_color_entry.insert(0, self.config["bg_color"])

        # Botão de seleção de cor
        def choose_color():
            # Abre o seletor de cores e pega a cor selecionada
            color = colorchooser.askcolor(title="Selecione uma cor", parent=edit_window)[1]
            if color:
                # Atualiza o campo de entrada com a cor selecionada
                bg_color_entry.delete(0, tk.END)
                bg_color_entry.insert(0, color)
                update_preview()  # Atualiza o preview após selecionar a cor

        ttk.Button(bg_frame, text="🎨 Seletor", command=choose_color).grid(row=1, column=1, padx=5, pady=5)

        # Botão de visualização
        preview_canvas = tk.Canvas(bg_frame, width=30, height=20, bg=self.config["bg_color"])
        preview_canvas.grid(row=1, column=2, padx=5, pady=5)

        def update_preview():
            color = bg_color_entry.get()
            if self.is_valid_color(color):
                preview_canvas.config(bg=color)

        bg_color_entry.bind("<KeyRelease>", lambda e: update_preview())

        # Botões de ação
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, pady=10)

        def save_colors():
            new_bg_color = bg_color_entry.get()
            if new_bg_color and not new_bg_color.startswith("#"):
                new_bg_color = "#" + new_bg_color

            if self.is_valid_color(new_bg_color):
                self.config["bg_color"] = new_bg_color
                self.config_manager.save_config()
                self.refresh_gui()
                edit_window.destroy()
            else:
                tk.messagebox.showerror("Erro", "Cor inválida. Por favor, insira um código hexadecimal válido.")

        ttk.Button(button_frame, text="Salvar", command=save_colors).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=edit_window.destroy).pack(side=tk.LEFT, padx=5)


    def is_valid_color(self, color):
        try:
            # Tenta criar um widget temporário com a cor fornecida
            temp_widget = tk.Label(self.root, bg=color)
            temp_widget.update_idletasks()  # Atualiza o widget para aplicar a cor
            return True
        except tk.TclError:
            return False

    def create_notepad_widget(self):
        self.notepad_frame = tk.Frame(self.root, bg=self.config["bg_color"])
        self.notepad_frame.pack(fill="both", expand=True)

        # Verifica o tema atual e define as cores do bloco de notas
        if self.config["dark_mode"] == "dark":
            notepad_bg_color = "black"
            notepad_fg_color = "white"
        elif self.config["dark_mode"] == "sepia":
            notepad_bg_color = SEPIA_BG_COLOR
            notepad_fg_color = SEPIA_TEXT_COLOR
        else:
            notepad_bg_color = "white"
            notepad_fg_color = "black"

        self.notepad_text = scrolledtext.ScrolledText(self.notepad_frame, width=50, height=10, wrap=tk.WORD, bg=notepad_bg_color, fg=notepad_fg_color)
        self.notepad_text.pack(padx=10, pady=10, fill="both", expand=True)

        self.notepad_toolbar = tk.Frame(self.notepad_frame, bg=self.config["bg_color"])
        self.notepad_toolbar.pack(fill="x", side="top")

        # Botões com tamanho fixo
        ttk.Button(self.notepad_toolbar, text="𝙉", width=3, command=lambda: self.notepad_text.tag_add("bold", "sel.first", "sel.last")).pack(side="left", padx=2)
        ttk.Button(self.notepad_toolbar, text="𝙄", width=3, command=lambda: self.notepad_text.tag_add("italic", "sel.first", "sel.last")).pack(side="left", padx=2)
        ttk.Button(self.notepad_toolbar, text="S͟", width=3, command=lambda: self.notepad_text.tag_add("underline", "sel.first", "sel.last")).pack(side="left", padx=2)
        ttk.Button(self.notepad_toolbar, text="Adicionar linha", command=self.add_separator).pack(side="left", padx=2)
    
        # Botão Salvar alinhado à esquerda e com tamanho fixo
        ttk.Button(self.notepad_toolbar, text="Salvar", width=10, command=self.save_notepad).pack(side="left", padx=2)

        default_font = ("Helvetica", "10")  # Tamanho da fonte padrão
        self.notepad_text.tag_config("bold", font=(default_font[0], default_font[1], "bold"))
        self.notepad_text.tag_config("italic", font=(default_font[0], default_font[1], "italic"))
        self.notepad_text.tag_config("underline", font=(default_font[0], default_font[1], "underline"))

        # Carrega o conteúdo do bloco de notas
        if not hasattr(self, 'notepad_initialized'):
            text, tags = self.notepad_manager.load_notepad()
            self.notepad_text.insert(tk.END, text)
            for tag in tags:
                self.notepad_text.tag_add(tag["tag"], tag["start"], tag["end"])
                self.notepad_initialized = True  # Marca como inicializado

        if not self.config["notepad_expanded"]:
            self.notepad_frame.pack_forget()

        # Vincula eventos de teclado para undo/redo
        self.notepad_text.bind("<Control-z>", self.undo)
        self.notepad_text.bind("<Control-y>", self.redo)
        self.notepad_text.bind("<Control-Z>", self.undo)  # Para sistemas que usam Shift
        self.notepad_text.bind("<Control-Y>", self.redo)  # Para sistemas que usam Shift

        # Salva o estado após uma pausa na digitação
        self.save_timer = None
        self.notepad_text.bind("<KeyRelease>", self._schedule_save_state)

    def _schedule_save_state(self, event=None):
        """Agenda o salvamento do estado após uma pausa na digitação."""
        if self.save_timer:
            self.root.after_cancel(self.save_timer)
        self.save_timer = self.root.after(1000, self.save_state)  # Salva após 1 segundo de inatividade

    def save_state(self):
        """Salva o estado atual do bloco de notas no histórico."""
        if not self.notepad_text:
            return  # Evita erros se o bloco de notas não estiver inicializado

        # Captura o texto e as tags
        text = self.notepad_text.get("1.0", tk.END)
        tags = self._capture_tags()

        # Adiciona o estado à pilha de undo
        if self.undo_stack and self.undo_stack[-1] == (text, tags):
            return  # Evita salvar estados duplicados
        self.undo_stack.append((text, tags))
        
        # Limpa a pilha de redo (não faz sentido refazer após uma nova ação)
        self.redo_stack.clear()

    def _capture_tags(self):
        """Captura todas as tags aplicadas no texto."""
        tags = []
        for tag in self.notepad_text.tag_names():
            if tag != "sel":
                ranges = self.notepad_text.tag_ranges(tag)
                for i in range(0, len(ranges), 2):
                    start = ranges[i]
                    end = ranges[i + 1]
                    tags.append({
                        "tag": tag,
                        "start": self.notepad_text.index(start),
                        "end": self.notepad_text.index(end)
                    })
        return tags

    def undo(self, event=None):
        """Desfaz a última ação."""
        if not self.undo_stack:
            return  # Nada para desfazer

        # Salva o estado atual na pilha de redo
        current_text = self.notepad_text.get("1.0", tk.END)
        current_tags = self._capture_tags()
        self.redo_stack.append((current_text, current_tags))
        
        # Restaura o estado anterior
        text, tags = self.undo_stack.pop()
        self._restore_state(text, tags)

    def redo(self, event=None):
        """Refaz a última ação desfeita."""
        if not self.redo_stack:
            return  # Nada para refazer

        # Salva o estado atual na pilha de undo
        current_text = self.notepad_text.get("1.0", tk.END)
        current_tags = self._capture_tags()
        self.undo_stack.append((current_text, current_tags))
        
        # Restaura o estado futuro
        text, tags = self.redo_stack.pop()
        self._restore_state(text, tags)

    def _restore_state(self, text, tags):
        """Restaura o texto e as tags no bloco de notas."""
        self.notepad_text.delete("1.0", tk.END)  # Limpa o conteúdo atual
        self.notepad_text.insert(tk.END, text)  # Insere o conteúdo salvo
    
        # Remove todas as tags existentes
        for tag in self.notepad_text.tag_names():
            if tag != "sel":
                self.notepad_text.tag_remove(tag, "1.0", tk.END)
    
        # Aplica as tags
        for tag in tags:
            self.notepad_text.tag_add(tag["tag"], tag["start"], tag["end"])

    def add_separator(self):
        self.notepad_text.insert(tk.END, "\n______________________\n")

    def save_notepad(self):
        content = self.notepad_text.get("1.0", tk.END)
        tags = []
        for tag in self.notepad_text.tag_names():
            if tag != "sel":
                ranges = self.notepad_text.tag_ranges(tag)
                for i in range(0, len(ranges), 2):
                    start = ranges[i]
                    end = ranges[i + 1]
                    tags.append({
                        "tag": tag,
                        "start": str(start),
                        "end": str(end)
                    })
        self.notepad_manager.save_notepad(content, tags)

    def refresh_gui(self):
        notepad_state = self.config["notepad_expanded"]

        for widget in self.root.winfo_children():
            widget.destroy()

        self.setup_ui()

        # Restaura geometria correta após recriação da UI
        if notepad_state:
            self.root.geometry(self.config["window_size_notepad"])
        else:
            self.root.geometry(self.config["window_size_normal"])

        self.root.update_idletasks()

        # Aplica as cores do tema sepia
        if self.config["dark_mode"] == "sepia":
            self.root.configure(bg=SEPIA_BG_COLOR)
            self.style.configure('TButton', background=SEPIA_BUTTON_BG, foreground=SEPIA_BUTTON_FG)
            self.style.map('TButton', 
                background=[('pressed', '#C4A484'), ('active', '#B8860B')],
                foreground=[('pressed', SEPIA_BUTTON_FG), ('active', SEPIA_BUTTON_FG)]
            )
            self.update_button_styles()
            self.style.configure('TFrame', background=SEPIA_BG_COLOR)
            self.notepad_text.config(bg=SEPIA_BG_COLOR, fg=SEPIA_TEXT_COLOR)


    def update_button_styles(self):
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Button):
                widget.configure(style='TButton')

class SnakeGame:
    def __init__(self, master):
        self.master = master
        self.master.title("Snake Game")
        self.master.geometry("400x450")
        self.canvas = tk.Canvas(self.master, width=400, height=400)
        self.canvas.pack()
        self.snake = [(200, 200), (220, 200), (240, 200)]
        self.direction = "right"
        self.direction_queue = []
        self.apple = self.generate_apple()
        self.score = 0
        self.game_active = False  # Adicionado para controlar o estado do jogo
        self.draw_grid()
        self.draw_snake()
        self.draw_apple()
        self.draw_score()
        self.master.bind("w", self.up)
        self.master.bind("a", self.left)
        self.master.bind("s", self.down)
        self.master.bind("d", self.right)
        self.start_button = tk.Button(self.master, text="Start", command=self.start_game)
        self.start_button.pack()

    def generate_apple(self):
        return (random.randint(0, 380) // 20 * 20, random.randint(0, 380) // 20 * 20)

    def draw_grid(self):
        for i in range(0, 400, 20):
            self.canvas.create_line(i, 0, i, 400, fill="#AAAAAA", width=1)
            self.canvas.create_line(0, i, 400, i, fill="#AAAAAA", width=1)

    def draw_snake(self):
        self.canvas.delete("snake")
        for x, y in self.snake:
            self.canvas.create_rectangle(x, y, x + 20, y + 20, fill="green", tag="snake")

    def draw_apple(self):
        self.canvas.delete("apple")
        self.canvas.create_oval(self.apple[0], self.apple[1], self.apple[0] + 20, self.apple[1] + 20, fill="red", tag="apple")

    def draw_score(self):
        self.canvas.delete("score")
        self.canvas.create_text(10, 10, text=f"Score: {self.score}", font=("Arial", 12), anchor="nw", tag="score")

    def start_game(self):
        self.game_active = True
        self.start_button.pack_forget()
        self.update()

    def update(self):
        if not self.game_active:  # Se o jogo não estiver ativo, não atualize
            return

        if self.direction_queue:
            new_direction = self.direction_queue.pop(0)
            if new_direction == "up" and self.direction != "down":
                self.direction = new_direction
            elif new_direction == "left" and self.direction != "right":
                self.direction = new_direction
            elif new_direction == "down" and self.direction != "up":
                self.direction = new_direction
            elif new_direction == "right" and self.direction != "left":
                self.direction = new_direction

        head = self.snake[-1]
        if self.direction == "right":
            new_head = (head[0] + 20, head[1])
        elif self.direction == "left":
            new_head = (head[0] - 20, head[1])
        elif self.direction == "up":
            new_head = (head[0], head[1] - 20)
        elif self.direction == "down":
            new_head = (head[0], head[1] + 20)

        self.snake.append(new_head)
        if self.snake[-1] == self.apple:
            self.score += 1
            self.apple = self.generate_apple()
        else:
            self.snake.pop(0)

        if (self.snake[-1][0] < 0 or self.snake[-1][0] >= 400 or
            self.snake[-1][1] < 0 or self.snake[-1][1] >= 400 or
            self.snake[-1] in self.snake[:-1]):
            self.game_active = False  # Para o jogo
            self.game_over()
            return  # Sai do método update para evitar chamadas recursivas

        self.draw_snake()
        self.draw_apple()
        self.draw_score()
        self.master.after(100, self.update)

    def game_over(self):
        self.canvas.delete("all")
        self.canvas.create_text(200, 100, text="Game Over!", font=("Arial", 24), fill="red")
        self.canvas.create_text(200, 150, text=f"Final Score: {self.score}", font=("Arial", 18))
    
        # Verifica se a pontuação está entre os top 3
        if self.is_new_high_score():
            self.request_player_name()  # Chama o método para solicitar o nome
        else:
            self.show_top_scores()  # Mostra os scores sem solicitar o nome

    def is_new_high_score(self):
        try:
            with open("scoresnake.dat", "r") as file:
                scores = [int(line.strip().split(",")[1]) for line in file.readlines()]
        except FileNotFoundError:
            scores = []

        # Verifica se a pontuação do jogador é maior que a menor pontuação no top 3
        return len(scores) < 3 or self.score > scores[-1]


    def request_player_name(self):
        name = tk.simpledialog.askstring("Nome do Jogador", "Digite seu nome (máx. 6 caracteres):")
        if name is None or name.strip() == "":
            messagebox.showerror("Erro", "Nome inválido! O score não será salvo.")
            self.show_top_scores()  # Mostra os scores sem salvar o novo
            return
        if len(name) > 6:
            messagebox.showerror("Erro", "Nome deve ter no máximo 6 caracteres!")
            self.request_player_name()  # Tenta novamente
            return
        self.save_score(name)  # Salva o score com o nome válido
        self.show_top_scores()  # Mostra os scores atualizados

    def save_score(self, name):
        try:
            with open("scoresnake.dat", "r") as file:
                scores = [line.strip().split(",") for line in file.readlines()]
        except FileNotFoundError:
            scores = []

        scores.append((name, str(self.score)))
        scores.sort(key=lambda x: int(x[1]), reverse=True)
        scores = scores[:3]  # Mantém apenas os top 3 scores

        with open("scoresnake.dat", "w") as file:
            for entry in scores:
                file.write(f"{entry[0]},{entry[1]}\n")

    def show_top_scores(self):
        self.canvas.create_text(200, 250, text="Top 3 Scores:", font=("Arial", 18))
        try:
            with open("scoresnake.dat", "r") as file:
                scores = [line.strip().split(",") for line in file.readlines()]
            for i, (name, score) in enumerate(scores):
                self.canvas.create_text(200, 300 + i * 30, text=f"{i + 1}. {name}: {score}", font=("Arial", 18))
        except FileNotFoundError:
            self.canvas.create_text(200, 300, text="Nenhum score registrado", font=("Arial", 18))

    def up(self, event):
        self.direction_queue.append("up")

    def left(self, event):
        self.direction_queue.append("left")

    def down(self, event):
        self.direction_queue.append("down")

    def right(self, event):
        self.direction_queue.append("right")

if __name__ == "__main__":
    cleanup_old_temp_dirs()  # Função de limpeza de pasta temporaria MEI na inicialização
    root = tk.Tk()
    app = SupportApp(root)
    root.mainloop()
