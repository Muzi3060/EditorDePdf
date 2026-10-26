"""Operações locais e transacionais em PDFs. Coordenadas em pontos não rotacionados."""
from pathlib import Path
import os
import tempfile
import pymupdf as fitz


class Document:
    def __init__(self):
        self.doc = None
        self.path = None
        self.history = []
        self.index = 0
        self.saved = None

    def open(self, path, password=''):
        doc = fitz.open(path)
        if not doc.is_pdf:
            doc.close()
            raise ValueError('O arquivo selecionado não é um PDF.')
        if doc.needs_pass and not doc.authenticate(password):
            doc.close()
            raise ValueError('Senha necessária ou incorreta.')
        if not len(doc):
            doc.close()
            raise ValueError('O PDF não contém páginas.')
        if self.doc:
            self.doc.close()
        self.doc, self.path = doc, Path(path).resolve()
        self.history = [self.bytes()]
        self.index = 0
        self.saved = self.history[0]

    def bytes(self):
        return self.doc.tobytes(garbage=4, deflate=True, encryption=fitz.PDF_ENCRYPT_NONE)

    @property
    def dirty(self):
        return self.doc is not None and self.history[self.index] != self.saved

    def edit(self, operation):
        before = self.history[self.index]
        try:
            operation(self.doc)
            after = self.bytes()
        except Exception:
            self.doc.close()
            self.doc = fitz.open(stream=before, filetype='pdf')
            raise
        self.history = self.history[:self.index + 1] + [after]
        self.index += 1

    def travel(self, delta):
        target = self.index + delta
        if 0 <= target < len(self.history):
            self.doc.close()
            self.index = target
            self.doc = fitz.open(stream=self.history[target], filetype='pdf')

    def save(self, path):
        target = Path(path).resolve()
        if target == self.path:
            raise ValueError('Escolha outro nome para preservar o arquivo original.')
        data = self.history[self.index]
        fd, temp = tempfile.mkstemp(prefix='.pdf-editor-', suffix='.pdf', dir=target.parent)
        try:
            with os.fdopen(fd, 'wb') as out:
                out.write(data)
            check = fitz.open(temp)
            if len(check) != len(self.doc):
                raise ValueError('Falha ao verificar o PDF salvo.')
            check.close()
            os.replace(temp, target)
        finally:
            if os.path.exists(temp):
                os.unlink(temp)
        self.saved = data


def selected_chars(page, rect):
    lines = []
    for block_index, block in enumerate(page.get_text('rawdict')['blocks']):
        for line in block.get('lines', []):
            chars = []
            for span in line['spans']:
                for char in span['chars']:
                    box = fitz.Rect(char['bbox'])
                    if rect.contains((box.tl + box.br) / 2):
                        chars.append((char, span))
            if chars:
                line['_block'] = block_index
                lines.append((line, chars))
    return lines


def erase(page, rect):
    page.add_redact_annot(rect, fill=False, cross_out=False)
    page.apply_redactions(images=2, graphics=2, text=0)


def replace(page, selection, text):
    from text_editing import prepare_replacement, apply_replacement
    plan = prepare_replacement(page, selection, text)
    apply_replacement(page, selection, plan)
