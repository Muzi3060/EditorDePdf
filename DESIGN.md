# Pesquisa e decisões de interface

Pesquisa realizada em 26/10/2026. Não existe um ranking universal que demonstre qual aparência todas as pessoas preferem. Avaliações de editores misturam preço, funções, desempenho e facilidade de uso; por isso, não tratamos uma nota geral como prova de superioridade visual.

## Referências consultadas

- **G2 — comparativo Acrobat e PDF Expert**: reúne avaliações e destaca relatos sobre facilidade de uso e interface intuitiva. É um sinal qualitativo; os públicos e volumes de avaliações diferem. https://www.g2.com/compare/adobe-acrobat-vs-pdf-expert
- **G2 — seleção de editores**: rankings e análise de avaliações valorizam navegação clara e acesso às ferramentas principais. Não foi usado um número de posição como meta estética. https://learn.g2.com/best-pdf-editor
- **Nielsen Norman Group — efeito estética/usabilidade**: aparência agradável pode elevar a percepção de facilidade; isso não substitui testes de funcionamento nem corrige problemas de usabilidade. https://www.nngroup.com/articles/aesthetic-usability-effect/
- **Microsoft — navegação de aplicativos Windows**: tornar destinos importantes fáceis de encontrar e reduzir a presença de opções secundárias. https://learn.microsoft.com/windows/apps/design/basics/navigation-basics
- **Microsoft — barras de comandos**: agrupar comandos e manter rótulos legíveis. https://learn.microsoft.com/en-ca/windows/apps/design/controls/command-bar

## O que foi aplicado

1. Fundo preto no espaço de leitura e superfícies em azul escuro, respeitando a preferência do usuário. Azul mais vivo reservado para seleção e ação principal.
2. Cabeçalho com arquivo atual, estado de salvamento, Abrir e Salvar cópia. Ações principais ocupam posições estáveis.
3. Ferramentas com ícones vetoriais próprios e nomes em português. Seleção tem fundo e borda, além da cor do texto.
4. Propriedades de fonte e cor aparecem somente ao adicionar texto. Isso reduz opções sem relação com a ferramenta atual.
5. Organização de páginas reunida em um menu identificado, com acesso direto à inserção de página. Evita várias linhas permanentes de botões.
6. Miniaturas para navegar e conferir a sequência. Geradas progressivamente; a área pode ser recolhida arrastando seu divisor.
7. Busca recolhível com contador de resultados; Ctrl+F abre e Esc fecha. Os contornos de resultado continuam temporários.
8. Navegação e zoom em uma barra inferior estável, incluindo Ajustar largura.
9. Tela inicial com uma ação clara para abrir PDF, ajuda sempre acessível, dicas ao passar o mouse, atalhos e foco de teclado visível.
10. Fonte Segoe UI no Windows e DejaVu Sans no Linux, usando controles Qt e dimensionamento de alta densidade do Qt 6.

## Verificação e limites

Capturas do aplicativo real em 1380×920 e 1000×700, incluindo tela inicial, documento e ajuda. Conferência de controles visíveis, hierarquia e legibilidade. Testes de integração das operações existentes e dos novos controles. Não foi realizado estudo com usuários, teste por leitor de tela ou medição formal de preferência. Trata-se de uma aplicação fundamentada nas referências, sem alegar que todos preferirão este visual.
