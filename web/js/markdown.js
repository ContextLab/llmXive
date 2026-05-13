// llmXive — Markdown → sanitized HTML wrapper around the vendored snarkdown.
//
// ALWAYS use these helpers (never window.snarkdown directly): the output is
// sanitized so untrusted Markdown (a project idea, an agent prompt fetched from
// GitHub) can't inject <script>, on*= event handlers, or javascript: URLs.

(function () {
  function _sanitize(html) {
    // Parse into a detached document, strip dangerous nodes/attrs, re-serialize.
    const doc = new DOMParser().parseFromString(
      "<div id='__md_root__'>" + html + "</div>", "text/html"
    );
    const root = doc.getElementById("__md_root__");
    if (!root) return "";
    root.querySelectorAll("script, style, iframe, object, embed, link, meta, base, form")
      .forEach(n => n.remove());
    root.querySelectorAll("*").forEach(el => {
      [...el.attributes].forEach(attr => {
        const name = attr.name.toLowerCase();
        const val = (attr.value || "").trim();
        if (name.startsWith("on")) { el.removeAttribute(attr.name); return; }
        if ((name === "href" || name === "src" || name === "xlink:href")) {
          // allow only http(s), mailto, relative, and anchor links
          if (/^\s*(javascript|data|vbscript):/i.test(val)) {
            el.removeAttribute(attr.name);
            return;
          }
        }
        if (name === "style") { el.removeAttribute(attr.name); }
      });
      // Force external links to open safely.
      if (el.tagName === "A" && el.getAttribute("href") && /^https?:/i.test(el.getAttribute("href"))) {
        el.setAttribute("target", "_blank");
        el.setAttribute("rel", "noopener noreferrer");
      }
    });
    return root.innerHTML;
  }

  // Map fenced-code-block info-strings (the bit after ```) to a Prism
  // language alias. snarkdown emits e.g. ```python\n…``` as
  // <pre><code class="language-python">…</code></pre>, so the class is
  // already there — but we also normalize a few common aliases to the
  // canonical Prism name so highlighting is consistent.
  const _LANG_ALIASES = {
    py: "python", sh: "bash", shell: "bash",
    js: "javascript", jsx: "javascript",
    yml: "yaml", md: "markdown", html: "markup", xml: "markup",
  };
  function _normalizeCodeLang(el) {
    if (!el || !el.classList) return;
    for (const cls of [...el.classList]) {
      const m = cls.match(/^language-(.+)$/i);
      if (!m) continue;
      const canon = _LANG_ALIASES[m[1].toLowerCase()];
      if (canon && canon !== m[1].toLowerCase()) {
        el.classList.remove(cls);
        el.classList.add("language-" + canon);
      }
    }
  }

  // Run Prism over a freshly-injected `.md-body` container. Safe to call
  // even when Prism isn't loaded — silently no-ops. Highlighting only
  // mutates the inner content of <code> elements that already have a
  // `language-*` class (which the renderer just produced from fenced
  // blocks), so we're not introducing new HTML sinks here.
  function highlightCodeBlocks(rootEl) {
    if (!rootEl || !window.Prism || typeof Prism.highlightElement !== "function") return;
    rootEl.querySelectorAll("pre > code[class*='language-'], code[class*='language-']").forEach(el => {
      _normalizeCodeLang(el);
      try { Prism.highlightElement(el); } catch (_) { /* swallow per-block errors */ }
    });
  }

  // Render a Markdown string to sanitized HTML. Always passes through
  // `_sanitize()` — see the sanitize comments above — before returning, so
  // callers can safely insert the result via insertAdjacentHTML.
  function renderMarkdown(rawMd) {
    if (rawMd == null) return "";
    const md = String(rawMd);
    const renderer = window.snarkdown;
    if (typeof renderer !== "function") {
      // Fallback: no renderer loaded — escape and preserve line breaks.
      const esc = md.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
      return "<pre class=\"md-fallback\">" + esc + "</pre>";
    }
    // snarkdown is block-naive about paragraphs; render block-by-block so blank
    // lines become paragraph breaks, then sanitize the whole thing.
    const blocks = md.replace(/\r\n/g, "\n").split(/\n{2,}/);
    const html = blocks.map(b => {
      const t = b.trim();
      if (!t) return "";
      const out = renderer(t);
      // If snarkdown already produced a block-level element, don't wrap it.
      return /^\s*<(h[1-6]|ul|ol|li|blockquote|pre|table|hr|p|div)\b/i.test(out)
        ? out : "<p>" + out + "</p>";
    }).join("\n");
    return _sanitize(html);
  }

  // Render Markdown into a target element AND syntax-highlight the result.
  // The HTML is sanitized by `renderMarkdown` first, then attached via
  // `replaceChildren` + `insertAdjacentHTML` (matches the pattern used in
  // dialog.js). Use this when injecting into the DOM — Prism walks the live
  // nodes so highlighting must happen AFTER the HTML is attached.
  function renderMarkdownInto(rootEl, rawMd) {
    if (!rootEl) return;
    const safeHtml = renderMarkdown(rawMd);
    rootEl.replaceChildren();
    rootEl.insertAdjacentHTML("beforeend", safeHtml);
    highlightCodeBlocks(rootEl);
  }

  // Fetch a .md file from a raw.githubusercontent.com URL and render it.
  async function fetchAndRenderMarkdown(rawUrl) {
    if (!rawUrl) throw new Error("no URL");
    const r = await fetch(rawUrl, { cache: "no-cache" });
    if (!r.ok) throw new Error("HTTP " + r.status + " fetching " + rawUrl);
    const text = await r.text();
    return renderMarkdown(text);
  }

  // Same as fetchAndRenderMarkdown, but injects directly into a target
  // element AND runs syntax highlighting. Use this for agent prompts,
  // pipeline-step descriptions, project ideas — anywhere we want fenced
  // code blocks to look styled rather than monochrome.
  async function fetchAndRenderMarkdownInto(rootEl, rawUrl) {
    const safeHtml = await fetchAndRenderMarkdown(rawUrl);
    if (!rootEl) return;
    rootEl.replaceChildren();
    rootEl.insertAdjacentHTML("beforeend", safeHtml);
    highlightCodeBlocks(rootEl);
  }

  window.LlmxiveMarkdown = {
    renderMarkdown, fetchAndRenderMarkdown,
    renderMarkdownInto, fetchAndRenderMarkdownInto,
    highlightCodeBlocks,
  };
})();
