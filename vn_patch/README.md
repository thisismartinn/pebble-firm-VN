# Vietnamese build of the Rebble 4.4.x firmware

**The firmware bundles (`.pbz`) and language packs (`.pbl`) are not stored in this repository.** The repo's
`.gitignore` ignores `dist/`, which is where the scripts write their output, and the files are published as
release assets instead. Only the tooling lives here; the commands below regenerate every file.

Rebble's `4.4.x-rbl` firmware for Pebble Time, Time Steel and Time Round is a binary patch of
Pebble's closed 4.3 firmware (see `pebble-dev/legacy-firmware-patcher`), so there is no source to
merge the Core Devices PRs into. What those PRs mean for Vietnamese is font data, and that can be
applied to the resource pack. `build_vn_pbz.py` does this:

1. reads a Vietnamese language pack (`.pbl`) whose extended Gothic fonts hold the missing glyphs,
2. pairs each extended font with its base `GOTHIC_14/18/24/28` (regular and bold) system font,
3. merges the glyphs into the base font records (no re-encoding; layouts and widths already match),
4. rebuilds `system_resources.pbpack`, fixes the CRCs/manifest/version tag, writes a new `.pbz`.

```
git clone https://github.com/pebble-dev/legacy-firmware-patcher
python3 build_vn_pbz.py --patcher-dir legacy-firmware-patcher --pbl vi_VN.pbl \
    --version v4.4.2-rbl-vn  Pebble-4.4.2-rbl-spalding.pbz  dist/Pebble-4.4.2-rbl-vn-spalding.pbz
python3 verify_pbz.py --patcher-dir legacy-firmware-patcher  Pebble-4.4.2-rbl-spalding.pbz  dist/...
```

Stock inputs: `https://github.com/pebble-dev/legacy-firmware-patcher/releases/download/rbl2-rc1/Pebble-4.4.2-rbl-{snowy_dvt,snowy_s3,spalding}.pbz` or `https://binaries.rebble.io/fw/{snowy_s3,snowy_dvt,spalding,silk}/Pebble-4.4.3-rbl-{snowy_s3,snowy_dvt,spalding,silk}.pbz`

## Which file for which watch

| Watch | File | `hwrev` in the bundle |
|---|---|---|
| Pebble Time | `Pebble-4.4.x-rbl-vn-snowy_dvt.pbz` | `snowy_dvt` |
| Pebble Time Steel | `Pebble-4.4.x-rbl-vn-snowy_s3.pbz` | `snowy_s3` |
| Pebble Time Round | `Pebble-4.4.x-rbl-vn-spalding.pbz` | `spalding` |
| Pebble 2 | `Pebble-4.4.x-rbl-vn-silk.pbz` (4.4.3 only) | `silk` |

The Time / Time Steel mapping follows Rebble's board names (the stock bundles are named the same way).
Check the hardware revision on the watch (Settings > System > Information) before flashing; the
bundles differ only in the firmware image, the fonts are identical.

## What each build contains (Rebble 4.4.3-rbl)

Space in the 512 KiB resource bank is the limit, so `build_vn_pbz.py` fits things in priority order and keeps
`--margin` (default 1 KiB) free: Vietnamese 14-28px (always) > Gothic 36 bold > Gothic 09 > Gothic 36 > coffee >
extra emoji in the order of `emoji_list.txt`. A `.pbz.json` file written next to each bundle records what it got.

| Build | Vietnamese in the base fonts | Extra emoji |
|---|---|---|
| Time, Time Steel | 14-28, 36 bold (built with `--skip-large 36 --skip-large 09`) | 31 of 52 |
| Time Round | 14-28, 36 bold (built with `--skip-large 09`; 36 regular does not fit) | 14 of 52 |
| Pebble 2 | only Đ đ Ơ ơ Ư ư (`--only-codepoints`); the rest comes from the language pack | 35 of 52 |

Why Pebble 2 can lean on the pack: the firmware draws codepoints up to U+02AF from the base font and the ones
above it can come from the pack's extension fonts, so the letters at or below U+02AF that the stock fonts lack
(Đ đ Ơ ơ Ư ư) are the only ones the base fonts must carry.

The glyphs for 36 / 36 bold are drawn by `compose_vn.py` from the font's own letters and marks (`preview_vn.py`
renders review sheets); the stock bold 36 Đ/đ and Ĩ/ĩ were wrong and are replaced. 09px is no longer built: the
only user in the firmware is the bundled Golf app's fixed English labels.

### Hook-above style

`hook_style.py` restyles the hook-above mark in the 14-28px fonts: the pixel that sticks out right of the top
bar is removed from all 22 hook-above glyphs; lowercase ỉ loses the two pixels at the left ends of its old hook's
top and bottom rows; capital Ỉ gets the font's own revised hook, centred on the stem and moved 1 px right.
Both builders apply it.

## Language pack v19

`build_lang_pack.py` turns the v16 pack into `dist/vi-VN_v19.pbl` (v17 and v18 were earlier revisions):
it repairs the truncated U+1EF5 (and keeps a blank row between the tail of the y and its dot at every size) and the mis-weighted, off-centre ỉ/Ỉ in the 14-28px fonts, restores the
stock capital Ĩ, applies the hook style, and puts real 36px fonts (with Ă/ă added) into slots 10/11
(GOTHIC_36_EXTENDED / _BOLD_EXTENDED in Core Devices' 21-slot layout; v16 had 28px fonts there). A pack cannot
carry 09px, there is no slot for it. Slots 1-9 are identical on both layouts, so one pack serves Core Devices
watches and current Pebbles; slots 10/11 feed Bitham fonts on older firmware, as in v16. `verify_lang_pack.py`
checks it.

### 36px composition rules (`compose_vn.py`)

- Capital Â Ê Ô with a grave, acute or hook: the tone mark goes above and to the right of the circumflex apex, the circumflex stays intact (it used to be tucked into it and merged into a wavy shape). Bold Ă with a tone mark centres it above the breve.
- Bold tilde on a capital circumflex or breve (Ẵ Ẫ Ễ Ỗ): the 6-row bold tilde has no room above the mark, so it is squeezed to 5 rows and stacked with a one-row gap, like the regular.
- Ĩ ĩ at 36 regular use the font's own 10-wide tilde; the letter widens to fit.
- Lowercase at 36 is unchanged.

## Extra emoji

`emoji_list.txt` names the emoji merged from Core Devices PR #1725's expanded emoji fonts
(`emoji_src/`, with their Apache-2.0 / OFL notices): up to 45 emoji (frog, noodles, scooter, extra faces...)
go into the four system EMOJI fonts, and U+2615 (coffee) into the eight Gothic fonts, because the
firmware draws U+2000-2BFF from the text font, not the emoji font. Edit the list and rebuild
(`--emoji-list none` skips the step). Each emoji costs about 170 bytes across the four sizes; the list is
in priority order and the builder drops from the end when the bank is full.

Not possible without changing firmware code: anything outside U+E000-E537 / U+1F300-1F6FF
(for example 🤔 🤣 🥰 🥺 🤗), flags and keycaps. That is what the C part of #1725 adds.

## Notes

- Glyphs present in both the stock fonts and the pack: Đ đ ĩ Ũ ũ take the pack's version (stock Gothic 18/28 draw
  Đ as D with a bar above); capital Ĩ keeps the stock glyph because the pack's has its tilde clipped to one row
  in five of the eight sizes.
- Defects in the pack that the builders repair (worth fixing in the pack itself): U+1EF5 (ỵ) is truncated in the
  18, 24 and 28 fonts; ỉ/Ỉ have the wrong stem weight and sit one pixel right of ì/í/ĩ.
- A full Vietnamese Silk (Pebble 2) build does not fit its 512 KiB bank (about 13 KB over), which is why Pebble 2
  gets the partial build above; the builder refuses to write a pack that does not fit.
- The pack contains no translated strings; the UI stays English.
- Every file is checked by `verify_pbz.py` / `verify_lang_pack.py` (CRCs, resource diffs, hash lookup of every Vietnamese letter, hook shapes). The 4.4.3 Time/Time Steel builds boot on hardware; on-device checks of 36px sizing and the new hook shapes are still pending.
- About 1 KB of the resource bank is left free on every build (by design, see above).

## Reproducing the current builds (Rebble 4.4.3-rbl)

```
# Time and Time Steel
python3 build_vn_pbz.py --skip-large 36 --skip-large 09 --patcher-dir legacy-firmware-patcher --pbl vi_VN_v16_1.pbl \
    --version v4.4.3-rbl-vn  Pebble-4.4.3-rbl-snowy_s3.pbz  dist/Pebble-4.4.3-rbl-vn-snowy_s3.pbz
# Time Round
python3 build_vn_pbz.py --skip-large 09 ... Pebble-4.4.3-rbl-spalding.pbz  dist/Pebble-4.4.3-rbl-vn-spalding.pbz
# Pebble 2: only Đ đ Ơ ơ Ư ư in the base fonts, the rest comes from the language pack
python3 build_vn_pbz.py --no-large --only-codepoints 110,111,1A0,1A1,1AF,1B0 ... Pebble-4.4.3-rbl-silk.pbz  dist/Pebble-4.4.3-rbl-vn-silk.pbz
# language pack
python3 build_lang_pack.py --patcher-dir legacy-firmware-patcher --pbl vi_VN_v16_1.pbl --stock-pbz Pebble-4.4.3-rbl-spalding.pbz dist/vi-VN_v19.pbl
```

`hook_style.py` holds the revised hook-above style (see its docstring); both builders apply it.

At 28px (regular and bold) `capital_marks.py` re-places the grave/acute/tilde on capital Â Ă Ê Ô (up-right of the circumflex apex with a gap row, tilde/breve combos centred) and `hook_shape.py` redraws the hook-above as a "?" with a blank row between it and any circumflex/breve below. Capitals with a circumflex/breve get a 3-row "?" because a 4-row one plus the gap would rise above the top row. Both builders apply it to 28px fonts only.
