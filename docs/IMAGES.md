# Images (Gallery thumbnails)

The site’s Gallery is optimized for fast initial loads:

- The masonry grid uses **small thumbnails**.
- The **full-size** images are only fetched when a visitor clicks an image (lightbox).

## Where files live

- Full-size images: `include/images/gallery/<file>`
- Thumbnails: `include/images/gallery/thumbs/<file>`

The thumbnail filename matches the original filename.

## Adding a new gallery photo

1. Add the full-size image to `include/images/gallery/`
2. Add an entry to `content/photos.yml` with `file:` and `captionHtml:`
3. Generate/update thumbnails (also updates `content/photos_meta.json` used for layout-stable placeholders):

```bash
python3 tools/generate_gallery_thumbs.py
```

Defaults: thumbnails are generated at **520px wide** (max) and saved as optimized JPEGs.

### Optional

- Remove thumbnails for images no longer referenced:

```bash
python3 tools/generate_gallery_thumbs.py --clean
```

## Notes

- The script respects EXIF orientation (via `ImageOps.exif_transpose`).
- Thumbnails are committed to the repo so the static deploy workflow pushes them automatically.
