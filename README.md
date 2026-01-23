# SuporteApp 🚀

O **SuporteApp** é uma ferramenta projetada para agilizar o atendimento de suporte técnico, permitindo acesso rápido a scripts de texto e automação de abertura de IPs/portas.

## ⚠️ Migração para Versão Web (IMPORTANTE)

O desenvolvimento da versão desktop (Windows `.exe`) foi oficialmente **encerrado na versão 3.6**. O projeto agora é 100% focado na **Versão Web**, que oferece maior compatibilidade, atualizações instantâneas e recursos modernos como o Modo Compacto (Windowed Popup).

### 🌐 Acesse a nova versão oficial aqui:

# [https://dreamerjp.github.io/SuporteApp-Web/](https://dreamerjp.github.io/SuporteApp-Web/)

> **Dica:** Para manter a experiência de aplicativo no PC, acesse o link no Chrome ou Edge, vá em _Três Pontinhos > Salvar e Compartilhar > Instalar como Aplicativo_.

---

## Histórico de Versões (Desktop)

### <h1>Versão 3.6 (Final):</h1>

- Última versão para PC.
- Interface modernizada com `ttkbootstrap`.
- IP Opener nativo e configurável.
- Sistema de abas por categoria.

### <h1>Versão 3.5:</h1>

![SuporteApp3.5](https://github.com/user-attachments/assets/b34a941f-8dbc-4a78-a90a-aa022cc72425)

### <h1>Versão 1.0:</h1>

![SuporteApp1.0](https://github.com/user-attachments/assets/b29ee307-17d7-41eb-adc0-1ba1038506f3)

---

## Desenvolvimento Antigo (PC)

Para fins de legado, o comando para criar o executável da versão 3.6 era:
`pyinstaller --onefile --noconsole --icon="ico.ico" --add-data "ico.ico;." --version-file=version_info.txt --runtime-tmpdir=. SuporteApp.py`
