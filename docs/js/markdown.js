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

  // Render a Markdown string to sanitized HTML.
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

  // Fetch a .md file from a raw.githubusercontent.com URL and render it.
  async function fetchAndRenderMarkdown(rawUrl) {
    if (!rawUrl) throw new Error("no URL");
    const r = await fetch(rawUrl, { cache: "no-cache" });
    if (!r.ok) throw new Error("HTTP " + r.status + " fetching " + rawUrl);
    const text = await r.text();
    return renderMarkdown(text);
  }

  window.LlmxiveMarkdown = { renderMarkdown, fetchAndRenderMarkdown };
})();
