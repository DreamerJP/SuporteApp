import os
import sys
import tkinter as tk
from tkinter import simpledialog, scrolledtext, filedialog, ttk
import json
import pygame

# Constantes para cores e caminhos de arquivo
DEFAULT_BG_COLOR = "#2C3E50"
DEFAULT_BTN_FG_COLOR = "#ECF0F1"
DEFAULT_BTN_BG_COLOR = "#E74C3C"
DEFAULT_EDIT_BTN_BG_COLOR = "#3498DB"
DARK_BG_COLOR = "#1E1E1E"
DARK_BTN_FG_COLOR = "#FFFFFF"
DARK_BTN_BG_COLOR = "#333333"
DARK_EDIT_BTN_BG_COLOR = "#555555"
DEFAULT_WINDOW_SIZE = "800x600+100+100"
DEFAULT_BG_IMAGE_PATH = "background.png"
CONFIG_FILE = "config.txt"
TEXTS_FILE = "texts.json"
NOTEPAD_FILE = "notepad.json"

class ConfigManager:
    """Gerencia o carregamento e salvamento das configurações do aplicativo."""
    def __init__(self):
        self.config_path = os.path.join(os.path.dirname(sys.executable), CONFIG_FILE)
        self.default_config = {
            "bg_image_path": DEFAULT_BG_IMAGE_PATH,
            "sound_enabled": True,
            "dark_mode": False,
            "bg_color": DEFAULT_BG_COLOR,
            "btn_fg_color": DEFAULT_BTN_FG_COLOR,
            "btn_bg_color": DEFAULT_BTN_BG_COLOR,
            "edit_btn_bg_color": DEFAULT_EDIT_BTN_BG_COLOR,
            "show_edit_buttons": True,
            "window_size": DEFAULT_WINDOW_SIZE,
            "notepad_expanded": True,
            "last_bg_image_path": DEFAULT_BG_IMAGE_PATH,
            "last_bg_color": DEFAULT_BG_COLOR,
            "last_btn_fg_color": DEFAULT_BTN_FG_COLOR,
            "last_btn_bg_color": DEFAULT_BTN_BG_COLOR,
            "last_edit_btn_bg_color": DEFAULT_EDIT_BTN_BG_COLOR
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
    """Classe principal do aplicativo."""
    def __init__(self, root):
        self.root = root
        self.root.title("Versão Suporte 2.0")

        self.config_manager = ConfigManager()
        self.text_manager = TextManager()
        self.notepad_manager = NotepadManager()

        self.root.geometry(self.config_manager.config["window_size"])

        self.config = self.config_manager.config
        self.texts = self.text_manager.texts

        self.setup_ui()
        pygame.mixer.init()
        self.click_sound = None
        self.load_sound()

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

    def save_window_size(self, event):
        if event.widget == self.root:
            self.config["window_size"] = self.root.wm_geometry()
            self.config_manager.save_config()

    def load_bg_image(self):
        try:
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

        self.scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side="right", fill="y")

        button_frame = tk.Frame(frame, bg=self.config["bg_color"])
        button_frame.pack(side="left", fill="both", expand=True)

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.create_buttons(button_frame)

    def create_buttons(self, button_frame):
        column, row = 0, 0
        for idx, (text, resumo) in enumerate(self.texts):
            button = ttk.Button(button_frame, text=resumo, command=lambda t=text: self.copy_to_clipboard(t))
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
        edit_window.title("Editar Texto")

        text_box = scrolledtext.ScrolledText(edit_window, wrap=tk.WORD, width=50, height=15)
        text_box.pack(padx=10, pady=10)
        text_box.insert(tk.END, self.texts[idx][0])

        def save_text():
            new_text = text_box.get("1.0", tk.END).strip()
            if new_text:
                self.texts[idx] = (new_text, self.texts[idx][1])
                self.text_manager.save_texts()
                self.refresh_gui()
                edit_window.destroy()

        ttk.Button(edit_window, text="Salvar", command=save_text).pack(pady=5)

    def create_menu(self):
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        self.view_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Visual", menu=self.view_menu)
        self.view_menu.add_command(label="Alterar Plano de Fundo", command=self.change_bg_image)
        self.view_menu.add_command(
            label="Desativar Modo Noturno" if self.config["dark_mode"] else "Ativar Modo Noturno",
            command=self.toggle_dark_mode
        )
        self.view_menu.add_command(label="Editar Cores", command=self.edit_colors)
        self.view_menu.add_command(
            label="Ocultar Botões de Edição" if self.config["show_edit_buttons"] else "Exibir Botões de Edição",
            command=self.toggle_edit_buttons
        )
        self.view_menu.add_command(
            label="Ocultar Bloco de Notas" if self.config["notepad_expanded"] else "Exibir Bloco de Notas",
            command=self.toggle_notepad
        )

        self.sound_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Som", menu=self.sound_menu)
        self.sound_menu.add_command(
            label="Desativar Som de Clique" if self.config["sound_enabled"] else "Ativar Som de Clique",
            command=self.toggle_sound
        )

        help_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Ajuda", menu=help_menu)
        help_menu.add_command(label="Sobre", command=self.show_about)

    def show_about(self):
        about_window = tk.Toplevel(self.root)
        about_window.title("Sobre")
        tk.Label(about_window, text="Versão Suporte 2.0\nDesenvolvido por Paulo Gama\nDreamerJPMG@gmail.com").pack(padx=20, pady=20)
        ttk.Button(about_window, text="Fechar", command=about_window.destroy).pack(pady=10)

    def toggle_sound(self):
        self.config["sound_enabled"] = not self.config["sound_enabled"]
        self.sound_menu.entryconfig(0, label="Desativar Som de Clique" if self.config["sound_enabled"] else "Ativar Som de Clique")
        self.config_manager.save_config()

    def toggle_dark_mode(self):
        self.config["dark_mode"] = not self.config["dark_mode"]
        self.view_menu.entryconfig(0, label="Desativar Modo Noturno" if self.config["dark_mode"] else "Ativar Modo Noturno")
    
        # Salvar o conteúdo atual do bloco de notas antes de recarregar a interface
        notepad_content = self.notepad_text.get("1.0", tk.END)
        notepad_tags = []
        for tag in self.notepad_text.tag_names():
            if tag != "sel":
                ranges = self.notepad_text.tag_ranges(tag)
                for i in range(0, len(ranges), 2):
                    start = ranges[i]
                    end = ranges[i + 1]
                    notepad_tags.append({
                        "tag": tag,
                        "start": str(start),
                        "end": str(end)
                    })
    
        if self.config["dark_mode"]:
            self.config["last_bg_image_path"] = self.config["bg_image_path"]
            self.config["last_bg_color"] = self.config["bg_color"]
            self.config["last_btn_fg_color"] = self.config["btn_fg_color"]
            self.config["last_btn_bg_color"] = self.config["btn_bg_color"]
            self.config["last_edit_btn_bg_color"] = self.config["edit_btn_bg_color"]
        
            self.config["bg_image_path"] = "ModoNoturno.png"
            self.config["bg_color"] = DARK_BG_COLOR
            self.config["btn_fg_color"] = DARK_BTN_FG_COLOR
            self.config["btn_bg_color"] = DARK_BTN_BG_COLOR
            self.config["edit_btn_bg_color"] = DARK_EDIT_BTN_BG_COLOR
        else:
            self.config["bg_image_path"] = self.config.get("last_bg_image_path", DEFAULT_BG_IMAGE_PATH)
            self.config["bg_color"] = self.config.get("last_bg_color", DEFAULT_BG_COLOR)
            self.config["btn_fg_color"] = self.config.get("last_btn_fg_color", DEFAULT_BTN_FG_COLOR)
            self.config["btn_bg_color"] = self.config.get("last_btn_bg_color", DEFAULT_BTN_BG_COLOR)
            self.config["edit_btn_bg_color"] = self.config.get("last_edit_btn_bg_color", DEFAULT_EDIT_BTN_BG_COLOR)
    
        self.config_manager.save_config()
    
        # Recarregar a interface
        self.refresh_gui()
    
        # Restaurar o conteúdo do bloco de notas após a recarga
        self.notepad_text.insert(tk.END, notepad_content)
        for tag in notepad_tags:
            self.notepad_text.tag_add(tag["tag"], tag["start"], tag["end"])

    def toggle_edit_buttons(self):
        self.config["show_edit_buttons"] = not self.config["show_edit_buttons"]
        self.view_menu.entryconfig(2, label="Ocultar Botões de Edição" if self.config["show_edit_buttons"] else "Exibir Botões de Edição")
        self.config_manager.save_config()
        self.refresh_gui()

    def toggle_notepad(self):
        self.config["notepad_expanded"] = not self.config["notepad_expanded"]
        self.view_menu.entryconfig(4, label="Ocultar Bloco de Notas" if self.config["notepad_expanded"] else "Exibir Bloco de Notas")
    
        if self.config["notepad_expanded"]:
            self.notepad_frame.pack(fill="both", expand=True)
        else:
            self.notepad_frame.pack_forget()
    
        # Ajustar a geometria da janela
        self.adjust_window_geometry()

    def adjust_window_geometry(self):
        # Obter a geometria atual da janela
        current_geometry = self.root.geometry()
        width, height, x, y = map(int, current_geometry.replace('x', '+').split('+'))
    
        # Definir a nova altura da janela com base no estado do bloco de notas
        if self.config["notepad_expanded"]:
            new_height = height + 200  # Aumentar a altura para acomodar o bloco de notas
        else:
            new_height = height - 200  # Reduzir a altura para recolher o bloco de notas
    
        # Aplicar a nova geometria
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

        tk.Label(edit_window, text="Cor do Fundo:").pack()
        bg_color_entry = tk.Entry(edit_window)
        bg_color_entry.insert(0, self.config["bg_color"])
        bg_color_entry.pack()

        def save_colors():
            self.config["bg_color"] = bg_color_entry.get()
            self.config_manager.save_config()
            self.refresh_gui()
            edit_window.destroy()

        ttk.Button(edit_window, text="Salvar", command=save_colors).pack(pady=5)

    def create_notepad_widget(self):
        self.notepad_frame = tk.Frame(self.root, bg=self.config["bg_color"])
        self.notepad_frame.pack(fill="both", expand=True)

        self.notepad_text = scrolledtext.ScrolledText(self.notepad_frame, width=50, height=10, wrap=tk.WORD)
        self.notepad_text.pack(padx=10, pady=10, fill="both", expand=True)

        self.notepad_toolbar = tk.Frame(self.notepad_frame, bg=self.config["bg_color"])
        self.notepad_toolbar.pack(fill="x", side="top")

        ttk.Button(self.notepad_toolbar, text="𝙉", command=lambda: self.notepad_text.tag_add("bold", "sel.first", "sel.last")).pack(side="left")
        ttk.Button(self.notepad_toolbar, text="𝙄", command=lambda: self.notepad_text.tag_add("italic", "sel.first", "sel.last")).pack(side="left")
        ttk.Button(self.notepad_toolbar, text="S͟", command=lambda: self.notepad_text.tag_add("underline", "sel.first", "sel.last")).pack(side="left")
        ttk.Button(self.notepad_toolbar, text="Adicionar linha", command=self.add_separator).pack(side="left")
        ttk.Button(self.notepad_toolbar, text="Salvar", command=self.save_notepad).pack(side="right")

        self.notepad_text.tag_config("bold", font=("Helvetica", "12", "bold"))
        self.notepad_text.tag_config("italic", font=("Helvetica", "12", "italic"))
        self.notepad_text.tag_config("underline", font=("Helvetica", "12", "underline"))

        text, tags = self.notepad_manager.load_notepad()
        self.notepad_text.insert(tk.END, text)
        for tag in tags:
            self.notepad_text.tag_add(tag["tag"], tag["start"], tag["end"])

        if not self.config["notepad_expanded"]:
            self.notepad_frame.pack_forget()

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
        for widget in self.root.winfo_children():
            widget.destroy()
        self.setup_ui()
        self.adjust_window_geometry()  # Ajustar a geometria ao recarregar a interface


if __name__ == "__main__":
    root = tk.Tk()
    app = SupportApp(root)
    root.mainloop()
