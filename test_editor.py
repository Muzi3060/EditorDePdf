"""Verificação de integração real, sem depender de monitor: QT_QPA_PLATFORM=offscreen."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import pymupdf as fitz
from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QApplication
from main import Window
from model import Document, erase, replace, selected_chars

app = QApplication.instance() or QApplication([])


class Integration(unittest.TestCase):
    def test_interface_controls(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'documento com espaço e acento.pdf'
            with fitz.open() as doc:
                for i in range(3):
                    page = doc.new_page()
                    page.insert_text((50,70), f'Pagina {i + 1}')
                doc.save(path)
            w = Window()
            w.show()
            app.processEvents()
            self.assertFalse(w.save_button.isEnabled())
            self.assertEqual(w.workspace.currentIndex(), 0)
            w.model.open(path)
            w.refresh()
            app.processEvents()
            self.assertTrue(w.save_button.isEnabled())
            self.assertNotIn('Abra um PDF', w.instruction.text())
            self.assertEqual(w.thumbnails.count(), 3)
            for i in range(3):
                w.render_thumbnail()
                self.assertFalse(w.thumbnails.item(i).icon().isNull())
            w.thumbnails.setCurrentRow(2)
            self.assertEqual(w.page, 2)
            w.show_search()
            self.assertFalse(w.search_panel.isHidden())
            w.search_input.setText('Pagina')
            w.find_next()
            self.assertIn('de 3', w.search_count.text())
            w.hide_search()
            self.assertTrue(w.search_panel.isHidden())
            self.assertFalse(w.search_hits)
            w.tool_buttons['text'].click()
            self.assertFalse(w.text_options.isHidden())
            w.tool_buttons['highlight'].click()
            self.assertTrue(w.text_options.isHidden())
            for width, height in [(1000,700),(1380,920)]:
                w.resize(width,height)
                app.processEvents()
                w.tool_buttons['text'].click()
                app.processEvents()
                self.assertGreaterEqual(w.text_options.height(), 200)
                self.assertLessEqual(w.color_btn.geometry().bottom(), w.text_options.height())
                w.fit_width()
                self.assertLessEqual(w.canvas.width(), w.scroll.viewport().width())
                self.assertFalse(w.grab().isNull())
            w.thumb_timer.stop()
            w.hide()
            w.model.doc.close()

    def test_page_tools_and_search(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'source.pdf'
            with fitz.open() as doc:
                for title in ('Primeira', 'Segunda', 'Terceira'):
                    page = doc.new_page()
                    page.insert_text((50, 70), title)
                doc.save(path)
            w = Window()
            w.error = lambda exc: (_ for _ in ()).throw(AssertionError(str(exc)))
            w.model.open(path)
            w.refresh()
            self.assertEqual(w.tabs.tabText(1), 'Ajuda')
            with patch('main.QInputDialog.getItem', return_value=('A4 paisagem', True)), patch('main.QInputDialog.getInt', return_value=(2, True)):
                w.add_blank()
            self.assertEqual(len(w.model.doc), 4)
            self.assertEqual(w.page, 1)
            self.assertGreater(w.model.doc[1].rect.width, w.model.doc[1].rect.height)
            w.travel(-1)
            self.assertEqual(len(w.model.doc), 3)
            w.travel(1)
            w.page = 0
            w.duplicate_page()
            self.assertEqual(w.page, 1)
            self.assertIn('Primeira', w.model.doc[1].get_text())
            w.model.edit(lambda d: d[1].insert_text((50, 100), 'Independente'))
            self.assertNotIn('Independente', w.model.doc[0].get_text())
            with patch('main.QInputDialog.getInt', return_value=(5, True)):
                w.move_page()
            self.assertIn('Independente', w.model.doc[4].get_text())
            with patch('main.QInputDialog.getInt', return_value=(1, True)):
                w.move_page()
            self.assertIn('Independente', w.model.doc[0].get_text())
            with patch('main.QFileDialog.getOpenFileName', return_value=(str(path), '')), patch('main.QInputDialog.getInt', side_effect=[(2, True), (3, True), (6, True)]):
                w.import_pages()
            self.assertEqual(len(w.model.doc), 7)
            self.assertIn('Segunda', w.model.doc[5].get_text())
            self.assertIn('Terceira', w.model.doc[6].get_text())
            w.search_input.setText('Primeira')
            w.find_next()
            self.assertEqual(len(w.search_hits), 2)
            first = w.page
            self.assertFalse(w.canvas.pixmap().isNull())
            w.find_next()
            self.assertNotEqual(w.page, first)
            w.find_next()
            self.assertEqual(w.page, first)
            w.clear_search()
            self.assertEqual(w.search_hits, [])
            output = Path(tmp) / 'extract.pdf'
            before = w.model.index
            with patch('main.QInputDialog.getInt', side_effect=[(6, True), (7, True)]), patch('main.QFileDialog.getSaveFileName', return_value=(str(output), '')):
                w.extract_pages()
            self.assertEqual(w.model.index, before)
            with fitz.open(output) as extracted:
                self.assertEqual(len(extracted), 2)
                self.assertIn('Segunda', extracted[0].get_text())
            saved = Path(tmp) / 'all.pdf'
            w.model.save(saved)
            with fitz.open(saved) as reopened:
                self.assertEqual(len(reopened), 7)
                self.assertIn('Independente', reopened[0].get_text())
                self.assertNotIn('Independente', reopened[1].get_text())
            w.model.doc.close()

    def test_workflow(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = Path(tmp) / 'original.pdf'
            doc = fitz.open()
            for rotation in (0, 90, 180, 270):
                page = doc.new_page(width=400, height=500)
                page.insert_text((50, 80), 'Original texto', fontsize=14)
                page.draw_rect(fitz.Rect(200, 200, 250, 250), fill=(1, 0, 0))
                page.set_rotation(rotation)
            doc.save(original)
            doc.close()
            source = original.read_bytes()
            window = Window()
            window.model.open(original)
            for i in range(4):
                window.page = i
                for zoom in (.6, 1, 1.7, 3):
                    window.zoom = zoom
                    window.refresh()
                    p = fitz.Point(100, 150)
                    display = p * window.model.doc[i].rotation_matrix
                    q = QPoint(round(display.x * zoom), round(display.y * zoom))
                    mapped = window.point(q)
                    self.assertLess(abs(mapped - p), 1.3)
                window.model.edit(lambda d, n=i: d[n].insert_text((100, 150), 'Adicionado', fontsize=12))
            page = window.model.doc[0]
            selected = selected_chars(page, fitz.Rect(48, 60, 110, 85))
            old = ''.join(c['c'] for c, _ in selected[0][1])
            window.model.edit(lambda d: replace(d[0], selected, 'Novo'))
            self.assertNotIn(old, window.model.doc[0].get_text())
            window.model.edit(lambda d: d[1].add_highlight_annot(d[1].search_for('Original', quads=True)))
            window.model.edit(lambda d: erase(d[2], fitz.Rect(195, 195, 255, 255)))
            self.assertEqual(len(window.model.doc[2].get_drawings()), 0)
            window.model.edit(lambda d: d[3].set_rotation(0))
            window.model.edit(lambda d: d.delete_page(3))
            self.assertEqual(len(window.model.doc), 3)
            window.model.travel(-1)
            self.assertEqual(len(window.model.doc), 4)
            window.model.travel(1)
            target = Path(tmp) / 'editado.pdf'
            window.model.save(target)
            self.assertFalse(window.model.dirty)
            self.assertEqual(original.read_bytes(), source)
            with fitz.open(target) as reopened:
                self.assertEqual(len(reopened), 3)
                self.assertIn('Novo', reopened[0].get_text())
                for page in reopened:
                    self.assertIn('Adicionado', page.get_text())
                    span = next(s for b in page.get_text('dict')['blocks'] for line in b.get('lines', []) for s in line['spans'] if s['text'] == 'Adicionado')
                    self.assertAlmostEqual(span['origin'][0], 100, places=2)
                    self.assertAlmostEqual(span['origin'][1], 150, places=2)
                    self.assertGreater(page.get_pixmap().width, 0)
                self.assertTrue(list(reopened[1].annots()))
                self.assertEqual(reopened[2].get_drawings(), [])
            with self.assertRaises(ValueError):
                window.model.save(original)
            window.model.travel(-1)
            self.assertTrue(window.model.dirty)
            window.model.travel(1)
            self.assertFalse(window.model.dirty)
            window.model.doc.close()


if __name__ == '__main__':
    unittest.main()
