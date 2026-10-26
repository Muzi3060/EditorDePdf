"""Resizable, wrapping text editor with non-destructive PDF preview."""
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QTextOption, QImage, QPixmap, QPalette, QColor
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPlainTextEdit,
    QDialogButtonBox, QCheckBox, QDoubleSpinBox, QScrollArea, QApplication, QWidget, QLayout)
import pymupdf as fitz
from text_editing import (selection_text, dominant_span, font_candidates,
    prepare_replacement, apply_replacement, prepare_addition, write_plan)


class GrowingTextEdit(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        option = self.document().defaultTextOption()
        option.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        self.document().setDefaultTextOption(option)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.textChanged.connect(self.schedule_height)
        self.setMinimumHeight(140)
        self.setMaximumHeight(300)

    def schedule_height(self):
        QTimer.singleShot(0, self.update_height)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.schedule_height()

    def update_height(self):
        block = self.document().begin()
        lines = 0
        while block.isValid():
            lines += max(1, block.layout().lineCount())
            block = block.next()
        height = max(140, min(300, lines * self.fontMetrics().lineSpacing() + 30))
        if self.minimumHeight() != height:
            self.setMinimumHeight(height)
            self.setMaximumHeight(height)


class TextEditDialog(QDialog):
    def __init__(self, parent, page, selection=None, point=None, size=14, color=(0, 0, 0)):
        super().__init__(parent)
        palette = self.palette()
        for role, color in ((QPalette.Window, '#101925'), (QPalette.Base, '#0a111c'),
                            (QPalette.Text, '#e0e7f1'), (QPalette.WindowText, '#e0e7f1'),
                            (QPalette.Button, '#142237'), (QPalette.ButtonText, '#e0e7f1'),
                            (QPalette.Highlight, '#2463df'), (QPalette.HighlightedText, '#ffffff')):
            palette.setColor(role, QColor(color))
        self.setPalette(palette)
        self.page = page
        self.selection = selection
        self.point = point
        self.color = color
        self.plan = None
        self.initial_text = selection_text(selection) if selection else ''
        self.candidates = font_candidates(page, dominant_span(selection)) if selection else None
        self.setWindowTitle('Editar texto selecionado' if selection else 'Adicionar texto')
        self.resize(920, 740)
        self.setMinimumWidth(640)
        screen = QApplication.primaryScreen()
        if screen:
            self.setMaximumHeight(max(540, screen.availableGeometry().height() - 50))
        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 14, 18, 14)
        body = QWidget()
        body.setObjectName('textDialogBody')
        layout = QVBoxLayout(body)
        layout.setSizeConstraint(QLayout.SetMinimumSize)
        body_scroll = QScrollArea()
        body_scroll.setObjectName('textDialogScroll')
        body_scroll.setWidgetResizable(True)
        body_scroll.setFrameShape(QScrollArea.NoFrame)
        body_scroll.setWidget(body)
        outer.addWidget(body_scroll, 1)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(10)
        title = QLabel('Edite todo o trecho selecionado' if selection else 'Escreva o texto que deseja adicionar')
        title.setStyleSheet('font-size:20px;font-weight:600;color:#cfe4ff;')
        layout.addWidget(title)
        hint = QLabel('O texto quebra automaticamente na caixa. Enter cria uma nova linha. Confira a prévia antes de aplicar.')
        hint.setWordWrap(True)
        layout.addWidget(hint)
        self.editor = GrowingTextEdit(self)
        self.editor.setAccessibleName('Texto para substituir' if selection else 'Texto para adicionar')
        self.editor.setPlainText(self.initial_text)
        layout.addWidget(self.editor)
        options = QHBoxLayout()
        options.addWidget(QLabel('Tamanho desejado'))
        self.font_size = QDoubleSpinBox()
        self.font_size.setRange(4, 144)
        self.font_size.setDecimals(2)
        self.font_size.setSuffix(' pt')
        self.font_size.setValue(dominant_span(selection)['size'] if selection else size)
        self.initial_size = self.font_size.value()
        options.addWidget(self.font_size)
        self.auto_fit = QCheckBox('Reduzir tamanho para caber')
        self.auto_fit.setChecked(bool(selection))
        self.auto_fit.setVisible(bool(selection))
        options.addWidget(self.auto_fit)
        options.addStretch()
        self.counter = QLabel()
        options.addWidget(self.counter)
        layout.addLayout(options)
        self.status = QLabel()
        self.status.setWordWrap(True)
        self.status.setMinimumHeight(44)
        layout.addWidget(self.status)
        layout.addWidget(QLabel('PRÉVIA NA PÁGINA · nada será alterado até você aplicar'))
        self.preview = QLabel()
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview_scroll = QScrollArea()
        self.preview_scroll.setObjectName('textPreview')
        self.preview_scroll.setWidgetResizable(False)
        self.preview_scroll.setAlignment(Qt.AlignCenter)
        self.preview_scroll.setWidget(self.preview)
        self.preview_scroll.setMinimumHeight(145)
        layout.addWidget(self.preview_scroll, 1)
        note = QLabel('A edição ocupa as linhas selecionadas e não empurra o restante da página. Em trechos com vários estilos, será usado o estilo predominante.' if selection else 'O clique marca o início da primeira linha. Textos longos continuam nas linhas seguintes, dentro da página.')
        note.setWordWrap(True)
        note.setStyleSheet('color:#9eacc0;font-size:12px;')
        layout.addWidget(note)
        self.buttons = QDialogButtonBox()
        self.cancel_button = self.buttons.addButton('Cancelar', QDialogButtonBox.RejectRole)
        self.apply_button = self.buttons.addButton('Aplicar alteração' if selection else 'Adicionar texto', QDialogButtonBox.AcceptRole)
        self.apply_button.setProperty('role', 'primary')
        self.buttons.rejected.connect(self.reject)
        self.buttons.accepted.connect(self.accept_validated)
        outer.addWidget(self.buttons)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(250)
        self.timer.timeout.connect(self.update_preview)
        self.editor.textChanged.connect(self.changed)
        self.font_size.valueChanged.connect(self.changed)
        self.auto_fit.toggled.connect(self.changed)
        self.update_preview()

    def changed(self, *args):
        self.plan = None
        self.apply_button.setEnabled(False)
        self.status.setText('Atualizando prévia…')
        self.timer.start()

    def prepare(self):
        text = self.editor.toPlainText()
        if self.selection:
            return prepare_replacement(self.page, self.selection, text,
                self.font_size.value(), self.auto_fit.isChecked(), self.candidates)
        return prepare_addition(self.page, self.point, text, self.font_size.value(), self.color)

    def update_preview(self):
        self.timer.stop()
        text = self.editor.toPlainText()
        self.counter.setText(f'{len(text)} caracteres')
        try:
            plan = self.prepare()
            # Preview is an isolated single-page copy, never the active document.
            with fitz.open() as scratch:
                scratch.insert_pdf(self.page.parent, from_page=self.page.number, to_page=self.page.number)
                page = scratch[0]
                if self.selection:
                    apply_replacement(page, self.selection, plan)
                    clip = fitz.Rect()
                    for _, chars in self.selection:
                        for char, _ in chars:
                            clip |= fitz.Rect(char['bbox'])
                    clip = fitz.Rect(clip.x0 - 12, clip.y0 - 12, clip.x1 + 12, clip.y1 + 12)
                else:
                    write_plan(page, plan)
                    clip = fitz.Rect(self.point.x - 12, self.point.y - plan.size * 1.5, page.cropbox.width, self.point.y + max(4, len(plan.lines)) * plan.size * 1.5)
                clip = clip * page.rotation_matrix & page.rect
                scale = max(.4, min(2, 800 / max(clip.width, 1)))
                pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=clip, alpha=False)
                image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888).copy()
                self.preview.setPixmap(QPixmap.fromImage(image))
                self.preview.setFixedSize(pix.width, pix.height)
            self.plan = plan
            status = f'Fonte: {plan.font_label} · {plan.size:g} pt · {len(plan.lines)} linhas.'
            if plan.warnings:
                status += '\n' + ' '.join(plan.warnings)
            self.status.setStyleSheet('color:#a5c9f6;')
            self.status.setText(status)
            self.apply_button.setEnabled(self.has_changes())
        except Exception as exc:
            self.plan = None
            self.preview.clear()
            self.preview.setFixedSize(1, 1)
            self.apply_button.setEnabled(False)
            self.status.setStyleSheet('color:#ffbf83;')
            self.status.setText(str(exc))

    def has_changes(self):
        return self.editor.toPlainText() != self.initial_text or (bool(self.selection) and abs(self.font_size.value() - self.initial_size) > .01)

    def accept_validated(self):
        self.update_preview()
        if self.plan is not None and self.has_changes():
            self.accept()
