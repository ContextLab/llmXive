---
action_items:
- id: bc2468315934
  severity: writing
  text: Figure 2 (category_pie_new.pdf) uses pie charts for eight axes. Pie charts
    hinder precise comparison of proportions. Replace with a grouped bar chart or
    stacked bar chart for better readability.
- id: be162247d6e7
  severity: writing
  text: Figure 3 (fig_analysis_combined.pdf) contains three sub-panels. Ensure each
    panel (a, b, c) has explicit axis labels and legends embedded in the image, not
    just in the caption, for standalone legibility.
- id: ca4b3bcc8eaa
  severity: writing
  text: Appendix qualitative figures (EE_case, SA_case, PS_case, PF_case) must clearly
    annotate model names and indicate success/failure status directly on the image
    or via a consistent legend to avoid ambiguity.
- id: 018502310049
  severity: writing
  text: Figure 4 (fig1_combined_degradation.pdf) Y-axis represents scores [0,100].
    Verify the axis label explicitly states 'Score' and includes the unit range for
    clarity.
- id: 03b55f8e30f8
  severity: writing
  text: Verify all color maps (especially in Figure 3 heatmaps) are colorblind-safe
    (e.g., viridis, cividis) to ensure accessibility for all readers.
artifact_hash: 583182a56bc8cd93d801cd098b02d980b9a48cb375dac6cc8130da68f508615f
artifact_path: projects/PROJ-630-wbench-a-comprehensive-multi-turn-benchm/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T06:06:35.924177Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

The figures generally support the paper's claims, but several require refinement for clarity and accessibility.

**Figure 2 (Dataset Composition):** The use of pie charts (`figures/category_pie_new.pdf`) to display composition across eight axes is suboptimal. Pie charts make it difficult for readers to compare slice sizes accurately, especially when there are many categories. I recommend replacing this with a grouped bar chart or a stacked bar chart, which allows for easier comparison of proportions across the different axes (e.g., Scene, Style, Perspective).

**Figure 3 (Correlation Analysis):** This multi-panel figure (`figures/fig_analysis_combined.pdf`) is critical for the key findings. Ensure that the sub-panels (a), (b), and (c) are clearly labeled within the image itself. Axis labels for the correlation heatmaps must be legible at print scale. Additionally, verify that the color maps used for the heatmaps are colorblind-safe (e.g., viridis or cividis) to ensure accessibility.

**Figure 4 (Degradation):** The per-turn degradation plot (`figures/fig1_combined_degradation.pdf`) needs explicit axis labeling. The Y-axis should clearly indicate "Score" and the range [0, 100]. The aggregation of turns $\ge4$ into "T4+" should be explained in the axis tick labels or legend to avoid confusion.

**Appendix Qualitative Figures:** The qualitative comparison figures (`figures/EE_case.orig.pdf`, `figures/SA_case.orig.pdf`, `figures/PS_case.orig.pdf`, `figures/PF_case.orig.pdf`) are essential for demonstrating metric validity. However, they must clearly annotate which model generated each video and whether the case represents a success or failure. Currently, the captions describe the content, but visual annotations (e.g., "Success", "Failure", Model Name) directly on the images would improve immediate comprehension without requiring the reader to cross-reference the text.

**Figure 5 (Human Alignment):** The scatter plot (`figures/human_vs_auto_10dims_1row.pdf`) should include a reference line (e.g., $y=x$) if applicable, or clearly label the axes with "Human Win Rate" and "Automated Score" to ensure the correlation is immediately interpretable.

Overall, the figures are well-placed but need minor adjustments to maximize their standalone clarity and accessibility.
