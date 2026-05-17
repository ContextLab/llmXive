---
artifact_hash: 815458de8568b35ab5a02599bda9f602ed2dc04d545bca014bc4749f57af838e
artifact_path: projects/PROJ-564-qwen-image-vae-2-0-technical-report/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-05-17T15:04:36.106431Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_text_formatting
score: 0.0
verdict: minor_revision
---

## Text Formatting Review

This review focuses exclusively on text formatting concerns: heading hierarchy, table/figure placement, citation style, LaTeX hygiene, and cross-reference consistency.

### 1. Package Hygiene (colm2024_conference.tex, lines 1–70)
Multiple duplicate package inclusions create compilation overhead and potential conflicts:
- `\usepackage{booktabs}` appears twice (lines 2 and 12)
- `\usepackage{enumitem}` appears twice (lines 4 and 32)
- `\usepackage{makecell}` appears twice (lines 7 and 38)
- `\usepackage{array}` appears three times (lines 13, 52, 60)
- `\usepackage{longtable}` appears twice (lines 17 and 34)
- `\usepackage{tcolorbox}` appears twice (lines 48 and 55)
- `\usepackage{inputenc}` and `\usepackage{fontenc}` each appear twice (lines 19–20 and 49–50)

**Recommendation**: Deduplicate all package declarations. This is a low-effort fix that improves compilation reliability.

### 2. Table Formatting Issues

**a. `\resizebox` Usage** (`sec/experiment.tex`, lines 14 and 68)
Both `tab:main_bench` and `tab:text_bench` use `\resizebox{\textwidth}{!}{...}`. This forces uniform font scaling within tables, potentially making column headers disproportionately small compared to body text.

**Recommendation**: Consider using `tabularx` or `adjustbox` with `\small`/`\footnotesize` instead of full-width scaling.

**b. Table Caption Placement** (`sec/experiment.tex`, lines 11–13)
The caption for `tab:main_bench` appears *before* the table content in the source, which is correct. However, the caption references "purple" highlighting while the actual color is defined as `blue!5`. This creates a visual-text mismatch.

**Recommendation**: Update caption text to match the actual color definition or fix the color specification.

### 3. Figure-Caption Consistency

**a. Cross-Reference Order** (`sec/experiment.tex`, lines 120–121)
`Figure~\ref{fig:text_recon_comparison}` is referenced in the text *before* the figure environment appears (lines 127–145). This violates standard academic convention where figures should precede their first textual mention.

**Recommendation**: Move the `figure*` environment to appear before the paragraph that first references it.

**b. Subfigure Caption Typo** (`sec/experiment.tex`, line 136)
Caption reads: "Ours OmniDoc-TokenBench" — should be "our OmniDoc-TokenBench" or simply "OmniDoc-TokenBench."

### 4. Equation Numbering and Labeling

Equations in `sec/training.tex` (lines 12–17) use `\begin{align}` with proper labeling. However, Equation 1 (`\mathcal{L}_{total}`) lacks a `\label{}` command, making cross-referencing impossible.

**Recommendation**: Add `\label{eq:total_loss}` to the first equation for consistency with other numbered equations.

### 5. Heading Hierarchy

The document uses `\section{}`, `\subsection{}`, and `\paragraph{}` consistently. However, `\paragraph{}` commands in `sec/model.tex` (lines 34, 52, 60) are not followed by `\subsubsection{}` where logical topic breaks occur, creating slight hierarchy gaps.

**Recommendation**: Consider using `\subsubsection{}` for major architectural components (GSC, Attention-Free Backbone, Asymmetry) to improve navigability.

### 6. Bibliography Style

Citation keys in `.tex` files match entries in `colm2024_conference.bib`. However, some references (e.g., `dinov3`, `qiu2025image`) cite arXiv preprints that may not be publicly verifiable at publication time.

**Recommendation**: Ensure all cited works have stable identifiers (DOI or persistent arXiv version) for reproducibility.

---

**Summary**: Minor formatting revisions are recommended before final publication. The primary issues are package deduplication, table caption accuracy, figure placement order, and equation labeling. These do not affect scientific content but impact professional presentation quality.
