"""
Корректная ширина строк с широкими unicode символами (CJK, emoji)
"""
from wcwidth import wcswidth


def str_display_width(text: str) -> int:
    """Возвращает реальную ширину строки в колонках терминала"""
    w = wcswidth(text)
    return w if w >= 0 else len(text)


def truncate_to_width(text: str, max_width: int) -> str:
    """Обрезает строку до max_width колонок"""
    result = []
    current = 0
    for ch in text:
        w = wcswidth(ch)
        if w < 0:
            w = 1
        if current + w > max_width:
            break
        result.append(ch)
        current += w
    return "".join(result)
