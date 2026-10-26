# Funções comuns e evolução do editor

Pesquisa em 26/10/2026, consultando fontes oficiais. A seleção abaixo considera a utilidade para uso pessoal e a viabilidade com Python, PySide6 e PyMuPDF. As classificações de esforço são estimativas de implementação neste projeto, não promessas dos fornecedores.

## O que foi implementado nesta atualização

| Função | Como usar |
|---|---|
| Inserir página em branco | Botão + Página em branco, escolha de tamanho e posição |
| Importar páginas / juntar PDFs | Importar PDF, escolha do intervalo e posição de inserção |
| Duplicar página | Cópia independente após a página atual |
| Mover página | Escolha da nova posição final |
| Extrair páginas | Exportação de um intervalo para outro PDF, preservando o documento aberto |
| Buscar texto | Ctrl+F, resultados destacados temporariamente e navegação circular |
| Ajuda dentro do aplicativo | Aba Ajuda ou F1; guia disponível sem conexão |

Continuam disponíveis texto, substituição, marca-texto, remoção real de áreas, giro, exclusão, zoom e histórico.

## Outras funções possíveis, ainda não implementadas

| Função | Viabilidade / esforço estimado | Cuidados |
|---|---|---|
| Miniaturas de páginas e organização por arrastar | Alta / médio | Cache e carregamento progressivo para PDFs extensos |
| Inserir imagens PNG/JPEG | Alta / baixo a médio | Proporção, transparência, posicionamento e rotação |
| Comentários, sublinhado e riscado | Alta / médio | Selecionar, editar e excluir anotações existentes |
| Exportar página para PNG e extrair texto | Alta / baixo | Escolha de resolução; texto escaneado não é extraível sem OCR |
| Numeração e marca d’água | Alta / médio | Margens, todas as rotações e prevenção de sobreposição |
| Impressão | Alta / médio | Integração com QtPrintSupport, escala, margens e impressoras locais |
| Recortar margens | Alta / médio | Recorte visual não elimina conteúdo; comunicar essa diferença |
| Editar metadados e marcadores | Alta / médio | Atualizar destinos quando as páginas mudarem |
| Preencher formulários existentes | Possível / médio a alto | Tipos de campos, aparência, cálculos e compatibilidade entre leitores |
| Reduzir tamanho do PDF | Possível / médio | Imagens podem perder qualidade; medir resultado e permitir ajuste |
| OCR offline | Possível / alto | Exige motor e idiomas adicionais, como Tesseract; fora do escopo atual |
| Exportar para Word com layout fiel | Limitada / alto | Conversão complexa e sem garantia de fidelidade; não priorizada |

Login, nuvem, servidor, assinatura digital, colaboração e recursos pagos continuam fora do escopo solicitado.

## Fontes

- Adobe Acrobat — organizar páginas (inserir, substituir, dividir, reordenar, girar e extrair): https://experienceleague.adobe.com/en/docs/document-cloud-learn/acrobat-learning/get-started/create/organize?lang=en
- Adobe Acrobat — mover e copiar páginas: https://helpx.adobe.com/acrobat/desktop/edit-documents/organize-pages/move-pages.html
- PDF24 — catálogo oficial (organização, anotações, números, marcas d’água, formulários, recorte): https://tools.pdf24.org/en/all-tools
- PDF24 — montagem de documentos: https://tools.pdf24.org/en/assemble-pdf
- PyMuPDF — APIs de inserção, cópia e movimentação: https://pymupdf.readthedocs.io/en/latest/document.html
- PyMuPDF — busca, anotações e edição em página: https://pymupdf.readthedocs.io/en/latest/page.html
- PyMuPDF — inclusão de imagens: https://pymupdf.readthedocs.io/en/latest/recipes-images.html
