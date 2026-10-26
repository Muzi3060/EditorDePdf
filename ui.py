"""Interface Qt compartilhada por Linux e Windows; recursos locais, sem fontes remotas."""
from pathlib import Path
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (QWidget, QFrame, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QButtonGroup, QSpinBox, QScrollArea, QTabWidget, QTextBrowser,
    QLineEdit, QMenu, QToolButton, QListWidget, QAbstractItemView, QSplitter,
    QStackedWidget, QGraphicsDropShadowEffect, QSizePolicy, QLayout)

PATHS = {
 'file':'<path d="M6 2h8l4 4v16H6z M14 2v5h5 M9 12h6 M9 16h6"/>',
 'open':'<path d="M3 7h7l2 2h9l-3 11H3z M3 7V4h7l2 3h7v2"/>',
 'save':'<path d="M4 3h14l3 3v15H3V3z M7 3v6h10V3 M7 21v-8h10v8"/>',
 'view':'<path d="M3 12s3-7 9-7 9 7 9 7-3 7-9 7-9-7-9-7z"/><circle cx="12" cy="12" r="3"/>',
 'text':'<path d="M4 6V3h16v3 M12 3v18 M8 21h8"/>',
 'replace':'<path d="M4 4h13 M10 4v11 M6 15h8 M15 14h6l-3-3 M21 14l-3 3 M3 20h13"/>',
 'highlight':'<path d="m9 15 8-12 5 4-9 11z M9 15l4 3-5 3H4z M3 23h17"/>',
 'erase':'<path d="m3 15 10-12 8 7-10 12H9z M8 9l8 7 M10 22h12"/>',
 'pages':'<path d="M8 3h13v16H8z M4 7H2v16h13v-2"/>',
 'plus':'<path d="M12 4v16 M4 12h16"/>',
 'import':'<path d="M14 3h7v18H8v-5 M3 10h12 M10 5l5 5-5 5"/>',
 'copy':'<rect x="8" y="8" width="13" height="13" rx="2"/><path d="M16 5V2H2v14h3"/>',
 'move':'<path d="M12 2v20 M2 12h20 M8 6l4-4 4 4 M8 18l4 4 4-4 M6 8l-4 4 4 4 M18 8l4 4-4 4"/>',
 'extract':'<path d="M12 3H3v18h18v-9 M14 2h8v8 M22 2 10 14"/>',
 'rotate':'<path d="M4 8a9 9 0 1 1 0 9 M4 2v6h6"/>',
 'trash':'<path d="M3 6h18 M8 6V3h8v3 M5 6l1 16h12l1-16 M10 10v8 M14 10v8"/>',
 'undo':'<path d="M8 4 2 10l6 6 M2 10h12a7 7 0 0 1 7 7v4"/>',
 'redo':'<path d="m16 4 6 6-6 6 M22 10H10a7 7 0 0 0-7 7v4"/>',
 'search':'<circle cx="10" cy="10" r="7"/><path d="m15 15 7 7"/>',
 'close':'<path d="m6 6 12 12 M6 18 18 6"/>',
 'left':'<path d="m15 5-7 7 7 7"/>',
 'right':'<path d="m9 5 7 7-7 7"/>',
 'minus':'<path d="M4 12h16"/>',
 'fit':'<path d="M2 8V3h5 M17 3h5v5 M2 16v5h5 M17 21h5v-5 M6 12h12 M9 9l-3 3 3 3 M15 9l3 3-3 3"/>',
 'help':'<circle cx="12" cy="12" r="10"/><path d="M9 8a3 3 0 0 1 6 0c0 3-3 2-3 6 M12 17v1"/>',
 'chevron':'<path d="m6 9 6 6 6-6"/>',
}


def icon(name, color='#aebdd1', size=20):
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24"><g fill="none" stroke="{color}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{PATHS[name]}</g></svg>'
    pix = QPixmap(size * 2, size * 2)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    QSvgRenderer(svg.encode()).render(painter)
    painter.end()
    pix.setDevicePixelRatio(2)
    return QIcon(pix)


def button(layout, text, callback, glyph=None, role=None, tooltip=None):
    btn = QPushButton(text)
    if glyph:
        btn.setIcon(icon(glyph, '#eef5ff' if role == 'primary' else '#aebdd1'))
        btn.setIconSize(QSize(18, 18))
    if role:
        btn.setProperty('role', role)
    btn.setCursor(Qt.PointingHandCursor)
    btn.setToolTip(tooltip or text)
    btn.setAccessibleName(text or tooltip or glyph)
    btn.clicked.connect(callback)
    layout.addWidget(btn)
    return btn


def label(text, name=None):
    item = QLabel(text)
    if name:
        item.setObjectName(name)
    return item


def setup(w, canvas_class):
    w.setMinimumSize(1000, 700)
    w.resize(1380, 920)
    root = QWidget()
    root.setObjectName('root')
    w.setCentralWidget(root)
    outer = QVBoxLayout(root)
    outer.setContentsMargins(0, 0, 0, 0)
    outer.setSpacing(0)
    header = QFrame()
    header.setObjectName('header')
    row = QHBoxLayout(header)
    row.setContentsMargins(22, 14, 22, 14)
    mark = label('PDF', 'mark')
    row.addWidget(mark)
    row.addWidget(label('Editor PDF', 'brand'))
    row.addSpacing(18)
    w.filename = label('Nenhum documento aberto', 'filename')
    w.filename.setMinimumWidth(80)
    w.filename.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
    row.addWidget(w.filename, 1)
    w.state_badge = label('PRONTO', 'badge')
    row.addWidget(w.state_badge)
    row.addSpacing(8)
    button(row, 'Abrir PDF', w.open_pdf, 'open', tooltip='Abrir PDF · Ctrl+O')
    w.save_button = button(row, 'Salvar cópia', w.save, 'save', 'primary', 'Salvar cópia · Ctrl+Shift+S')
    outer.addWidget(header)
    body = QHBoxLayout()
    body.setContentsMargins(0, 0, 0, 0)
    body.setSpacing(0)
    outer.addLayout(body, 1)
    sidebar = QFrame()
    sidebar.setObjectName('sidebar')
    sidebar.setMinimumWidth(192)
    sidebar.setMaximumWidth(212)
    side = QVBoxLayout(sidebar)
    side.setContentsMargins(16, 24, 16, 16)
    side.setSpacing(6)
    side.setSizeConstraint(QLayout.SetMinimumSize)
    side.addWidget(label('FERRAMENTAS', 'section'))
    side.addSpacing(10)
    w.tool_buttons = {}
    group = QButtonGroup(w)
    w.document_controls = []
    for key, title in [('view','Visualizar'),('text','Adicionar texto'),('replace','Substituir texto'),('highlight','Destacar texto'),('erase','Apagar área')]:
        btn = button(side, title, lambda checked=False, k=key: w.select_tool(k), key, 'tool')
        btn.setCheckable(True)
        group.addButton(btn)
        w.tool_buttons[key] = btn
        btn.setChecked(key == 'view')
        w.document_controls.append(btn)
    side.addSpacing(24)
    w.text_options = QFrame()
    w.text_options.setObjectName('properties')
    w.text_options.setMinimumHeight(200)
    options = QVBoxLayout(w.text_options)
    options.setContentsMargins(12, 14, 12, 14)
    options.setSpacing(10)
    options.addWidget(label('FORMATO DO TEXTO', 'section'))
    options.addWidget(label('Tamanho da fonte'))
    w.size = QSpinBox()
    w.size.setRange(5,144)
    w.size.setValue(14)
    w.size.setSuffix(' pt')
    w.size.setAccessibleName('Tamanho do texto em pontos')
    options.addWidget(w.size)
    options.addWidget(label('Cor do texto'))
    w.color_btn = button(options, w.color.name().upper(), w.choose_color)
    side.addWidget(w.text_options)
    side.addStretch()
    side.addWidget(label('PRECISA DE AJUDA?', 'section'))
    help_note = label('Veja exemplos e aprenda\na usar cada ferramenta.', 'muted')
    side.addWidget(help_note)
    side.addSpacing(6)
    button(side, 'Guia de uso', lambda: w.tabs.setCurrentIndex(1), 'help', tooltip='Abrir ajuda · F1')
    sidebar_scroll = QScrollArea()
    sidebar_scroll.setObjectName('sidebarScroll')
    sidebar_scroll.setFixedWidth(212)
    sidebar_scroll.setWidgetResizable(True)
    sidebar_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    sidebar_scroll.setWidget(sidebar)
    body.addWidget(sidebar_scroll)
    w.tabs = QTabWidget()
    w.tabs.setDocumentMode(True)
    body.addWidget(w.tabs, 1)
    editor = QWidget()
    editor.setObjectName('editor')
    main = QVBoxLayout(editor)
    main.setContentsMargins(0,0,0,0)
    main.setSpacing(0)
    w.tabs.addTab(editor, 'Documento')
    help_view = QTextBrowser()
    help_view.setObjectName('help')
    help_view.setOpenExternalLinks(False)
    help_view.setHtml(Path(__file__).with_name('ajuda.html').read_text(encoding='utf-8'))
    w.tabs.addTab(help_view, 'Ajuda')
    w.page_actions = []
    pages_menu = w.menuBar().addMenu('Páginas')
    for title, callback, glyph in [('Adicionar página em branco…',w.add_blank,'plus'),('Importar páginas de outro PDF…',w.import_pages,'import'),('Duplicar página atual',w.duplicate_page,'copy'),('Mover página atual…',w.move_page,'move'),('Extrair páginas para outro PDF…',w.extract_pages,'extract'),('Girar página 90°',w.rotate,'rotate'),('Excluir página atual',w.delete,'trash')]:
        action = pages_menu.addAction(icon(glyph), title)
        action.triggered.connect(callback)
        w.page_actions.append(action)
    w.menuBar().addMenu('Ajuda').addAction('Como usar o aplicativo', lambda: w.tabs.setCurrentIndex(1))
    commands = QFrame()
    commands.setObjectName('commands')
    toolbar = QHBoxLayout(commands)
    toolbar.setContentsMargins(18,10,18,10)
    toolbar.setSpacing(8)
    w.undo = button(toolbar, '', lambda: w.travel(-1), 'undo', 'icon', 'Desfazer · Ctrl+Z')
    w.redo = button(toolbar, '', lambda: w.travel(1), 'redo', 'icon', 'Refazer · Ctrl+Y')
    separator = QFrame(); separator.setFrameShape(QFrame.VLine); separator.setObjectName('separator');toolbar.addWidget(separator)
    w.document_controls.append(button(toolbar, 'Adicionar página', w.add_blank, 'plus'))
    organize = QToolButton()
    organize.setText('Organizar páginas')
    organize.setIcon(icon('pages'))
    organize.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
    organize.setPopupMode(QToolButton.InstantPopup)
    organize.setMenu(pages_menu)
    organize.setToolTip('Importar, duplicar, mover, extrair, girar ou excluir páginas')
    toolbar.addWidget(organize)
    w.document_controls.append(organize)
    toolbar.addStretch()
    w.search_toggle = button(toolbar, 'Buscar', w.toggle_search, 'search', tooltip='Buscar texto · Ctrl+F')
    w.document_controls.append(w.search_toggle)
    main.addWidget(commands)
    w.search_panel = QFrame()
    w.search_panel.setObjectName('searchPanel')
    search = QHBoxLayout(w.search_panel)
    search.setContentsMargins(18,8,18,8)
    w.search_input = QLineEdit()
    w.search_input.setPlaceholderText('Digite uma palavra ou expressão…')
    w.search_input.setAccessibleName('Buscar texto no documento')
    w.search_input.returnPressed.connect(w.find_next)
    search.addWidget(w.search_input,1)
    w.search_count = label('', 'muted');search.addWidget(w.search_count)
    button(search,'Próxima',w.find_next,'right')
    button(search,'',w.hide_search,'close','icon','Fechar e limpar busca · Esc')
    main.addWidget(w.search_panel)
    w.search_panel.hide()
    w.search_query='';w.search_hits=[];w.search_cursor=-1
    w.instruction = label('', 'instruction')
    w.instruction.setWordWrap(True)
    main.addWidget(w.instruction)
    w.workspace = QStackedWidget()
    empty = QWidget(); empty.setObjectName('empty')
    empty_layout = QVBoxLayout(empty);empty_layout.addStretch()
    empty_layout.addWidget(label('PDF', 'emptyMark'),0,Qt.AlignHCenter)
    empty_layout.addSpacing(22)
    empty_layout.addWidget(label('Abra seu PDF para começar.', 'emptyTitle'),0,Qt.AlignHCenter)
    empty_layout.addWidget(label('Abra um documento para editar texto, destacar\ninformações e organizar suas páginas.', 'emptySubtitle'),0,Qt.AlignHCenter)
    empty_layout.addSpacing(20)
    empty_buttons=QHBoxLayout();empty_buttons.addStretch()
    button(empty_buttons,'Escolher um PDF',w.open_pdf,'open','primary')
    empty_buttons.addStretch();empty_layout.addLayout(empty_buttons)
    empty_layout.addStretch()
    w.workspace.addWidget(empty)
    split = QSplitter(Qt.Horizontal)
    rail = QFrame();rail.setObjectName('rail')
    rail_layout=QVBoxLayout(rail);rail_layout.setContentsMargins(8,16,8,8)
    rail_layout.addWidget(label('PÁGINAS','section'))
    w.thumbnails=QListWidget()
    w.thumbnails.setObjectName('thumbnails')
    w.thumbnails.setIconSize(QSize(80,110))
    w.thumbnails.setSpacing(8)
    w.thumbnails.setMovement(QListWidget.Static)
    w.thumbnails.setViewMode(QListWidget.IconMode)
    w.thumbnails.setResizeMode(QListWidget.Adjust)
    w.thumbnails.setFlow(QListWidget.TopToBottom)
    w.thumbnails.setWrapping(False)
    w.thumbnails.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    w.thumbnails.setEditTriggers(QAbstractItemView.NoEditTriggers)
    w.thumbnails.setAccessibleName('Miniaturas das páginas')
    w.thumbnails.currentRowChanged.connect(w.thumbnail_go)
    rail_layout.addWidget(w.thumbnails)
    rail.setMinimumWidth(126);rail.setMaximumWidth(200)
    split.addWidget(rail)
    w.scroll=QScrollArea();w.scroll.setObjectName('pageViewport')
    w.scroll.setWidgetResizable(False);w.scroll.setAlignment(Qt.AlignCenter)
    w.canvas=canvas_class();w.canvas.setObjectName('paper')
    w.scroll.setWidget(w.canvas)
    shadow=QGraphicsDropShadowEffect(w.canvas);shadow.setBlurRadius(32);shadow.setOffset(0,6);shadow.setColor(QColor(0,0,0,120));w.canvas.setGraphicsEffect(shadow)
    w.canvas.gesture.connect(w.gesture)
    split.addWidget(w.scroll);split.setSizes([140,950]);split.setCollapsible(0,True);split.setCollapsible(1,False)
    w.workspace.addWidget(split)
    main.addWidget(w.workspace,1)
    footer=QFrame();footer.setObjectName('footer')
    nav=QHBoxLayout(footer);nav.setContentsMargins(18,10,18,10)
    w.previous=button(nav,'',lambda:w.navigate(-1),'left','icon','Página anterior')
    nav.addWidget(label('Página','muted'))
    w.number=QSpinBox();w.number.setRange(1,1);w.number.setFixedWidth(75);w.number.setAccessibleName('Página atual');w.number.valueChanged.connect(w.go);nav.addWidget(w.number)
    w.total=label('de 0','muted');nav.addWidget(w.total)
    w.next=button(nav,'',lambda:w.navigate(1),'right','icon','Próxima página')
    nav.addStretch()
    w.document_controls.append(button(nav,'Ajustar largura',w.fit_width,'fit'))
    w.document_controls.append(button(nav,'',lambda:w.change_zoom(1/1.2),'minus','icon','Diminuir zoom'))
    w.zoom_label=label('100%','zoom');nav.addWidget(w.zoom_label)
    w.document_controls.append(button(nav,'',lambda:w.change_zoom(1.2),'plus','icon','Aumentar zoom'))
    main.addWidget(footer)
    w.thumb_key=None;w.thumb_pending=0
    from PySide6.QtCore import QTimer
    w.thumb_timer=QTimer(w);w.thumb_timer.setInterval(15);w.thumb_timer.timeout.connect(w.render_thumbnail)
    w.setStyleSheet(Path(__file__).with_name('style.qss').read_text(encoding='utf-8'))
