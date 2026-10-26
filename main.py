import sys
import traceback
from pathlib import Path
import pymupdf as fitz
from PySide6.QtCore import Qt, QRect, Signal, QTimer, QPoint
from PySide6.QtGui import QColor, QImage, QPixmap, QPainter, QPen, QShortcut, QKeySequence, QCursor
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QScrollArea, QFileDialog, QMessageBox, QInputDialog,
    QColorDialog, QSpinBox, QButtonGroup, QFrame, QTabWidget, QTextBrowser, QLineEdit, QDialog)
from model import Document, selected_chars, erase, replace
from text_dialog import TextEditDialog
from text_editing import apply_replacement, write_plan


class Canvas(QLabel):
    gesture = Signal(object, object)

    def __init__(self):
        super().__init__()
        self.start = self.end = None
        self.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.setCursor(Qt.CrossCursor)
        self.drag_scroll = QTimer(self)
        self.drag_scroll.setInterval(35)
        self.drag_scroll.timeout.connect(self.scroll_selection)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.pixmap() and not self.pixmap().isNull():
            self.start = self.end = event.position().toPoint()
            self.drag_scroll.start()

    def mouseMoveEvent(self, event):
        if self.start is not None:
            self.end = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event):
        if self.start is not None:
            self.drag_scroll.stop()
            start = self.start
            self.start = self.end = None
            self.update()
            self.gesture.emit(start, event.position().toPoint())

    def scroll_selection(self):
        if self.start is None:
            self.drag_scroll.stop()
            return
        owner = self.parentWidget()
        while owner is not None and not isinstance(owner, QScrollArea):
            owner = owner.parentWidget()
        if owner is None:
            return
        cursor = owner.viewport().mapFromGlobal(QCursor.pos())
        for position, extent, bar in ((cursor.y(), owner.viewport().height(), owner.verticalScrollBar()),
                                      (cursor.x(), owner.viewport().width(), owner.horizontalScrollBar())):
            delta = -18 if position < 30 else 18 if position > extent - 30 else 0
            if delta:
                bar.setValue(bar.value() + delta)
        self.end = self.mapFromGlobal(QCursor.pos())
        self.end.setX(max(0, min(self.width() - 1, self.end.x())))
        self.end.setY(max(0, min(self.height() - 1, self.end.y())))
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.start is not None:
            painter = QPainter(self)
            painter.setPen(QPen(QColor('#70b6ff'), 2))
            painter.setBrush(QColor(60, 140, 255, 45))
            painter.drawRect(QRect(self.start, self.end).normalized())


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.model = Document()
        self.page = 0
        self.zoom = 1.0
        self.tool = 'view'
        self.color = QColor('#182033')
        self.setWindowTitle('Editor PDF')
        from ui import setup
        setup(self, Canvas)
        self.statusBar().showMessage('Pronto para abrir um documento')
        self.select_tool('view')
        for key, callback in [('Ctrl+F', self.show_search), ('Escape', self.hide_search), ('F1', lambda: self.tabs.setCurrentIndex(1)), ('Ctrl+O', self.open_pdf), ('Ctrl+Shift+S', self.save), ('Ctrl+Z', lambda: self.travel(-1)), ('Ctrl+Y', lambda: self.travel(1))]:
            QShortcut(QKeySequence(key), self, activated=callback)
        self.refresh()

    def show_search(self):
        self.tabs.setCurrentIndex(0)
        self.search_panel.show()
        self.search_input.setFocus()
        self.search_input.selectAll()

    def hide_search(self):
        self.search_panel.hide()
        self.clear_search()

    def toggle_search(self):
        if self.search_panel.isHidden():
            self.show_search()
        else:
            self.hide_search()

    def fit_width(self):
        if self.model.doc is not None:
            self.zoom = max(.25, min(4, (self.scroll.viewport().width() - 56) / self.model.doc[self.page].rect.width))
            self.safe_refresh()

    def thumbnail_go(self, index):
        if self.model.doc is not None and 0 <= index < len(self.model.doc) and index != self.page:
            self.page = index
            self.safe_refresh()

    def update_thumbnails(self):
        from PySide6.QtWidgets import QListWidgetItem
        from PySide6.QtCore import QSize
        key = (id(self.model.doc), self.model.index)
        self.thumbnails.blockSignals(True)
        try:
            if key != self.thumb_key:
                self.thumb_timer.stop()
                self.thumbnails.clear()
                for i in range(len(self.model.doc)):
                    item = QListWidgetItem(str(i + 1))
                    item.setSizeHint(QSize(100, 146))
                    item.setToolTip(f'Ir para a página {i + 1}')
                    self.thumbnails.addItem(item)
                self.thumb_key = key
                self.thumb_pending = 0
                self.thumb_timer.start()
            self.thumbnails.setCurrentRow(self.page)
        finally:
            self.thumbnails.blockSignals(False)

    def render_thumbnail(self):
        try:
            if self.model.doc is None or self.thumb_pending >= len(self.model.doc):
                self.thumb_timer.stop()
                return
            from PySide6.QtGui import QIcon
            page = self.model.doc[self.thumb_pending]
            scale = min(80 / page.rect.width, 110 / page.rect.height)
            pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
            image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888).copy()
            self.thumbnails.item(self.thumb_pending).setIcon(QIcon(QPixmap.fromImage(image)))
            self.thumb_pending += 1
        except Exception:
            # A broken thumbnail must not prevent opening the page itself.
            self.thumb_timer.stop()

    def button(self, layout, text, callback):
        btn = QPushButton(text)
        btn.clicked.connect(callback)
        layout.addWidget(btn)
        return btn

    def error(self, exc):
        QMessageBox.warning(self, 'Não foi possível concluir', str(exc))

    def confirm_dirty(self):
        if not self.model.dirty:
            return True
        choice = QMessageBox.question(self, 'Alterações não salvas', 'Deseja salvar uma cópia antes de continuar?', QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel, QMessageBox.Save)
        if choice == QMessageBox.Save:
            return self.save()
        return choice == QMessageBox.Discard

    def open_pdf(self):
        if not self.confirm_dirty():
            return
        path, _ = QFileDialog.getOpenFileName(self, 'Abrir PDF', '', 'PDF (*.pdf)')
        if not path:
            return
        try:
            probe = fitz.open(path)
            encrypted = probe.needs_pass
            probe.close()
            password = ''
            if encrypted:
                from PySide6.QtWidgets import QLineEdit
                password, ok = QInputDialog.getText(self, 'PDF protegido', 'Senha:', QLineEdit.Password)
                if not ok:
                    return
            self.model.open(path, password)
            self.page = 0
            self.clear_search()
            self.tabs.setCurrentIndex(0)
            self.refresh()
        except Exception as exc:
            self.error(exc)

    def save(self):
        if not self.model.doc:
            return False
        path, _ = QFileDialog.getSaveFileName(self, 'Salvar cópia editada', str(self.model.path.with_name(self.model.path.stem + '_editado.pdf')), 'PDF (*.pdf)')
        if not path:
            return False
        if not path.lower().endswith('.pdf'):
            path += '.pdf'
        try:
            self.model.save(path)
            self.refresh()
            self.statusBar().showMessage('Cópia salva: ' + path)
            return True
        except Exception as exc:
            self.error(exc)
            return False

    def select_tool(self, tool):
        self.tool = tool
        self.text_options.setVisible(tool == 'text')
        self.canvas.setCursor(Qt.ArrowCursor if tool == 'view' else Qt.CrossCursor)
        self.instruction.setText({'view':'Navegue pelas páginas e ajuste o zoom para inspecionar o documento.', 'text':'Clique para adicionar texto. A caixa aceita várias linhas e mostra uma prévia antes de aplicar.', 'replace':'Arraste sobre uma ou várias linhas. Edite o trecho completo e confira a prévia antes de aplicar.', 'highlight':'Arraste sobre as palavras que deseja destacar em amarelo.', 'erase':'Arraste sobre uma área. Texto, imagens e desenhos serão removidos efetivamente.'}[tool])

    def choose_color(self):
        color = QColorDialog.getColor(self.color, self, 'Cor do texto')
        if color.isValid():
            self.color = color
            self.color_btn.setText(color.name().upper())
        self.update_color_swatch()

    def update_color_swatch(self):
        pix = QPixmap(18, 18)
        pix.fill(self.color)
        from PySide6.QtGui import QIcon
        self.color_btn.setIcon(QIcon(pix))

    def refresh(self):
        doc = self.model.doc
        self.workspace.setCurrentIndex(1 if doc is not None else 0)
        self.save_button.setEnabled(doc is not None)
        for control in self.document_controls:
            control.setEnabled(doc is not None)
        self.number.setEnabled(doc is not None)
        self.previous.setEnabled(doc is not None and self.page > 0)
        self.next.setEnabled(doc is not None and self.page < len(doc) - 1)
        self.update_color_swatch()
        for action in self.page_actions:
            action.setEnabled(doc is not None)
        self.undo.setEnabled(bool(doc and self.model.index > 0))
        self.redo.setEnabled(bool(doc and self.model.index < len(self.model.history) - 1))
        if not doc:
            self.instruction.setText('Abra um PDF para começar. Consulte a aba Ajuda quando precisar.')
            self.canvas.setText('Abra um arquivo PDF\npara visualizar e editar suas páginas.')
            self.canvas.resize(500, 150)
            return
        self.select_tool(self.tool)
        self.page = min(self.page, len(doc) - 1)
        page = doc[self.page]
        pix = page.get_pixmap(matrix=fitz.Matrix(self.zoom, self.zoom), alpha=False)
        image = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888).copy()
        rendered = QPixmap.fromImage(image)
        if self.search_hits and self.search_cursor >= 0:
            index, hit = self.search_hits[self.search_cursor]
            if index == self.page:
                display = hit * page.rotation_matrix
                painter = QPainter(rendered)
                painter.setPen(QPen(QColor('#168aff'), 2))
                painter.setBrush(QColor(30, 150, 255, 70))
                painter.drawRect(QRect(round(display.x0 * self.zoom), round(display.y0 * self.zoom), round(display.width * self.zoom), round(display.height * self.zoom)))
                painter.end()
        self.canvas.setPixmap(rendered)
        self.canvas.setFixedSize(pix.width, pix.height)
        self.number.blockSignals(True)
        self.number.setRange(1, len(doc))
        self.number.setValue(self.page + 1)
        self.number.blockSignals(False)
        self.total.setText(f'de {len(doc)}')
        self.zoom_label.setText(f'{self.zoom:.0%}')
        from PySide6.QtCore import Qt
        title = self.model.path.name
        self.filename.setText(self.filename.fontMetrics().elidedText(title, Qt.ElideMiddle, max(100, self.width() - 700)))
        self.filename.setToolTip(str(self.model.path))
        self.state_badge.setText('ALTERADO' if self.model.dirty else 'SALVO')
        self.update_thumbnails()
        self.setWindowTitle(self.filename.text() + ' — Editor PDF')
        self.statusBar().showMessage('Pronto')
        if not page.get_text().strip():
            self.statusBar().showMessage('Página sem texto extraível: pode ser escaneada. Sem OCR; adicione texto ou apague áreas.')

    def go(self, value):
        self.page = value - 1
        self.safe_refresh()

    def safe_refresh(self):
        try:
            self.refresh()
        except Exception as exc:
            self.error(exc)

    def navigate(self, delta):
        if self.model.doc:
            self.number.setValue(max(1, min(len(self.model.doc), self.page + 1 + delta)))

    def change_zoom(self, factor):
        self.zoom = max(.25, min(4, self.zoom * factor))
        self.safe_refresh()

    def apply(self, operation):
        try:
            self.model.edit(operation)
            self.clear_search()
            self.refresh()
            return True
        except Exception as exc:
            self.error(exc)

    def travel(self, delta):
        if self.model.doc:
            self.model.travel(delta)
            self.clear_search()
            self.safe_refresh()

    def rotate(self):
        if self.model.doc:
            self.apply(lambda doc: doc[self.page].set_rotation((doc[self.page].rotation + 90) % 360))

    def delete(self):
        if not self.model.doc:
            return
        if len(self.model.doc) == 1:
            self.error('O documento precisa manter pelo menos uma página.')
            return
        if QMessageBox.question(self, 'Excluir página', f'Excluir a página {self.page + 1}?') == QMessageBox.Yes:
            self.apply(lambda doc: doc.delete_page(self.page))

    def insertion_position(self):
        value, ok = QInputDialog.getInt(self, 'Posição das novas páginas',
            'Inserir antes da página (última posição = fim do documento):',
            self.page + 2, 1, len(self.model.doc) + 1)
        return value - 1 if ok else None

    def page_range(self, count):
        first, ok = QInputDialog.getInt(self, 'Intervalo de páginas', 'Primeira página:', 1, 1, count)
        if not ok:
            return None
        last, ok = QInputDialog.getInt(self, 'Intervalo de páginas', 'Última página (inclusive):', count, first, count)
        return (first - 1, last - 1) if ok else None

    def add_blank(self):
        if self.model.doc is None:
            self.error('Abra um PDF antes de adicionar páginas.')
            return
        size, ok = QInputDialog.getItem(self, 'Página em branco', 'Tamanho:',
            ['A4 retrato', 'A4 paisagem', 'Mesmo tamanho visual da página atual'], 0, False)
        if not ok:
            return
        rect = self.model.doc[self.page].rect
        width, height = (595, 842) if size == 'A4 retrato' else (842, 595) if size == 'A4 paisagem' else (rect.width, rect.height)
        position = self.insertion_position()
        if position is not None and self.apply(lambda doc: doc.new_page(position, width=width, height=height)):
            self.page = position
            self.safe_refresh()

    def import_pages(self):
        if self.model.doc is None:
            self.error('Abra o PDF que receberá as páginas primeiro.')
            return
        path, _ = QFileDialog.getOpenFileName(self, 'Importar páginas', '', 'PDF (*.pdf)')
        if not path:
            return
        try:
            with fitz.open(path) as source:
                if not source.is_pdf:
                    raise ValueError('Escolha um arquivo PDF.')
                if source.needs_pass:
                    password, ok = QInputDialog.getText(self, 'PDF protegido', 'Senha:', QLineEdit.Password)
                    if not ok:
                        return
                    if not source.authenticate(password):
                        raise ValueError('Senha incorreta.')
                if not len(source):
                    raise ValueError('O PDF não contém páginas.')
                interval = self.page_range(len(source))
                if interval is None:
                    return
                position = self.insertion_position()
                if position is not None and self.apply(lambda doc: doc.insert_pdf(source, from_page=interval[0], to_page=interval[1], start_at=position)):
                    self.page = position
                    self.safe_refresh()
        except Exception as exc:
            self.error(exc)

    def duplicate_page(self):
        if self.model.doc is not None:
            current = self.page
            # Import from a snapshot for an independent copy, including annotations.
            with fitz.open(stream=self.model.history[self.model.index], filetype='pdf') as source:
                if self.apply(lambda doc: doc.insert_pdf(source, from_page=current, to_page=current, start_at=current + 1)):
                    self.page = current + 1
                    self.safe_refresh()

    def move_page(self):
        if self.model.doc is None:
            return
        destination, ok = QInputDialog.getInt(self, 'Mover página', 'Nova posição da página atual:', self.page + 1, 1, len(self.model.doc))
        destination -= 1
        if ok and destination != self.page:
            current = self.page
            if self.apply(lambda doc: doc.move_page(current, -1 if destination == len(doc) - 1 else destination + 1 if destination > current else destination)):
                self.page = destination
                self.safe_refresh()

    def extract_pages(self):
        if self.model.doc is None:
            return
        interval = self.page_range(len(self.model.doc))
        if interval is None:
            return
        path, _ = QFileDialog.getSaveFileName(self, 'Extrair páginas para uma cópia', str(self.model.path.with_name(self.model.path.stem + '_paginas.pdf')), 'PDF (*.pdf)')
        if not path:
            return
        if not path.lower().endswith('.pdf'):
            path += '.pdf'
        try:
            output = Document()
            output.doc = fitz.open()
            try:
                output.doc.insert_pdf(self.model.doc, from_page=interval[0], to_page=interval[1])
                output.path = self.model.path
                output.history = [output.bytes()]
                output.save(path)
            finally:
                output.doc.close()
            self.statusBar().showMessage('Páginas exportadas: ' + path)
        except Exception as exc:
            self.error(exc)

    def clear_search(self):
        self.search_hits = []
        self.search_cursor = -1
        self.search_query = ''
        self.search_count.setText('')
        self.safe_refresh()

    def find_next(self):
        if self.model.doc is None:
            return
        query = self.search_input.text().strip()
        if not query:
            self.clear_search()
            return
        try:
            if query != self.search_query:
                self.search_hits = [(i, rect) for i, page in enumerate(self.model.doc) for rect in page.search_for(query)]
                self.search_query = query
                self.search_cursor = -1
            if not self.search_hits:
                self.search_count.setText('Nenhum resultado')
                self.statusBar().showMessage('Texto não encontrado. A busca não reconhece texto em imagens escaneadas.')
                return
            self.search_cursor = (self.search_cursor + 1) % len(self.search_hits)
            self.page, rect = self.search_hits[self.search_cursor]
            self.safe_refresh()
            display = rect * self.model.doc[self.page].rotation_matrix
            self.scroll.ensureVisible(round(display.x0 * self.zoom), round(display.y0 * self.zoom), 60, 60)
            self.search_count.setText(f'{self.search_cursor + 1} de {len(self.search_hits)}')
            self.statusBar().showMessage(f'Resultado {self.search_cursor + 1} de {len(self.search_hits)}')
        except Exception as exc:
            self.error(exc)

    def point(self, qpoint):
        page = self.model.doc[self.page]
        # Raster dimensions may round up; the render transform itself uses exact zoom.
        return fitz.Point(qpoint.x() / self.zoom, qpoint.y() / self.zoom) * page.derotation_matrix

    def gesture(self, start, end):
        if not self.model.doc or self.tool == 'view':
            return
        try:
            p1, p2 = self.point(start), self.point(end)
            page = self.model.doc[self.page]
            bounds = page.rect * page.derotation_matrix
            if not bounds.contains(p1):
                return
            rect = fitz.Rect(p1, p2).normalize() & bounds
            if self.tool == 'text':
                dialog = TextEditDialog(self, page, point=p1, size=self.size.value(), color=self.color.getRgbF()[:3])
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    self.apply(lambda doc: write_plan(doc[self.page], dialog.plan))
                dialog.timer.stop()
                dialog.deleteLater()
                return
            if rect.is_empty or rect.width < 1 or rect.height < 1:
                return
            if self.tool == 'erase':
                if QMessageBox.question(self, 'Apagar conteúdo', 'Remover efetivamente todo o conteúdo da área? Imagens e desenhos que cruzam a seleção podem ser afetados.') == QMessageBox.Yes:
                    self.apply(lambda doc: erase(doc[self.page], rect))
                return
            selection = selected_chars(page, rect)
            if not selection:
                raise ValueError('Nenhum texto extraível selecionado. PDFs escaneados não têm OCR neste aplicativo.')
            if self.tool == 'highlight':
                quads = [fitz.recover_char_quad(line['dir'], span, char) for line, chars in selection for char, span in chars]
                self.apply(lambda doc: doc[self.page].add_highlight_annot(quads))
                return
            dialog = TextEditDialog(self, page, selection=selection)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.apply(lambda doc: apply_replacement(doc[self.page], selection, dialog.plan))
            dialog.timer.stop()
            dialog.deleteLater()
        except Exception as exc:
            self.error(exc)

    def closeEvent(self, event):
        if self.confirm_dirty():
            event.accept()
        else:
            event.ignore()


def main():
    if sys.platform == 'win32':
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('EditorPDF.Desktop')
    app = QApplication(sys.argv)
    from PySide6.QtGui import QIcon
    app.setWindowIcon(QIcon(str(Path(__file__).with_name('app.svg'))))
    app.setApplicationName('Editor PDF')
    app.setApplicationVersion('0.2.1')
    from PySide6.QtCore import QTranslator, QLibraryInfo
    app.qt_translator = QTranslator(app)
    if app.qt_translator.load('qtbase_pt_BR', QLibraryInfo.path(QLibraryInfo.TranslationsPath)):
        app.installTranslator(app.qt_translator)
    app.setStyle('Fusion')
    from PySide6.QtGui import QFont
    app.setFont(QFont('Segoe UI' if sys.platform == 'win32' else 'DejaVu Sans', 10))
    window = Window()
    def report(kind, value, tb):
        traceback.print_exception(kind, value, tb)
        window.error(value)
    sys.excepthook = report
    if '--smoke-test' in sys.argv:
        # Used by Windows packaging to check frozen Qt, MuPDF and bundled resources.
        window.model.open(Path(__file__).with_name('exemplo.pdf'))
        window.refresh()
        window.show()
        app.processEvents()
        window.render_thumbnail()
        assert not window.canvas.pixmap().isNull()
        assert window.tabs.count() == 2
        assert window.thumbnails.count() == len(window.model.doc)
        page = window.model.doc[0]
        old_text = 'Documento de exemplo para editar localmente.'
        new_text = 'Teste de substituição confirmado.'
        region = page.search_for(old_text)[0]
        errors = []
        window.error = lambda error: errors.append(str(error))
        def confirm_smoke_dialog():
            dialog = app.activeModalWidget()
            if not isinstance(dialog, TextEditDialog):
                errors.append('A janela de edição não foi aberta.')
                if dialog is not None:
                    dialog.reject()
                return
            dialog.editor.setPlainText(new_text)
            dialog.update_preview()
            if dialog.plan is None or not dialog.apply_button.isEnabled():
                errors.append(dialog.status.text())
                dialog.reject()
                return
            dialog.apply_button.click()
        window.select_tool('replace')
        QTimer.singleShot(50, confirm_smoke_dialog)
        window.gesture(QPoint(round(region.x0), round(region.y0)), QPoint(round(region.x1), round(region.y1)))
        assert not errors, errors
        assert new_text in window.model.doc[0].get_text()
        assert old_text not in window.model.doc[0].get_text()
        window.thumb_timer.stop()
        window.model.doc.close()
        return
    window.show()
    if len(sys.argv) > 1:
        try:
            window.model.open(sys.argv[1])
            window.refresh()
        except Exception as exc:
            window.error(exc)
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
