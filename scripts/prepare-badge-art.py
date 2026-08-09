#!/usr/bin/env python3
"""One-time prep of the Badge Forge artwork (images/badge-art.png).

Input is the AI-rendered club medallion (silver on black, photographic). It
arrives with three problems for forge use, all fixed here:

  1. A serif "BKG" is baked into the centre field where the forge draws the
     member's callsign. Those glyphs (plus their emboss halo) are healed back
     to matte black by diffusion inpainting — every masked pixel is iteratively
     averaged from its neighbours until the field's own sheen flows through —
     then re-grained to match the surrounding texture. Everything else (the
     divider dashes, the thin ring under the text, the arcs) is untouched.
  2. The medallion sits on an opaque near-white ground with a baked drop
     shadow, and its polished rim genuinely dissolves into that white (there
     is no drawn outer edge). The badge circle is fitted from edge chords,
     everything outside made transparent, and the outermost few pixels are
     gently darkened so the coin has a machined edge on any background.
  3. A ~28 KB C2PA metadata block and 24-bit colour we don't need: the render
     is greyscale start to finish, so a 256-colour palette is visually
     lossless and cuts the committed file roughly 10x.

Run from the repo root:  python3 scripts/prepare-badge-art.py <input.png> [checkdir]
Writes images/badge-art.png and a before/after check image to [checkdir].

Deliberately NOT run in CI — the 2 MB input render is not committed. This
script documents how images/badge-art.png was produced and lets someone redo
it if the artwork is ever regenerated.
"""

import sys
import pathlib

import numpy as np
from PIL import Image

REPO = pathlib.Path(__file__).resolve().parent.parent

# Region of the baked "BKG" lettering, with margin (source-pixel coords).
TEXT_BOX = (455, 755, 815, 915)          # x0, y0, x1, y1

# Fitted below; the rim's bright gradient reaches background level here.
RIM_EDGE_DARKEN = 8                       # px of edge rolled down in tone
ALPHA_FEATHER = 2.0                       # px of soft alpha at the cut


def fit_badge_circle(lum):
    """Fit the badge's outer circle from horizontal edge chords.

    The polished rim is the same luminance as the white ground, so the
    reliable landmark is the dark ring just inside it (lum minimum ~48 at
    r~526). Chords are sampled across the middle half of the image — clear of
    the baked drop shadow, which hugs the bottom — and the circle is
    least-squares fitted with one outlier-rejection pass.
    """
    H, W = lum.shape
    pts = []
    for y in range(H // 4, 3 * H // 4, 6):
        dark = np.nonzero(lum[y] < 190)[0]
        if dark.size < 50:
            continue
        pts.append((dark.min(), y))
        pts.append((dark.max(), y))
    pts = np.asarray(pts, float)

    def lsq_circle(p):
        A = np.c_[p[:, 0], p[:, 1], np.ones(len(p))]
        b = -(p[:, 0] ** 2 + p[:, 1] ** 2)
        (D, E, F), *_ = np.linalg.lstsq(A, b, rcond=None)
        cx, cy = -D / 2, -E / 2
        return cx, cy, np.sqrt(cx * cx + cy * cy - F)

    cx, cy, r = lsq_circle(pts)
    d = np.abs(np.hypot(pts[:, 0] - cx, pts[:, 1] - cy) - r)
    keep = d < np.percentile(d, 80)
    return lsq_circle(pts[keep])


def dilate(mask, px):
    """Binary dilation by a px-radius square, no scipy needed."""
    out = mask.copy()
    for _ in range(px):
        grown = out.copy()
        grown[1:, :] |= out[:-1, :]
        grown[:-1, :] |= out[1:, :]
        grown[:, 1:] |= out[:, :-1]
        grown[:, :-1] |= out[:, 1:]
        out = grown
    return out


def diffusion_inpaint(channel, mask, iters=700):
    """Fill masked pixels by repeatedly averaging their 4-neighbours.

    Converges to the smooth (harmonic) surface spanned by the surrounding
    field, which is exactly right for matte black with a soft radial sheen.
    """
    filled = channel.copy()
    filled[mask] = filled[~mask].mean()
    for _ in range(iters):
        avg = (np.roll(filled, 1, 0) + np.roll(filled, -1, 0) +
               np.roll(filled, 1, 1) + np.roll(filled, -1, 1)) / 4.0
        filled[mask] = avg[mask]
    return filled


def main():
    src = pathlib.Path(sys.argv[1])
    im = Image.open(src).convert("RGB")
    a = np.asarray(im).astype(np.float32)
    H, W, _ = a.shape
    lum = a.mean(axis=2)

    cx, cy, r_dark = fit_badge_circle(lum)
    # Rim gradient measured on the source: dark-ring minimum at r_dark, rim
    # brightens outward and merges with the background ~30px later. Cutting a
    # touch inside that keeps the outermost kept pixel silver, not background.
    r_out = r_dark + 30
    print(f"badge circle: centre ({cx:.1f}, {cy:.1f}), dark ring r {r_dark:.1f}, cut r {r_out:.1f}")

    # ---- heal the baked lettering --------------------------------------
    # Mask the letters only. A thin engraved ring passes right under the
    # lettering, and a plain brightness threshold would catch it too and heal
    # a gap into it. Letters are distinguished structurally: a bright
    # connected component that stays fully inside the text box is a letter; a
    # component that touches the box border (the ring, the arcs) continues
    # outside and is protected.
    x0, y0, x1, y1 = TEXT_BOX
    box = np.zeros_like(lum, bool)
    box[y0:y1, x0:x1] = True
    bright = box & (lum > 45)

    # component labelling by iterative label-minimisation (no scipy)
    lab = np.where(bright, np.arange(lum.size, dtype=np.int64).reshape(lum.shape), -1)
    while True:
        n = lab.copy()
        for ax, sh in ((0, 1), (0, -1), (1, 1), (1, -1)):
            r = np.roll(lab, sh, axis=ax)
            np.copyto(n, r, where=bright & (r >= 0) & ((n < 0) | (r < n)))
        if np.array_equal(n, lab):
            break
        lab = n
    border = np.zeros_like(bright)
    border[y0, x0:x1] = border[y1 - 1, x0:x1] = True
    border[y0:y1, x0] = border[y0:y1, x1 - 1] = True
    passing_through = np.unique(lab[border & bright])
    letters = bright & ~np.isin(lab, passing_through)
    # Dilate far enough to swallow the letters' dark emboss halo — if any of
    # it survives at the mask boundary, the diffusion drags its darkness
    # inward and a ghost of the lettering remains in the healed field.
    mask = dilate(letters, 13) & box & ~dilate(bright & ~letters, 2)
    print(f"inpainting {mask.sum():,} px "
          f"({np.isin(lab[bright], passing_through).sum():,} ring/arc px protected)")

    sub = slice(y0 - 20, y1 + 20), slice(x0 - 20, x1 + 20)
    m = mask[sub]
    for c in range(3):
        a[sub + (c,)] = diffusion_inpaint(a[sub + (c,)], m)

    # matte grain to match the field (measured sd ~3), only on healed pixels
    rng = np.random.default_rng(73)
    noise = rng.normal(0, 2.8, a[sub].shape[:2])
    for c in range(3):
        a[sub + (c,)][m] += noise[m]

    # ---- transparent outside the circle, machined edge -----------------
    # The rim is a polished gradient that runs all the way to background
    # white, so a bare cut would end in white-on-anything. A shallow tone
    # roll-off over the outer few pixels gives the coin a defined machined
    # edge without repainting the rim.
    Y, X = np.mgrid[0:H, 0:W].astype(np.float32)
    dist = np.hypot(X - cx, Y - cy)
    alpha = np.clip((r_out - dist) / ALPHA_FEATHER + 0.5, 0, 1) * 255
    edge = np.clip((dist - (r_out - RIM_EDGE_DARKEN)) / RIM_EDGE_DARKEN, 0, 1)
    a *= (1 - 0.35 * edge ** 2)[..., None]

    out = np.dstack([np.clip(a, 0, 255).astype(np.uint8), alpha.astype(np.uint8)])
    img = Image.fromarray(out, "RGBA")

    # FASTOCTREE is the only PIL quantizer that keeps the alpha channel.
    q = img.quantize(colors=256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.FLOYDSTEINBERG)
    dest = REPO / "images" / "badge-art.png"
    q.save(dest, optimize=True)
    print(f"wrote {dest} ({dest.stat().st_size / 1024:.0f} KB, {img.size[0]}x{img.size[1]})")

    # ---- visual check --------------------------------------------------
    checkdir = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else REPO
    check = Image.new("RGB", (W * 2 + 30, H), (24, 24, 24))
    check.paste(im, (0, 0))
    on_grey = Image.new("RGBA", (W, H), (110, 110, 110, 255))
    on_grey.alpha_composite(Image.open(dest).convert("RGBA"))
    check.paste(on_grey.convert("RGB"), (W + 30, 0))
    cp = checkdir / "badge-art-check.png"
    check.save(cp)
    print(f"check image: {cp}")


if __name__ == "__main__":
    main()
