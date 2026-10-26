# Validação desta entrega

## Ambientes

- Linux x86_64, Python 3.14.8, PySide6 6.10.2, PyMuPDF 1.27.2.3.
- Binários Windows x64: Python 3.12.10 oficial (embeddable), mesmas versões de PySide6/PyMuPDF, executados por Wine 11.20 no Linux. Wine se identifica como Windows 10; isso não equivale a teste em Windows nativo.
- Empacotamento Windows com PyInstaller 6.22.0 e hooks-contrib 2026.9, usando o Python Windows no Wine. Arquivo resultante identificado como PE32+ x86-64 GUI.

## Testes de integração

Comando no Linux: `QT_QPA_PLATFORM=offscreen python -m unittest discover -v`.
Os mesmos onze testes foram executados com Python e bibliotecas Windows pelo Wine. **Resultado na versão 0.2.0: 11 testes aprovados em cada ambiente**, incluindo o caso opcional com o PDF fornecido localmente. Sem `EDITOR_PDF_REGRESSION_FILE`, esse caso é ignorado e os demais dez são executados.

Cobertura:

1. PDF real com rotações 0°, 90°, 180° e 270°, quatro níveis de zoom e conversão de coordenadas. Adição e substituição de texto com remoção do original, destaque, remoção vetorial, giro, exclusão, desfazer/refazer, preservação do arquivo original e salvamento/reabertura. Texto, posição, anotações e conteúdo removido conferidos no PDF reaberto.
2. Operações reais da janela com respostas dos diálogos simuladas: página em branco, importação de intervalo, duplicação independente, movimentação para início/fim, extração sem modificar o documento aberto e busca circular. Ordem e conteúdo conferidos após salvar e reabrir.
3. Painel de tamanho/cor com altura mínima e acesso por rolagem em janela compacta; arquivo com espaços e acentos no nome, tela inicial, habilitação de comandos, geração das miniaturas, navegação por miniatura, painel de busca, contador, propriedades contextuais e ajuste de largura. Renderização da janela em 1000×700 e 1380×920.

4. Substituição de várias linhas com fonte incorporada em quatro rotações; posições das linhas conferidas após reabrir; vizinhos não selecionados preservados. Testes de seleção parcial, duas colunas, exclusão de todo o trecho, fonte alternativa, ajuste de tamanho e recusa segura de texto que não caiba.
5. Caixa de texto com quebra automática e expansão vertical, prévia isolada sem modificar o documento aberto, botões de aplicação habilitados apenas para texto válido e rolagem durante seleção por arraste. Adição de texto com várias linhas.
6. Regressão com o PDF enviado pelo usuário: seis linhas selecionadas na página de teste, fonte CFF Sabon reutilizada a 9 pt, texto editado persistido após salvar/reabrir, texto externo e bytes dos fluxos de imagem preservados. No Linux, comparação independente com Poppler da região fora da edição: limite de erro médio de 1 nível por canal (0–255) e menos de 1% dos canais com diferença acima de 20, admitindo pequenas diferenças de antialiasing nas bordas. As renderizações completas antes/depois foram inspecionadas visualmente. O arquivo de entrada permaneceu intacto e não é distribuído no repositório ou na Release.

## Executável e interface

O modo `--smoke-test` do executável Windows foi executado por Wine, sem usar o Python externo. Ele abre o exemplo incluído no pacote, monta a janela e a aba de ajuda, renderiza a página e uma miniatura e verifica os controles, além de abrir a nova caixa de edição e gerar uma prévia de várias linhas. Resultado: código de saída 0.

O mesmo teste de inicialização foi executado no código-fonte Linux. Capturas `interface.png`, `inicio.png`, `ajuda.png` e `edicao-texto.png` são da interface real Qt renderizada em modo offscreen no Linux. Foram inspecionadas visualmente, assim como uma captura em 1000×700. Não são imagens conceituais.

O PDF de integração é criado em pasta temporária. `exemplo.pdf` é um arquivo separado para inspeção manual. Avisos do driver gráfico do Wine não impediram os testes offscreen.

## O que ainda não foi validado

- Instalação e uso em Windows 10/11 nativo, inclusive os scripts `.bat`, permissões/antivírus/SmartScreen e integração com explorador de arquivos.
- Interação física com mouse/teclado e diálogos nativos de arquivo, cor, senha e confirmação de fechamento em sessão gráfica real.
- Uso interativo em leitores de terceiros: a renderização independente foi verificada com Poppler no Linux, além de PyMuPDF; não foi feita inspeção manual em Acrobat/Edge.
- PDFs de terceiros com fontes exóticas, cropboxes incomuns, formulários, camadas, arquivos danificados ou proteção por senha.
- Recorte de pixels em imagens escaneadas: o código usa a API de redação real do PyMuPDF; o teste cobre remoção de texto e vetores.
- Estudo com usuários, leitor de tela e avaliação formal de acessibilidade ou preferência estética.

Qt 6 fornece suporte a telas de alta densidade, mas escalas de 125%, 150% e múltiplos monitores em Windows nativo ainda não foram exercitadas. As verificações offscreen não confirmam os plugins gráficos de cada computador de destino.
