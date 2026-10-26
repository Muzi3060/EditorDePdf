import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import tempfile
import shutil
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch
import pymupdf as fitz
from PySide6.QtCore import Qt, QPoint
from PySide6.QtWidgets import QApplication
from model import Document, selected_chars
from text_editing import (selection_text, prepare_replacement, apply_replacement,
    prepare_addition, write_plan, dominant_span)
from text_dialog import TextEditDialog
from main import Window

app = QApplication.instance() or QApplication([])


def example(rotation=0):
    doc = fitz.open()
    page = doc.new_page(width=500, height=400)
    page.insert_font(fontname='EmbeddedTest', fontbuffer=fitz.Font('tiro').buffer)
    for i, text in enumerate(('ORIGINAL_PRIMEIRA_LINHA', 'ORIGINAL_SEGUNDA_LINHA', 'ORIGINAL_TERCEIRA_LINHA')):
        page.insert_text((40, 60 + i * 20), text, fontname='EmbeddedTest', fontsize=12)
    page.insert_text((300, 60), 'BLOCO_INTACTO', fontsize=10)
    page.draw_rect(fitz.Rect(300, 100, 360, 160), fill=(0, .5, 1))
    page.set_rotation(rotation)
    return doc


class TextEditing(unittest.TestCase):
    def test_multiline_preserves_embedded_font_and_rotation(self):
        for rotation in (0, 90, 180, 270):
            with self.subTest(rotation=rotation), example(rotation) as doc:
                page = doc[0]
                selection = selected_chars(page, fitz.Rect(39, 40, 230, 105))
                self.assertEqual(len(selection), 3)
                original_font = dominant_span(selection)['font']
                text = 'Uma alteração em várias linhas, preservando a fonte e o restante da página.'
                plan = prepare_replacement(page, selection, text)
                self.assertEqual(plan.font_label, original_font)
                self.assertEqual(plan.size, 12)
                self.assertGreater(len(plan.lines), 1)
                apply_replacement(page, selection, plan)
                with fitz.open(stream=doc.tobytes(garbage=4), filetype='pdf') as reopened:
                    page = reopened[0]
                    result = page.get_text()
                    self.assertNotIn('ORIGINAL_', result)
                    self.assertIn('BLOCO_INTACTO', result)
                    self.assertEqual(page.rotation, rotation)
                    words = ''.join(result.replace('BLOCO_INTACTO', '').split())
                    self.assertEqual(words, ''.join(text.split()))
                    self.assertEqual(len(page.get_drawings()), 1)
                    for point, chunk in plan.lines:
                        boxes = page.search_for(chunk)
                        self.assertTrue(boxes, chunk)
                        self.assertAlmostEqual(boxes[0].x0, point.x, delta=.6)
                        spans = [s for b in page.get_text('dict')['blocks'] for line in b.get('lines', []) for s in line['spans'] if s['text'] == chunk]
                        self.assertTrue(spans)
                        self.assertAlmostEqual(spans[0]['origin'][1], point.y, delta=.1)
                        self.assertGreater(page.get_pixmap().width, 0)

    def test_partial_selection_does_not_erase_neighbours(self):
        with fitz.open() as doc:
            page = doc.new_page()
            page.insert_text((40, 60), 'ANTES MIOLO DEPOIS', fontsize=12)
            chars = page.get_text('rawdict')['blocks'][0]['lines'][0]['spans'][0]['chars']
            region = fitz.Rect(chars[6]['bbox']) | fitz.Rect(chars[10]['bbox'])
            selection = selected_chars(page, region)
            self.assertEqual(''.join(c['c'] for c, _ in selection[0][1]), 'MIOLO')
            apply_replacement(page, selection, prepare_replacement(page, selection, 'NOVO'))
            self.assertIn('ANTES', page.get_text())
            self.assertIn('DEPOIS', page.get_text())
            self.assertIn('NOVO', page.get_text())
            self.assertNotIn('MIOLO', page.get_text())

    def test_overflow_is_non_destructive_and_fit_is_reported(self):
        with example() as doc:
            page = doc[0]
            selected = selected_chars(page, fitz.Rect(39, 40, 230, 105))
            before = page.get_text()
            with self.assertRaises(ValueError):
                prepare_replacement(page, selected, 'texto ' * 2000)
            self.assertEqual(before, page.get_text())
            self.assertEqual(list(page.annots() or []), [])
            # Fixed original slots allow wrapping and optional reduction, with an explicit warning.
            for count in range(15, 70):
                try:
                    plan = prepare_replacement(page, selected, 'palavra ' * count)
                except ValueError:
                    continue
                if plan.size < 11.9:
                    self.assertTrue(any('reduzido' in msg for msg in plan.warnings))
                    break
            else:
                self.fail('Expected a successful auto-fit case')

    def test_delete_whole_selection_and_fallback_font(self):
        with example() as doc:
            page = doc[0]
            selected = selected_chars(page, fitz.Rect(39, 40, 230, 105))
            # Force a missing original font, emulating a non-extractable subset.
            for _, chars in selected:
                for _, span in chars:
                    span['font'] = 'MissingFont'
            plan = prepare_replacement(page, selected, 'Edição com acentos: ação.')
            self.assertTrue(plan.warnings)
            apply_replacement(page, selected, plan)
            self.assertIn('ação', page.get_text())
        with example() as doc:
            page = doc[0]
            selected = selected_chars(page, fitz.Rect(39, 40, 230, 105))
            apply_replacement(page, selected, prepare_replacement(page, selected, ''))
            self.assertNotIn('ORIGINAL_', page.get_text())
            self.assertIn('BLOCO_INTACTO', page.get_text())

    def test_two_columns_use_separate_original_slots(self):
        with example() as doc:
            page = doc[0]
            selected = selected_chars(page, fitz.Rect(0, 30, 490, 110))
            plan = prepare_replacement(page, selected, 'novo texto ' * 14)
            for point, text in plan.lines:
                right = point.x + plan.font.text_length(text, fontsize=plan.size)
                self.assertTrue((point.x < 230 and right < 231) or (point.x >= 300 and right <= 401))

    def test_wrapping_dialog_grows_and_validates_preview(self):
        with example() as doc:
            page = doc[0]
            selected = selected_chars(page, fitz.Rect(39, 40, 230, 105))
            dialog = TextEditDialog(None, page, selection=selected)
            dialog.show()
            app.processEvents()
            original_height = dialog.editor.minimumHeight()
            dialog.editor.setPlainText('Uma frase muito longa que precisa continuar na linha seguinte. ' * 100)
            app.processEvents()
            dialog.editor.update_height()
            self.assertGreater(dialog.editor.minimumHeight(), original_height)
            self.assertEqual(dialog.editor.horizontalScrollBarPolicy(), Qt.ScrollBarAlwaysOff)
            dialog.update_preview()
            self.assertFalse(dialog.apply_button.isEnabled())
            self.assertIsNone(dialog.plan)
            dialog.editor.setPlainText('Novo trecho de várias linhas. ' * 3)
            dialog.update_preview()
            self.assertIsNotNone(dialog.plan)
            self.assertTrue(dialog.apply_button.isEnabled())
            self.assertFalse(dialog.preview.pixmap().isNull())
            self.assertIn('ORIGINAL_', page.get_text())  # Preview did not change the document.
            dialog.timer.stop()
            dialog.hide()

    def test_multiline_addition_and_drag_scroll(self):
        with example(90) as doc:
            page = doc[0]
            plan = prepare_addition(page, fitz.Point(40, 200), 'Texto adicionado em duas linhas.\nSegunda linha com acentos.', 12, (0, 0, 1))
            write_plan(page, plan)
            self.assertIn('Segunda linha', page.get_text())
            w = Window()
            w.model.doc = fitz.open(stream=doc.tobytes(), filetype='pdf')
            w.model.path = Path('exemplo.pdf').resolve()
            w.model.history = [w.model.bytes()]
            w.zoom = 3
            w.refresh()
            w.show()
            app.processEvents()
            w.canvas.start = QPoint(50, 50)
            bottom = w.scroll.viewport().mapToGlobal(QPoint(100, w.scroll.viewport().height() - 1))
            with patch('main.QCursor.pos', return_value=bottom):
                w.canvas.scroll_selection()
            self.assertGreater(w.scroll.verticalScrollBar().value(), 0)
            w.canvas.start = None
            w.canvas.drag_scroll.stop()
            w.thumb_timer.stop()
            w.hide()
            w.model.doc.close()


@unittest.skipUnless(os.environ.get('EDITOR_PDF_REGRESSION_FILE'), 'PDF externo opcional não informado')
class RealPDFRegression(unittest.TestCase):
    def test_real_document_fonts_save_and_reopen(self):
        # Fixture supplied locally by the user; never added to Git or Releases.
        source = Path(os.environ['EDITOR_PDF_REGRESSION_FILE'])
        before = source.read_bytes()
        with tempfile.TemporaryDirectory() as tmp, fitz.open(source) as doc:
            page = doc[2]
            selected = selected_chars(page, fitz.Rect(79, 110, 296, 183))
            self.assertGreaterEqual(len(selected), 6)
            unchanged_text = page.get_text(clip=fitz.Rect(350, 100, 550, 700))
            image_hashes = {item[0]: doc.xref_stream(item[0]) for item in page.get_images()}
            old_font = dominant_span(selected)['font']
            plan = prepare_replacement(page, selected, 'Texto de teste: edição de várias linhas com a fonte original. Agora podemos editar um parágrafo inteiro, com acentos e pontuação, preservando o restante da página.')
            self.assertEqual(plan.font_label, old_font)
            self.assertEqual(plan.size, 9)
            apply_replacement(page, selected, plan)
            output = Path(tmp) / 'editado.pdf'
            doc.save(output, garbage=4, deflate=True)
            with fitz.open(output) as reopened:
                page = reopened[2]
                self.assertIn('Texto de teste:', page.get_text())
                self.assertNotIn('Welcome to the Hellbreakers', page.get_text())
                self.assertEqual(unchanged_text, page.get_text(clip=fitz.Rect(350, 100, 550, 700)))
                for xref, data in image_hashes.items():
                    # Image object IDs can change when garbage collection runs.
                    self.assertIn(data, [reopened.xref_stream(item[0]) for item in page.get_images()])
                self.assertGreater(page.get_pixmap().width, 0)
            if shutil.which('pdftoppm'):
                from PySide6.QtGui import QImage
                images = []
                for name, pdf in [('before', source), ('after', output)]:
                    prefix = str(Path(tmp) / name)
                    subprocess.run(['pdftoppm', '-f', '3', '-l', '3', '-singlefile', '-r', '72', '-x', '350', '-y', '100', '-W', '200', '-H', '600', '-png', str(pdf), prefix], check=True, capture_output=True)
                    images.append(QImage(prefix + '.png'))
                self.assertFalse(images[0].isNull())
                self.assertEqual(images[0].size(), images[1].size())
                a, b = bytes(images[0].constBits()), bytes(images[1].constBits())
                differences = [abs(x-y) for x,y in zip(a,b)]
                # Rewritten PDF operators may slightly change edge antialiasing.
                # Image streams and unselected text are checked exactly above.
                self.assertLess(sum(differences) / len(differences), 1.0)
                self.assertLess(sum(x > 20 for x in differences) / len(differences), .01)
        self.assertEqual(before, source.read_bytes())


if __name__ == '__main__':
    unittest.main()
