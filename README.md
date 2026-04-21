# lindabairdmezzo

Linda Baird’s static website.

## Local development

Prereqs: Node 20+

```bash
npm install
npm run serve
```

Eleventy outputs the static site to `_site/`.

## Content editing (non-technical)

Edit these files:

- `content/about.md` — About section (HTML allowed)
- `content/videos.yml` — YouTube embeds + captions
- `content/photos.yml` — Gallery images + captions
- `content/resume.yml` — Resume table
- `content/engagements.yml` — Engagements table

### Gallery images (important)

The gallery uses **thumbnails** for fast page load.

- Full-size images go in `include/images/gallery/`
- Thumbnails are generated into `include/images/gallery/thumbs/`

After adding or changing gallery images, run:

```bash
python3 tools/generate_gallery_thumbs.py
```

Details: `docs/IMAGES.md`

## Deploy (staging → production)

This repo uses GitHub Pages with two deploy targets:

- **Staging:** push/merge to the `staging` branch → publishes to `/staging/`
- **Production:** merge to `main` → publishes to `/`

See: `docs/DEPLOY.md` (includes the **one-time GitHub Pages enablement step**).
