import tkinter as tk
from tkinter import simpledialog, scrolledtext, filedialog
import json
import os
import sys
import winsound

class SupportApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Versão Suporte técnico")

        # Determinar o caminho base do executável
        if getattr(sys, 'frozen', False):
            self.base_path = sys._MEIPASS
        else:
            self.base_path = os.path.dirname(os.path.abspath(__file__))

        # Carregar configurações
        self.load_config()

        self.root.configure(bg=self.bg_color)

        # Carregar imagem de fundo
        self.load_background_image()

        self.texts = []
        self.load_texts()
        self.create_widgets()
        self.create_menu()

    def load_background_image(self):
        """Carrega a imagem de fundo do diretório do executável"""
        try:
            bg_path = os.path.join(self.base_path, "background.png")
            self.bg_image = tk.PhotoImage(file=bg_path)
            self.bg_image_path = bg_path
        except Exception as e:
            print(f"Erro ao carregar imagem de fundo: {e}")
            self.bg_image = None
            self.bg_image_path = ""

    def create_widgets(self):
        if self.bg_image:
            self.canvas = tk.Canvas(self.root, width=self.bg_image.width(), height=self.bg_image.height())
            self.canvas.pack(fill="both", expand=True)
            self.canvas.create_image(0, 0, image=self.bg_image, anchor="nw")
        else:
            # Fallback se a imagem não for encontrada
            self.canvas = tk.Canvas(self.root, bg=self.bg_color)
            self.canvas.pack(fill="both", expand=True)

        for idx, (text, resumo) in enumerate(self.texts):
            frame = tk.Frame(self.canvas, bg=self.bg_color)
            self.canvas.create_window(10, 10 + idx * 60, anchor="nw", window=frame)

            button = tk.Button(frame, text=resumo, command=lambda t=text: self.copy_to_clipboard(t), bg=self.btn_bg_color, fg=self.btn_fg_color, relief="flat")
            button.pack(side="left", padx=5)

            edit_button = tk.Button(frame, text="Editar", command=lambda idx=idx: self.open_edit_window(idx), bg=self.edit_btn_bg_color, fg=self.btn_fg_color, relief="flat")
            edit_button.pack(side="left", padx=5)

        exit_button = tk.Button(self.root, text="Sair", command=self.root.quit, bg="#95A5A6", fg="#2C3E50", relief="flat")
        exit_button.pack(pady=20, anchor="se")

    def create_menu(self):
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        theme_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Temas", menu=theme_menu)
        theme_menu.add_command(label="Alterar Plano de Fundo", command=self.change_bg_image)

        self.sound_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Som", menu=self.sound_menu)
        self.sound_menu.add_command(label="Desativar Som de Clique" if self.sound_enabled else "Ativar Som de Clique", command=self.toggle_sound)

        self.view_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Visual", menu=self.view_menu)
        self.view_menu.add_command(label="Desativar Modo Noturno" if self.dark_mode else "Ativar Modo Noturno", command=self.toggle_dark_mode)

    def copy_to_clipboard(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        if self.sound_enabled:
            self.root.after(1, lambda: winsound.PlaySound("click.wav", winsound.SND_FILENAME | winsound.SND_ASYNC))

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
                self.save_texts()
                self.refresh_gui()
                edit_window.destroy()

        save_button = tk.Button(edit_window, text="Salvar", command=save_text)
        save_button.pack(pady=5)

    def toggle_sound(self):
        self.sound_enabled = not self.sound_enabled
        new_label = "Desativar Som" if self.sound_enabled else "Ativar Som"
        self.sound_menu.entryconfig(0, label=new_label)
        self.save_config()

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        new_label = "Desativar Darkmode" if self.dark_mode else "Ativar Darkmode"
        self.view_menu.entryconfig(0, label=new_label)
        self.save_config()
        self.refresh_gui()

    def load_config(self):
        default_path = os.path.join(self.base_path, "background.png")
        
        if os.path.exists("config.txt"):
            try:
                with open("config.txt", "r") as file:
                    config = json.load(file)
                    # Verificar se o caminho salvo ainda existe
                    if os.path.exists(config.get("bg_image_path", "")):
                        self.bg_image_path = config["bg_image_path"]
                    else:
                        self.bg_image_path = default_path
                    
                    self.sound_enabled = config.get("sound_enabled", True)
                    self.dark_mode = config.get("dark_mode", False)
            except json.JSONDecodeError:
                self.bg_image_path = default_path
                self.sound_enabled = True
                self.dark_mode = False
        else:
            self.bg_image_path = default_path
            self.sound_enabled = True
            self.dark_mode = False

        self.bg_color = "#2C3E50" if not self.dark_mode else "#1C1C1C"
        self.btn_fg_color = "#ECF0F1" if not self.dark_mode else "#DDDDDD"
        self.btn_bg_color = "#E74C3C" if not self.dark_mode else "#B22222"
        self.edit_btn_bg_color = "#3498DB" if not self.dark_mode else "#1E90FF"

    def save_config(self):
        config = {
            "bg_image_path": self.bg_image_path,
            "sound_enabled": self.sound_enabled,
            "dark_mode": self.dark_mode
        }
        with open("config.txt", "w") as file:
            json.dump(config, file)

    def load_texts(self):
        if os.path.exists("texts.json"):
            with open("texts.json", "r", encoding="utf-8") as file:
                self.texts = json.load(file)
        else:
            self.texts = [
                ("EXEMPLO", "BOTÃO"),
            ]

    def save_texts(self):
        with open("texts.json", "w", encoding="utf-8") as file:
            json.dump(self.texts, file, ensure_ascii=False, indent=4)

    def change_bg_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.gif")],
            initialdir=self.base_path  # Começa a procurar no diretório do executável
        )
        if file_path:
            try:
                self.bg_image_path = file_path
                self.bg_image = tk.PhotoImage(file=file_path)
                self.save_config()
                self.refresh_gui()
            except Exception as e:
                print(f"Erro ao carregar nova imagem: {e}")

    def refresh_gui(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.create_widgets()
        self.create_menu()

if __name__ == "__main__":
    root = tk.Tk()
    app = SupportApp(root)
    root.mainloop()
