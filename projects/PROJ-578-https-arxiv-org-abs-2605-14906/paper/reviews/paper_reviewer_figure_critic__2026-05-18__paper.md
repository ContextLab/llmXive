---
action_items:
- id: dd6a09a52ef8
  severity: writing
  text: Figure 2 (per_type_heatmap) uses a green colormap. This may be inaccessible
    to colorblind readers. Replace with a colorblind-safe palette (e.g., Viridis or
    Cividis) to ensure legibility.
- id: 851602e25ca2
  severity: writing
  text: Appendix Figure (wrong_answer_pie.pdf) uses a pie chart for error distribution.
    Pie charts are generally less accurate for comparing proportions than bar charts.
    Consider converting to a grouped or stacked bar chart.
- id: 1c436788e78b
  severity: writing
  text: Figure 1 (pipeline.pdf) caption is minimal ('construction pipeline'). Expand
    to briefly describe the four visual components (session simulation, question construction,
    etc.) to improve accessibility and standalone readability.
- id: b35c181f9e48
  severity: writing
  text: Table 1 embeds a donut chart (composition_donut.pdf). This consumes significant
    space and may reduce text legibility. Consider moving the distribution data to
    a bar chart in the main text or appendix to free up table space.
artifact_hash: d50a4f0b1e568c7504bc9f36b9def267fba709bab11751ed7e3ec317ba0682a2
artifact_path: projects/PROJ-578-https-arxiv-org-abs-2605-14906/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-05-18T14:32:33.765591Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

**Figure Review Summary**

The paper utilizes 15 figures across the main text and appendix to convey benchmark construction, performance results, and error analysis. While the figure selection is comprehensive, several visual design choices require refinement to meet accessibility standards and scientific visualization best practices.

**Main Text Figures**
- **Figure 1 (Pipeline)**: The caption is overly terse ("construction pipeline"). Given the figure's complexity, the caption should summarize the four stages (session simulation, question construction, evidence session, history assembly) to allow the figure to stand alone for accessibility tools.
- **Figure 2 (Per-Type Heatmap)**: The caption notes a "green colormap." Green-only or green-dominant scales are often problematic for deuteranopia. Please verify the palette against WCAG 2.1 contrast guidelines or switch to a perceptually uniform, colorblind-safe palette (e.g., Viridis).
- **Figure 4 (Context Degradation & Error Decomp)**: This is the strongest figure set. The use of confidence interval bands (95% CI) in `context_degradation_lines.pdf` is excellent practice for uncertainty visualization. The decomposition in `visual_error_decomposition.pdf` aligns well with the textual analysis.
- **Table 1**: Embedding `composition_donut.pdf` inside the benchmark comparison table is unconventional. Donut charts inside tables often reduce text legibility due to size constraints. Consider extracting this distribution to a standalone figure or a bar chart within the table.

**Appendix Figures**
- **Candidate Examples (`ie_entity_candidates.pdf`, etc.)**: These are well-captioned and essential for understanding the task definition. Ensure the image resolution is sufficient for print (current file sizes suggest reasonable quality).
- **`wrong_answer_pie.pdf`**: Pie charts are discouraged in quantitative analysis because humans struggle to compare angles. Since this figure shows error distribution across seven labels, a stacked bar chart would allow for more precise comparison of error category frequencies.
- **`subtype_correlation_heatmap.pdf`**: Ensure axis labels are large enough to be read when printed at standard conference poster size (typically 10pt minimum).

**Accessibility & Alt Text**
- LaTeX captions currently serve as alt text. Most are descriptive, but Figure 1 and the donut chart in Table 1 need richer descriptions to support screen readers.
- Verify that all color-coded figures (heatmaps, line plots) are distinguishable in grayscale, as print versions may lose color fidelity.

**Overall**
The figures effectively support the claims, but the color choices and chart types in Figures 1, 2, and the Appendix Pie Chart should be updated to ensure broader accessibility and clearer data communication.
