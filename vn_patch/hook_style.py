#!/usr/bin/env python3
"""Restyle the hook-above mark (hỏi) in the Gothic 14-28 fonts.

The pack draws the hook as a small "?" whose second row sticks out one pixel to the right of the top bar.
The revised style drops that pixel:   ###        ###
                                       ..##  ->   ..#
                                       .#..       .#.
It is applied to every glyph that carries the mark.  The pack's hook above i/I (ỉ, Ỉ) is a different,
wider shape (`###. / ..## / .##.`); those two glyphs are rebuilt from the font's own stem and the
revised hook, centred on the stem (Ỉ is then moved one pixel to the right).
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
    """hook: set of pixels of the old-style mark -> revised mark (drops what sticks out right of the top bar)."""
    top = min(y for _, y in hook)
    bar_right = max(x for x, y in hook if y == top)
    return {(x, y) for x, y in hook if y == top or x <= bar_right}


def own_hook(font):
    """The mark as drawn above `a` in this font: the pixels of ả above the top of a."""
    a, _ = decode_glyph(font.glyphs[ord("a")])
    ar, _ = decode_glyph(font.glyphs[0x1EA3])
    top = min(y for _, y in a)
    return {p for p in ar if p[1] < top}


def restyle(font, i_shift=(0, 1)):
    """-> {codepoint: record} with the new hook; `i_shift` = (dx for ỉ, dx for Ỉ)."""
    old = own_hook(font)
    new = revised(old)
    x0 = min(x for x, _ in old); y0 = min(y for _, y in old)
    rel_old = {(x - x0, y - y0) for x, y in old}
    drop_rel = rel_old - {(x - x0, y - y0) for x, y in new}
    out = {}
    for cp in HOOK_GLYPHS:
        if cp not in font.glyphs:
            continue
        px, adv = decode_glyph(font.glyphs[cp])
        # find where the old mark sits in this glyph (it is drawn identically everywhere)
        hits = [(dx, dy) for dx in range(-3, 12) for dy in range(-3, 12)
                if shift(rel_old, dx, dy) <= px and min(y for _, y in px) == dy + min(y for _, y in rel_old) or
                (shift(rel_old, dx, dy) <= px and dy + 0 == min(y for _, y in px))]
        hits = [h for h in hits if shift(rel_old, *h) <= px]
        if not hits:
            raise SystemExit("hook mark not found in U+%X" % cp)
        dx, dy = min(hits, key=lambda h: h[1])                 # topmost placement
        removed = shift(drop_rel, dx, dy)
        out[cp] = encode_glyph(px - removed, adv)
    for cp, stem in I_HOOK.items():
        sp, sadv = decode_glyph(font.glyphs[stem])
        gp, gadv = decode_glyph(font.glyphs[cp])
        top = min(y for _, y in sp)
        rows = sorted({y for _, y in gp if y < top})            # the three rows the old hook occupies
        h_top = rows[0]
        mark = shift({(x - x0, y - y0) for x, y in new}, 0, 0)  # revised mark, top-left at (0, 0)
        centre = (min(x for x, _ in sp) + max(x for x, _ in sp)) // 2
        bar_w = max(x for x, y in mark if y == 0) + 1
        left = centre - bar_w // 2 + (i_shift[1] if cp == 0x1EC8 else i_shift[0])
        px = sp | shift(mark, left, h_top)
        out[cp] = encode_glyph(px, max(sadv, gadv, max(x for x, _ in px) + 1))
    return out
