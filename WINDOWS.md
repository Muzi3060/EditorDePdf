# Usar no Windows

Alvo: Windows 10/11 de 64 bits (x86_64). Não há necessidade de conta, servidor ou assinatura.

## Pacote pronto (sem instalar Python)

Extraia **EditorPDF-Windows-x64.zip** e abra **EditorPDF.exe**. Preserve a pasta `_internal` e os demais arquivos ao lado dele. Pode também abrir um PDF arrastando-o para o executável. O pacote inclui uma pasta `codigo-fonte` com o projeto correspondente.

A compilação e os testes foram realizados usando Python Windows em Wine no Linux; consulte as limitações no relatório de validação. Não há alegação de teste em uma instalação nativa de Windows.

## Com Python

1. Instale Python 3.12 ou 3.13 de **64 bits** em https://www.python.org/downloads/windows/ . Inclua o Python Launcher ou marque a opção de adicionar Python ao PATH.
2. Extraia o ZIP completo em uma pasta gravável, como Documentos\Editor-PDF. Não execute os arquivos de dentro do ZIP.
3. Dê duplo clique em **iniciar_windows.bat**. Na primeira execução ele cria `.venv` e instala as dependências; esse passo precisa de internet. Depois a inicialização é offline.
4. Se preferir separar os passos, use primeiro **instalar_windows.bat** e depois **iniciar_windows.bat**.

Também é possível arrastar um PDF para `iniciar_windows.bat`, ou usar no terminal:

```bat
py -3 windows_setup.py "C:\Documentos\meu arquivo.pdf"
```

Não exige administrador. Preserve a pasta inteira: `main.py`, `model.py`, `ui.py`, `style.qss` e `ajuda.html` trabalham juntos. Não copie um ambiente `.venv` de Linux para Windows: o iniciador cria o ambiente correto para o sistema de destino.

## Gerar um executável sem exigir Python no computador de destino

Em um Windows com Python instalado, abra **gerar_executavel_windows.bat**. O processo instala PyInstaller, executa os testes e cria `dist\EditorPDF\EditorPDF.exe`, com as bibliotecas e recursos na mesma pasta. Faz ainda um teste de inicialização do executável e gera `dist\EditorPDF-Windows-x64.zip`.

Distribua **a pasta inteira ou o ZIP inteiro**, não apenas o `.exe`. A máquina que recebe essa distribuição não precisa ter Python ou internet. A geração inicial precisa de internet; a execução final não. O aplicativo não tem assinatura de código comercial.

O script PyInstaller usa os mesmos arquivos da versão Linux. As licenças das bibliotecas acompanham seus metadados no pacote. Para redistribuição, preserve os avisos, este projeto e o código-fonte correspondente, conforme AGPL e demais licenças.

## Se não iniciar

- Execute o `.bat` por um terminal para ler o erro.
- Se Python não for encontrado, revise o Launcher/PATH e reabra o terminal.
- Se aparecer falta de `VCRUNTIME140`/`MSVCP140`, instale o Microsoft Visual C++ Redistributable x64 oficial: https://learn.microsoft.com/cpp/windows/latest-supported-vc-redist .
- Use caminho gravável e extraia todos os arquivos do ZIP.
- A instalação offline das dependências é possível com uma pasta `wheels` contendo os wheels Windows de todas as dependências. O iniciador a detecta e usa `--no-index`.

Consulte VALIDACAO.md para distinguir o que foi executado neste ambiente e o que ainda depende de Windows nativo.
