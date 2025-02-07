import tkinter as tk
from tkinter import simpledialog, scrolledtext, colorchooser, filedialog
import json
import os

class SupportApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Programa de Suporte")

        self.root.configure(bg="#2C3E50")  # Cor de fundo da janela principal

        self.bg_image_path = "background.png"
        self.bg_image = tk.PhotoImage(file=self.bg_image_path)
        
        self.texts = []
        self.load_texts()
        self.create_widgets()

    def create_widgets(self):
        menu = tk.Menu(self.root)
        self.root.config(menu=menu)
        
        themes_menu = tk.Menu(menu)
        menu.add_cascade(label="Temas", menu=themes_menu)
        themes_menu.add_command(label="Alterar plano de fundo", command=self.change_background)
        themes_menu.add_command(label="Alterar cores dos botões", command=self.change_button_colors)

        canvas = tk.Canvas(self.root, width=self.bg_image.width(), height=self.bg_image.height())
        canvas.pack(fill="both", expand=True)
        canvas.create_image(0, 0, image=self.bg_image, anchor="nw")

        self.button_color = "#E74C3C"
        self.text_color = "#ECF0F1"
        self.edit_button_color = "#3498DB"

        for idx, (text, resumo) in enumerate(self.texts):
            frame = tk.Frame(canvas, bg="#2C3E50")
            canvas.create_window(10, 10 + idx * 60, anchor="nw", window=frame)

            button = tk.Button(frame, text=resumo, command=lambda t=text: self.copy_to_clipboard(t), bg=self.button_color, fg=self.text_color, relief="flat")
            button.pack(side="left", padx=5)

            edit_button = tk.Button(frame, text="Editar", command=lambda idx=idx: self.open_edit_window(idx), bg=self.edit_button_color, fg=self.text_color, relief="flat")
            edit_button.pack(side="left", padx=5)

        exit_button = tk.Button(self.root, text="Sair", command=self.root.quit, bg="#95A5A6", fg="#2C3E50", relief="flat")
        exit_button.pack(pady=20, anchor="se")

    def copy_to_clipboard(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)

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

    def change_background(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp")])
        if file_path:
            self.bg_image_path = file_path
            self.bg_image = tk.PhotoImage(file=file_path)
            self.refresh_gui()

    def change_button_colors(self):
        color_code = colorchooser.askcolor(title="Escolha a cor do botão")[1]
        if color_code:
            self.button_color = color_code
            self.refresh_gui()

    def load_texts(self):
        if os.path.exists("texts.json"):
            with open("texts.json", "r", encoding="utf-8") as file:
                self.texts = json.load(file)
        else:
            self.texts = [
                ("Bom dia! Em que posso ajudar? 😊", "Início atendimento"),
                ("Já realizou o procedimento de reiniciar os equipamentos de internet? 🔄", "Reiniciar equipamentos"),
                ("Obrigado por aguardar. 😀\nFiz algumas alterações na conexão, e acredito que o problema foi resolvido.\nPor favor, pode verificar se ficou melhor?", "Alterações na conexão"),
                ("Entendi. 👍\nUm momento por favor que estou verificando a conexão.\nEla poderá cair por alguns segundos, mas já retornará.", "Verificando conexão"),
                ("Nesse caso ofereço uma visita técnica para verificação dos equipamentos de internet, e o local em que eles estão instalados. Algumas vezes o aparelho pode estar instalado em um local que não propaga bem o sinal Wi-Fi e outros cômodos podem não chegar o sinal. Assim o técnico pode recomendar as opções, que seria a troca dos equipamentos de local, a instalação de um ponto adicional, ou se for um problema no próprio roteador ele já realiza o reparo.", "Visita técnica"),
                ("A visita técnica não tem custo, e caso seja identificado um problema nos equipamentos realizaremos o reparo também sem custo. Já os serviços de instalação de um ponto adicional, e mudança dos equipamentos de local, tem um custo. Se o técnico identificar a necessidade ele vai lhe indicar, assim caso aprove, podemos agendar uma visita para realizar o serviço.", "Custo da visita técnica"),
                ("Reservamos o direito de acesso às configurações do roteador aos nossos técnicos, a fim de garantir que as configurações estejam de acordo para o funcionamento da internet. Caso seja alguma configuração especifica que necessite, ou alguma informação podemos passar por atendimento mesmo.", "Configurações do roteador"),
                ("Se fizer questão de receber os dados de acesso posso fornecer, porém informo que em caso que essas configurações sofram alterações e resultem na falta de internet/necessidade de uma visita técnica para reconfiguração e reparo, a visita poderá ter o custo do chamado técnico. Gostaria de alguma informação ou ajuste especifico das configurações do roteador, ou prefere receber os dados de acesso do mesmo?", "Dados de acesso"),
                ("Há alguns requisitos para realização do teste de velocidade. Como a velocidade da banda contratada é muito alta, celulares, ou dispositivos conectados na rede Wi-Fi não costumam ser fortes o suficiente para atingir a velocidade máxima, e o teste fica limitado a capacidade do dispositivo/tecnologia WiFi.", "Requisitos para teste de velocidade"),
                ("Recomendamos para teste um computador conectado via cabo de rede. O computador e o cabo tem que suportar conexão gigabit (superior a 100mega). Recomendamos também os sites speedtest.net / fast.com / nperf.com Outros sites por possuir muita propaganda acabam interferindo no resultado, ou não tendo servidores próximos disponíveis.", "Sites recomendados"),
                ("Caso não tenha um computador via cabo de rede disponível o teste pode ser realizado via Wi-Fi, porém cada rede Wi-Fi e dispositivo possuem capacidade diferente. Por exemplo dispositivos conectados na rede Wi-Fi 2.4Ghz costumam atingir a velocidade máxima de 40 a 50mega. Já na rede Wi-Fi 5Ghz pode chegar a média de 250mega.", "Teste via Wi-Fi"),
                ("Não estou conseguindo acessar o roteador remotamente. Pode reiniciá-lo? Basta retirar da tomada por cerca de 5 segundos, em seguida conectar novamente.", "Reiniciar roteador"),
                ("Boa tarde! 😀\nPode me informar algum exemplo de site/aplicativo que costuma acessar e notar este problema?", "Exemplo de site/aplicativo"),
                ("Devido ao termino do meu turno, estou encerrando este atendimento, a fim de que outro técnico possa lhe atender, caso você precise. Havendo algo mais para auxiliarmos por favor entre em contato novamente. Tenha uma ótima noite! 😀", "Encerramento do atendimento"),
                ("As visitas no período da tarde ocorrem entre as 13h30 e 18h. Devido à duração variada das visitas, não tenho como informar um horário específico. Caso tenha alguma restrição de horário, basta me informar, que aviso ao técnico para não passar no horário que não estará disponível.", "Horário das visitas"),
            ]

    def save_texts(self):
        with open("texts.json", "w", encoding="utf-8") as file:
            json.dump(self.texts, file, ensure_ascii=False, indent=4)

    def refresh_gui(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.create_widgets()

if __name__ == "__main__":
    root = tk.Tk()
    app = SupportApp(root)
    root.mainloop()
