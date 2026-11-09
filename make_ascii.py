#!/usr/bin/env python3
"""Turn a photo into the ASCII portrait used on the profile card.

Run it once on your own computer; only the text it writes (ascii.txt) goes in the repo,
never the photo itself.

    python3 make_ascii.py photo.jpg            # writes ascii.txt and ascii_light.txt
    python3 make_ascii.py photo.jpg --preview  # also prints it

Needs Pillow (pip install pillow).
"""
import argparse

from PIL import Image, ImageOps

# Dark to bright. On the dark card, bright pixels get the densest characters.
RAMP = " .'`^\",:;Il!i><~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"

COLS, ROWS = 40, 25          # matches the card: 25 lines, 20 px apart
CELL_ASPECT = 20 / 9.6       # line height / character width of a 16 px monospace font


def to_ascii(path, cols=COLS, rows=ROWS, background_cutoff=None, invert=False, gamma=1.0, crop=None):
    img = Image.open(path)
    img = ImageOps.exif_transpose(img).convert("L")
    if crop:  # fractions of width/height: left, top, right, bottom
        w, h = img.size
        l, t, r, b = crop
        img = img.crop((int(l * w), int(t * h), int(r * w), int(b * h)))

    # Crop the middle of the photo to the shape the text block will have.
    target = cols / (rows * CELL_ASPECT)
    w, h = img.size
    if w / h > target:
        new_w = int(h * target)
        left = (w - new_w) // 2
        img = img.crop((left, 0, left + new_w, h))
    else:
        new_h = int(w / target)
        top = max(0, (h - new_h) // 3)  # keep more of the top, where the face usually is
        img = img.crop((0, top, w, top + new_h))

    img = img.resize((cols, rows), Image.LANCZOS)
    img = ImageOps.autocontrast(img, cutoff=2)
    if invert:
        img = ImageOps.invert(img)

    dark, light = [], []
    for y in range(rows):
        d_row, l_row = [], []
        for x in range(cols):
            v = img.getpixel((x, y)) / 255
            if background_cutoff is not None and v >= background_cutoff:
                d_row.append(" ")
                l_row.append(" ")
                continue
            v = v ** gamma
            # Dark card: light text, so bright skin gets dense characters.
            d_row.append(RAMP[min(len(RAMP) - 1, int(v * len(RAMP)))])
            # Light card: dark text, so the mapping flips and dark hair gets dense characters.
            l_row.append(RAMP[min(len(RAMP) - 1, int((1 - v) * len(RAMP)))])
        dark.append("".join(d_row).rstrip())
        light.append("".join(l_row).rstrip())
    return dark, light


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("photo")
    p.add_argument("--out", default="ascii.txt")
    p.add_argument("--cols", type=int, default=COLS)
    p.add_argument("--rows", type=int, default=ROWS)
    p.add_argument("--background-cutoff", type=float, default=None,
                   help="0-1; pixels brighter than this become blank (for a plain light background)")
    p.add_argument("--invert", action="store_true", help="swap light and dark")
    p.add_argument("--gamma", type=float, default=1.0, help="above 1 darkens, below 1 brightens")
    p.add_argument("--crop", type=lambda v: [float(x) for x in v.split(",")], default=None,
                   help="left,top,right,bottom as fractions, e.g. 0.12,0.08,0.88,0.78 to frame the head")
    p.add_argument("--preview", action="store_true")
    a = p.parse_args()

    dark, light = to_ascii(a.photo, a.cols, a.rows, a.background_cutoff, a.invert, a.gamma, a.crop)
    light_out = a.out.replace(".txt", "_light.txt")
    for path, lines in ((a.out, dark), (light_out, light)):
        with open(path, "w") as f:
            f.write("\n".join(lines) + "\n")
    if a.preview:
        print("\n".join(dark))
    print(f"wrote {a.out} and {light_out} ({a.cols}x{a.rows})")


if __name__ == "__main__":
    main()
