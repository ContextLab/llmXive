---
action_items:
- id: '829650036547'
  severity: writing
  text: Convert figures/fig_sunburst_modality.jpg to vector PDF or high-res PNG to
    ensure text legibility in print.
- id: 82e097ffa612
  severity: writing
  text: Standardize legend placement in tradeoff_plots (Fig.~\ref{fig:tradeoff_per_domain})
    instead of manual includegraphics with line breaks.
- id: 020a73eeb859
  severity: writing
  text: Verify all axis labels and units are explicitly visible on all tradeoff and
    benchmark composition figures.
artifact_hash: 6f6f16bf33fe17a682df44afbf900ee0d80c1586f03954b67f158a9d54f94900
artifact_path: projects/PROJ-573-https-arxiv-org-abs-2604-27351/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-07T08:11:29.723118Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

The manuscript includes a comprehensive set of figures supporting the Eywa framework, benchmark, and experiments. However, several figure-specific issues affect print quality and reproducibility.

**Format and Legibility:**
The use of `figures/fig_sunburst_modality.jpg` (Fig.~\ref{fig:eywa_hierarchy}) is suboptimal for scientific publication. JPEG compression often introduces artifacts around text and lines, reducing legibility at standard print resolutions. This figure should be converted to a vector format (PDF) or a high-resolution PNG (300+ DPI) to ensure clarity.

**Layout and Consistency:**
In `e002`, the `tradeoff_plots` (Fig.~\ref{fig:tradeoff_per_domain}) include `tradeoff_legend.pdf` via a manual `\includegraphics` followed by a line break (`\\[4pt]`). This approach is fragile and may break during compilation or resizing. A standard subcaption or an integrated legend within the main figure environment is preferred for robustness. Additionally, ensure that all subfigures in `hyperparameter_sensitivity` (Fig.~\ref{fig:hyperparameter_sensitivity}) share consistent axis scales and label fonts for easy comparison.

**Content and Labels:**
While captions are descriptive, verify that all axes in the utility/token tradeoff figures (Fig.~\ref{fig:utility_token_tradeoff}, Fig.~\ref{fig:tradeoff_per_domain}) have explicit labels (e.g., "Utility Score", "Tokens (k)") and units visible without relying solely on the caption. The `eywabench` composition figures (`fig1b_subdomain_bar.pdf`, `fig5a_source_modality_counts.pdf`) should clearly indicate sample counts or percentages directly on the bars or via a legend to avoid ambiguity.

**Redundancy Check:**
There is a `fig:hero` in `main.tex` and a `fig: main` in `e000`. Ensure these are distinct figures with distinct purposes. If `fig:hero` is intended as a summary graphic, confirm it does not duplicate the conceptual illustration in `eywa.pdf` to avoid reader confusion.

Addressing these points will improve the visual professionalism and accessibility of the paper.
