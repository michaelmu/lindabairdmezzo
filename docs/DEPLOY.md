# Deploy process (staging -> production)

This site is a **purely static** site built with **Astro**.

## Branches

- `staging` → staging deploy
- `main` → production deploy

## URLs

- GitHub Pages staging: https://michaelmu.github.io/lindabairdmezzo/staging/
- GitHub Pages production: https://michaelmu.github.io/lindabairdmezzo/
- S3/CloudFront production: depends on your AWS setup

## How deploy works

This repo now has two deploy workflows:

- GitHub Pages: `.github/workflows/pages.yml`
  - On pushes to `staging`, the build uses `PATH_PREFIX=/lindabairdmezzo/staging/` and publishes into `staging/` on `gh-pages`.
  - On pushes to `main`, the build uses `PATH_PREFIX=/lindabairdmezzo/` and publishes to the root of `gh-pages`.
- Amazon S3: `.github/workflows/deploy-s3.yml`
  - On pushes to `main`, the build uses the configured production base path and syncs `_site/` into Amazon S3.
  - AWS auth uses GitHub OIDC and a short-lived IAM role, not long-lived secret keys.

## One-time GitHub Pages setup (required)

Until GitHub Pages is enabled, the URLs above will return `404` even if `gh-pages` has the files.

In GitHub:

1. Repo -> **Settings -> Pages**
2. Source: **Deploy from a branch**
3. Branch: **gh-pages**
4. Folder: **/(root)**
5. Save

## One-time AWS/GitHub setup (required for S3 production deploy)

See:

- `docs/DEPLOY-AWS-S3.md`
- `ops/aws/github-oidc-trust-policy.json`
- `ops/aws/s3-deploy-policy.json`

## Local build

```bash
npm ci --include=dev
PATH_PREFIX=/ npm run build
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

### Deploy fails before upload
- Check required repo variables:
  - `AWS_REGION`
  - `AWS_ROLE_ARN`
  - `AWS_S3_BUCKET_PROD`
- Confirm the AWS IAM role trust policy matches this repo and branch names.

### GitHub Pages URL returns 404
- GitHub Pages likely is not enabled yet.

### CSS/images are broken on GitHub Pages
- Path prefix might be wrong. Confirm the `PATH_PREFIX` values in `.github/workflows/pages.yml` and that generated HTML links include `/lindabairdmezzo/...`.

### CSS/images are broken on S3/CloudFront
- Path prefix might be wrong. Confirm `SITE_BASE_PATH_PROD` matches the actual public URL path for the S3-backed site.
