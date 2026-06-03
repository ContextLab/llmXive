---
action_items:
- id: 15dd3bd5dca0
  severity: writing
  text: Add accessibility metadata (alt text) to all figures to ensure compliance
    with modern publication standards for visually impaired readers.
- id: 8ccbba6221df
  severity: writing
  text: Increase font size in subcaptions for Figs. 3 and 5 (causal-cd, dmd-is-worse-than-cd)
    currently set to \footnotesize, which may be illegible at print scale.
- id: d0d2488c89cc
  severity: writing
  text: Verify axis labels and legend clarity in performance plots (Figs. 3, 5) to
    ensure they are self-explanatory without relying solely on the main caption.
artifact_hash: bc6ea3b7abb50e6d2d0c61521fe88f76d18733e7f3e4d74c5eba9d5fe9acb8e6
artifact_path: projects/PROJ-580-https-arxiv-org-abs-2605-15141/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-03T10:20:31.499168Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

The manuscript presents a comprehensive set of figures that effectively support the narrative of Causal Forcing++. Figure 1 (overall framework) provides a clear architectural overview, and Figure 4 (action-conditioned world model) offers necessary qualitative evidence for the extension claim. However, several figure-specific issues require attention to meet publication standards.

First, accessibility is a significant omission. None of the figures include alt text or detailed descriptions for screen readers. Given the complexity of the framework diagram in Fig. 1 and the visual comparisons in Fig. 7 (ablation), adding textual descriptions of the visual content is essential for inclusive access.

Second, legibility in subfigures needs improvement. In `Figures_tex/causal-cd.tex` and `Figures_tex/dmd-is-worse-than-cd.tex`, subcaptions are explicitly set to `\footnotesize`. When compiled into a two-column format or printed, this font size risks becoming illegible. Increasing this to `\scriptsize` at minimum, or ensuring the main caption carries the descriptive burden, is recommended.

Third, the visual ablation study in Fig. 7 relies heavily on subtle artifacts (e.g., "blurs the mouse’s legs," "antler separation"). To ensure these distinctions are clear at print resolution, the source images must be high-resolution (300+ DPI). The current LaTeX code does not specify resolution parameters, so the authors should verify the exported PDF quality. Additionally, while `Figures_tex/performance_comparison.tex` visualizes results, ensure it complements Table 1 rather than duplicating it; if it shows video frames, the caption should explicitly highlight the qualitative differences (e.g., motion consistency) that the table metrics do not capture.

Finally, regarding color choices, the preamble defines several custom colors (e.g., `pearDark`, `mygreen`). Ensure that any plots using these colors are colorblind-safe, particularly in Fig. 3 and Fig. 5 where performance comparisons are made. Avoid relying solely on red/green distinctions if possible. Addressing these points will significantly enhance the figures' clarity and accessibility.
