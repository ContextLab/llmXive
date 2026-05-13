# llmxive.cls — LaTeX paper template

A clean, modern LaTeX document class for papers published through the [llmXive](../) automated discovery pipeline. Matches the website's visual language: **Fraunces** serif headlines, **JetBrains Mono** for UI/labels, **Dartmouth green** accents on a near-white paper.

## Files

| File            | Purpose                                              |
| --------------- | ---------------------------------------------------- |
| `llmxive.cls`   | The document class — drop into your paper directory  |
| `example.tex`   | Demo paper exercising every supported element        |

## Quick start

```bash
# place llmxive.cls next to your .tex file
lualatex example.tex
lualatex example.tex   # second pass for cross-references and TOC
```

We **strongly recommend `lualatex`** so the variable Fraunces font's `wght` and `opsz` axes are honored. `xelatex` loads the font but ignores the axes, producing an over-heavy rendering (everything looks Bold). If you only have `pdflatex` available, the class falls back to `libertinus` + `inconsolata` automatically — the output remains coherent, just not pixel-identical to the web style.

## Minimal document

```latex
\documentclass{llmxive}

\title{Your paper title}
\author{First Author, Second Author}
\affiliation{Institution One \,\textbullet\, Institution Two}
\correspondence{first@example.com}
\paperid{llmXive-2026-014}
\paperstatus{Peer Reviewed}
\runningtitle{Short title for header}

\begin{document}
\maketitle

\begin{abstract}
Your abstract here.
\end{abstract}

\keywords{kw1, kw2, kw3}

\section{Introduction}
...

\end{document}
```

## What's supported

The class is built on top of `article` and is designed to absorb arxiv tex sources with minimal fuss. The following are styled to match the llmXive look out of the box:

- **Sectioning** (`\section`, `\subsection`, `\subsubsection`, `\paragraph`)
- **Math** via `amsmath`, `amssymb`, `mathtools` (numbered equations, `align`, `equation`, etc.)
- **Theorem-like environments** (`theorem`, `lemma`, `proposition`, `corollary`, `definition`, `remark`, `example`, `proof`)
- **Figures and tables** with `caption` + `booktabs` styling
- **Code listings** via `listings` — preconfigured `style=llmx`
- **Bibliography** — numeric, llmXive-styled (use the standard `thebibliography` env, or feed in a `.bbl` from BibTeX/biber)
- **Hyperlinks** via `hyperref` — colored in Dartmouth green
- **Footnotes, lists, captions, table of contents** — all themed
- **Custom callout**: `\begin{keyresult}[Headline finding]...\end{keyresult}` for highlighting key takeaways
- **Margin notes**: `\llmxnote{...}`
- **Draft mode**: `\documentclass[draft]{llmxive}` adds a subtle "DRAFT" watermark and enables `\todo{...}`

## Converting an arxiv tex source

**Automated path (preferred).** Use `scripts/restyle_arxiv_paper.py` from the repo root:

```bash
python3 scripts/restyle_arxiv_paper.py \
  projects/PROJ-XXX-.../paper/source \
  --arxiv-id 2510.21958 \
  --paper-status "Peer Reviewed" \
  --affiliation "Dartmouth College" \
  --correspondence "first.last@example.edu" \
  --editorial-summary path/to/summary.md \
  --artifact-links path/to/artifacts.json
```

The script:
1. **Sanitizes figure PDFs** through ghostscript into `figs-sanitized/` (workaround for Adobe Illustrator export quirks that lualatex would otherwise clip). Originals under `figs/` are untouched.
2. **Wraps the original `main.tex`** in `\documentclass{llmxive}` while preserving the body bytes EXACTLY. Only the preamble is rewritten — conflicting packages are commented out, the original title block is moved into class metadata.
3. **Auto-extracts artifact URLs** (github.com, osf.io, zenodo.org, huggingface.co, doi.org) from the paper body so links are deterministic — never hallucinated.
4. **Renders the editorial summary** on the title page as an eLife-style callout, alongside the artifact links.

Then compile twice with **lualatex** (see Quick start above).

**Manual path.** If you can't run the script:
1. Unpack the arxiv source.
2. Replace the original `\documentclass{...}` line with `\documentclass{llmxive}`.
3. Remove or comment out any of these commonly-conflicting packages — the class already loads them:
   - `geometry`, `hyperref`, `caption`, `titlesec`, `fancyhdr`, `xcolor`, `microtype`, `graphicx`, `booktabs`, `amsmath`, `amssymb`, `amsthm`, `mathtools`, `enumitem`, `listings`
4. Add the llmXive metadata: `\paperid`, `\paperstatus`, `\affiliation`, `\correspondence`, `\runningtitle`.
5. (Optional) Add editorial summary + artifacts via `\seteditorialsummary{...}`, `\seteditorialartifacts{...}`, `\seteditorialbyline{...}` — see `\maketitle` block in the class for full details.
6. Compile twice with `lualatex`.

Most papers will compile on the first try. The remaining edge cases are usually:
- Custom fonts in the source (remove — the class sets fonts)
- Hard-coded colors (replace with the `llmx*` palette if you want to match)
- Custom `\maketitle` redefinitions (remove)

## Editorial summary + artifact links (publication flow)

When a paper is accepted, the publication agent drafts a short eLife-style **Editorial Summary** in markdown — typically with `## Significance`, `## Strengths`, and `## Limitations` subsections — and the restyle script renders it as a tinted callout at the top of the title page. The summary is metadata, not body content; the original paper text is unchanged.

Beneath the summary, an **Artifacts** strip lists project-specific links (project page on GitHub, peer-review threads) plus auto-extracted URLs from the paper body (code repos, data archives, DOI links). The script never invents URLs — they're either explicitly supplied via `--artifact-links` JSON, or extracted from the tex source.

Markdown subset supported in the summary:
- `## Heading` → eLife-style section header
- `**bold**` and `*italic*` → text emphasis
- `[label](url)` → hyperlink

## Palette

| Token           | Hex      | Where it's used                              |
| --------------- | -------- | -------------------------------------------- |
| `llmxGreen`     | `#00693E`| Section numbers, links, captions labels, accents |
| `llmxGreenDeep` | `#004F2E`| `\texttt` inline code, hover-equivalent      |
| `llmxGreen2`    | `#0A8A55`| Listings strings                             |
| `llmxInk`       | `#0A2818`| Body text                                    |
| `llmxInk2`      | `#2D4A3E`| Abstract, definitions, captions              |
| `llmxMuted`     | `#5A7268`| Footers, affiliations, secondary mono labels |
| `llmxLine`      | `#C9D6CC`| Hairlines, rules, borders                    |
| `llmxBg`        | `#F0F5F1`| Page background tint (reference only)        |
| `llmxTint`      | `#E6EFE8`| Callout fills                                |

All colors are exported as `xcolor` names, so you can use them directly in your tex: `\textcolor{llmxGreen}{...}`.

## License

Same license as the llmXive repository.
