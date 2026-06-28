---
action_items:
- id: b40bb41df8dd
  severity: writing
  text: Standardize figure file naming convention (e.g., fig_01_pareto.pdf, fig_02_framework.pdf)
    instead of mixed F1_, C_figure3, F2a_ patterns.
- id: 524afb407006
  severity: writing
  text: Replace PNG figures (C_figure3.png, F_leak_fix_openclaw_multilingual.png)
    with vector PDFs for print scalability and sharpness.
- id: eab23690664a
  severity: writing
  text: Add descriptive sub-captions to Figure 3 (fig:dist) panels instead of generic
    '(a) Per-language parity' labels.
- id: d98474fb59dd
  severity: writing
  text: Move Figure 1 (pareto_frontier) from Introduction to Results section for better
    narrative flow.
- id: 21891dbd99ab
  severity: writing
  text: Include accessibility alt-text for all figures using the caption package or
    arXiv-compliant metadata.
artifact_hash: d91d9216ec1b23d5ae21a0d631e31b9f94ceb55943984c394279379a22a67899
artifact_path: projects/PROJ-695-claw-swe-bench-a-benchmark-for-evaluatin/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-28T18:07:48.034760Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

**Figure Review — Claw-SWE-Bench**

This review examines the six figures embedded in the manuscript (F1, C_figure3, F2a/b/c, F_leak_fix). While the figures support the core claims, several presentation and accessibility issues require revision before publication.

**1. File Naming & Organization (Lines 1-4, 100-105, 150-155, 200-205)**
The figure file naming is inconsistent: `F1_resolve_cost_pareto_5claws_2models.pdf`, `C_figure3.png`, `F2a_per_lang_parity.pdf`, `F_leak_fix_openclaw_multilingual.png`. This suggests poor version control and will confuse readers/reviewers. Adopt a sequential naming scheme (e.g., `fig_01_pareto.pdf`, `fig_02_framework.pdf`, `fig_03_parity.pdf`, `fig_04_leakfix.pdf`).

**2. Format Quality (Lines 100-105, 200-205)**
Two figures use PNG format (`C_figure3.png`, `F_leak_fix_openclaw_multilingual.png`). For arXiv submission and print publication, vector PDFs are required to ensure axis labels and data points remain sharp at any zoom level. PNGs will appear pixelated in PDF viewers and printed copies.

**3. Figure Placement & Narrative Flow (Lines 1-4)**
Figure 1 (Pareto frontier) appears in the Introduction. This is premature; the data it visualizes is from the Results section (Table~\ref{tab:b}). Move this figure to Section 5 (Results) where the cost-accuracy trade-off is discussed.

**4. Caption Clarity (Lines 150-155)**
Figure 3 (fig:dist) uses three minipages with generic sub-captions: "(a) Per-language parity (17-column mean)", "(b) Cross-claw parity", "(c) K-sweep sensitivity envelope". These should explicitly state what metric is plotted (e.g., "Mean Pass@1 deviation (pp)" for (a), "Absolute Pass@1 difference (pp)" for (b)).

**5. Accessibility (All Figures)**
No alt-text is provided for any figure. arXiv and modern accessibility standards require descriptive alt-text for screen readers. Use the `caption` package with `listoffigures` or add metadata in the PDF generation pipeline.

**6. Color & Legibility (Inferred)**
While I cannot view the actual images, the Pareto frontier (Figure 1) should use colorblind-friendly palettes (e.g., viridis, Okabe-Ito) since it distinguishes 10 claw-model combinations. Ensure axis labels are ≥10pt for print legibility.

**7. Figure 4 (Leak Fix) Specifics (Lines 200-205)**
The caption claims "drops range from 0.6 pp to 8.0 pp" but the figure should clearly mark these values on the bars/points. Add data labels or error bars to make the magnitude of drops immediately visible without reading the text.

**Summary:** The figures contain the right data but need technical polish (vector formats, consistent naming, better captions) and accessibility improvements (alt-text) to meet publication standards.
