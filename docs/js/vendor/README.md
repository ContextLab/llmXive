# Vendored third-party libraries

These files are committed copies of small, audited open-source libraries used by
the static site (which has no build step). They are intentionally placed here —
not loaded loose, not from a CDN — so the site stays self-contained and the
licenses are recorded.

## `markdown.min.js`

- **Library**: [snarkdown](https://github.com/developit/snarkdown)
- **Version**: 2.0.0
- **License**: MIT (© Jason Miller)
- **Source**: <https://unpkg.com/snarkdown@2.0.0/dist/snarkdown.umd.js>
- **Why**: a ~2 KB Markdown → HTML renderer for showing `.md` artifacts (project
  ideas, agent prompts, pipeline-step descriptions) inline in modals. UMD build —
  exposes `window.snarkdown(src)`.
- **Wrapper**: `web/js/markdown.js` wraps it with output sanitization
  (`renderMarkdown` / `fetchAndRenderMarkdown`) — always call the wrapper, never
  `snarkdown` directly, so untrusted Markdown can't inject `<script>` /
  `on*=` handlers / `javascript:` URLs.

To update: download a new build to this file, bump the version above, and
re-test the modals that render Markdown.
