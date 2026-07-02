---
action_items:
- id: 6b1b767afcc6
  severity: writing
  text: In changhai_cold_admission_staircase.tex, y-axis ticks lack explicit units.
    Add 's' to tick labels or ensure the rotated axis title is large enough to be
    the sole unit source for print legibility.
- id: 25238bc4c5b9
  severity: writing
  text: In changhai_hotset_ladder.tex, the right y-axis (latency) lacks grid lines,
    making it hard to correlate the line plot with values. Add faint grid lines for
    the right axis ticks.
- id: cf2f89368ffe
  severity: writing
  text: In mint_system_blocks.tex, color distinguishes hot/cold paths. Ensure line
    styles (solid/dashed) are applied to all elements, not just the legend, for grayscale/print
    safety.
- id: 83e27db453b8
  severity: writing
  text: In e2_training_utilization.tex, the caption mentions utilization metrics not
    visualized in the schematic timeline. Either add a utilization overlay or clarify
    the figure is purely schematic.
artifact_hash: 9b74dd1f4b8f2d4815ea056f5e26899cdd80d0bb7bac2914c7ef2512791b5d74
artifact_path: projects/PROJ-566-mint-managed-infrastructure-for-training/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T20:07:26.544961Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

The figures in the MinT paper effectively communicate the system architecture and performance, but several issues regarding legibility and accessibility need addressing.

**Axis Labels and Units:**
In `figures/changhai_cold_admission_staircase.tex` and `figures/changhai_latency_cold_load_panels.tex` (Panel C), the y-axis represents time in seconds. While the rotated label "cumulative add_lora time (s)" is present, the tick marks (0, 5, 10...) do not explicitly state the unit. In print, if the rotated label is obscured, the unit might be lost. Include the unit in tick labels (e.g., "5s") or ensure the axis title is sufficiently prominent.

**Dual-Axis Clarity:**
Figures `changhai_hotset_ladder.tex` and `changhai_true_unique_frontier.tex` use a dual-axis design. The right y-axis (latency) has tick marks that are disconnected from the data points. The lack of grid lines makes it difficult to map the latency line to specific time values. Add faint horizontal grid lines corresponding to the right-axis ticks to improve readability.

**Color Reliance:**
Figures like `mint_system_blocks.tex` rely heavily on color (blue for "hot", amber for "cold") to distinguish components. While the legend uses line styles, the main diagram elements rely on color. For black-and-white printing, the distinction may be ambiguous. Ensure all critical distinctions have distinct line styles or patterns in addition to color to make the figures grayscale-safe.

**Schematic vs. Quantitative:**
Figure `e2_training_utilization.tex` is a schematic timeline. The caption mentions "average GPU utilization" and "peak memory," but these are not explicitly visualized. If the figure is meant to show utilization, a bar or area chart overlay would be more effective. If purely schematic, adjust the caption to avoid implying quantitative data not present in the visual.

**Legend Consistency:**
Ensure all legends are consistent across figures and that symbols match exactly with those in the figures, particularly in `mint_teaser.tex` where the legend description could be clearer.

Addressing these points will enhance the clarity and accessibility of the figures for all readers.
