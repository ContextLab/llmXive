# llmXive paper house style

The LaTeX class and preamble that re-publish llmXive papers in the project's
visual identity — Fraunces (serif), JetBrains Mono (code), Dartmouth green
`#00693E` — matching the website at <https://context-lab.com/llmXive>.

## Two entry points

### `llmxive.cls` — for papers llmXive writes itself

A self-contained document class for projects where the paper-stage pipeline
generates the LaTeX from scratch (the normal llmXive flow: paper_specifier →
paper_clarifier → paper_planner → paper_tasker → paper_writing). Use it like
`article`:

```latex
\documentclass[11pt]{llmxive}
\title{...}
\author{...}
\arxivid{2510.21958}           % optional
\githubrepo{https://...}        % optional
\begin{document}
\maketitle
\begin{abstract} ... \end{abstract}
...
\bibliographystyle{plainnat}
\bibliography{...}
\end{document}
```

### `preamble.tex` — for re-styling external papers (e.g. arXiv submissions)

A drop-in preamble snippet for the `submission_intake` → `paper_initializer`
flow. The external paper already has its own `\documentclass{article}` (or
similar) and packages; we keep its structure and only re-style the typography +
colors. Put after the existing preamble, before `\begin{document}`:

```latex
\documentclass[11pt]{article}
\usepackage{...}                 % the paper's own packages
\input{papers/.style/preamble.tex}
\begin{document} ... \end{document}
```

## Compilation

Required engine: **XeLaTeX** or **LuaLaTeX** (the class uses `fontspec`).

The compile MUST run from the **llmXive repository root** so the fontspec
`Path=papers/.style/fonts/` resolves. Example for a paper under
`projects/PROJ-562/paper/source/`:

```sh
cd /path/to/llmXive
xelatex -output-directory=projects/PROJ-562/paper/pdf \
        projects/PROJ-562/paper/source/main.tex
```

The agent's `paper_initializer` wraps `xelatex` in a script that always `cd`s
to the repo root first.

## Vendored fonts

- [Fraunces](https://github.com/undercasetype/Fraunces) — SIL OFL 1.1 (variable
  font; `wght` axis 100..900, `opsz` 9..144, `SOFT`, `WONK`)
- [JetBrains Mono](https://github.com/JetBrains/JetBrainsMono) — SIL OFL 1.1

Bundled under `fonts/` so the class is self-contained on any TeX Live install
with `fontspec` (no system-font dependency).

## Design notes

- One column, 11pt body, generous margins (1in / 1.1in vertical).
- Section numbers in Dartmouth green; section title in bold.
- Title block: a small green-bordered `llmXive` wordmark top-left (matches the
  website header), publication-source line in monospace.
- Captions: bold green label, small body.
- Code listings: `listings` styled with green accent + mono.
- Links: `colorlinks=true`, internal links in `--accent-2`, external in
  `--accent`.

See `sample.tex` for a tested compile of "A Stylometric Application of Large
Language Models" (PROJ-562) using the class.
