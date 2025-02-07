import os
import sys
import tkinter as tk
from tkinter import simpledialog, scrolledtext, filedialog
import json
import winsound


class SupportApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Versão Suporte 1.5")

        # Carregar configurações
        self.load_config()

        # Cor de fundo da janela principal
        self.root.configure(bg=self.bg_color)

        # Carregar imagem de fundo
        self.load_bg_image()

        self.texts = []
        self.load_texts()
        self.create_widgets()
        self.create_menu()
        self.create_notepad_widget()

        # Salvar tamanho e posição da janela
        self.root.bind("<Configure>", self.save_window_size)

    def save_window_size(self, event):
        self.window_size = self.root.wm_geometry()
        self.save_config()

    def load_config(self):
        config_path = os.path.join(
            os.path.dirname(sys.executable), "config.txt")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as file:
                    config = json.load(file)
                    self.bg_image_path = config.get(
                        "bg_image_path", "background.png")
                    self.sound_enabled = config.get("sound_enabled", True)
                    self.dark_mode = config.get("dark_mode", False)
                    self.bg_color = config.get("bg_color", "#2C3E50")
                    self.btn_fg_color = config.get("btn_fg_color", "#ECF0F1")
                    self.btn_bg_color = config.get("btn_bg_color", "#E74C3C")
                    self.edit_btn_bg_color = config.get(
                        "edit_btn_bg_color", "#3498DB")
                    self.show_edit_buttons = config.get(
                        "show_edit_buttons", True)
                    self.window_size = config.get(
                        "window_size", "800x600+100+100")
            except json.JSONDecodeError:
                self.bg_image_path = "background.png"
                self.sound_enabled = True
                self.dark_mode = False
                self.bg_color = "#2C3E50"
                self.btn_fg_color = "#ECF0F1"
                self.btn_bg_color = "#E74C3C"
                self.edit_btn_bg_color = "#3498DB"
                self.show_edit_buttons = True
                self.window_size = "800x600+100+100"
        else:
            self.bg_image_path = "background.png"
            self.sound_enabled = True
            self.dark_mode = False
            self.bg_color = "#2C3E50"
            self.btn_fg_color = "#ECF0F1"
            self.btn_bg_color = "#E74C3C"
            self.edit_btn_bg_color = "#3498DB"
            self.show_edit_buttons = True
            self.window_size = "800x600+100+100"

        # Pro curar automaticamente o diretório de imagens de fundo
        if not os.path.exists(self.bg_image_path):
            self.bg_image_path = os.path.join(
                os.path.dirname(sys.executable), "background.png")
            if not os.path.exists(self.bg_image_path):
                self.bg_image_path = self.select_bg_image_dir()

        # Carregar tamanho e posição da janela
        self.root.geometry(self.window_size)

    def save_config(self):
        config_path = os.path.join(
            os.path.dirname(sys.executable), "config.txt")
        config = {
            "bg_image_path": self.bg_image_path,
            "sound_enabled": self.sound_enabled,
            "dark_mode": self.dark_mode,
            "bg_color": self.bg_color,
            "btn_fg_color": self.btn_fg_color,
            "btn_bg_color": self.btn_bg_color,
            "edit_btn_bg_color": self.edit_btn_bg_color,
            "show_edit_buttons": self.show_edit_buttons,
            "window_size": self.window_size
        }
        with open(config_path, "w") as file:
            json.dump(config, file)

    def load_bg_image(self):
        try:
            if os.path.isabs(self.bg_image_path):
                self.bg_image = tk.PhotoImage(file=self.bg_image_path)
            else:
                self.bg_image = tk.PhotoImage(file=os.path.join(
                    os.path.dirname(sys.executable), self.bg_image_path))
        except tk.TclError:
            self.bg_image_path = self.select_bg_image_dir()
            self.bg_image = tk.PhotoImage(file=self.bg_image_path)

    def select_bg_image_dir(self):
        file_path = filedialog.askopenfilename(title="Selecione a imagem de fundo", filetypes=[
                                               ("Image files", "*.png")])
        if file_path:
            return file_path
        else:
            return "background.png "  # Retorna um valor padrão caso o usuário cancele a sele ç ã o

    def create_widgets(self):
        # Criar o Canvas
        self.canvas = tk.Canvas(self.root, width=self.bg_image.width(), height=self.bg_image.height())
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_image(0, 0, image=self.bg_image, anchor="nw")

        # Frame para a Scrollbar e o Canvas
        frame = tk.Frame(self.canvas)
        self.canvas.create_window(10, 10, anchor="nw", window=frame)

        # Scrollbar
        self.scrollbar = tk.Scrollbar(frame, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side="right", fill="y")

        # Frame para os botões
        button_frame = tk.Frame(frame, bg=self.bg_color)
        button_frame.pack(side="left", fill="both", expand=True)

        # Configurar o Canvas para usar a Scrollbar
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        button_frame.rowconfigure(0, weight=1)
        button_frame.columnconfigure(0, weight=1)

        # Adicionar os botões
        column = 0
        row = 0
        for idx, (text, resumo) in enumerate(self.texts):
            button = tk.Button(button_frame, text=resumo, command=lambda t=text: self.copy_to_clipboard(
                t), bg=self.btn_bg_color, fg=self.btn_fg_color, relief="flat")
            button.grid(row=row, column=column, padx=5, pady=5, sticky="nsew")

            edit_button = tk.Button(button_frame, text="Editar", command=lambda idx=idx: self.open_edit_window(
                idx), bg=self.edit_btn_bg_color, fg=self.btn_fg_color, relief="flat")
            if self.show_edit_buttons:
                edit_button.grid(row=row + 1, column=column,
                                 padx=5, pady=5, sticky="nsew")
            else:
                edit_button.grid_forget()

            row += 2
            if row > 16:  # Ajuste esse valor para controlar a quantidade de linhas
                row = 0
                column += 1

        # Atualizar a região do Canvas para a rolagem
        button_frame.update_idletasks()  # Atualiza o layout do button_frame
        self.canvas.config(scrollregion=self.canvas.bbox("all"))  # Define a região de rolagem

    def create_menu(self):
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        theme_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Temas", menu=theme_menu)
        theme_menu.add_command(
            label="Alterar Plano de Fundo", command=self.change_bg_image)

        self.sound_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Som", menu=self.sound_menu)
        self.sound_menu.add_command(
            label="Desativar Som de Clique" if self.sound_enabled else "Ativar Som de Clique", command=self.toggle_sound)

        self.view_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Visual", menu=self.view_menu)
        self.view_menu.add_command(
            label="Desativar Modo Noturno" if self.dark_mode else "Ativar Modo Noturno", command=self.toggle_dark_mode)
        self.view_menu.add_command(
            label="Editar Cores", command=self.edit_colors)
        self.view_menu.add_command(
            label="Ocultar Botões de Edição" if self.show_edit_buttons else "Exibir Botões de Edição", command=self.toggle_edit_buttons)

    def copy_to_clipboard(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        if self.sound_enabled:
            self.root.after(1, lambda: winsound.PlaySound(os.path.join(os.path.dirname(
                sys.executable), "click.wav"), winsound.SND_FILENAME | winsound.SND_ASYNC))  # SOM

    def open_edit_window(self, idx):
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Editar Texto")

        text_box = scrolledtext.ScrolledText(
            edit_window, wrap=tk.WORD, width=50, height=15)
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

    def toggle_edit_buttons(self):
        self.show_edit_buttons = not self.show_edit_buttons
        new_label = "Ocultar Botões de Edição" if self.show_edit_buttons else "Exibir Botões de Edição"
        self.view_menu.entryconfig(3, label=new_label)
        self.save_config()
        self.refresh_gui()

    def load_texts(self):
        texts_path = os.path.join(
            os.path.dirname(sys.executable), "texts.json")
        if os.path.exists(texts_path):
            with open(texts_path, "r", encoding="utf-8") as file:
                self.texts = json.load(file)
        else:
            self.texts = [
                ("EXEMPLO", "BOTÃO"),
            ]

    def save_texts(self):
        texts_path = os.path.join(
            os.path.dirname(sys.executable), "texts.json")
        with open(texts_path, "w", encoding="utf-8") as file:
            json.dump(self.texts, file, ensure_ascii=False, indent=4)

    def change_bg_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.gif")])
        if file_path:
            self.bg_image_path = file_path
            self.bg_image = tk.PhotoImage(file=file_path)
            self.save_config()
            self.refresh_gui()

    def refresh_gui(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.create_widgets()
        self.create_menu()
        self.create_notepad_widget()

    def create_notepad_widget(self):
        self.notepad_frame = tk .Frame(self.root, bg=self.bg_color)
        self.notepad_frame.pack(fill="both", expand=True)

        self.notepad_text = scrolledtext.ScrolledText(
            self.notepad_frame, width=50, height=10, wrap=tk.WORD)
        self.notepad_text.pack(padx=10, pady=10, fill="both", expand=True)

        self.notepad_toolbar = tk.Frame(self.notepad_frame, bg=self.bg_color)
        self.notepad_toolbar.pack(fill="x", side="top")

        self.bold_button = tk.Button(self.notepad_toolbar, text="Negrito",
                                     command=lambda: self.notepad_text.tag_add("bold", "sel.first", "sel.last"))
        self.bold_button.pack(side="left")

        self.italic_button = tk.Button(self.notepad_toolbar, text="Itálico",
                                       command=lambda: self.notepad_text.tag_add("italic", "sel.first", "sel.last"))
        self.italic_button.pack(side="left")

        self.underline_button = tk.Button(self.notepad_toolbar, text="Sublinhado",
                                          command=lambda: self.notepad_text.tag_add("underline", "sel.first", "sel.last"))
        self.underline_button.pack(side="left")

        self.separator_button = tk.Button(
            self.notepad_toolbar, text="Adicionar separação", command=self.add_separator)
        self.separator_button.pack(side="left")

        self.save_notepad_button = tk.Button(
            self.notepad_toolbar, text="Salvar Alterações", command=self.save_notepad)
        self.save_notepad_button.pack(side="right")

        self.notepad_text.tag_config("bold", font=("Helvetica", "12", "bold"))
        self.notepad_text.tag_config(
            "italic", font=("Helvetica", "12", "italic"))
        self.notepad_text.tag_config(
            "underline", font=("Helvetica", "12", "underline"))

        self.load_notepad()

    def load_notepad(self):
        notepad_path = os.path.join(
            os.path.dirname(sys.executable), "notepad.txt")
        if os.path.exists(notepad_path):
            with open(notepad_path, "r", encoding="utf-8") as file:
                self.notepad_text.insert(tk.END, file.read())

    def save_notepad(self):
        notepad_path = os.path.join(
            os.path.dirname(sys.executable), "notepad.txt")
        with open(notepad_path, "w", encoding="utf-8") as file:
            file.write(self.notepad_text.get("1.0", tk.END))

    def add_separator(self):
        self.notepad_text.insert(tk.END, "\n______________________\n")

    def edit_colors(self):
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Editar Cores")

        tk.Label(edit_window, text="Cor do Fundo:").pack()
        bg_color_entry = tk.Entry(edit_window)
        bg_color_entry.insert(0, self.bg_color)
        bg_color_entry.pack()

        tk.Label(edit_window, text="Cor do Texto dos Botões:").pack()
        btn_fg_color_entry = tk.Entry(edit_window)
        btn_fg_color_entry.insert(0, self.btn_fg_color)
        btn_fg_color_entry.pack()

        tk.Label(edit_window, text="Cor do Fundo dos Botões:").pack()
        btn_bg_color_entry = tk.Entry(edit_window)
        btn_bg_color_entry.insert(0, self.btn_bg_color)
        btn_bg_color_entry.pack()

        tk.Label(edit_window, text="Cor do Fundo do Botão de Edição:").pack()
        edit_btn_bg_color_entry = tk.Entry(edit_window)
        edit_btn_bg_color_entry.insert(0, self.edit_btn_bg_color)
        edit_btn_bg_color_entry.pack()

        def save_colors():
            self.bg_color = bg_color_entry.get()
            self.btn_fg_color = btn_fg_color_entry.get()
            self.btn_bg_color = btn_bg_color_entry.get()
            self.edit_btn_bg_color = edit_btn_bg_color_entry.get()
            self.save_config()
            self.refresh_gui()
            edit_window.destroy()

        save_button = tk.Button(
            edit_window, text="Salvar", command=save_colors)
        save_button.pack(pady=5, side="bottom")


if __name__ == "__main__":
    root = tk.Tk()
    app = SupportApp(root)
    root.mainloop()
