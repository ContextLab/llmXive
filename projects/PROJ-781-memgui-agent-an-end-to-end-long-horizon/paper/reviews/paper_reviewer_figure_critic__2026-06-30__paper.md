---
action_items:
- id: 655de60ba226
  severity: writing
  text: 'Figure 1 (main-performance.png): The caption claims a token saving of ''~1.5k''
    by step 150, but the y-axis of subplot (a) lacks a visible scale or gridlines
    to verify this magnitude. Add explicit y-axis ticks and units (tokens) to validate
    the claim visually.'
- id: 42d01b371fcb
  severity: science
  text: 'Figure 3 (dataset-stats.drawio): Subplot (b) compares trajectory lengths
    (28.8 vs 15.3), but the bar chart lacks error bars or standard deviation indicators.
    Given the variance in long-horizon tasks, visualizing uncertainty is required
    to support the statistical significance of the difference.'
- id: 145b9051c937
  severity: writing
  text: 'Figure 5 (failure-heatmap.drawio): The heatmap uses color intensity to represent
    failure counts (99 vs 58), but the color bar legend is missing. Without a scale,
    readers cannot distinguish between minor and major reductions in specific failure
    categories.'
- id: df8eff2555de
  severity: writing
  text: 'Figure 6 (case-study-good.drawio): The figure is extremely dense with text
    overlays (screenshots, folding directives, memory writes). At standard print resolution
    (300 DPI), the text within the ''Folded History'' and ''Memory'' boxes is likely
    illegible. Consider splitting into two panels or increasing font size/contrast
    significantly.'
- id: 0fe8ca7cdd1e
  severity: writing
  text: 'Figure 7 (training_curves.png): The x-axis label ''Training Steps'' is present,
    but the y-axes for ''Loss'' and ''Gradient Norm'' lack units or scale markers.
    Ensure all axes have clear numerical ticks to allow reproduction of the training
    dynamics.'
artifact_hash: 7ba9201f0f49d9384a35f3eca07d4fd8d448c0da222a8a4e9472044b7e857c18
artifact_path: projects/PROJ-781-memgui-agent-an-end-to-end-long-horizon/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T19:33:46.666205Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

The figures in this manuscript generally support the narrative of context efficiency and performance gains, but several critical issues regarding legibility, axis labeling, and data visualization standards must be addressed before publication.

**Clarity and Legibility:**
Figure 6 (`case-study-good.drawio`) is the most problematic. It attempts to display a full trajectory with screenshots, XML tags, and JSON-like structures simultaneously. At the current resolution and font size, the text within the `<folding>` and `<memory>` blocks is illegible when printed. This figure fails to "earn its place" in its current form as it obscures the very details (the specific folding logic) it aims to demonstrate. I recommend splitting this into two figures: one showing the high-level state transition and another zooming in on the specific text content of the context actions.

**Axis Labels and Units:**
Figure 1 (`main-performance.png`) subplot (a) claims a token reduction of "~1.5k" but the y-axis is devoid of numerical ticks or gridlines. A reader cannot visually verify the magnitude of the savings without guessing. Explicitly label the y-axis with "Input Tokens" and include major gridlines. Similarly, Figure 7 (`training_curves.png`) lacks y-axis scales for the loss and gradient norm curves, making it impossible to assess the convergence behavior quantitatively.

**Statistical Representation:**
Figure 3 (`dataset-stats.drawio`) presents a comparison of average trajectory lengths (28.8 vs 15.3). However, it displays only the mean values as bars. Long-horizon tasks inherently have high variance; omitting error bars (standard deviation or confidence intervals) makes the visual comparison misleading. The visual difference might appear significant, but without uncertainty bounds, the claim of a "1.9x" improvement lacks visual statistical support.

**Color and Legend Usage:**
Figure 5 (`failure-heatmap.drawio`) uses a heatmap to show failure counts across ablation variants. While the color gradient is intuitive, the figure lacks a color bar legend mapping colors to specific counts (e.g., 0 to 100). Without this, the reduction from 99 to 58 is a guess based on the caption rather than a visual fact. Add a discrete or continuous color bar with labeled ticks.

**Alt Text:**
The LaTeX source includes `\caption` text but lacks explicit `alt` text or `description` fields for accessibility. Ensure that the generated PDF or the arXiv submission includes descriptive alt text for all figures, particularly the complex diagrams like Figure 2 (`framework.drawio`) which describes a multi-component state transition.

Addressing these issues will significantly improve the reproducibility and professional quality of the visual evidence presented.
