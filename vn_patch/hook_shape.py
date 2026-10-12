#!/usr/bin/env python3
"""Give the hook-above mark (hỏi) a proper "?" shape at 28px, in the style of the 36px hook.

The 28px hook, after the pixel-sticking-out fix, is a "┐" (top bar plus a short vertical stroke) and is lighter
at bold than at regular.  This replaces it with a "?" whose stroke matches the weight of the font.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pbfmerge import decode_glyph, encode_glyph
import hook_style as H


def bitmap(rows):
    return {(x, y) for y, r in enumerate(rows) for x, c in enumerate(r) if c == "#"}


# Four rows tall, like the old hook: only four rows are free above a capital circumflex.
SHAPES = {                                       # keyed by the stroke width of the font's own ı
    1: bitmap([".##.", "#..#", "..#.", ".#.."]),                      # 28 regular: 1 px strokes
    2: bitmap([".###.", "##.##", "...##", "..##."]),                  # 28 bold: heavier right-hand stroke
}

# hook glyph -> the same letter without the hook (the hook is exactly the difference)
BASE = {0x1EA3: 0x61, 0x1EA2: 0x41, 0x1EA9: 0xE2, 0x1EA8: 0xC2, 0x1EB3: 0x103, 0x1EB2: 0x102,
        0x1EBB: 0x65, 0x1EBA: 0x45, 0x1EC3: 0xEA, 0x1EC2: 0xCA, 0x1ECF: 0x6F, 0x1ECE: 0x4F,
        0x1ED5: 0xF4, 0x1ED4: 0xD4, 0x1EDF: 0x1A1, 0x1EDE: 0x1A0, 0x1EE7: 0x75, 0x1EE6: 0x55,
        0x1EED: 0x1B0, 0x1EEC: 0x1AF, 0x1EF7: 0x79, 0x1EF6: 0x59}


# Capitals with a circumflex / breve have no room for a gap plus the 4-row mark inside the font's top row, so
# they get this 3-row version (no tail) instead.
SHAPES3 = {1: bitmap([".##.", "#..#", "..#."]),
           2: bitmap([".###.", "##.##", "...##"])}


def bb(px):
    xs, ys = [p[0] for p in px], [p[1] for p in px]
    return min(xs), min(ys), max(xs), max(ys)


def shift(px, dx, dy):
    return {(x + dx, y + dy) for x, y in px}


def replace_hooks(font, shape, shape3=None):
    """-> {codepoint: record} with the new "?" in every hook-above glyph (including ỉ / Ỉ).  The new mark keeps
    the horizontal centre and the bottom row of the old one."""
    out = {}
    for cp in H.HOOK_GLYPHS:
        if cp not in font.glyphs:
            continue
        px, adv = decode_glyph(font.glyphs[cp])
        base, _ = decode_glyph(font.glyphs[BASE[cp]])
        old = px - base
        ox0, oy0, ox1, oy1 = bb(old)
        sx0, sy0, sx1, sy1 = bb(shape)
        left = (ox0 + ox1) // 2 - (sx1 - sx0) // 2
        new = shift(shape, left - sx0, oy1 - sy1)
        # on a circumflex / breve the hook must not touch the mark below it: keep one blank row between them
        def settle(new):
            while any((x + dx, y + 1) in base for x, y in new for dx in (-1, 0, 1)) or \
                    any((x, y) in base for x, y in new):
                new = shift(new, 0, -1)
            return new
        new = settle(new)
        if shape3 and min(y for _, y in new) < 0:            # would stick out above the top row
            new = settle(shift(shape3, left - bb(shape3)[0], oy1 - bb(shape3)[3]))
        out[cp] = encode_glyph(base | new, adv)
    for cp, stem in H.I_HOOK.items():
        sp, sadv = decode_glyph(font.glyphs[stem]); gp, gadv = decode_glyph(font.glyphs[cp])
        top = min(y for _, y in sp)
        above = {p for p in gp if p[1] < top}
        hy = min(y for _, y in above)
        seed = min(p for p in above if p[1] == hy)
        hook = H._component(above, seed)
        hx0, hy0, hx1, hy1 = bb(hook)
        sx0, sy0, sx1, sy1 = bb(shape)
        centre = (min(x for x, _ in sp) + max(x for x, _ in sp)) // 2 + (1 if cp == 0x1EC8 else 0)
        new = shift(shape, centre - (sx1 - sx0) // 2 - sx0, hy1 - sy1)
        out[cp] = encode_glyph((gp - hook) | new, max(sadv, gadv, bb(new)[2] + 1))
    return out


NEEDED = sorted({ord("A"), ord("H"), 0xC0, 0xC1, 0xC2, 0xC3, 0xCA, 0xD4, 0x102, 0x131, ord("I")} | set(BASE.values()))


def stroke_width(font):
    px, _ = decode_glyph(font.glyphs[0x131])
    return len({x for x, _ in px})


def apply_28(font, stock):
    """Capital tone-mark placement and the "?" hook for a 28px extended font.  `font` needs the stock letters (see
    NEEDED) next to the Vietnamese glyphs; `stock` supplies any that are missing.  Returns the changed codepoints."""
    import capital_marks as CM
    added = [cp for cp in NEEDED if cp not in font.glyphs and cp in stock.glyphs]
    for cp in added:
        font.glyphs[cp] = stock.glyphs[cp]
    w = min(stroke_width(font), 2)
    changes = CM.restyle(font)
    font.glyphs.update(changes)
    hooks = replace_hooks(font, SHAPES[w], SHAPES3[w])
    font.glyphs.update(hooks)
    return added, set(changes) | set(hooks)


def hook_ok_28(px):
    """True when the topmost 8-connected component of a 28px hook glyph is exactly one of the "?" shapes, i.e. it
    does not touch the circumflex / breve / letter below it, and nothing is above row 0."""
    if not px or min(y for _, y in px) < 0:
        return False
    seed = min(p for p in px if p[1] == min(y for _, y in px))
    comp, todo = set(), [seed]
    while todo:
        p = todo.pop()
        if p in comp or p not in px:
            continue
        comp.add(p)
        todo += [(p[0] + dx, p[1] + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]
    x0, y0, _, _ = bb(comp)
    norm = shift(comp, -x0, -y0)
    return any(norm == s for s in list(SHAPES.values()) + list(SHAPES3.values()))
