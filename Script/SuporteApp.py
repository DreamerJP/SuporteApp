"""
SuporteApp - Um aplicativo de suporte com interface gráfica para copiar textos, editar configurações e iniciar um jogo Snake.
Contém funcionalidades para atualização automática, gerenciamento de configurações e notas.
"""

import os
import sys
import tkinter as tk
from tkinter import (
    simpledialog,
    scrolledtext,
    filedialog,
    ttk,
    messagebox,
    colorchooser,
)
import json
import pygame
import random
import subprocess
import tempfile
import requests
import time
import shutil
import traceback


def get_resource_path(relative_path):
    """Obtém o caminho absoluto para um recurso, considerando se está em modo desenvolvimento ou executável."""
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# Constantes para cores e caminhos de arquivo
DEFAULT_BG_COLOR = "#FFFFFF"  # Cor de fundo padrão
DEFAULT_WINDOW_SIZE = "800x600+100+100"
DEFAULT_BG_IMAGE_PATH = "background.png"
CONFIG_FILE = "config.txt"
TEXTS_FILE = "texts.json"
NOTEPAD_FILE = "notepad.json"


def handle_rmtree_error(func, path, exc_info):
    """Manipulador de erros para shutil.rmtree: ajusta permissões para permitir a exclusão."""
    import stat

    if not os.access(path, os.W_OK):
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise


def cleanup_old_temp_dirs():
    """
    Limpa diretórios temporários antigos (_MEI*) no diretório do executável.
    Essa função é executada no início do programa para evitar acúmulo de pastas temporárias.
    """
    try:
        if not getattr(sys, "frozen", False):
            return

        exe_dir = os.path.dirname(sys.executable)
        current_temp_dir = getattr(sys, "_MEIPASS", None)

        for entry in os.listdir(exe_dir):
            entry_path = os.path.join(exe_dir, entry)

            if (
                os.path.isdir(entry_path)
                and entry.startswith("_MEI")
                and entry_path != current_temp_dir
            ):
                print(f"[CLEANUP] Tentando excluir: {entry_path}")
                try:
                    shutil.rmtree(entry_path, ignore_errors=True)
                    print(f"[CLEANUP] Diretório excluído: {entry_path}")
                except Exception as e:
                    print(f"[CLEANUP] Erro ao excluir {entry_path}: {str(e)}")

    except Exception as main_error:
        print(f"[CLEANUP] Erro crítico durante a limpeza: {str(main_error)}")


class Updater:
    """
    Gerencia a verificação e atualização do aplicativo.

    Atributos:
        current_version (str): Versão atual do aplicativo.
        version_url (str): URL para verificação de uma nova versão.
    """

    def __init__(self, current_version):
        self.current_version = current_version
        self.version_url = (
            "https://raw.githubusercontent.com/DreamerJP/SuporteApp/main/version.json"
        )

    def check_for_updates(self):
        """
        Verifica se há uma nova versão consultando a URL definida.

        Retorna:
            dict ou None: Informações da nova versão, se disponível.
        """
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
        """
        Faz o download do novo executável, cria e valida o script BAT para substituição e reinicia o aplicativo.

        Parâmetros:
            download_url (str): URL para download do novo executável.
        """
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
            bat_path = self.write_and_validate_bat(
                bat_content, current_exe, new_exe_path
            )

            subprocess.Popen(
                [bat_path],
                shell=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            time.sleep(2)  # Pequena pausa para garantir que o script BAT seja iniciado
            sys.exit(0)
        except Exception as e:
            print(f"Falha crítica na atualização: {str(e)}")
            messagebox.showerror("Erro de Atualização", f"Detalhes: {str(e)}")

    def generate_bat_script(self, old_exe, new_exe):
        """
        Gera o conteúdo do script BAT necessário para atualizar o executável.

        Parâmetros:
            old_exe (str): Caminho do executável atual.
            new_exe (str): Caminho do novo executável baixado.

        Retorna:
            str: Conteúdo do script BAT.
        """
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
        """
        Escreve o arquivo BAT com codificação UTF-8 com BOM e valida se os caminhos estão corretos.

        Parâmetros:
            content (str): Conteúdo do script BAT.
            old_exe (str): Caminho do executável atual.
            new_exe (str): Caminho do novo executável.

        Retorna:
            str: Caminho completo do script BAT escrito.
        """
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
    """
    Gerencia o carregamento e salvamento das configurações do aplicativo.

    As configurações incluem caminhos de arquivos, temas e tamanhos de janelas.
    """

    def __init__(self):
        self.config_path = os.path.join(os.path.dirname(sys.executable), CONFIG_FILE)
        self.default_config = {
            "bg_image_path": DEFAULT_BG_IMAGE_PATH,
            "sound_enabled": True,
            "bg_color": DEFAULT_BG_COLOR,
            "show_edit_buttons": True,
            "window_size_normal": DEFAULT_WINDOW_SIZE,
            "window_size_notepad": "800x800+100+100",
            "notepad_expanded": True,
            "last_bg_image_path": DEFAULT_BG_IMAGE_PATH,
            "last_bg_color": DEFAULT_BG_COLOR,
        }
        self.config = self.load_config()

    def load_config(self):
        """
        Carrega as configurações a partir do arquivo de configuração ou retorna as configurações padrão.

        Retorna:
            dict: Configurações carregadas.
        """
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
        """Salva as configurações atuais no arquivo de configuração."""
        with open(self.config_path, "w") as file:
            json.dump(self.config, file)


class TextManager:
    """
    Gerencia o carregamento e salvamento dos textos que serão copiados pelos botões.
    """

    def __init__(self):
        self.texts_path = os.path.join(os.path.dirname(sys.executable), TEXTS_FILE)
        self.texts = self.load_texts()
        # Dicionário para armazenar as categorias
        self.categories = self.extract_categories()

    def load_texts(self):
        """
        Carrega os textos do arquivo ou retorna uma lista padrão.

        Retorna:
            list: Lista de tuplas (texto, rótulo do botão, categoria).
        """
        if os.path.exists(self.texts_path):
            try:
                with open(self.texts_path, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    # Se for uma lista simples de tuplas [texto, rótulo]
                    if isinstance(data, list) and len(data) > 0:
                        # Verifica o formato dos dados
                        if isinstance(data[0], list):
                            # Se já tiver 3 elementos, mantém como está
                            if len(data[0]) == 3:
                                return data
                            # Se tiver 2 elementos, adiciona a categoria "Geral"
                            elif len(data[0]) == 2:
                                return [(text, label, "Geral") for text, label in data]
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        return [("EXEMPLO", "BOTÃO", "Geral")]

    def save_texts(self):
        """Salva os textos atuais no arquivo de configuração, mantendo a formatação UTF-8."""
        with open(self.texts_path, "w", encoding="utf-8") as file:
            json.dump(self.texts, file, ensure_ascii=False, indent=4)

    def extract_categories(self):
        """Extrai as categorias únicas dos textos carregados."""
        categories = set()
        for item in self.texts:
            # Se o item tiver categoria, usa ela; senão, usa 'Geral'
            if len(item) >= 3:
                categories.add(item[2])
            else:
                categories.add("Geral")

        # Garante que 'Geral' sempre exista
        categories.add("Geral")
        return sorted(list(categories))

    def add_category(self, category_name):
        """Adiciona uma nova categoria se ela não existir."""
        if category_name and category_name not in self.categories:
            self.categories.append(category_name)
            self.categories.sort()
            return True
        return False

    def rename_category(self, old_name, new_name):
        """Renomeia uma categoria e atualiza todos os textos associados."""
        if old_name in self.categories and new_name and new_name not in self.categories:
            # Atualiza todos os textos com a categoria antiga
            for i, item in enumerate(self.texts):
                if len(item) >= 3 and item[2] == old_name:
                    self.texts[i] = (item[0], item[1], new_name)

            # Atualiza a lista de categorias
            self.categories.remove(old_name)
            self.categories.append(new_name)
            self.categories.sort()
            self.save_texts()
            return True
        return False

    def delete_category(self, category_name):
        """Deleta uma categoria e move seus textos para 'Geral'."""
        if category_name in self.categories and category_name != "Geral":
            # Move todos os textos para a categoria 'Geral'
            for i, item in enumerate(self.texts):
                if len(item) >= 3 and item[2] == category_name:
                    self.texts[i] = (item[0], item[1], "Geral")

            # Remove a categoria
            self.categories.remove(category_name)
            self.save_texts()
            return True
        return False


class NotepadManager:
    """
    Gerencia o conteúdo do bloco de notas, permitindo salvar e carregar textos e suas formatações.
    """

    def __init__(self):
        self.notepad_path = os.path.join(os.path.dirname(sys.executable), NOTEPAD_FILE)

    def load_notepad(self):
        """
        Carrega o conteúdo do bloco de notas, retornando o texto e as formatações (tags).

        Retorna:
            tuple: (texto, lista de tags) ou ("", []) se não for possível carregar.
        """
        if os.path.exists(self.notepad_path):
            try:
                with open(self.notepad_path, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    return data["text"], data["tags"]
            except (FileNotFoundError, json.JSONDecodeError):
                return "", []
        return "", []

    def save_notepad(self, content, tags):
        """
        Salva o conteúdo e as tags (formatações) no arquivo referente ao bloco de notas.

        Parâmetros:
            content (str): Conteúdo do bloco de notas.
            tags (list): Lista de tags aplicadas ao texto.
        """
        data = {"text": content, "tags": tags}
        with open(self.notepad_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)


class Tooltip:
    """
    Exibe pequenos textos de apoio (tooltips) para widgets, com um delay configurável.
    """

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.id = None
        self.x = self.y = 0
        self.widget.bind("<Enter>", self.showtip)
        self.widget.bind("<Leave>", self.hidetip)

    def showtip(self, event=None):
        """Agenda a exibição do tooltip com um pequeno delay."""
        self.id = self.widget.after(100, self.display_tip)

    def display_tip(self):
        """Cria e exibe a janela do tooltip próximo ao widget."""
        if self.tip_window or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            tw,
            text=self.text,
            justify=tk.LEFT,
            background="#ffffe0",
            relief=tk.SOLID,
            borderwidth=1,
            font=("tahoma", 8, "normal"),
        )
        label.pack()

    def hidetip(self, event=None):
        """Remove o tooltip da tela e limpa o timer."""
        if self.tip_window:
            self.tip_window.destroy()
        self.tip_window = None
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None


class SupportApp:
    """
    Gerencia a interface principal do SuporteApp, incluindo a criação de botões, menus, bloco de notas e integração com o jogo Snake.
    """

    def __init__(self, root):
        self.root = root
        self.root.title("SuporteApp")

        try:
            if getattr(sys, "frozen", False):
                icon_path = os.path.join(sys._MEIPASS, "ico.ico")
                self.root.iconbitmap(icon_path)
        except Exception as e:
            print(f"Icone não carregado: {e}")

        self.current_version = "3.4"
        self.updater = Updater(self.current_version)
        self.check_updates()

        # Inicializa os gerenciadores
        self.config_manager = ConfigManager()
        self.text_manager = TextManager()
        self.notepad_manager = NotepadManager()

        # Carrega as configurações
        self.config = self.config_manager.config
        self.texts = self.text_manager.texts

        # Inicialização do áudio com sistema de fallback
        self.initialize_audio()

        # Variável para armazenar a categoria atual
        self.current_category = "Todas"

        # Define a geometria inicial
        initial_size = self.config.get(
            (
                "window_size_notepad"
                if self.config["notepad_expanded"]
                else "window_size_normal"
            ),
            DEFAULT_WINDOW_SIZE,
        )
        self.root.geometry(initial_size)
        self.root.update_idletasks()  # Força atualização do layout

        # Initialize button_windows
        self.button_windows = []

        self.setup_ui()
        pygame.mixer.init()
        self.click_sound = None
        self.load_sound()

        # Inicializa pilhas de undo
        self.undo_stack = []
        self.user_script = ""  # Armazena o script do usuário
        # Define o arquivo para salvar o script (na mesma pasta do executável)
        self.script_file = os.path.join(
            os.path.dirname(sys.executable), "user_script.py"
        )
        self.load_user_script()

    def initialize_audio(self):
        """Inicializa o sistema de áudio com fallback e logging apropriado."""
        self.audio_available = False
        self.click_sound = None

        if not self.config["sound_enabled"]:
            print("Som desativado nas configurações.")
            return

        try:
            pygame.mixer.quit()  # Garante que não há instância anterior
            pygame.mixer.init()
            self.audio_available = True
            print("Sistema de áudio inicializado com sucesso.")

            try:
                self.click_sound = pygame.mixer.Sound("click.wav")
                print("Som de clique carregado com sucesso.")
            except Exception as e:
                print(f"Aviso: Não foi possível carregar o som de clique: {e}")
                self.audio_available = False

        except Exception as e:
            print(f"Aviso: Sistema de áudio não disponível: {e}")
            self.config["sound_enabled"] = False
            self.config_manager.save_config()
            print("Som desativado automaticamente devido a problemas de inicialização.")

    def check_updates(self):
        """
        Verifica e notifica sobre atualizações disponíveis chamando o Updater.
        """
        version_info = self.updater.check_for_updates()
        if version_info:
            if messagebox.askyesno(
                "Atualização Disponível",
                f"Uma nova versão ({version_info['version']}) está disponível. Deseja atualizar agora?",
            ):
                self.updater.download_and_install(version_info["download_url"])

    def load_sound(self):
        """
        Inicializa o som para clique dos botões (usando pygame) e trata falhas de carregamento.
        """
        try:
            self.click_sound = pygame.mixer.Sound("click.wav")
        except Exception as e:
            print(f"Erro ao carregar som: {e}")
            self.config["sound_enabled"] = False
            self.sound_menu.entryconfig(0, label="Erro - Som Desativado")

    def setup_ui(self):
        """Configura a interface gráfica (UI), criando canvas, botões, menus e blocos de notas."""
        self.root.configure(bg=self.config["bg_color"])
        self.create_canvas()
        self.load_bg_image()
        self.create_buttons()
        self.create_menu()
        self.create_notepad_widget()
        self.root.bind("<Configure>", self.save_window_size)
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.update_button_styles()

    def save_window_size(self, event):
        """
        Salva o tamanho atual da janela, incluindo a posição.
        Se a geometria não incluir a posição, adiciona a partir de winfo_x/y.
        """
        if event.widget == self.root:
            current_geometry = self.root.wm_geometry()
            if not current_geometry:
                return
            if "+" not in current_geometry:
                x = self.root.winfo_x()
                y = self.root.winfo_y()
                current_geometry += f"+{x}+{y}"
            if self.config["notepad_expanded"]:
                self.config["window_size_notepad"] = current_geometry
            else:
                self.config["window_size_normal"] = current_geometry
            self.config_manager.save_config()

    def create_canvas(self):
        self.canvas = tk.Canvas(self.root, bg=self.config["bg_color"])
        self.canvas.pack(fill="both", expand=True)

    def load_bg_image(self):
        """Carrega a imagem de fundo padrão ou personalizada"""
        self.bg_image = None  # Inicializa bg_image como None

        try:
            self.bg_image = tk.PhotoImage(file=self.config["bg_image_path"])
        except Exception as e:
            print(f"Erro ao carregar imagem: {e}")

            # Solicita ao usuário para selecionar uma nova imagem
            if messagebox.askyesno(
                "Imagem de Fundo Não Encontrada",
                "O arquivo de imagem de fundo não foi encontrado. Deseja selecionar uma nova imagem?",
            ):
                new_image_path = self.select_bg_image()
                if new_image_path:
                    self.config["bg_image_path"] = new_image_path
                    self.bg_image = tk.PhotoImage(file=new_image_path)
                    self.config_manager.save_config()
                else:
                    # Se o usuário não selecionar uma nova imagem, inicia sem plano de fundo
                    self.canvas.configure(bg=self.config["bg_color"])
                    return

        # Adiciona a imagem ao canvas já criado, se a imagem foi carregada com sucesso
        if self.bg_image:
            self.canvas.create_image(0, 0, image=self.bg_image, anchor="nw")

    def select_bg_image(self):
        file_path = filedialog.askopenfilename(
            title="Selecione a imagem de fundo", filetypes=[("Image files", "*.png")]
        )
        return file_path if file_path else DEFAULT_BG_IMAGE_PATH

    def create_widgets(self):
        self.canvas = tk.Canvas(self.root, bg=self.config["bg_color"])
        self.canvas.pack(fill="both", expand=True)

        if self.bg_image:
            self.canvas.create_image(0, 0, image=self.bg_image, anchor="nw")

        self.create_buttons()

    def create_buttons(self):
        # Limpar botões existentes
        for btn in self.button_windows:
            self.canvas.delete(btn)
        self.button_windows = []

        # Configurações de posicionamento
        start_x, start_y = 10, 10
        button_width = 150
        button_height = 30
        padding = 5
        max_colunas = 8
        bots_por_coluna = 10

        # Filtra textos por categoria
        filtered_texts = self.texts
        if self.current_category != "Todas":
            filtered_texts = [
                text
                for text in self.texts
                if len(text) >= 3 and text[2] == self.current_category
            ]

        for idx, text_item in enumerate(filtered_texts):
            # Garante que text_item sempre tenha 3 elementos
            if len(text_item) == 2:
                text, resumo = text_item
                category = "Geral"
            else:
                text, resumo, category = text_item

            # Calcula coluna e linha conforme sistema anterior
            col = idx // bots_por_coluna  # Cada coluna tem 10 botões
            linha = idx % bots_por_coluna  # 0-9

            # Para após atingir o máximo de colunas
            if col >= max_colunas:
                break

            # Posição X baseada na coluna (cada coluna tem 100 + 25 + 10 = 135 de largura)
            x = start_x + (col * 185)

            # Posição Y baseada na linha
            y = start_y + (linha * (button_height + padding))

            # Botão principal
            btn = ttk.Button(
                self.canvas,
                text=resumo,
                command=lambda t=text: self.copy_to_clipboard(t),
            )
            btn_window = self.canvas.create_window(
                x, y, anchor="nw", window=btn, width=button_width, height=button_height
            )
            self.button_windows.append(btn_window)

            # Tooltip mostrando a categoria
            Tooltip(btn, f"Categoria: {category}")

            # Botão de edição
            if self.config["show_edit_buttons"]:
                edit_btn = ttk.Button(
                    self.canvas,
                    text="✎",
                    width=2,
                    command=lambda i=self.texts.index(text_item): self.open_edit_window(
                        i
                    ),
                )
                edit_window = self.canvas.create_window(
                    x + button_width + 5,  # Posição ao lado do botão principal
                    y,
                    anchor="nw",
                    window=edit_btn,
                    width=25,
                    height=button_height,
                )
                self.button_windows.append(edit_window)

        # Atualizar scrollregion
        total_colunas = min(len(filtered_texts) // bots_por_coluna + 1, max_colunas)
        total_width = start_x + (total_colunas * 185)
        total_height = start_y + (bots_por_coluna * (button_height + padding))
        self.canvas.config(scrollregion=(0, 0, total_width, total_height))

    def copy_to_clipboard(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)

        # Reproduz som apenas se o sistema de áudio estiver disponível
        if self.config["sound_enabled"] and self.audio_available and self.click_sound:
            try:
                pygame.mixer.find_channel(True).play(self.click_sound)
            except Exception as e:
                print(f"Erro ao reproduzir som: {e}")
                self.audio_available = (
                    False  # Desativa o áudio se ocorrer erro durante a reprodução
                )

    def open_edit_window(self, idx):
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Editar Texto e Nome do Botão")

        # Campo para editar o nome do botão
        tk.Label(edit_window, text="Nome do Botão:").pack(padx=10, pady=(10, 0))
        name_entry = tk.Entry(edit_window, width=50)
        name_entry.pack(padx=10, pady=(0, 10))
        name_entry.insert(tk.END, self.texts[idx][1])

        # Campo para editar o texto do botão
        tk.Label(edit_window, text="Texto do Botão:").pack(padx=10, pady=(10, 0))
        text_box = scrolledtext.ScrolledText(
            edit_window, wrap=tk.WORD, width=50, height=15
        )
        text_box.pack(padx=10, pady=(0, 10))
        text_box.insert(tk.END, self.texts[idx][0])

        # Campo para selecionar a categoria
        tk.Label(edit_window, text="Categoria:").pack(padx=10, pady=(10, 0))
        category_var = tk.StringVar(edit_window)

        # Obtém a categoria atual do botão ou usa 'Geral' como padrão
        current_category = self.texts[idx][2] if len(self.texts[idx]) >= 3 else "Geral"
        category_var.set(current_category)

        category_dropdown = ttk.Combobox(
            edit_window, textvariable=category_var, values=self.text_manager.categories
        )
        category_dropdown.pack(padx=10, pady=(0, 10))

        # Botão para criar nova categoria
        def add_new_category():
            new_category = simpledialog.askstring(
                "Nova Categoria", "Digite o nome da nova categoria:"
            )
            if new_category and new_category.strip():
                if self.text_manager.add_category(new_category.strip()):
                    # Atualiza o dropdown
                    category_dropdown["values"] = self.text_manager.categories
                    category_var.set(new_category.strip())
                else:
                    messagebox.showinfo("Info", "Esta categoria já existe.")

        ttk.Button(edit_window, text="+ Nova Categoria", command=add_new_category).pack(
            pady=5
        )

        # Frame para os botões de ação
        button_frame = tk.Frame(edit_window)
        button_frame.pack(pady=10)

        def save_text():
            new_text = text_box.get("1.0", tk.END).strip()
            new_name = name_entry.get()
            if new_name and new_text:
                self.texts[idx] = (new_text, new_name, category_var.get())
                self.text_manager.save_texts()
                self.update_category_menu()
                self.refresh_gui()
                edit_window.destroy()

        # Botão Salvar
        ttk.Button(button_frame, text="Salvar", command=save_text).pack(
            side=tk.LEFT, padx=5
        )

        # Botão Deletar
        def delete_button():
            if messagebox.askyesno(
                "Confirmar", "Tem certeza que deseja deletar este botão?"
            ):
                del self.texts[idx]
                self.text_manager.save_texts()
                self.refresh_gui()
                edit_window.destroy()

        ttk.Button(button_frame, text="Deletar Botão", command=delete_button).pack(
            side=tk.LEFT, padx=5
        )

    def add_new_button(self):
        """Abre janela para adicionar novo botão com campos ampliados"""
        add_window = tk.Toplevel(self.root)
        add_window.title("Adicionar Novo Botão")
        add_window.geometry("500x550")

        # Nome do Botão (Label + Entry)
        tk.Label(add_window, text="Nome do Botão:", font=("Arial", 10, "bold")).pack(
            padx=10, pady=(10, 0)
        )
        name_entry = tk.Entry(add_window, width=50)
        name_entry.pack(padx=10, pady=(0, 10))

        # Texto do Botão (Label + ScrolledText)
        tk.Label(
            add_window, text="Texto para Copiar:", font=("Arial", 10, "bold")
        ).pack(padx=10, pady=(10, 0))
        text_box = scrolledtext.ScrolledText(
            add_window, wrap=tk.WORD, width=50, height=15, font=("Arial", 10)
        )
        text_box.pack(padx=10, pady=(0, 10))

        # Seleção de Categoria
        tk.Label(add_window, text="Categoria:", font=("Arial", 10, "bold")).pack(
            padx=10, pady=(10, 0)
        )
        category_var = tk.StringVar(add_window)
        category_var.set("Geral")  # Valor padrão

        category_dropdown = ttk.Combobox(
            add_window, textvariable=category_var, values=self.text_manager.categories
        )
        category_dropdown.pack(padx=10, pady=(0, 10))

        # Botão para criar nova categoria
        def add_new_category():
            new_category = simpledialog.askstring(
                "Nova Categoria", "Digite o nome da nova categoria:"
            )
            if new_category and new_category.strip():
                if self.text_manager.add_category(new_category.strip()):
                    # Atualiza o dropdown
                    category_dropdown["values"] = self.text_manager.categories
                    category_var.set(new_category.strip())
                else:
                    messagebox.showinfo("Info", "Esta categoria já existe.")

        ttk.Button(add_window, text="+ Nova Categoria", command=add_new_category).pack(
            pady=5
        )

        # Botão de Confirmação
        def confirm_add():
            new_name = name_entry.get().strip()
            new_text = text_box.get("1.0", tk.END).strip()

            if not new_name or not new_text:
                messagebox.showerror("Erro", "Ambos os campos são obrigatórios!")
                return

            # Adiciona o texto com a categoria selecionada
            self.texts.append((new_text, new_name, category_var.get()))
            self.text_manager.save_texts()
            self.update_category_menu()
            self.refresh_gui()
            add_window.destroy()

        ttk.Button(add_window, text="Adicionar", command=confirm_add).pack(pady=10)

    def create_menu(self):
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        # Menu "Visual"
        self.view_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Visual", menu=self.view_menu)

        # Outras opções do menu "Visual"
        self.view_menu.add_command(
            label="Alterar Plano de Fundo", command=self.change_bg_image
        )
        self.view_menu.add_command(
            label="Editar esquema de cores", command=self.edit_colors
        )
        self.view_menu.add_command(
            label=(
                "Ocultar Botões de Edição"
                if self.config["show_edit_buttons"]
                else "Exibir Botões de Edição"
            ),
            command=self.toggle_edit_buttons,
        )
        self.view_menu.add_command(
            label=(
                "Ocultar Bloco de Notas"
                if self.config["notepad_expanded"]
                else "Exibir Bloco de Notas"
            ),
            command=self.toggle_notepad,
        )
        self.view_menu.add_separator()
        # Movendo "Novo Botão" para o menu Visual
        self.view_menu.add_command(label="➕ Novo Botão", command=self.add_new_button)

        # Menu "Som"
        self.sound_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Som", menu=self.sound_menu)
        self.sound_menu.add_command(
            label=(
                "Desativar Som de Clique"
                if self.config["sound_enabled"]
                else "Ativar Som de Clique"
            ),
            command=self.toggle_sound,
        )

        # Menu "Categorias"
        self.category_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Categorias", menu=self.category_menu)
        self.category_menu.add_command(
            label="Adicionar Categoria", command=self.add_category
        )
        self.category_menu.add_command(
            label="Gerenciar Categorias", command=self.manage_categories
        )
        self.category_menu.add_separator()

        # Sub-menu para selecionar categorias
        self.update_category_menu()

        # Adiciona um separador visual no menu (usando cascade vazio com um label de separador)
        menu_bar.add_cascade(label="│", state="disabled")

        # Botões de Script diretamente na barra de menu (sem submenu)
        menu_bar.add_command(label="Script", command=self.execute_script)
        menu_bar.add_command(label="✎", command=self.edit_script)

        # Adiciona outro separador visual
        menu_bar.add_cascade(label="│", state="disabled")

        # Menu "Ajuda" - Movido para o final
        help_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Ajuda", menu=help_menu)
        help_menu.add_command(label="Sobre", command=self.show_about)

    def update_category_menu(self):
        """Atualiza o menu de categorias com as categorias disponíveis."""
        # Remove itens existentes após o separador
        items = self.category_menu.index("end")
        if items > 2:  # Se tiver itens além do separador
            for i in range(items, 2, -1):
                self.category_menu.delete(i)

        # Adiciona todas as categorias
        self.category_menu.add_radiobutton(
            label="Todas",
            variable=tk.StringVar(value=self.current_category),
            value="Todas",
            command=lambda: self.filter_by_category("Todas"),
        )

        # Adiciona cada categoria como radiobutton
        for category in self.text_manager.categories:
            self.category_menu.add_radiobutton(
                label=category,
                variable=tk.StringVar(value=self.current_category),
                value=category,
                command=lambda c=category: self.filter_by_category(c),
            )

    def filter_by_category(self, category):
        """Filtra os botões pela categoria selecionada."""
        self.current_category = category
        self.refresh_gui()

    def add_category(self):
        """Abre uma janela para adicionar nova categoria."""
        new_category = simpledialog.askstring(
            "Nova Categoria", "Digite o nome da nova categoria:"
        )
        if new_category and new_category.strip():
            if self.text_manager.add_category(new_category.strip()):
                self.update_category_menu()
                messagebox.showinfo(
                    "Sucesso", f"Categoria '{new_category}' adicionada com sucesso!"
                )
            else:
                messagebox.showinfo("Info", "Esta categoria já existe.")

    def manage_categories(self):
        """Abre uma janela para gerenciar categorias existentes."""
        manage_window = tk.Toplevel(self.root)
        manage_window.title("Gerenciar Categorias")
        manage_window.geometry("400x300")
        manage_window.transient(self.root)
        manage_window.focus_set()

        # Frame para a lista de categorias
        frame = tk.Frame(manage_window)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Listbox com as categorias
        tk.Label(frame, text="Categorias:").pack(anchor="w")
        categories_listbox = tk.Listbox(frame, height=10)
        categories_listbox.pack(fill="both", expand=True)

        # Adiciona as categorias à listbox
        for category in self.text_manager.categories:
            categories_listbox.insert(tk.END, category)

        # Frame para os botões
        button_frame = tk.Frame(frame)
        button_frame.pack(fill="x", pady=10)

        # Função para renomear categoria
        def rename_category():
            selected_idx = categories_listbox.curselection()
            if selected_idx:
                old_name = categories_listbox.get(selected_idx)
                if old_name == "Geral":
                    messagebox.showinfo(
                        "Info", "Não é possível renomear a categoria 'Geral'."
                    )
                    return

                new_name = simpledialog.askstring(
                    "Renomear Categoria", f"Novo nome para '{old_name}':"
                )
                if new_name and new_name.strip():
                    if self.text_manager.rename_category(old_name, new_name.strip()):
                        # Atualiza a listbox
                        categories_listbox.delete(0, tk.END)
                        for category in self.text_manager.categories:
                            categories_listbox.insert(tk.END, category)

                        # Atualiza o menu de categorias
                        self.update_category_menu()
                        messagebox.showinfo(
                            "Sucesso", f"Categoria renomeada para '{new_name}'!"
                        )
                    else:
                        messagebox.showerror(
                            "Erro", "Não foi possível renomear a categoria."
                        )

        # Função para excluir categoria
        def delete_category():
            selected_idx = categories_listbox.curselection()
            if selected_idx:
                name = categories_listbox.get(selected_idx)
                if name == "Geral":
                    messagebox.showinfo(
                        "Info", "Não é possível excluir a categoria 'Geral'."
                    )
                    return

                if messagebox.askyesno(
                    "Confirmar Exclusão",
                    f"Excluir a categoria '{name}'?\nTodos os textos serão movidos para 'Geral'.",
                ):
                    if self.text_manager.delete_category(name):
                        # Atualiza a listbox
                        categories_listbox.delete(0, tk.END)
                        for category in self.text_manager.categories:
                            categories_listbox.insert(tk.END, category)

                        # Atualiza o menu de categorias
                        self.update_category_menu()

                        # Se a categoria atual for a excluída, muda para 'Todas'
                        if self.current_category == name:
                            self.current_category = "Todas"
                            self.refresh_gui()

                        messagebox.showinfo("Sucesso", f"Categoria '{name}' excluída!")
                    else:
                        messagebox.showerror(
                            "Erro", "Não foi possível excluir a categoria."
                        )

        # Adiciona os botões
        ttk.Button(button_frame, text="Renomear", command=rename_category).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="Excluir", command=delete_category).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="Fechar", command=manage_window.destroy).pack(
            side=tk.RIGHT, padx=5
        )

    def execute_script(self):
        # Executa o script armazenado no self.user_script em um novo processo Python do sistema, sem abrir janela de CMD e sem travar o app principal
        if self.user_script.strip() == "":
            messagebox.showinfo("Script vazio", "Nenhum script foi definido.")
            return

        self.save_user_script()  # Garante que o script está salvo no arquivo

        import shutil
        import subprocess
        import os

        def find_system_python():
            # Tenta encontrar o Python do sistema
            for py in ("python.exe", "python3.exe", "python", "python3"):
                path = shutil.which(py)
                if path:
                    return path
            return None

        python_path = find_system_python()
        if not python_path:
            messagebox.showerror(
                "Python não encontrado",
                "Não foi possível localizar o Python instalado no sistema. Instale o Python para executar scripts.",
            )
            return

        # Define o creationflags para não abrir janela de CMD no Windows
        creationflags = 0
        if os.name == "nt":
            creationflags = subprocess.CREATE_NO_WINDOW

        try:
            subprocess.Popen(
                [python_path, self.script_file],
                creationflags=creationflags,
            )
            # Opcional: mostrar mensagem de que o script foi iniciado
            # messagebox.showinfo("Script", "Script iniciado em segundo plano.")
        except Exception as e:
            messagebox.showerror("Erro na Execução", f"Ocorreu um erro: {e}")

    def edit_script(self):
        # Abre uma janela Toplevel para editar o script Python
        editor = tk.Toplevel(self.root)
        editor.title("Editor de Script Python")
        editor.geometry("800x600")  # Tamanho maior verticalmente
        st = scrolledtext.ScrolledText(editor, wrap=tk.WORD, font=("Courier New", 10))
        st.pack(expand=True, fill="both", padx=10, pady=10)
        st.insert(tk.END, self.user_script)  # Carrega o script atual
        btn_frame = tk.Frame(editor)
        btn_frame.pack(pady=5)

        def save_script():
            self.user_script = st.get("1.0", tk.END)
            self.save_user_script()  # Salva o script no arquivo
            messagebox.showinfo("Script", "Script salvo com sucesso.")

        ttk.Button(btn_frame, text="Salvar", command=save_script).pack(
            side=tk.LEFT, padx=5
        )

    def load_user_script(self):
        # Carrega o script se o arquivo existir
        if os.path.exists(self.script_file):
            with open(self.script_file, "r", encoding="utf-8") as f:
                self.user_script = f.read()

    def save_user_script(self):
        # Salva o conteúdo de user_script no arquivo
        with open(self.script_file, "w", encoding="utf-8") as f:
            f.write(self.user_script)

    def toggle_sound(self):
        self.config["sound_enabled"] = not self.config["sound_enabled"]
        self.sound_menu.entryconfig(
            0,
            label=(
                "Desativar Som de Clique"
                if self.config["sound_enabled"]
                else "Ativar Som de Clique"
            ),
        )
        self.config_manager.save_config()

    def toggle_edit_buttons(self):
        self.config["show_edit_buttons"] = not self.config["show_edit_buttons"]
        self.view_menu.entryconfig(
            2,
            label=(
                "Ocultar Botões de Edição"
                if self.config["show_edit_buttons"]
                else "Exibir Botões de Edição"
            ),
        )
        self.config_manager.save_config()
        self.refresh_gui()

    def toggle_notepad(self, no_save=False):
        """
        Alterna a visibilidade do bloco de notas e ajusta a geometria da janela.

        Parâmetros:
            no_save (bool): Se True, não salva o estado atual nas configurações.
        """
        # Salvar estado anterior
        prev_state = self.config["notepad_expanded"]

        # Alterna estado
        self.config["notepad_expanded"] = not self.config["notepad_expanded"]

        # Ajusta interface
        if self.config["notepad_expanded"]:
            self.notepad_frame.pack(fill="both", expand=True)
        else:
            self.notepad_frame.pack_forget()

        # Aplica geometria salva
        new_geometry = self.config[
            (
                "window_size_notepad"
                if self.config["notepad_expanded"]
                else "window_size_normal"
            )
        ]
        self.root.geometry(new_geometry)

        # Atualiza menu
        self.view_menu.entryconfig(
            3,
            label=(
                "Ocultar Bloco de Notas"
                if self.config["notepad_expanded"]
                else "Exibir Bloco de Notas"
            ),
        )

        if not no_save:
            self.config_manager.save_config()

    def show_about(self):
        """
        Exibe uma janela com informações sobre o aplicativo, incluindo detalhes do desenvolvedor e licença.
        """
        about_window = tk.Toplevel(self.root)
        about_window.title("Sobre o SuporteApp")
        about_window.geometry("400x320")  # Altura reduzida já que removemos uma seção
        about_window.resizable(False, False)
        about_window.configure(bg="#f5f5f7")  # Fundo claro e moderno
        about_window.grab_set()  # Torna o diálogo modal

        # Frame principal com área de conteúdo
        main_frame = tk.Frame(about_window, bg="#f5f5f7", padx=25, pady=20)
        main_frame.pack(fill="both", expand=True)

        # Cabeçalho com título e versão
        header_frame = tk.Frame(main_frame, bg="#f5f5f7")
        header_frame.pack(fill="x", pady=(0, 15))

        tk.Label(
            header_frame,
            text="SuporteApp",
            font=("Helvetica", 18, "bold"),
            fg="#2C3E50",
            bg="#f5f5f7",
        ).pack(side="left")

        tk.Label(
            header_frame,
            text=f"v{self.current_version}",
            font=("Helvetica", 12),
            fg="#7F8C8D",
            bg="#f5f5f7",
        ).pack(side="right", padx=(10, 0), pady=(5, 0))

        # Linha separadora
        separator = tk.Frame(main_frame, height=1, bg="#e0e0e0")
        separator.pack(fill="x", pady=10)

        # Container para informações do desenvolvedor
        dev_container = tk.Frame(main_frame, bg="#f5f5f7")
        dev_container.pack(fill="x", pady=10)

        # Cria uma grade para informações do desenvolvedor
        info_data = [
            ("Desenvolvedor:", "Paulo Gama", "black", None),
            (
                "E-mail:",
                "DreamerJPMG@gmail.com",
                "#0078D4",
                "mailto:DreamerJPMG@gmail.com",
            ),
            (
                "GitHub:",
                "github.com/DreamerJP",
                "#0078D4",
                "https://github.com/DreamerJP",
            ),
        ]

        for row, (label, value, color, link) in enumerate(info_data):
            tk.Label(
                dev_container,
                text=label,
                font=("Helvetica", 10, "bold"),
                bg="#f5f5f7",
                anchor="e",
                width=13,
            ).grid(row=row, column=0, sticky="e", padx=(0, 10), pady=6)

            # Para links, cria um label com sublinhado e cursor especial
            if link:
                lbl = tk.Label(
                    dev_container,
                    text=value,
                    font=("Helvetica", 10, "underline"),
                    fg=color,
                    bg="#f5f5f7",
                    cursor="hand2",
                )
                lbl.grid(row=row, column=1, sticky="w", pady=6)
                lbl.bind("<Button-1>", lambda e, url=link: self.open_link(url))
            else:
                tk.Label(
                    dev_container,
                    text=value,
                    font=("Helvetica", 10),
                    fg=color,
                    bg="#f5f5f7",
                ).grid(row=row, column=1, sticky="w", pady=6)

        # Segunda linha separadora
        separator2 = tk.Frame(main_frame, height=1, bg="#e0e0e0")
        separator2.pack(fill="x", pady=10)

        # Seção de licença
        license_frame = tk.Frame(main_frame, bg="#f5f5f7")
        license_frame.pack(fill="x", pady=5)

        tk.Label(
            license_frame,
            text="Distribuído sob Licença Apache-2.0",
            font=("Helvetica", 9),
            fg="#555555",
            bg="#f5f5f7",
        ).pack(anchor="w")

        tk.Label(
            license_frame,
            text="© 2025 Todos os direitos reservados",
            font=("Helvetica", 9),
            fg="#555555",
            bg="#f5f5f7",
        ).pack(anchor="w")

        # Easter Egg - Emoji de cobra (canto inferior direito)
        snake_label = tk.Label(
            about_window,
            text="🐍",
            font=("Segoe UI Emoji", 16),
            bg="#f5f5f7",
            fg="#2a702a",
            cursor="hand2",
        )
        snake_label.place(relx=0.95, rely=0.95, anchor="se")
        snake_label.bind("<Button-1>", lambda e: self.start_snake_game(about_window))

    def open_link(self, text):
        """Abre links externos no navegador padrão"""
        links = {
            "DreamerJPMG@gmail.com": "mailto:DreamerJPMG@gmail.com",
            "github.com/DreamerJP": "https://github.com/DreamerJP",
        }
        url = links.get(text, "")
        if url:
            import webbrowser

            webbrowser.open_new(url)

    def add_snake_emoji_easter_egg(self, window):
        """Adiciona o emoji de cobra como Easter Egg"""
        snake_frame = tk.Frame(window, bg="#F0F0F0")
        snake_frame.place(relx=1.0, rely=1.0, anchor="se")

        snake_label = tk.Label(
            snake_frame,
            text="🐍",
            font=("Arial", 16),
            bg="#F0F0F0",
            fg="#2a702a",
            cursor="hand2",
        )
        snake_label.pack(padx=0, pady=0)  # Remover padding
        snake_label.bind("<Button-1>", lambda e: self.start_snake_game(window))

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
        width, height, x, y = map(int, current_geometry.replace("x", "+").split("+"))

        # Define a nova altura da janela com base no estado do bloco de notas
        if self.config["notepad_expanded"]:
            new_height = height + 200  # Aumenta a altura para acomodar o bloco de notas
        else:
            new_height = height - 200  # Reduz a altura para recolher o bloco de notas

        # Aplica a nova geometria
        self.root.geometry(f"{width}x{new_height}+{x}+{y}")

    def change_bg_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png")])
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
        ttk.Label(bg_frame, text="Digite o código hexadecimal ou use o seletor:").grid(
            row=0, column=0, columnspan=3, pady=5
        )

        # Entrada para o código hexadecimal
        bg_color_entry = ttk.Entry(bg_frame, width=10)
        bg_color_entry.grid(row=1, column=0, padx=5, pady=5)
        bg_color_entry.insert(0, self.config["bg_color"])

        # Botão de seleção de cor
        def choose_color():
            # Abre o seletor de cores e pega a cor selecionada
            color = colorchooser.askcolor(
                title="Selecione uma cor", parent=edit_window
            )[1]
            if color:
                # Atualiza o campo de entrada com a cor selecionada
                bg_color_entry.delete(0, tk.END)
                bg_color_entry.insert(0, color)
                update_preview()  # Atualiza o preview após selecionar a cor

        ttk.Button(bg_frame, text="🎨 Seletor", command=choose_color).grid(
            row=1, column=1, padx=5, pady=5
        )

        # Botão de visualização
        preview_canvas = tk.Canvas(
            bg_frame, width=30, height=20, bg=self.config["bg_color"]
        )
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
                self.update_button_styles()  # Adicione esta linha
                self.refresh_gui()
                edit_window.destroy()
            else:
                tk.messagebox.showerror(
                    "Erro",
                    "Cor inválida. Por favor, insira um código hexadecimal válido.",
                )

        ttk.Button(button_frame, text="Salvar", command=save_colors).pack(
            side=tk.LEFT, padx=5
        )

    def is_valid_color(self, color):
        try:
            # Tenta criar um widget temporário com a cor fornecida
            temp_widget = tk.Label(self.root, bg=color)
            temp_widget.update_idletasks()  # Atualiza o widget para aplicar a cor
            return True
        except tk.TclError:
            return False

    def get_contrast_color(self, hex_color):
        """Determina a cor do texto com base no brilho da cor de fundo"""
        if hex_color.startswith("#"):
            hex_color = hex_color.lstrip("#")
        else:
            return "black"  # Fallback para cores inválidas

        try:
            r, g, b = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            return "white" if luminance < 0.5 else "black"
        except:
            return "black"

    def adjust_color(self, hex_color, delta):
        """Ajusta o brilho da cor para efeitos de hover/pressed"""
        hex_color = hex_color.lstrip("#")
        r = max(0, min(255, int(hex_color[0:2], 16) + delta))
        g = max(0, min(255, int(hex_color[2:4], 16) + delta))
        b = max(0, min(255, int(hex_color[4:6], 16) + delta))
        return f"#{r:02x}{g:02x}{b:02x}"

    def create_notepad_widget(self):
        self.notepad_frame = tk.Frame(self.root, bg=self.config["bg_color"])
        self.notepad_frame.pack(fill="both", expand=True)

        # Usa cores dinâmicas do tema
        notepad_bg_color = self.config["bg_color"]
        notepad_fg_color = self.get_contrast_color(notepad_bg_color)

        default_font = ("Helvetica", 10)
        self.notepad_text = scrolledtext.ScrolledText(
            self.notepad_frame,
            width=50,
            height=10,
            wrap=tk.WORD,
            font=default_font,
            bg=notepad_bg_color,
            fg=notepad_fg_color,
            insertbackground=notepad_fg_color,  # Cor do cursor
        )
        self.notepad_text.pack(padx=10, pady=10, fill="both", expand=True)

        self.notepad_toolbar = tk.Frame(self.notepad_frame, bg=self.config["bg_color"])
        self.notepad_toolbar.pack(fill="x", side="top")

        # Botões com toggle de formatação
        bold_btn = ttk.Button(
            self.notepad_toolbar,
            text="𝙉",
            width=3,
            command=lambda: self.toggle_tag("bold"),
        )
        bold_btn.pack(side="left", padx=2)
        Tooltip(bold_btn, "Negrito - Clique para aplicar/remover todas as formatações")

        italic_btn = ttk.Button(
            self.notepad_toolbar,
            text="𝙄",
            width=3,
            command=lambda: self.toggle_tag("italic"),
        )
        italic_btn.pack(side="left", padx=2)
        Tooltip(
            italic_btn, "Itálico - Clique para aplicar/remover todas as formatações"
        )

        underline_btn = ttk.Button(
            self.notepad_toolbar,
            text="S͟",
            width=3,
            command=lambda: self.toggle_tag("underline"),
        )
        underline_btn.pack(side="left", padx=2)
        Tooltip(
            underline_btn,
            "Sublinhado - Clique para aplicar/remover todas as formatações",
        )

        separator_btn = ttk.Button(
            self.notepad_toolbar, text="Separação", command=self.add_separator
        )
        separator_btn.pack(side="left", padx=2)
        Tooltip(separator_btn, "Inserir Linha Divisória")

        save_btn = ttk.Button(
            self.notepad_toolbar, text="Salvar", width=10, command=self.save_notepad
        )
        save_btn.pack(side="left", padx=2)
        Tooltip(save_btn, "Salvar Conteúdo (Ctrl+S)")

        # Configuração das tags
        self.notepad_text.tag_config(
            "bold", font=(default_font[0], default_font[1], "bold")
        )
        self.notepad_text.tag_config(
            "italic", font=(default_font[0], default_font[1], "italic")
        )
        self.notepad_text.tag_config(
            "underline", font=(default_font[0], default_font[1], "underline")
        )

        # Carrega o conteúdo do bloco de notas
        if not hasattr(self, "notepad_initialized"):
            text, tags = self.notepad_manager.load_notepad()
            self.notepad_text.insert(tk.END, text)
            for tag in tags:
                self.notepad_text.tag_add(tag["tag"], tag["start"], tag["end"])
            self.notepad_initialized = True

        if not self.config["notepad_expanded"]:
            self.notepad_frame.pack_forget()

        # Vincula eventos de teclado
        self.notepad_text.bind("<Control-z>", self.undo)
        self.notepad_text.bind("<Control-Z>", self.undo)
        self.notepad_text.bind("<Control-s>", lambda e: self.save_notepad())
        self.notepad_text.bind("<Control-S>", lambda e: self.save_notepad())

        # Salva o estado após uma pausa na digitação
        self.save_timer = None
        self.notepad_text.bind("<KeyRelease>", self._schedule_save_state)

    def toggle_tag(self, tag_name):
        """Alterna a formatação da tag na seleção atual, removendo todas as tags se necessário"""
        try:
            sel_start = self.notepad_text.index("sel.first")
            sel_end = self.notepad_text.index("sel.last")

            # Verifica se a tag específica está presente em toda a seleção
            tag_present = all(
                tag_name in self.notepad_text.tag_names(f"{index}.0")
                for index in range(
                    int(sel_start.split(".")[0]), int(sel_end.split(".")[0]) + 1
                )
            )

            if tag_present:
                # Se a tag já está presente, remove todas as tags da seleção
                for tag in ["bold", "italic", "underline"]:
                    self.notepad_text.tag_remove(tag, sel_start, sel_end)
            else:
                # Se a tag não está presente, remove todas as tags primeiro
                for tag in ["bold", "italic", "underline"]:
                    self.notepad_text.tag_remove(tag, sel_start, sel_end)
                # Depois aplica a nova tag
                self.notepad_text.tag_add(tag_name, sel_start, sel_end)

        except tk.TclError:
            # Não há texto selecionado, não faz nada
            pass

    def _schedule_save_state(self, event=None):
        """Agenda o salvamento do estado após uma pausa na digitação."""
        if self.save_timer:
            self.root.after_cancel(self.save_timer)
        self.save_timer = self.root.after(
            1000, self.save_state
        )  # Salva após 1 segundo de inatividade

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

    def _capture_tags(self):
        """Captura todas as tags aplicadas no texto."""
        tags = []
        for tag in self.notepad_text.tag_names():
            if tag != "sel":
                ranges = self.notepad_text.tag_ranges(tag)
                for i in range(0, len(ranges), 2):
                    start = ranges[i]
                    end = ranges[i + 1]
                    tags.append(
                        {
                            "tag": tag,
                            "start": self.notepad_text.index(start),
                            "end": self.notepad_text.index(end),
                        }
                    )
        return tags

    def undo(self, event=None):
        """Desfaz a última ação."""
        if not self.undo_stack:
            return  # Nada para desfazer

        # Restaura o estado anterior
        text, tags = self.undo_stack.pop()
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
                    tags.append({"tag": tag, "start": str(start), "end": str(end)})
        self.notepad_manager.save_notepad(content, tags)

    def refresh_gui(self):
        """Atualiza toda a interface com as novas configurações"""
        # Captura estado atual
        current_geometry = self.root.wm_geometry()
        notepad_expanded = self.config["notepad_expanded"]
        notepad_content = (
            self.notepad_text.get("1.0", tk.END).strip()
            if hasattr(self, "notepad_text")
            else ""
        )
        notepad_tags = self._capture_tags() if hasattr(self, "notepad_text") else []

        # Destrói todos os widgets
        for widget in self.root.winfo_children():
            widget.destroy()

        # Recria interface
        self.setup_ui()

        # Restaura estado
        self.root.after(
            100,
            lambda: [
                self.root.wm_geometry(current_geometry),
                self.config.update({"notepad_expanded": notepad_expanded}),
                (
                    self.toggle_notepad(no_save=True)
                    if notepad_expanded != self.config["notepad_expanded"]
                    else None
                ),
                self._restore_notepad_content(notepad_content, notepad_tags),
                self.update_notepad_colors(),  # NOVO: Atualizar cores do bloco de notas
            ],
        )

    def update_notepad_colors(self):
        """Atualiza dinamicamente as cores do bloco de notas"""
        if hasattr(self, "notepad_text"):
            bg_color = self.config["bg_color"]
            fg_color = self.get_contrast_color(bg_color)

            # Aplica novas cores
            self.notepad_text.configure(
                bg=bg_color, fg=fg_color, insertbackground=fg_color
            )
            self.notepad_frame.configure(bg=bg_color)
            self.notepad_toolbar.configure(bg=bg_color)

    def update_button_styles(self):
        """Atualiza o estilo dos botões com base na cor de fundo"""
        bg_color = self.config["bg_color"]
        fg_color = self.get_contrast_color(bg_color)

        # Aplica o novo estilo
        self.style.configure(
            "TButton",
            background=bg_color,
            foreground=fg_color,
            font=("Helvetica", 9),
            padding=3,
        )

        # Atualiza o mapeamento de estados
        self.style.map(
            "TButton",
            background=[
                ("pressed", self.adjust_color(bg_color, -30)),
                ("active", self.adjust_color(bg_color, -20)),
            ],
            foreground=[("pressed", fg_color), ("active", fg_color)],
        )

        # Reaplica o estilo a todos os botões
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Button):
                widget.configure(style="TButton")

        # Atualiza cor do cursor do bloco de notas
        if hasattr(self, "notepad_text"):
            fg_color = self.get_contrast_color(self.config["bg_color"])
            self.notepad_text.configure(insertbackground=fg_color)


class SnakeGame:
    """
    Implementa o jogo Snake dentro de uma janela tkinter.

    Responsável pela criação da tela de título, controle do jogo, movimento da cobra,
    geração e desenho de maçãs e powerups, e gerenciamento dos scores.
    """

    def __init__(self, master):
        self.master = master
        self.master.title("Space Snake")
        self.master.geometry("400x440")
        self.master.configure(bg="black")

        # Definições de tamanho do jogo
        self.game_width = 400
        self.game_height = (
            400  # Alterado para garantir divisibilidade por 20 (tamanho da célula)
        )
        self.cell_size = 20

        # Criar o canvas exatamente com o tamanho do campo de jogo, sem espaçamento adicional
        self.canvas = tk.Canvas(
            master,
            width=self.game_width,
            height=self.game_height,
            bg="#0a0a2a",
            highlightthickness=0,
        )
        self.canvas.pack(
            fill="both", expand=False
        )  # Removido expand=True para manter tamanho fixo

        # Variáveis de estado do jogo
        self.snake = [(200, 200), (220, 200), (240, 200)]
        self.direction = "right"
        self.direction_queue = []
        self.apple = self.generate_apple()
        self.score = 0
        self.apples_eaten = 0
        self.game_active = False
        self.game_paused = False
        self.speed = 120  # Velocidade inicial em ms
        self.powerup_active = None
        self.powerup_end_time = 0
        self.active_powerup = None
        self.powerup_spawn_time = 0
        self.powerup_cooldown = 15  # Segundos entre powerups

        # Elementos de UI
        self.score_display = tk.Label(
            self.master,
            text="Pontuação: 0 | Velocidade: 100%",
            bg="black",
            fg="white",
            font=("Arial", 10),
        )
        self.score_display.pack(fill="x", side="bottom", pady=0)

        # Bind de teclas
        self.master.bind("<w>", self.up)
        self.master.bind("<a>", self.left)
        self.master.bind("<s>", self.down)
        self.master.bind("<d>", self.right)
        self.master.bind("<space>", self.toggle_pause)

        # Exibe a tela de título
        self.show_title_screen()

    def show_title_screen(self):
        """
        Exibe a tela de título com estrelas animadas, título e botão para iniciar o jogo.
        """
        self.create_stars()
        self.draw_title()
        self.create_button()
        self.animate_stars()

    def create_stars(self):
        """Cria e posiciona estrelas para a tela de título e armazena suas propriedades para animação."""
        self.stars = []
        for _ in range(100):
            while True:
                x = random.randint(0, 400)
                y = random.randint(0, 420)
                if not (100 <= y <= 150 and 150 <= x <= 250) and not (
                    300 <= y <= 350 and 150 <= x <= 250
                ):
                    break

            size = random.choice([1, 1, 1, 2, 2, 3])
            star = self.canvas.create_oval(
                x, y, x + size, y + size, fill=self.get_star_color(), outline=""
            )
            self.stars.append(
                {
                    "id": star,
                    "timer": random.randint(10, 40),
                    "base_brightness": random.choice([50, 100, 150]),
                }
            )
            self.canvas.lower(star)

    def get_star_color(self, brightness=None):
        brightness = brightness or random.choice([50, 100, 150])
        return f"#{brightness:02x}{brightness:02x}{brightness:02x}"

    def animate_stars(self):
        """Atualiza dinamicamente o brilho das estrelas para efeito de animação."""
        if not self.canvas.winfo_exists():
            return

        for star in self.stars:
            star["timer"] -= 1

            if star["timer"] <= 0:
                new_brightness = star["base_brightness"] + random.randint(-20, 30)
                new_brightness = max(30, min(new_brightness, 180))

                self.canvas.itemconfig(
                    star["id"], fill=self.get_star_color(new_brightness)
                )
                star["timer"] = random.randint(15, 25)

        self.master.after(100, self.animate_stars)

    def draw_title(self):
        """Desenha o título 'SPACE SNAKE' com camadas de cor para um efeito de sombra."""
        text = "SPACE SNAKE"
        layers = [
            {"offset": (2, 2), "color": "#002200"},
            {"offset": (1, 1), "color": "#004400"},
            {"offset": (0, 0), "color": "#00ff00"},
        ]

        for layer in layers:
            self.canvas.create_text(
                200 + layer["offset"][0],
                125 + layer["offset"][1],
                text=text,
                font=("Arial Black", 36, "bold"),
                fill=layer["color"],
                anchor="center",
            )

    def create_button(self):
        """Cria o botão de 'INICIAR JOGO' e associa os eventos de mouse para interação."""
        self.btn_bg = self.canvas.create_rectangle(
            130, 300, 270, 350, fill="#001100", outline="#00ff00", width=2
        )
        self.btn_text = self.canvas.create_text(
            200,
            325,
            text="INICIAR JOGO",
            font=("Arial", 14, "bold"),
            fill="#00ff00",
            anchor="center",
        )

        self.canvas.tag_raise(self.btn_bg)
        self.canvas.tag_raise(self.btn_text)

        self.canvas.tag_bind(
            self.btn_bg,
            "<Enter>",
            lambda e: self.canvas.itemconfig(self.btn_bg, fill="#002200"),
        )
        self.canvas.tag_bind(
            self.btn_bg,
            "<Leave>",
            lambda e: self.canvas.itemconfig(self.btn_bg, fill="#001100"),
        )
        self.canvas.tag_bind(self.btn_bg, "<Button-1>", self.start_game)
        self.canvas.tag_bind(self.btn_text, "<Button-1>", self.start_game)

    def start_game(self, event=None):
        """
        Inicia o jogo, reiniciando variáveis de controle, redesenhando canvas e começando o loop principal.
        """
        self.canvas.delete("all")
        self.game_active = True
        self.game_paused = False
        self.snake = [(200, 200), (220, 200), (240, 200)]
        self.direction = "right"
        self.direction_queue = []
        self.apple = self.generate_apple()
        self.score = 0
        self.apples_eaten = 0
        self.speed = 120
        self.powerup_active = None
        self.draw_stars()
        self.draw_snake()
        self.draw_apple()
        self.update_score_display()
        self.update()

    def draw_stars(self):
        """Desenha estrelas no fundo do canvas com efeito de profundidade."""
        for _ in range(150):  # Aumentado o número de estrelas
            x = random.randint(0, 400)
            y = random.randint(0, 400)
            size = random.randint(1, 3)
            # Criar estrelas com diferentes níveis de brilho para dar sensação de profundidade
            brightness = random.randint(100, 255)
            # Estrelas menores ficam mais escuras para simular distância
            if size == 1:
                brightness = random.randint(100, 180)
            elif size == 3:
                brightness = random.randint(200, 255)

            # Adicionar pequeno brilho ao redor das estrelas maiores
            if size >= 2 and random.random() > 0.7:
                glow_size = size + random.randint(1, 3)
                # Corrigido: Usar int() para converter valores divididos por float para inteiro
                glow_brightness = int(brightness // 2)  # Metade do brilho para o brilho
                self.canvas.create_oval(
                    x - glow_size // 2,
                    y - glow_size // 2,
                    x + size + glow_size // 2,
                    y + size + glow_size // 2,
                    fill="",
                    outline=f"#{glow_brightness:02x}{glow_brightness:02x}{glow_brightness:02x}",
                    width=1,
                )

            self.canvas.create_oval(
                x,
                y,
                x + size,
                y + size,
                fill=f"#{brightness:02x}{brightness:02x}{brightness:02x}",
                outline="",
            )

    def generate_apple(self):
        # Usa as variáveis de dimensão para garantir que a maçã apareça dentro dos limites corretos
        x = random.randint(0, (self.game_width // self.cell_size) - 1) * self.cell_size
        y = random.randint(0, (self.game_height // self.cell_size) - 1) * self.cell_size
        self.planet_color = random.choice(
            [
                ("#0047AB", "#89CFF0", "#00008B"),
                ("#964B00", "#D2691E", "#8B4513"),
                ("#808080", "#A9A9A9", "#696969"),
                ("#8B0000", "#FF4500", "#8B4513"),
            ]
        )
        # Gera crateras fixas para os planetas
        self.apple_craters = []
        for _ in range(3):
            cx = random.randint(x + 2, x + 18)
            cy = random.randint(y + 2, y + 18)
            self.apple_craters.append((cx, cy))
        return (x, y)

    def draw_snake(self):
        self.canvas.delete("snake")

        # Cor base da cobra depende do powerup ativo
        if self.powerup_active == "invincible":
            base_color = "#FFD700"  # Dourado para invencibilidade
            glow_color = "#FFFFA0"  # Brilho amarelo claro
            shadow_color = "#B8860B"  # Sombra dourada escura
        else:
            base_color = "#00CC00"  # Verde vivo
            glow_color = "#80FF80"  # Brilho verde claro
            shadow_color = "#006600"  # Sombra verde escura

        # Desenha cada segmento da cobra
        for i, (x, y) in enumerate(self.snake):
            # Cria um efeito de sombra projetada para profundidade
            offset = 3
            self.canvas.create_rectangle(
                x + offset,
                y + offset,
                x + 20 + offset,
                y + 20 + offset,
                fill="#222222",
                outline="",
                tag="snake",  # type: ignore
            )  # type: ignore

            # Desenha o segmento principal com gradiente simulado
            self.canvas.create_rectangle(
                x,
                y,
                x + 20,
                y + 20,
                fill=base_color,
                outline=shadow_color,
                width=1,
                tag="snake",  # type: ignore
            )  # type: ignore

            # Se for a cabeça da cobra (último elemento)
            if i == len(self.snake) - 1:
                # Olhos da cobra
                eye_offset = 5
                # Determina a posição dos olhos baseado na direção
                if self.direction == "right":
                    eyes = [(x + 15, y + 5), (x + 15, y + 15)]
                elif self.direction == "left":
                    eyes = [(x + 5, y + 5), (x + 5, y + 15)]
                elif self.direction == "up":
                    eyes = [(x + 5, y + 5), (x + 15, y + 5)]
                else:  # down
                    eyes = [(x + 5, y + 15), (x + 15, y + 15)]

                # Desenha os olhos
                for ex, ey in eyes:
                    # Contorno preto do olho
                    self.canvas.create_oval(
                        ex - 3,
                        ey - 3,
                        ex + 3,
                        ey + 3,
                        fill="white",
                        outline="black",
                        width=1,
                        tag="snake",  # type: ignore
                    )  # type: ignore
                    # Pupila
                    self.canvas.create_oval(
                        ex - 1,
                        ey - 1,
                        ex + 1,
                        ey + 1,
                        fill="black",
                        outline="",
                        tag="snake",  # type: ignore
                    )  # type: ignore

            # Reflexo superior-esquerdo (efeito de luz)
            if i < len(self.snake) - 1 or self.direction in ["down", "right"]:
                self.canvas.create_polygon(
                    x, y, x + 6, y, x, y + 6, fill=glow_color, outline="", tag="snake"  # type: ignore
                )  # type: ignore

            # Padrão de escamas na cobra (linhas horizontais e verticais)
            if i % 2 == 0:  # Alterna o padrão das escamas
                for j in range(4):
                    self.canvas.create_line(
                        x + 5 * j,
                        y,
                        x + 5 * j,
                        y + 20,
                        fill=shadow_color,
                        width=1,
                        tag="snake",  # type: ignore
                    )  # type: ignore
            else:
                for j in range(4):
                    self.canvas.create_line(
                        x,
                        y + 5 * j,
                        x + 20,
                        y + 5 * j,
                        fill=shadow_color,
                        width=1,
                        tag="snake",  # type: ignore
                    )  # type: ignore

            # Adiciona um detalhe de brilho se for invencível
            if self.powerup_active == "invincible" and random.random() > 0.7:
                sparkle_x = x + random.randint(5, 15)
                sparkle_y = y + random.randint(5, 15)
                self.canvas.create_text(
                    sparkle_x,
                    sparkle_y,
                    text="✦",
                    fill="white",
                    font=("Arial", 8),
                    tag="snake",  # type: ignore
                )  # type: ignore

    def draw_apple(self):
        self.canvas.delete("apple")
        x, y = self.apple
        size = 20
        base, mid, dark = self.planet_color

        # Desenha sombra mais suave com degradê
        for i in range(4, 0, -1):
            alpha = 40 + i * 40  # Transparência simulada com tons de cinza
            shadow_color = f"#{alpha:02x}{alpha:02x}{alpha:02x}"
            offset = i + 2
            self.canvas.create_oval(
                x + offset,
                y + offset,
                x + size + offset - i,
                y + size + offset - i,
                fill=shadow_color,
                outline="",
                tag="apple",  # type: ignore
            )  # type: ignore

        # Base do planeta (círculo principal)
        self.canvas.create_oval(
            x, y, x + size, y + size, fill=base, outline=dark, width=2, tag="apple"  # type: ignore
        )  # type: ignore

        # Superfície do planeta (variação de cor)
        self.canvas.create_oval(
            x + 4, y + 4, x + size - 4, y + size - 4, fill=mid, outline="", tag="apple"  # type: ignore
        )  # type: ignore

        # Crateras com efeito de profundidade
        for cx, cy in self.apple_craters:
            crater_size = random.randint(3, 5)
            # Sombra da cratera
            self.canvas.create_oval(
                cx + 1,
                cy + 1,
                cx + crater_size + 1,
                cy + crater_size + 1,
                fill="black",
                outline="",
                width=0,
                tag="apple",  # type: ignore
            )  # type: ignore
            # Cratera
            self.canvas.create_oval(
                cx,
                cy,
                cx + crater_size,
                cy + crater_size,
                fill=dark,
                outline="black",
                width=1,
                tag="apple",  # type: ignore
            )  # type: ignore

        # Reflexo de luz na parte superior (brilho)
        highlight_arc = self.canvas.create_arc(
            x + 3,
            y + 3,
            x + size - 3,
            y + size - 3,
            start=20,
            extent=60,
            style=tk.ARC,
            outline="white",
            width=2,
            tag="apple",  # type: ignore
        )  # type: ignore

        # Brilho adicional cintilante
        light_x = x + random.randint(4, 8)
        light_y = y + random.randint(4, 8)
        self.canvas.create_oval(
            light_x,
            light_y,
            light_x + 3,
            light_y + 3,
            fill="white",
            outline="",
            tag="apple",  # type: ignore
        )  # type: ignore

    def update_score_display(self):
        speed_percent = int((120 / self.speed) * 100)
        powerup_text = ""
        if self.powerup_active:
            if self.powerup_active == "bonus_points":
                powerup_text = " | Bônus Coletado!"
            else:
                remaining = int(self.powerup_end_time - time.time())
                powerup_text = f" | {self.powerup_active.capitalize()} ({remaining}s)"

        self.score_display.config(
            text=f"Pontuação: {self.score} | Velocidade: {speed_percent}%{powerup_text}"
        )

    def update(self):
        if not self.game_active or self.game_paused:
            return

        if self.powerup_active and time.time() > self.powerup_end_time:
            self.deactivate_powerup()

        if (
            not self.active_powerup
            and time.time() - self.powerup_spawn_time > self.powerup_cooldown
            and random.random() < 0.3
        ):
            self.spawn_powerup()

        if self.direction_queue:
            new_direction = self.direction_queue.pop(0)
            if (
                new_direction == "up"
                and self.direction != "down"
                or new_direction == "down"
                and self.direction != "up"
                or new_direction == "left"
                and self.direction != "right"
                or new_direction == "right"
                and self.direction != "left"
            ):
                self.direction = new_direction

        head = self.snake[-1]
        new_head = {
            "right": (head[0] + self.cell_size, head[1]),
            "left": (head[0] - self.cell_size, head[1]),
            "up": (head[0], head[1] - self.cell_size),
            "down": (head[0], head[1] + self.cell_size),
        }[self.direction]

        # Implementação do "wrap around" no modo invencível
        if self.powerup_active == "invincible":
            x, y = new_head
            # Ajusta a posição se ultrapassar as bordas usando as variáveis de dimensão
            if x < 0:
                x = self.game_width - self.cell_size
            elif x >= self.game_width:
                x = 0

            if y < 0:
                y = self.game_height - self.cell_size
            elif y >= self.game_height:
                y = 0

            new_head = (x, y)

        self.snake.append(new_head)

        if self.snake[-1] == self.apple:
            self.apples_eaten += 1
            self.score += 10
            self.apple = self.generate_apple()
        else:
            self.snake.pop(0)

        # Verificação de colisão - modificada para o modo invencível
        if not self.powerup_active == "invincible":
            # No modo normal, qualquer colisão causa game over
            # Usa as variáveis de dimensão para verificar os limites
            if (
                self.snake[-1][0] < 0
                or self.snake[-1][0] >= self.game_width
                or self.snake[-1][1] < 0
                or self.snake[-1][1] >= self.game_height
                or self.snake[-1] in self.snake[:-1]
            ):
                self.game_over()
                return
        # Modo invencível - não há verificação de colisão (removida a verificação com o corpo)

        if (
            self.active_powerup
            and (new_head[0], new_head[1]) == self.active_powerup["pos"]
        ):
            self.activate_powerup()

        self.draw_snake()
        self.draw_apple()

        # Desenha o powerup ativo se existir
        if self.active_powerup:
            x, y = self.active_powerup["pos"]
            self.draw_powerup(x, y)

        # Se tiver powerup ativo, adicionar efeitos visuais
        if self.powerup_active == "invincible" and random.random() > 0.8:
            # Adiciona um rastro de partículas para invencibilidade
            x, y = self.snake[-1]
            sparkle_x = x + random.randint(-5, 25)
            sparkle_y = y + random.randint(-5, 25)
            sparkle = self.canvas.create_text(
                sparkle_x,
                sparkle_y,
                text="✦",
                fill="#FFD700",
                font=("Arial", 8),
                tags="effect",
            )
            # Remove o efeito após um tempo
            self.master.after(300, lambda s=sparkle: self.canvas.delete(s))

        elif self.powerup_active == "speed" and random.random() > 0.8:
            # Adiciona um rastro de velocidade
            if len(self.snake) >= 2:
                x, y = self.snake[-2]  # Posição anterior da cabeça
                trail = self.canvas.create_oval(
                    x + 5,
                    y + 5,
                    x + 15,
                    y + 15,
                    fill="#87CEFA",
                    outline="",
                    tags="effect",
                )
                # Desaparece gradualmente
                self.master.after(
                    100, lambda t=trail: self.canvas.itemconfig(t, fill="#ADD8E6")
                )
                self.master.after(200, lambda t=trail: self.canvas.delete(t))

        self.update_score_display()
        self.master.after(self.speed, self.update)

    def spawn_powerup(self):
        types = [
            ("invincible", "gold", 10),
            ("speed", "deep sky blue", 15),
            ("bonus_points", "medium orchid", 0),
        ]
        power_type, color, duration = random.choice(types)

        # Usa as variáveis de dimensão para o posicionamento
        while True:
            x = (
                random.randint(0, (self.game_width // self.cell_size) - 1)
                * self.cell_size
            )
            y = (
                random.randint(0, (self.game_height // self.cell_size) - 1)
                * self.cell_size
            )
            if (x, y) not in self.snake and (x, y) != self.apple:
                break

        self.active_powerup = {
            "type": power_type,
            "pos": (x, y),
            "duration": duration,
            "color": color,
        }
        self.draw_powerup(x, y)
        self.powerup_spawn_time = time.time()

    def draw_powerup(self, x, y):
        self.canvas.delete("powerup")
        power_type = self.active_powerup["type"]
        color = self.active_powerup["color"]

        # Sombra do powerup
        for i in range(3, 0, -1):
            shadow_opacity = 60 + i * 30
            shadow_color = (
                f"#{shadow_opacity:02x}{shadow_opacity:02x}{shadow_opacity:02x}"
            )
            offset = i + 1
            self.canvas.create_oval(
                x + offset,
                y + offset,
                x + 20 + offset - i,
                y + 20 + offset - i,
                fill=shadow_color,
                outline="",
                tags="powerup",
            )

        # Base do powerup
        self.canvas.create_oval(
            x, y, x + 20, y + 20, fill=color, outline="white", width=2, tags="powerup"
        )

        # Adiciona efeito brilhante ao redor
        for i in range(1, 4):
            glow_alpha = 120 - i * 30
            glow_color = (
                color
                if i == 1
                else f"#{glow_alpha:02x}{glow_alpha:02x}{glow_alpha:02x}"
            )

            self.canvas.create_oval(
                x - i * 2,
                y - i * 2,
                x + 20 + i * 2,
                y + 20 + i * 2,
                outline=glow_color,
                width=1,
                dash=(i * 2, i),
                tags="powerup",
            )

        # Adiciona um símbolo diferente para cada tipo de powerup
        symbol = "⚡"  # padrão
        if power_type == "invincible":
            symbol = "★"
        elif power_type == "speed":
            symbol = "⚡"
        elif power_type == "bonus_points":
            symbol = "✱"

        self.canvas.create_text(
            x + 10,
            y + 10,
            text=symbol,
            fill="white",
            font=("Arial", 12, "bold"),
            tags="powerup",
        )

        # Reflexo de luz (efeito 3D)
        self.canvas.create_arc(
            x + 5,
            y + 5,
            x + 15,
            y + 15,
            start=20,
            extent=60,
            style=tk.ARC,
            outline="white",
            width=2,
            tags="powerup",
        )

    def activate_powerup(self):
        power_type = self.active_powerup["type"]
        duration = self.active_powerup["duration"]

        self.powerup_active = power_type
        self.powerup_end_time = (
            time.time() + duration if power_type != "bonus_points" else 0
        )

        if power_type == "speed":
            self.speed = max(50, self.speed - 30)
        elif power_type == "bonus_points":
            self.score += 150
            self.powerup_active = None

        self.canvas.delete("powerup")
        self.active_powerup = None
        self.draw_snake()
        self.update_score_display()

    def deactivate_powerup(self):
        if self.powerup_active == "speed":
            self.speed += 30
        self.powerup_active = None
        self.draw_snake()
        self.update_score_display()

    def toggle_pause(self, event=None):
        if self.game_active:
            self.game_paused = not self.game_paused
            status = "PAUSADO | " if self.game_paused else ""
            self.score_display.config(text=f"{status}Pontuação: {self.score}")
            if not self.game_paused:
                self.update()

    def game_over(self):
        self.game_active = False
        self.canvas.delete("all")

        # Fundo mais detalhado para a tela de fim de jogo
        self.draw_stars()

        # Adiciona um overlay semi-transparente - ajustado para as dimensões do jogo
        self.canvas.create_rectangle(
            0, 0, self.game_width, self.game_height, fill="#000000", stipple="gray50"
        )

        # Título de fim de jogo com efeito de profundidade
        for i in range(3, 0, -1):
            offset = i * 2
            # Corrigido: Usar cálculos de inteiros apenas
            red_value = 100 - i * 30
            color = f"#{red_value:02x}0000"  # Tons de vermelho
            self.canvas.create_text(
                200 + offset,
                150 + offset,
                text="Fim de Jogo!",
                font=("Arial Black", 24),
                fill=color,
            )

        self.canvas.create_text(
            200,
            150,
            text="Fim de Jogo!",
            font=("Arial Black", 24, "bold"),
            fill="#FF3333",
        )

        # Pontuação com efeito de sombra
        self.canvas.create_text(
            202,
            202,
            text=f"Pontuação Final: {self.score}",
            font=("Arial", 16),
            fill="#333333",
        )
        self.canvas.create_text(
            200,
            200,
            text=f"Pontuação Final: {self.score}",
            font=("Arial", 16),
            fill="white",
        )

        if self.is_new_high_score():
            # Destaque para novo recorde
            self.canvas.create_text(
                200,
                230,
                text="NOVO RECORDE!",
                font=("Arial", 14, "bold"),
                fill="#FFD700",
            )
            self.request_player_name()
        else:
            self.show_top_scores()

        # Botão de reinício com estilo 3D
        self.start_button = tk.Button(
            self.master,
            text="🔄 Jogar Novamente",
            command=self.restart_game,
            bg="#1E88E5",
            fg="white",
            font=("Arial", 12, "bold"),
            relief="raised",
            borderwidth=3,
            padx=15,
            pady=8,
            activebackground="#0D47A1",
            activeforeground="white",
        )
        self.start_button.place(relx=0.5, rely=0.9, anchor="center")

    def is_new_high_score(self):
        try:
            with open("scoresnake.dat", "r") as file:
                scores = [int(line.strip().split(",")[1]) for line in file.readlines()]
        except FileNotFoundError:
            scores = []

        return len(scores) < 3 or self.score > (min(scores) if scores else 0)

    def request_player_name(self):
        name = simpledialog.askstring(
            "Nome do Jogador", "Digite seu nome (máx. 6 caracteres):"
        )
        if not name or name.strip() == "":
            messagebox.showerror("Erro", "Nome inválido! O score não será salvo.")
            self.show_top_scores()
            return
        if len(name) > 6:
            messagebox.showerror("Erro", "Nome deve ter no máximo 6 caracteres!")
            self.request_player_name()
            return
        self.save_score(name)

    def save_score(self, name):
        try:
            with open("scoresnake.dat", "r") as file:
                scores = [line.strip().split(",") for line in file.readlines()]
        except FileNotFoundError:
            scores = []

        scores.append([name, str(self.score)])
        scores.sort(key=lambda x: int(x[1]), reverse=True)
        scores = scores[:3]

        with open("scoresnake.dat", "w") as file:
            for entry in scores:
                file.write(f"{entry[0]},{entry[1]}\n")

        self.show_top_scores()

    def show_top_scores(self):
        y_position = 250
        self.canvas.create_text(
            200, y_position, text="Top 3 Scores:", font=("Arial", 16), fill="white"
        )

        try:
            with open("scoresnake.dat", "r") as file:
                scores = [line.strip().split(",") for line in file.readlines()]

            for i, (name, score) in enumerate(scores[:3]):
                self.canvas.create_text(
                    200,
                    y_position + 30 + (i * 30),
                    text=f"{i+1}. {name}: {score}",
                    font=("Arial", 14),
                    fill="white",
                )
        except FileNotFoundError:
            self.canvas.create_text(
                200,
                y_position + 30,
                text="Nenhum recorde registrado",
                font=("Arial", 14),
                fill="white",
            )

    def restart_game(self):
        self.start_button.place_forget()
        self.start_game()

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
