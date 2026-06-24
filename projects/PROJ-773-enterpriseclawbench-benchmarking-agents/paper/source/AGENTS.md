# Repository Guidelines

## Project Structure & Module Organization

This repository is a FrontisBench manuscript and release-artifact workspace. The root contains the ACL LaTeX entry points (`acl_latex.tex`, `acl_lualatex.tex`), bibliography/style files, and `formatting.md`. Generated and source assets live under `assets/`: `assets/data/` stores CSV/JSON figure and table inputs, `assets/figure/` stores rendered figures, and `assets/case_studies/` stores release-safe case-study materials. Supporting notes, evidence reports, and outlines are in `docs/`; exploratory Chinese drafts are in `draft/`. Figure/data regeneration code is in `scripts/make_main_text_figures.py`.

## Build, Test, and Development Commands

- `latexmk -pdf acl_latex.tex`: compile the main ACL manuscript with pdfLaTeX.
- `lualatex acl_lualatex.tex`: compile the LuaLaTeX variant when CJK/font handling is needed.
- `/hpc_data/jczhong/frontis-bench/frontis-bench-handoff/code/.venv/bin/python scripts/make_main_text_figures.py`: regenerate manuscript figures and compact data. This requires the hard-coded `/hpc_data/...` source files and writes to `assets/figure/` and `assets/data/`.
- `git diff -- assets/data assets/figure acl_latex.tex`: review manuscript-facing changes before committing.

## Coding Style & Naming Conventions

Use 4-space indentation for Python, keep imports grouped as standard library then third-party, and prefer `pathlib.Path` for paths as in the existing script. Use `snake_case` for functions, variables, generated CSV/JSON stems, and figure filenames. Keep LaTeX macros in the preamble and use existing commands such as `\fb{}`, `\hm{}`, and `\liteset{}` instead of repeating terms manually. Do not modify ACL style/template files unless the change is explicitly about formatting infrastructure.

## Testing Guidelines

There is no formal test suite. Validate changes by running the relevant regeneration or LaTeX compile command, then inspect the changed SVG/PDF/PNG assets and manuscript output. For data edits, confirm headers and row schemas remain compatible with `scripts/make_main_text_figures.py` and the mappings documented in `assets/data/README.md`.

## Commit & Pull Request Guidelines

Recent commits use short, imperative summaries such as `Revise judge reliability narrative` and `Prepare release-safe case study appendix`. Follow that style: one focused subject line, with a body only when context or validation details are useful. Pull requests should describe manuscript, data, and figure impacts separately; list commands run; link related evidence notes in `docs/evidence/`; and include rendered screenshots or PDFs for visual changes.

## Security & Configuration Tips

Treat unreleased benchmark data as sensitive. Do not add raw enterprise logs, proprietary attachments, local `/hpc_data` dumps, or unredacted screenshots. Keep generated release-safe artifacts in `assets/case_studies/` and ensure new outputs are anonymized before inclusion.
