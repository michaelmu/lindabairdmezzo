# Deploy process (staging → production)

This site is a **purely static** site built with **Eleventy (11ty)**.

## Branches

- `staging` → staging deploy
- `main` → production deploy

## URLs

- Staging: https://michaelmu.github.io/lindabairdmezzo/staging/
- Production: https://michaelmu.github.io/lindabairdmezzo/

## How deploy works

GitHub Actions (`.github/workflows/pages.yml`) builds the site and publishes to the `gh-pages` branch.

- On pushes to `staging`, the build uses `PATH_PREFIX=/lindabairdmezzo/staging/` and publishes into the `staging/` folder on `gh-pages`.
- On pushes to `main`, the build uses `PATH_PREFIX=/lindabairdmezzo/` and publishes to the root of `gh-pages`.

## One-time GitHub Pages setup (required)

Until GitHub Pages is enabled, the URLs above will return **404** even if `gh-pages` has the files.

In GitHub:

1. Repo → **Settings → Pages**
2. Source: **Deploy from a branch**
3. Branch: **gh-pages**
4. Folder: **/(root)**
5. Save

## Local build

```bash
npm install
npm run build
# output: _site/
```

To preview locally:

```bash
npm run serve
```

## Content editing

Non-technical edits live in `content/`:

- `content/about.md`
- `content/photos.yml`
- `content/videos.yml`
- `content/resume.yml`
- `content/engagements.yml`

## Typical workflow

1. Make changes on a feature branch.
2. Merge into `staging`.
3. Linda reviews staging URL.
4. Merge `staging` → `main` to ship production.

## Troubleshooting

### Staging/prod URL returns 404
- GitHub Pages likely not enabled (see One-time setup).

### CSS/images are broken on Pages
- Path prefix might be wrong. Confirm `PATH_PREFIX` values in the workflow and that generated HTML links include `/lindabairdmezzo/…`.

### Staging overwrote production
- Ensure workflow deploy uses `destination_dir` + `keep_files: true`.
