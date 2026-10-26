"""Local text reflow, using embedded fonts and the selected lines as safe slots."""
from dataclasses import dataclass
from collections import Counter
import re
import pymupdf as fitz


@dataclass
class TextPlan:
    font: object
    font_label: str
    size: float
    original_size: float
    color: tuple
    lines: list
    warnings: list


def selection_text(selection):
    parts = []
    previous = None
    for line, chars in selection:
        text = ''.join(c['c'] for c, _ in chars).rstrip('\r\n\t ')
        block = line.get('_block', 0)
        if parts:
            parts.append('\n' if block != previous else ' ')
        parts.append(text)
        previous = block
    return ''.join(parts)


def dominant_span(selection):
    spans = {}
    counts = Counter()
    for _, chars in selection:
        for char, span in chars:
            key = (span['font'], round(span['size'], 3), span['color'])
            spans[key] = span
            counts[key] += 1 if char['c'].isspace() else 3
    return spans[counts.most_common(1)[0][0]]


def font_candidates(page, span):
    """Extract only to memory; never depend on the font being installed on the PC."""
    result = []
    normalized = lambda s: re.sub(r'[^a-z0-9]', '', s.split('+')[-1].lower())
    for item in page.get_fonts(full=True):
        if normalized(item[3]) != normalized(span['font']):
            continue
        try:
            _, _, _, data = page.parent.extract_font(item[0])
            if data:
                font = fitz.Font(fontbuffer=data)
                if font.is_writable:
                    result.append((font, span['font'], ''))
                    break
        except (ValueError, RuntimeError):
            continue
    standard = {
        'helvetica': 'helv', 'helvetica-bold': 'hebo', 'helvetica-oblique': 'heit',
        'helvetica-boldoblique': 'hebi', 'times-roman': 'tiro', 'times-bold': 'tibo',
        'times-italic': 'tiit', 'times-bolditalic': 'tibi', 'courier': 'cour',
        'courier-bold': 'cobo', 'courier-oblique': 'coit', 'courier-boldoblique': 'cobi',
        'symbol': 'symb', 'zapfdingbats': 'zadb',
    }
    if span['font'].lower() in standard:
        result.append((fitz.Font(standard[span['font'].lower()]), span['font'], ''))
    name = span['font'].lower()
    serif = bool(span['flags'] & 4) and not any(x in name for x in ('goodot', 'helvetica', 'arial', 'sans'))
    bold = bool(span['flags'] & 16)
    italic = bool(span['flags'] & 2)
    base = ('tibi' if bold and italic else 'tibo' if bold else 'tiit' if italic else 'tiro') if serif else ('hebi' if bold and italic else 'hebo' if bold else 'heit' if italic else 'helv')
    result.append((fitz.Font(base), 'Times' if serif else 'Helvetica', 'A fonte original não pôde ser reutilizada para todos os caracteres; será usada uma fonte semelhante.'))
    result.append((fitz.Font('cjk'), 'Droid Sans Fallback', 'Alguns caracteres exigem uma fonte Unicode alternativa; a aparência será diferente.'))
    return result


def choose_font(candidates, text):
    chars = {ord(c) for c in text if not c.isspace()}
    for font, label, warning in candidates:
        if all(font.has_glyph(c) for c in chars):
            return font, label, warning
    raise ValueError('Há caracteres sem desenho nas fontes disponíveis. Remova símbolos especiais ou use outro texto.')


def slots_from_selection(selection, font, size):
    slots = []
    for line, chars in selection:
        if abs(line['dir'][0] - 1) > .01 or abs(line['dir'][1]) > .01:
            raise ValueError('A seleção contém texto vertical ou inclinado. Selecione texto horizontal; a rotação da página é suportada.')
        visible = [(c, s) for c, s in chars if c['c'] not in '\r\n\t']
        if not visible:
            continue
        x = visible[0][0]['origin'][0]
        right = max(fitz.Rect(c['bbox']).x1 for c, _ in visible)
        # Never enlarge into adjacent text, illustrations or another column.
        slots.append((x, visible[0][0]['origin'][1], max(.1, right - x + .35)))
    return slots


def flow(text, slots, font, size):
    remaining = text.replace('\r\n', '\n').replace('\r', '\n').replace('\t', '    ')
    output = []
    for x, y, width in slots:
        if not remaining:
            break
        head, newline, tail = remaining.partition('\n')
        if not head:
            remaining = tail if newline else ''
            continue
        low, high = 0, len(head)
        while low < high:
            middle = (low + high + 1) // 2
            if font.text_length(head[:middle], fontsize=size) <= width:
                low = middle
            else:
                high = middle - 1
        if low == 0:
            return None
        if low < len(head):
            # Prefer word boundaries, but allow long words/URLs to wrap as well.
            spaces = [m.end() for m in re.finditer(r'\s+', head[:low + 1]) if m.end() <= low]
            cut = spaces[-1] if spaces else low
            chunk = head[:cut].rstrip()
            remaining = remaining[cut:].lstrip(' ')
        else:
            chunk = head
            remaining = tail if newline else ''
        if chunk:
            output.append((fitz.Point(x, y), chunk))
    return output if not remaining.strip() else None


def prepare_replacement(page, selection, text, size=None, auto_fit=True, candidates=None):
    if not selection:
        raise ValueError('Selecione texto extraível antes de editar.')
    span = dominant_span(selection)
    original = float(span['size'])
    size = float(size if size is not None else original)
    requested = size
    candidates = candidates or font_candidates(page, span)
    font, label, warning = choose_font(candidates, text)
    slots = slots_from_selection(selection, font, size)
    lines = flow(text, slots, font, size)
    if lines is None and auto_fit:
        minimum = min(size, 6.0)
        if flow(text, slots, font, minimum) is not None:
            low, high = minimum, size
            for _ in range(16):
                mid = (low + high) / 2
                if flow(text, slots, font, mid) is not None:
                    low = mid
                else:
                    high = mid
            size = int(low * 100) / 100
            lines = flow(text, slots, font, size)
    if lines is None:
        raise ValueError('O texto ainda ultrapassa as linhas selecionadas. Selecione mais linhas, reduza o tamanho ou encurte o texto. Nada foi apagado.')
    warnings = [warning] if warning else []
    styles = {(s['font'], s['size'], s['color']) for _, chars in selection for _, s in chars}
    if len(styles) > 1:
        warnings.append('O trecho tem estilos diferentes. O novo texto usará a fonte, o tamanho e a cor predominantes.')
    if size < requested - .05:
        warnings.append(f'Tamanho reduzido de {requested:g} para {size:g} pt para caber na área.')
    return TextPlan(font, label, size, original, fitz.sRGB_to_pdf(span['color']), lines, warnings)


def write_plan(page, plan):
    writer = fitz.TextWriter(page.rect)
    for point, text in plan.lines:
        writer.append(point, text, font=plan.font, fontsize=plan.size)
    if plan.lines:
        writer.write_text(page, color=plan.color)


def apply_replacement(page, selection, plan):
    # Small rectangles centered on glyphs avoid deleting neighbouring lines.
    for _, chars in selection:
        for char, _ in chars:
            if char['c'] in '\r\n\t':
                continue
            box = fitz.Rect(char['bbox'])
            if box.is_empty:
                continue
            center = (box.tl + box.br) / 2
            halfw = max(.05, box.width * .2)
            halfh = max(.05, box.height * .2)
            page.add_redact_annot(fitz.Rect(center.x - halfw, center.y - halfh, center.x + halfw, center.y + halfh), fill=False, cross_out=False)
    page.apply_redactions(images=0, graphics=0, text=0)
    write_plan(page, plan)


def prepare_addition(page, point, text, size, color, auto_fit=False):
    candidates = [(fitz.Font('helv'), 'Helvetica', ''), (fitz.Font('cjk'), 'Droid Sans Fallback', 'Será usada uma fonte Unicode alternativa para representar todos os caracteres.')]
    font, label, warning = choose_font(candidates, text)
    bounds = page.rect * page.derotation_matrix
    step = size * max(1.2, font.ascender - font.descender)
    slots = []
    y = point.y
    while y - size * font.descender <= bounds.y1:
        slots.append((point.x, y, max(0, bounds.x1 - point.x - 2)))
        y += step
    if point.y - size * font.ascender < bounds.y0 or not slots:
        raise ValueError('Não há espaço nessa posição. Clique mais abaixo e longe da borda direita.')
    lines = flow(text, slots, font, size)
    if lines is None:
        raise ValueError('O texto ultrapassa a página. Diminua o tamanho ou escolha uma posição com mais espaço.')
    return TextPlan(font, label, size, size, color, lines, [warning] if warning else [])
