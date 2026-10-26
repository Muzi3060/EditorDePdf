# Editor PDF

Editor desktop local para Linux e Windows 10/11 x64, em Python, PySide6 e PyMuPDF. Tema preto com destaques em azul. A aba Ajuda (F1) explica o uso de cada ferramenta com exemplos. Não usa servidor, contas, telemetria ou internet durante o uso.

## Windows: iniciar por duplo clique

No pacote **EditorPDF-Windows-x64.zip**, extraia tudo e abra `EditorPDF.exe`. Mantenha a pasta `_internal` ao lado do executável. Essa distribuição inclui Python e bibliotecas, e funciona sem instalação de Python ou conexão.

No pacote de código-fonte, instale Python 3.12/3.13 x64 e abra `iniciar_windows.bat`; ele prepara as dependências na primeira execução. Instruções e geração do executável em `WINDOWS.md`.

## Interface atualizada

Miniaturas navegáveis, ícones vetoriais próprios, propriedades de texto contextuais, menu Organizar páginas, busca recolhível (Ctrl+F / Esc), contador de resultados, estado de salvamento, ajuste de largura e tela inicial. A pesquisa e as razões de cada decisão estão em `DESIGN.md`; as referências não substituem testes com usuários.

## Linux: instalar e iniciar

Requer Python 3.10 a 3.14 (validado com Python 3.14 em Linux x86_64). No terminal, dentro desta pasta:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

Também aceita `python main.py exemplo.pdf`. A instalação inicial exige internet; depois o programa funciona offline. Para instalação offline em outra máquina compatível, baixe antes os wheels com `pip download -r requirements.txt -d wheels` e instale com `pip install --no-index --find-links=wheels -r requirements.txt`.

Em distribuições Linux que não tragam as bibliotecas de desktop Qt, instale pelo gerenciador da distribuição os componentes de xcb, xkbcommon e OpenGL. Por exemplo, no Ubuntu: `sudo apt install libxcb-cursor0 libxkbcommon-x11-0 libegl1`. Use uma sessão gráfica para abrir a janela.

## Novidades: organizar páginas, buscar e consultar ajuda

- **Adicionar página**: A4 retrato/paisagem ou tamanho visual da página atual; escolha a posição.
- **Organizar páginas → Importar páginas de outro PDF**: escolha um intervalo e a posição. Para juntar PDFs, importe na última posição.
- **Duplicar**: cópia independente após a página atual.
- **Mover**: informe a posição final desejada.
- **Extrair páginas**: salve um intervalo em outro PDF sem alterar o aberto.
- **Busca**: Ctrl+F, digite o texto e pressione Enter; avance com Buscar próxima. O contorno azul é temporário e não é salvo.
- **Ajuda**: aba Ajuda, menu Ajuda ou F1; funciona offline. Os arquivos `ui.py`, `style.qss`, `app.svg` e `ajuda.html` devem acompanhar `main.py`.

Veja `PESQUISA.md` para as fontes consultadas, funções incluídas e avaliação de futuras melhorias. Importação não transporta marcadores do arquivo de origem e pode omitir links para páginas fora do intervalo.

## Uso

- **Abrir PDF**: permite informar senha quando necessária. Navegue com Anterior/Próxima ou o número da página e ajuste o zoom.
- **Adicionar texto**: escolha tamanho e cor na lateral e clique na página. O ponto é o início da linha de base do texto. Aceita uma linha na fonte Helvetica.
- **Substituir texto**: arraste sobre caracteres de uma única linha horizontal. A seleção considera o centro de cada caractere; o diálogo mostra exatamente o texto selecionado. O conteúdo original é removido por redação real e o novo entra na mesma origem, com tamanho e cor inicial. Usa Helvetica regular, negrito ou itálico como aproximação. Sempre pede ciência dessa diferença. Recusa texto que não caiba na largura do trecho ou caracteres não suportados.
- **Destacar texto**: arraste sobre palavras; cria anotações amarelas sobre os caracteres selecionados.
- **Apagar área**: arraste e confirme. Usa redação real, removendo texto, pixels de imagens e desenhos que cruzem a área. Um desenho vetorial pode ser eliminado por inteiro se tocar a seleção. Não é um retângulo branco sobreposto.
- **Girar 90° / Excluir página**: operam na página atual; o documento mantém pelo menos uma página.
- **Desfazer / Refazer**: histórico de estados completos em memória, inclusive para exclusão e redação. Ctrl+Z / Ctrl+Y.
- **Salvar cópia**: Ctrl+Shift+S. O arquivo originalmente aberto nunca é sobrescrito; use outro nome. Para continuar, a cópia salva não precisa ser reaberta. Fechar ou abrir outro arquivo com alterações pede salvar, descartar ou cancelar.

## Limitações

PDF não é um documento Word. Não há refluxo de parágrafos, edição livre de fontes ou OCR. Páginas escaneadas podem receber texto e apagamentos, mas destacar/substituir exige texto extraível. A barra inferior avisa quando a página não tem texto extraível. Fontes incorporadas, ligaduras, textos verticais/inclinados e estilos mistos podem impedir uma substituição fiel; prefira trechos curtos. Texto adicionado fica alinhado às coordenadas originais da página; em página rotacionada, acompanha a orientação do conteúdo original.

Redações removem o conteúdo visual selecionado e o salvamento reescreve o PDF com coleta de objetos não usados. Não é uma ferramenta de sanitização completa: metadados, anexos, campos, camadas ou anotações preexistentes podem guardar informações fora do conteúdo tratado. Não edita nem remove anotações preexistentes por seleção de área. PDFs complexos devem ser conferidos após salvar. Cópias de PDFs protegidos são salvas sem senha. O histórico guarda o conteúdo anterior em RAM enquanto a sessão existir e pode consumir bastante memória em PDFs grandes; renderização e operações são síncronas e podem pausar a janela. Histórico não persiste após fechar.

## Verificação

```bash
QT_QPA_PLATFORM=offscreen python -m unittest -v test_editor.py
```

O teste cria um PDF real com páginas em 0°, 90°, 180° e 270°, verifica conversão das posições em quatro níveis de zoom, adição, substituição com remoção do original, destaque, remoção vetorial, giro, exclusão, desfazer/refazer e salvamento/reabertura. Confere texto e coordenadas persistidos, anotações e preservação do arquivo original. `exemplo.pdf` é fornecido para inspeção manual.

A validação offscreen não substitui interação física com mouse/diálogos nem abertura em leitor de terceiros; consulte VALIDACAO.md para o resultado desta entrega.

## Licenças das dependências

Verificado em 26/10/2026 nas fontes oficiais:

- **PySide6 / Qt for Python**: edição comunitária LGPLv3/GPLv3; alternativa comercial. Este aplicativo utiliza QtCore, QtGui e QtWidgets por ligação dinâmica, sem modificar Qt. Documentação: https://doc.qt.io/qtforpython-6/ e https://doc.qt.io/qt-6/licensing.html . Shiboken6 e pacotes Qt são dependências transitivas; preserve seus avisos e licenças se redistribuir.
- **PyMuPDF / MuPDF**: licença aberta GNU AGPLv3, com alternativa comercial. Usamos a edição aberta, sem recursos pagos. Fontes: https://pymupdf.readthedocs.io/en/latest/about.html e https://pymupdf.io/licensing . A redistribuição do conjunto requer cumprir as obrigações aplicáveis da AGPL, incluindo disponibilização do código correspondente; uso pessoal local não exige assinatura comercial.
- **Python**: licença PSF, https://docs.python.org/3/license.html .

O código original deste projeto é oferecido sob AGPL-3.0-or-later para compatibilidade com PyMuPDF. Texto da licença: https://www.gnu.org/licenses/agpl-3.0.html . Os termos próprios das dependências continuam aplicáveis.


Os textos completos AGPL, LGPL, GPL e licença Python acompanham esta entrega em `LICENSE.txt` e `third_party_licenses/`. Ícones da interface e do aplicativo foram criados no código do projeto, sem biblioteca de ícones externa. PyInstaller é usado apenas para empacotar; sua licença GPL com exceção do bootloader permite distribuir aplicações sob seus próprios termos: https://pyinstaller.org/en/stable/license.html .
