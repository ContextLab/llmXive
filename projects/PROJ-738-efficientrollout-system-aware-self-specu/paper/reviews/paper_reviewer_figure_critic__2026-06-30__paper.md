---
action_items:
- id: dc178119b9fe
  severity: writing
  text: Figures in appendix/0_rollout_tail.tex (Fig. rollout_bottleneck_appendix)
    and figures/figure_motivation.tex (Fig. rollout_bottleneck) contain subfigures
    with empty captions (\caption{}). These must be filled with descriptive text explaining
    the specific data shown in each panel (e.g., 'Step-time decomposition for Llama3.1-8B')
    to ensure the figures are self-contained and legible without relying solely on
    the main caption.
- id: c8f8a7588b6d
  severity: science
  text: Figure 1 (main_teaser) and Figure 2 (rollout_bottleneck) are referenced as
    critical visual summaries of the method and motivation. However, the LaTeX source
    relies on external PDFs (e.g., figures/main_teaser.pdf) without providing the
    source data or generation scripts in the repository. For reproducibility, the
    paper should either include the raw data used to generate these plots or provide
    the plotting code in the supplementary material.
- id: 939500aebee9
  severity: writing
  text: Several figures (e.g., Fig. app_gamma_elevation, Fig. app_eagle3_mal) use
    small font sizes for axis labels and legends relative to the plot area. At standard
    print resolution (300 DPI), these may become illegible. Authors should increase
    font sizes or line widths to ensure clarity in the camera-ready version.
artifact_hash: f5cd2bf8ec4b16de31454f2a2486d371422b77f233615f81a71aa09fed433b62
artifact_path: projects/PROJ-738-efficientrollout-system-aware-self-specu/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T10:48:06.257438Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

The figure presentation in "EfficientRollout" is generally consistent with the technical depth of the manuscript, but several critical issues regarding legibility and self-containment require attention before acceptance.

First, a significant number of subfigures lack individual captions. Specifically, in `appendix/0_rollout_tail.tex` (Figure `rollout_bottleneck_appendix`) and `figures/figure_motivation.tex` (Figure `rollout_bottleneck`), the subfigures (a), (b), and (c) are defined with empty `\caption{}` commands. While the main caption provides a high-level summary, reviewers and readers often examine subfigures in isolation. Each panel requires a specific caption describing the metric, model, and conditions shown (e.g., "Step-time decomposition for Qwen2.5-7B over 20 steps"). Without these, the figures are not self-explanatory.

Second, the visual density of several plots poses a legibility risk. Figures such as `fig:app_gamma_elevation` (adaptive $\gamma$ schedules) and `fig:app_eagle3_mal` (block efficiency over steps) utilize small fonts for axis labels and legends. Given the multi-panel layout (often 3 subfigures side-by-side), the text is likely to be unreadable when printed or viewed at standard zoom levels. The authors should increase the font size of axis labels, tick marks, and legend entries to ensure they meet the conference's legibility standards.

Third, while the paper claims to be reproducible, the figures rely entirely on pre-compiled PDFs (e.g., `figures/main_teaser.pdf`, `figures/appendix_sd_grid.pdf`). The LaTeX source does not include the plotting scripts or the raw data files used to generate these visualizations. For a systems paper where the visual evidence (e.g., the roofline boundary in Fig. `toggle_boundary`) is central to the argument, providing the generation code or data in the supplementary material is essential for verification.

Finally, the "Teaser" figure (Fig. `main_teaser`) is a high-level schematic. While it effectively outlines the three components, it lacks specific quantitative annotations (e.g., arrows indicating the magnitude of speedup or specific latency values) that would make it more informative. Adding these details would strengthen the visual impact of the introduction.

Addressing the empty sub-captions and improving font legibility are mandatory for the camera-ready version. Providing the plotting artifacts is strongly recommended to support the reproducibility claims.
