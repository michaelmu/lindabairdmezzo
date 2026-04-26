# lindabairdmezzo

Linda Baird’s static website.

## Local development

Prereqs: Node 20+

```bash
npm ci --include=dev
npm run serve
```

Astro outputs the static site to `_site/`.

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

## Deploy (staging -> production)

This repo uses GitHub Actions with two deployment targets:

- **GitHub Pages**
  - `staging` -> `/staging/`
  - `main` -> `/`
- **Amazon S3**
  - `main` only

See:

- `docs/DEPLOY.md`
- `docs/DEPLOY-AWS-S3.md`

## Analytics

- Analytics page route: `/analytics/`
- Snapshot source files: `content/analytics/`
- Current cuts: traffic trends, top pages, device type, browser family, operating system, and referrer source
- Refresh locally:

```bash
npm run analytics:export
```

- Scheduled refresh workflow: `.github/workflows/refresh-analytics.yml` (hourly at `:17` past the hour UTC)
