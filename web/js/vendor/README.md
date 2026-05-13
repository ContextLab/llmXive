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

## `prism.min.js`

- **Library**: [Prism](https://prismjs.com/)
- **Version**: 1.29.0
- **License**: MIT
- **Source**: cdnjs Prism 1.29.0 components, concatenated in load order:
  - `prism-core.min.js`
  - `prism-markup.min.js`
  - `prism-clike.min.js`
  - `prism-javascript.min.js`
  - `prism-bash.min.js`
  - `prism-json.min.js`
  - `prism-yaml.min.js`
  - `prism-python.min.js`
  - `prism-markdown.min.js`
- **Why**: syntax highlighting for code blocks rendered from agent prompts
  (Python tools, bash hooks, YAML config snippets, JSON contracts, etc.).
  Themed in `css/site.css` to match the site palette — Dartmouth-green
  keywords + accent strings + muted comments.
- **Wrapper**: `web/js/markdown.js` calls `Prism.highlightElement(el)` on
  every `<code class="language-*">` block produced by `renderMarkdown` /
  `fetchAndRenderMarkdown`. Auto-detects language hints from snarkdown's
  fenced-code-block class.

To update: re-download each component from cdnjs at the new version, bump
the version above, re-concatenate in the SAME ORDER (core first, then markup,
then clike, then the rest), and re-test the agent-registry + artifact
modals.
