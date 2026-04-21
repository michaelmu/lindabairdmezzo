#!/usr/bin/env python3
"""Generate small thumbnail images for the photo gallery.

Why:
- The gallery grid should load quickly and not “pop” as large images arrive.
- We display *thumbnails* in the masonry grid, and only load the full image
  when a user opens it (lightbox).

What it does:
- Reads `content/photos.yml` for the list of gallery images.
- For each image file in `include/images/gallery/`, writes a thumbnail to:
    include/images/gallery/thumbs/<same filename>.jpg

Defaults:
- Max thumbnail width: 520px (keeps the masonry crisp on retina without being heavy)
- JPEG quality: 72 (visually good, small files)

Usage:
  python3 tools/generate_gallery_thumbs.py

Optional flags:
  --max-width 520
  --quality 72
  --clean        (delete thumbs for images no longer referenced)
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import yaml
from PIL import Image, ImageOps


REPO_ROOT = Path(__file__).resolve().parents[1]
PHOTOS_YML = REPO_ROOT / "content" / "photos.yml"
GALLERY_DIR = REPO_ROOT / "include" / "images" / "gallery"
THUMBS_DIR = GALLERY_DIR / "thumbs"


def load_photo_files() -> list[str]:
    data = yaml.safe_load(PHOTOS_YML.read_text("utf-8")) or {}
    photos = data.get("photos", [])
    files = []
    for p in photos:
        f = (p or {}).get("file")
        if f:
            files.append(str(f))
    return files


def make_thumb(src: Path, dst: Path, max_width: int, quality: int) -> tuple[tuple[int, int], tuple[int, int]]:
    im = Image.open(src)
    # Respect EXIF orientation if present (some phone exports rely on this)
    im = ImageOps.exif_transpose(im)
    im = im.convert("RGB")
    w, h = im.size

    if w > max_width:
        new_h = round(h * (max_width / w))
        im = im.resize((max_width, new_h), Image.Resampling.LANCZOS)

    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst, format="JPEG", quality=quality, optimize=True, progressive=True)
    return (w, h), im.size


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-width", type=int, default=520)
    ap.add_argument("--quality", type=int, default=72)
    ap.add_argument("--clean", action="store_true")
    args = ap.parse_args()

    files = load_photo_files()
    if not files:
        raise SystemExit(f"No photos found in {PHOTOS_YML}")

    THUMBS_DIR.mkdir(parents=True, exist_ok=True)

    referenced_thumbs = set()
    changed = 0

    for fname in files:
        src = GALLERY_DIR / fname
        if not src.exists():
            raise SystemExit(f"Missing gallery image: {src}")

        # Always write thumbs as .jpg with the same base name.
        # (Keeps URL scheme simple: thumbs/<original file name>)
        dst = THUMBS_DIR / (Path(fname).name)
        referenced_thumbs.add(dst.name)

        before = dst.stat().st_size if dst.exists() else None
        orig_size, new_size = make_thumb(src, dst, args.max_width, args.quality)
        after = dst.stat().st_size
        if before != after:
            changed += 1
        print(f"thumb: {fname}  {orig_size[0]}x{orig_size[1]} -> {new_size[0]}x{new_size[1]}  ({after/1024:.0f}KB)")

    if args.clean:
        removed = 0
        for p in THUMBS_DIR.glob("*"):
            if p.is_file() and p.name not in referenced_thumbs:
                p.unlink()
                removed += 1
        if removed:
            print(f"removed {removed} unused thumbs")

    print(f"done. updated {changed} thumbnails")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
