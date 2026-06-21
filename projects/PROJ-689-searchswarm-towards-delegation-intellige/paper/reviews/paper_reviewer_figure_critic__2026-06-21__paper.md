---
action_items:
- id: 8aa49da31068
  severity: writing
  text: "Add explicit axis labels (including units where appropriate) to all quantitative\
    \ plots (e.g., Fig\u202F1 sub\u2011figures, Fig\u202F4 distribution plots) so\
    \ readers can interpret the numbers without consulting the caption."
- id: d24a1e7f936f
  severity: writing
  text: "Replace or supplement the current color palette in pie charts (Fig\u202F\
    3) and bar charts with a color\u2011blind\u2011friendly scheme; include a legend\
    \ that maps colors to benchmark names or tool categories."
- id: d7d37e606ab8
  severity: writing
  text: "Provide descriptive alt\u2011text for each \\includegraphics command (e.g.,\
    \ using the \\\\caption* or \\\\pdfstringdefDisableCommands) to improve accessibility\
    \ for screen\u2011reader users."
- id: dc8105ae3cfd
  severity: writing
  text: "Ensure that sub\u2011figure sizes are large enough to remain legible when\
    \ printed at 1\u2011column width; consider increasing the width of the sub\u2011\
    figures in Fig\u202F1 and Fig\u202F4 or providing a separate high\u2011resolution\
    \ version."
- id: f22df00ca5ee
  severity: writing
  text: "Verify that every figure is explicitly referenced in the main text (e.g.,\
    \ Fig\u202F4 is only mentioned in the Appendix; consider moving the most informative\
    \ plots into the main body or summarising their key take\u2011aways)."
artifact_hash: 23164a835e9fc14f10b36f04bd2aeba4213e5a3b759192c46a449dbfe25b61f3
artifact_path: projects/PROJ-689-searchswarm-towards-delegation-intellige/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-21T09:50:13.757985Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

The manuscript includes several key visualizations (Figures 1–4 and additional appendix plots) that are essential for supporting the claimed performance improvements of SearchSwarm. While the figures are generally well‑placed, there are notable issues that affect clarity, accessibility, and readability:

**1. Missing axis labels and units**  
- Figure 1 (four‑panel benchmark comparison) and Figure 4 (tool‑usage distribution) lack explicit X/Y axis labels and units. The caption mentions the metrics, but readers cannot determine the exact scale (e.g., percentage score) without guessing. Adding clear axis titles such as “Benchmark” and “Score (%)” will make the plots self‑contained.

**2. Color palette and legends**  
- The pie charts in Figure 3 and any bar charts rely on default color schemes that are not guaranteed to be distinguishable for color‑blind users. Switching to a color‑blind‑safe palette (e.g., ColorBrewer or Tableau) and providing a legend that maps each color to the corresponding tool or benchmark will improve interpretability.

**3. Legibility at print size**  
- Sub‑figures in Figure 1 are rendered at 0.49 linewidth each, which can become cramped in a two‑column layout. Increasing the sub‑figure width or supplying a higher‑resolution PDF version will ensure that tick labels, legends, and text remain readable when printed.

**4. Accessibility (alt‑text)**  
- The LaTeX source includes only `\includegraphics` commands without any descriptive alt‑text. Adding brief alt descriptions (e.g., “Bar chart comparing SearchSwarm to baseline models on BrowseComp”) using `\caption*` or PDF string definitions will make the paper more accessible to screen‑reader users.

**5. Figure referencing**  
- All figures should be explicitly referenced in the main narrative. Figure 4, which presents detailed tool‑usage distributions, is discussed only in the Appendix. Since these plots convey important insights about delegation behavior, a concise summary should be incorporated into the main text, or the most salient plot should be moved to the main body.

Addressing these points will enhance the clarity, accessibility, and overall impact of the visual evidence supporting the paper’s contributions.
