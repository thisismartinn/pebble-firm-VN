#!/usr/bin/env python3
"""Re-place the tone marks on capital letters that already carry a circumflex or a breve (Ầ Ấ Ẫ Ằ Ắ Ẵ, Ề Ế Ễ, Ồ Ố Ỗ).

The pack draws them with the tone mark flush against, or overlapping, the circumflex/breve, so the strokes fuse
(the same problem the 36px glyphs had).  Rule, learned from the 36px work:

  * grave / acute on a circumflex: above and to the right of the apex, the circumflex left intact,
  * tilde, and any tone mark on a breve: straight above, centred,
  * always with a blank row between the tone mark and the circumflex/breve.

The circumflex / breve letter and the grave / acute / tilde shapes come from the font's own stock glyphs
(Â, À, Á, Ã ...), so strokes match the weight.  Hook-above and dot-below glyphs are not touched here.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pbfmerge import decode_glyph, encode_glyph

# (circumflex/breve letter in the stock font, plain letter, {tone: codepoint})
FAMILIES = [
    (0xC2, "A", {"grave": 0x1EA6, "acute": 0x1EA4, "tilde": 0x1EAA}),
    (0x102, "A", {"grave": 0x1EB0, "acute": 0x1EAE, "tilde": 0x1EB4}),
    (0xCA, "E", {"grave": 0x1EC0, "acute": 0x1EBE, "tilde": 0x1EC4}),
    (0xD4, "O", {"grave": 0x1ED2, "acute": 0x1ED0, "tilde": 0x1ED6}),
]
TONE_SOURCE = {"grave": 0xC0, "acute": 0xC1, "tilde": 0xC3}      # À Á Ã over a plain A


def shift(px, dx, dy):
    return {(x + dx, y + dy) for x, y in px}


def bbox(px):
    xs, ys = [p[0] for p in px], [p[1] for p in px]
    return min(xs), min(ys), max(xs), max(ys)


def restyle(font, gap=1):
    """-> {codepoint: record} for the capital circumflex/breve + grave/acute/tilde glyphs."""
    g = lambda cp: decode_glyph(font.glyphs[cp])
    cap_top = bbox(g(ord("H"))[0])[1]
    a_px, _ = g(ord("A"))
    a_top = bbox(a_px)[1]
    marks = {}
    for tone, cp in TONE_SOURCE.items():
        m = {p for p in g(cp)[0] if p[1] < a_top}
        marks[tone] = m
    out = {}
    for stock_cp, plain, tones in FAMILIES:
        base, adv = g(stock_cp)
        circ = stock_cp != 0x102
        own = {p for p in base if p[1] < cap_top - 1}               # the circumflex / breve
        ox0, oy0, ox1, oy1 = bbox(own)
        apex = {x for x, y in own if y == oy0}
        a_centre = (bbox(a_px)[0] + bbox(a_px)[2]) // 2
        for tone, cp in tones.items():
            if cp not in font.glyphs:
                continue
            m = marks[tone]
            mx0, my0, mx1, my1 = bbox(m)
            mh, mw = my1 - my0 + 1, mx1 - mx0 + 1
            top = max(0, oy0 - gap - mh)
            if circ and tone in ("grave", "acute"):
                left = max(apex) if tone == "grave" else max(apex) + 1
            else:
                left = ((ox0 + ox1) // 2) - mw // 2
            px = base | shift(m, left - mx0, top - my0)
            out[cp] = encode_glyph(px, adv)
    return out
