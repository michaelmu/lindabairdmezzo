# Deploy to AWS S3 via GitHub Actions

This repo also deploys the static site to **Amazon S3** from **GitHub Actions** using **GitHub OIDC** and a short-lived AWS IAM role.

This does **not** replace the existing GitHub Pages deploy. Pages still handles staging and the existing public GitHub-hosted site.

The workflow is:

- `.github/workflows/deploy-s3.yml`
- `main` branch -> production deploy to S3/CloudFront

## Deployment model

The workflow only pushes built files to S3 and optionally invalidates CloudFront.

It does **not** provision AWS infrastructure.

Recommended production shape:

- S3 bucket for site artifacts
- CloudFront distribution in front of the bucket
- Optional S3 prefix if you are serving production from a non-root path

## GitHub Actions variables

Set these in:

- Repo -> Settings -> Secrets and variables -> Actions -> Variables

Required:

- `AWS_REGION`
- `AWS_ROLE_ARN`
- `AWS_S3_BUCKET_PROD`

Optional:

- `S3_PREFIX_PROD`
  - default: empty
- `SITE_BASE_PATH_PROD`
  - default: `/`
- `CLOUDFRONT_DISTRIBUTION_ID_PROD`
- `CLOUDFRONT_INVALIDATION_PATHS_PROD`
  - default: `/*`

Notes:

- `SITE_BASE_PATH_PROD` must match how the site is actually served, not just where objects live in S3.
- If you upload into a prefix such as `public/` but serve the site from the domain root through CloudFront, keep `SITE_BASE_PATH_PROD=/`.

## AWS setup

### 1. Create the S3 bucket setup

Create the production bucket or production prefix you want the workflow to sync into.

If you use CloudFront with a private bucket, keep S3 Block Public Access enabled and configure CloudFront origin access separately.

If you use the S3 website endpoint directly, you will need public-read website hosting, which is simpler but weaker and does not give you the same HTTPS/custom-domain flexibility as CloudFront.

### 2. Add the GitHub OIDC provider in IAM

Use:

- provider URL: `https://token.actions.githubusercontent.com`
- audience: `sts.amazonaws.com`

Reference:

- GitHub OIDC in AWS: `docs.github.com/.../oidc-in-aws`
- AWS OIDC provider setup: `docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html`

### 3. Create the deploy role

Use the trust policy template in:

- `ops/aws/github-oidc-trust-policy.json`

Replace:

- `<AWS_ACCOUNT_ID>`

This template is scoped to `repo:michaelmu/lindabairdmezzo:ref:refs/heads/main`.

### 4. Attach the deploy permissions policy

Use the permissions template in:

- `ops/aws/s3-deploy-policy.json`

Replace:

- `<BUCKET_NAME>`
- `<AWS_ACCOUNT_ID>`
- `<CLOUDFRONT_DISTRIBUTION_ID>`

If you are not using CloudFront invalidation yet, remove the `InvalidateCloudFront` statement.

## GitHub CLI examples

Once you know the values, you can set repo variables with `gh`:

```bash
gh variable set AWS_REGION --body us-west-2
gh variable set AWS_ROLE_ARN --body arn:aws:iam::123456789012:role/github-actions-lindabairdmezzo-deploy
gh variable set AWS_S3_BUCKET_PROD --body linda-site-prod
gh variable set SITE_BASE_PATH_PROD --body /
gh variable set CLOUDFRONT_DISTRIBUTION_ID_PROD --body E1234567890ABC
```

## Local build parity

The workflow builds with:

```bash
npm ci
PATH_PREFIX=/ npm run build
```

Examples:

```bash
PATH_PREFIX=/ npm run build
```

## Operational notes

- The workflow uses `aws-actions/configure-aws-credentials` with OIDC, so no long-lived AWS secret keys are required in GitHub.
- The workflow assumes `aws` is available on the GitHub-hosted runner.
- The repo is static; deploy output is `_site/`.
