import { defineConfig } from 'astro/config';

function normalizeBase(v) {
  if (!v) return '/';
  // ensure leading and trailing slash
  let b = v;
  if (!b.startsWith('/')) b = '/' + b;
  if (!b.endsWith('/')) b = b + '/';
  return b;
}

// PATH_PREFIX is set by CI for GitHub Pages.
// Examples:
// - /lindabairdmezzo/
// - /lindabairdmezzo/staging/
const base = normalizeBase(process.env.PATH_PREFIX || '/');

export default defineConfig({
  base,
  outDir: './_site',
});
