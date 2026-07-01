---
action_items:
- id: 3912ffbf767f
  severity: writing
  text: Figure 1 (OPID_v2.pdf) and Figure 2 (training_dynamics) lack visible axis
    labels and units in the provided source. The caption for Fig 2 mentions 'smoothed
    trends' but the plot does not explicitly label the smoothing window or method
    on the axis. Ensure all axes have clear labels (e.g., 'Training Steps', 'Success
    Rate (%)') and units are defined in captions or legends.
- id: 4afc0d25ba30
  severity: writing
  text: Figure 3 (sample_efficiency_line) and Figure 4 (generalization_bar) rely on
    color coding (topcolor/secondcolor) to distinguish methods. The source code uses
    custom LaTeX colors but does not provide a legend or pattern differentiation (e.g.,
    hatching) for grayscale printing. Add a legend or distinct markers to ensure legibility
    at print scale.
- id: d849bef2ca77
  severity: writing
  text: Figure 5 (case_comparison) is a qualitative comparison but lacks a scale bar
    or step counter visualization within the image itself. The caption mentions 'six
    steps' but the figure does not visually annotate the step count or the specific
    hallucination point, reducing its immediate interpretability without reading the
    text.
- id: 95f7df2cc3a9
  severity: writing
  text: Appendix Figure 1 (critical_steps_on_alfworld) and Figure 2 (training_advantage_alfworld)
    are referenced in the text but their axis labels and units are not visible in
    the LaTeX source. Verify that these figures include 'Average Critical Steps' and
    'Advantage Magnitude' labels with appropriate units.
artifact_hash: ebe41e02149487ccd15d4c76bf5323b1b6f5d76f7c2ba35eb80cabef31288797
artifact_path: projects/PROJ-795-opid-on-policy-skill-distillation-for-ag/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T00:06:27.205930Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

The manuscript contains several figures that are critical for understanding the OPID framework and its empirical results, but they currently lack necessary metadata for standalone interpretation and print legibility.

**Figure 1 (Overview):** The pipeline diagram (`figures/OPID_v2.pdf`) is central to the method. While the caption describes the flow, the figure itself must clearly label the "Analyzer," "Router," and "Policy" blocks with distinct visual styles. Ensure that the arrows indicating data flow (e.g., "on-policy trajectories" vs. "routed skill") are thick enough to be visible when printed in grayscale.

**Figure 2 (Training Dynamics):** This figure (`figures/episode_success_rate_smoothed.pdf` and `figures/episode_length_smoothed.pdf`) compares OPID and GRPO. The current source lacks explicit axis labels (e.g., "Steps" vs. "Success Rate"). The caption mentions "translucent curves" for raw data, but the legend distinguishing "Raw" vs. "Smoothed" is missing from the visual itself. Without a legend, the reader cannot distinguish the two line styles. Additionally, the y-axis for "Episode length" needs a unit (e.g., "Steps").

**Figure 3 & 4 (Sample Efficiency & Generalization):** These figures (`figures/sample_efficiency_line.pdf` and `figures/generalization_bar.pdf`) use color to denote performance tiers (best/second-best). In a print context, color differentiation can fail. The bar chart in Figure 4 should include error bars if statistical significance is claimed, or at least distinct patterns (hatching) for the bars to differentiate "OPID" from "GRPO" without relying solely on color. The line chart in Figure 3 needs a clear legend indicating which line corresponds to which data percentage (20%, 40%, etc.).

**Figure 5 (Case Study):** The qualitative comparison (`figures/OPID_case.pdf`) is effective but dense. The caption states the GRPO agent "hallucinates," but the figure does not visually highlight the specific token or state where this occurs. Adding a red box or arrow pointing to the hallucinated object in the image would significantly improve clarity.

**Appendix Figures:** The figures in the appendix (`critical_steps_on_alfworld.pdf`, `training_advantage_alfworld.pdf`) are referenced for diagnostic purposes. They currently appear to lack axis titles in the source code. Ensure "Average Critical Steps" and "Advantage Magnitude" are explicitly labeled on the axes.

**Alt Text:** None of the figures currently have `alt` text or `description` fields in the LaTeX source (e.g., using the `alttext` package or similar). For accessibility and future archival, every figure environment should include a concise text description of the visual content.

**Conclusion:** The figures are conceptually sound but require technical refinement regarding axis labeling, legend inclusion, and print-scale legibility (grayscale/patterns) to meet publication standards.
