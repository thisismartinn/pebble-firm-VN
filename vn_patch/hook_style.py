#!/usr/bin/env python3
"""Restyle the hook-above mark (hỏi) in the Gothic 14-28 fonts.

The pack draws the hook as a small "?" whose second row sticks out one pixel to the right of the top bar.
The revised style drops that pixel:   ###        ###
                                       ..##  ->   ..#
                                       .#..       .#.
It is applied to every glyph that carries the mark.  The pack's hook above i/I (ỉ, Ỉ) is a different,
wider shape (`###. / ..## / .##.`); those two glyphs are rebuilt from the font's own stem and the
revised hook, centred on the stem (Ỉ is then moved one pixel to the right); ỉ only loses the two pixels at
the left ends of its old hook's top and bottom rows.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pbfmerge import decode_glyph, encode_glyph

HOOK_GLYPHS = [0x1EA2, 0x1EA3, 0x1EA8, 0x1EA9, 0x1EB2, 0x1EB3, 0x1EBA, 0x1EBB, 0x1EC2, 0x1EC3,
               0x1ECE, 0x1ECF, 0x1ED4, 0x1ED5, 0x1EDE, 0x1EDF, 0x1EE6, 0x1EE7, 0x1EEC, 0x1EED,
               0x1EF6, 0x1EF7]
I_HOOK = {0x1EC9: 0x131, 0x1EC8: ord("I")}          # ỉ <- ı, Ỉ <- I


def shift(px, dx, dy):
    return {(x + dx, y + dy) for x, y in px}


def revised(hook):
    """hook: set of pixels of an old-style mark -> revised mark (drops what sticks out right of the top bar)."""
    top = min(y for _, y in hook)
    bar_right = max(x for x, y in hook if y == top)
    return {(x, y) for x, y in hook if y == top or x <= bar_right}


def drop_protrusion(px):
    """Per glyph: the mark is the topmost thing in these glyphs, so its bar is the top row; remove the pixels of
    the second row that stick out to the right of that bar.  (Lowercase ả ẻ ỏ ủ ỷ already have the revised
    shape at 14 regular; capitals and hooks combined with a circumflex, breve or horn do not.)"""
    top = min(y for _, y in px)
    bar_right = max(x for x, y in px if y == top)
    return {(x, y) for x, y in px if not (y == top + 1 and x > bar_right)}


def reference_hook(font, upper=False):
    """The revised mark as the font draws it above ả (or Ả): (pixels above the letter, relative to its top-left)."""
    base = decode_glyph(font.glyphs[ord("A" if upper else "a")])[0]
    full = decode_glyph(font.glyphs[0x1EA2 if upper else 0x1EA3])[0]
    top = min(y for _, y in base)
    hook = revised({p for p in full if p[1] < top})
    x0, y0 = min(x for x, _ in hook), min(y for _, y in hook)
    return {(x - x0, y - y0) for x, y in hook}


def _component(px, seed):
    """8-connected component of `px` containing `seed`."""
    comp, todo = set(), [seed]
    while todo:
        p = todo.pop()
        if p in comp or p not in px:
            continue
        comp.add(p)
        todo += [(p[0] + dx, p[1] + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]
    return comp


def restyle(font, upper_i_shift=1):
    """-> {codepoint: record} for the glyphs whose hook changes.

    * every hook-above glyph loses the pixel(s) sticking out right of the top bar,
    * ỉ: the two pixels at the left ends of the old hook's top and bottom rows are removed,
    * Ỉ: the font's own revised hook (as drawn above ả), centred on the stem, bottom row where the old
      hook's bottom row was, then moved `upper_i_shift` pixels to the right.
    Needs the font to contain a, ả, ı, I and the hook glyphs.
    """
    out = {}
    for cp in HOOK_GLYPHS:
        if cp not in font.glyphs:
            continue
        px, adv = decode_glyph(font.glyphs[cp])
        new = drop_protrusion(px)
        if new != px:
            out[cp] = encode_glyph(new, adv)
    for cp, stem in I_HOOK.items():
        sp, sadv = decode_glyph(font.glyphs[stem])
        gp, gadv = decode_glyph(font.glyphs[cp])
        top = min(y for _, y in sp)
        above = {p for p in gp if p[1] < top}
        hy = min(y for _, y in above)
        hook = _component(above, min((p for p in above if p[1] == hy)))   # the hook, not a taller stem top
        hb = max(y for _, y in hook)
        if cp == 0x1EC9:
            drop = {(min(x for x, y in hook if y == hy), hy), (min(x for x, y in hook if y == hb), hb)}
            out[cp] = encode_glyph(gp - drop, gadv)
            continue
        mark = reference_hook(font)
        mh = max(y for _, y in mark) + 1
        bar_w = max(x for x, y in mark if y == 0) + 1
        centre = (min(x for x, _ in sp) + max(x for x, _ in sp)) // 2
        left = centre - bar_w // 2 + upper_i_shift
        px = (gp - above) | shift(mark, left, hb - (mh - 1))
        out[cp] = encode_glyph(px, max(sadv, gadv, max(x for x, _ in px) + 1))
    return out
