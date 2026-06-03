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

  // Code-fence-aware block splitter. snarkdown is block-naive about
  // paragraphs, so we render block-by-block (blank lines = paragraph
  // breaks) — BUT a naive `split(/\n{2,}/)` shatters fenced code blocks
  // that contain blank lines (very common in agent prompts and code
  // samples) into broken fragments where fences never close. So: walk
  // the source line-by-line, toggling an "inside fence" flag on the
  // exact ``` / ~~~ run that opened the current fence, and only treat
  // blank lines as block separators outside fences. Matches CommonMark
  // §4.5 closely enough for our content (agent prompts, project ideas,
  // technical specs).
  function _splitBlocks(md) {
    const lines = md.split("\n");
    const blocks = [];
    let buf = [];
    let inFence = false;
    let fenceChar = "";   // "`" or "~"
    let fenceLen = 0;      // length of the opener (closer must match or exceed)
    const fenceRe = /^(\s{0,3})(`{3,}|~{3,})(.*)$/;
    const flush = () => {
      if (buf.length && buf.some(l => l.trim() !== "")) {
        blocks.push(buf.join("\n"));
      }
      buf = [];
    };
    for (const line of lines) {
      const m = line.match(fenceRe);
      if (m) {
        const marker = m[2];
        if (!inFence) {
          // opening fence: close any accumulated paragraph block first
          flush();
          inFence = true;
          fenceChar = marker[0];
          fenceLen = marker.length;
          buf.push(line);
          continue;
        }
        // already inside a fence — close only if the marker matches the
        // opener's char and is at least as long (CommonMark §4.5).
        if (marker[0] === fenceChar && marker.length >= fenceLen && m[3].trim() === "") {
          buf.push(line);
          inFence = false;
          fenceChar = "";
          fenceLen = 0;
          flush();
          continue;
        }
      }
      if (inFence) {
        buf.push(line);
        continue;
      }
      if (line.trim() === "") {
        flush();
      } else {
        buf.push(line);
      }
    }
    if (buf.length) flush();
    return blocks;
  }

  // Render a Markdown string to sanitized HTML. Always passes through
  // `_sanitize()` — see the sanitize comments above — before returning, so
  // callers can safely insert the result via insertAdjacentHTML.
  // Strip a leading YAML frontmatter block `---\n...\n---` if present.
  // The project idea files (projects/PROJ-*/idea/*.md) and most authored
  // markdown begin with a YAML frontmatter block that the modal's left
  // pane should NOT render as body content (it leaks the project's
  // metadata as a stream of "field:" / "submitter:" / "paper_authors:"
  // lines, which is what the user reported on PROJ-583's MinT card).
  // Strips ONLY when the file begins with `---` on its own line, has a
  // matching closing `---` on its own line, and the closing fence is
  // within the first ~10 KiB (avoids accidentally swallowing horizontal
  // rules in long-form content).
  function _stripFrontmatter(md) {
    if (!md || !md.startsWith("---")) return md;
    // The opening fence must be its own line: `---\n`. `md.charAt(3)` is
    // either '\n' (own-line fence) or '-'/whitespace (a wider HR).
    if (md.charAt(3) !== "\n") return md;
    // Find the closing fence — a line that is EXACTLY `---`. Restrict the
    // search to the first 10 KiB so a runaway document never spends time
    // here.
    const head = md.slice(4, 10 * 1024);
    const m = head.match(/(^|\n)---(\n|$)/);
    if (!m) return md;
    const endIdx = 4 + m.index + m[0].length;
    return md.slice(endIdx).replace(/^\n+/, "");
  }

  // GFM pipe-table preprocessor. snarkdown (the vendored renderer) has NO
  // table grammar, so GFM pipe tables pass through as literal `| a | b |`
  // text and the CSS `<table>` rules never apply. We convert standard GFM
  // pipe tables to real <table> HTML BEFORE snarkdown runs.
  //
  // A table is: a header row (`| a | b |`), a delimiter row
  // (`|---|:--:|` — hyphen runs with optional leading/trailing `:` for
  // alignment), and ≥1 body rows. Pipes may optionally lead/trail each row.
  // Alignment is emitted as an `align="left|center|right"` attribute (the
  // markdown sanitizer strips `style=`, but standard table attrs survive).
  // Inline markdown inside a cell is rendered by running snarkdown's inline
  // parser over the cell text and stripping the wrapping <p>; if no renderer
  // is available the cell content is HTML-escaped plain text.
  const _TABLE_DELIM_RE = /^\s*\|?\s*:?-{1,}:?\s*(\|\s*:?-{1,}:?\s*)*\|?\s*$/;
  function _escapeHtml(s) {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
  // Split a `| a | b | c |` row into trimmed cell strings, honoring `\|`
  // escapes and tolerating optional leading/trailing pipes.
  function _splitRow(line) {
    let s = line.trim();
    if (s.startsWith("|")) s = s.slice(1);
    if (s.endsWith("|") && !s.endsWith("\\|")) s = s.slice(0, -1);
    const cells = [];
    let cur = "";
    for (let i = 0; i < s.length; i++) {
      const ch = s[i];
      if (ch === "\\" && s[i + 1] === "|") { cur += "|"; i++; continue; }
      if (ch === "|") { cells.push(cur.trim()); cur = ""; continue; }
      cur += ch;
    }
    cells.push(cur.trim());
    return cells;
  }
  function _parseAligns(delimLine) {
    return _splitRow(delimLine).map(spec => {
      const left = spec.startsWith(":");
      const right = spec.endsWith(":");
      if (left && right) return "center";
      if (right) return "right";
      if (left) return "left";
      return "";
    });
  }
  function _renderCell(text, renderer) {
    if (typeof renderer !== "function") return _escapeHtml(text);
    // snarkdown handles inline bold/italic/code/links; strip a single
    // wrapping <p> snarkdown never adds (it's inline-first) — but be safe.
    let out = renderer(text);
    out = out.replace(/^\s*<p>([\s\S]*)<\/p>\s*$/i, "$1");
    return out;
  }
  function _convertTables(md, renderer) {
    const lines = md.split("\n");
    const out = [];
    let i = 0;
    while (i < lines.length) {
      const header = lines[i];
      const delim = lines[i + 1];
      const headerIsRow = header != null && header.indexOf("|") !== -1 && header.trim() !== "";
      if (headerIsRow && delim != null && _TABLE_DELIM_RE.test(delim) && delim.indexOf("-") !== -1) {
        const headCells = _splitRow(header);
        const aligns = _parseAligns(delim);
        // Delimiter column count must match header column count (GFM rule).
        if (aligns.length === headCells.length) {
          const body = [];
          let j = i + 2;
          while (j < lines.length && lines[j].indexOf("|") !== -1 && lines[j].trim() !== "") {
            body.push(_splitRow(lines[j]));
            j++;
          }
          if (body.length >= 1) {
            const al = idx => (aligns[idx] ? ' align="' + aligns[idx] + '"' : "");
            let html = "<table><thead><tr>";
            headCells.forEach((c, idx) => {
              html += "<th" + al(idx) + ">" + _renderCell(c, renderer) + "</th>";
            });
            html += "</tr></thead><tbody>";
            body.forEach(row => {
              html += "<tr>";
              for (let k = 0; k < headCells.length; k++) {
                const c = row[k] != null ? row[k] : "";
                html += "<td" + al(k) + ">" + _renderCell(c, renderer) + "</td>";
              }
              html += "</tr>";
            });
            html += "</tbody></table>";
            out.push(html);
            i = j;
            continue;
          }
        }
      }
      out.push(header);
      i++;
    }
    return out.join("\n");
  }

  function renderMarkdown(rawMd) {
    if (rawMd == null) return "";
    let md = _stripFrontmatter(String(rawMd).replace(/\r\n/g, "\n"));
    const renderer = window.snarkdown;
    if (typeof renderer !== "function") {
      // Fallback: no renderer loaded — escape and preserve line breaks.
      const esc = md.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
      return "<pre class=\"md-fallback\">" + esc + "</pre>";
    }
    // Convert GFM pipe tables to <table> HTML before snarkdown sees them.
    md = _convertTables(md, renderer);
    const blocks = _splitBlocks(md);
    const html = blocks.map(b => {
      const t = b.replace(/^\n+|\n+$/g, "");
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
    // Exposed for testing only — not part of the documented API.
    _splitBlocks, _convertTables,
  };
})();
