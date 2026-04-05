import fs from "node:fs";
import path from "node:path";
import yaml from "js-yaml";

function readYaml(filePath) {
  const raw = fs.readFileSync(filePath, "utf8");
  return yaml.load(raw);
}

export default function (eleventyConfig) {
  // Static assets
  eleventyConfig.addPassthroughCopy({ "include": "include" });
  eleventyConfig.addPassthroughCopy({ "favicon.ico": "favicon.ico" });

  // Content data (repo-owned)
  eleventyConfig.addGlobalData("aboutHtml", () => fs.readFileSync("content/about.md", "utf8"));
  eleventyConfig.addGlobalData("photos", () => readYaml("content/photos.yml").photos ?? []);
  eleventyConfig.addGlobalData("videos", () => readYaml("content/videos.yml").videos ?? []);
  eleventyConfig.addGlobalData("resume", () => readYaml("content/resume.yml").resume ?? []);
  eleventyConfig.addGlobalData("engagements", () => readYaml("content/engagements.yml").engagements ?? []);
  eleventyConfig.addGlobalData("currentYear", () => String(new Date().getFullYear()));

  // GitHub Pages path prefix (set by CI). Examples:
  // - /lindabairdmezzo/
  // - /lindabairdmezzo/staging/
  const prefix = process.env.PATH_PREFIX || "/";

  return {
    pathPrefix: prefix,
    dir: {
      input: "src",
      output: "_site",
      includes: "_includes"
    }
  };
}
