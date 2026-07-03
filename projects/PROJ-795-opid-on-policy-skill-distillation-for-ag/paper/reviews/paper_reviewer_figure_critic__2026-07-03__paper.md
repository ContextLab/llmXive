---
action_items:
- id: 26038a2f66f0
  severity: science
  text: 'Figure 1: The caption claims OPID is ''competitive'' on Search-based QA,
    but the chart shows OPID (49.2) is significantly outperformed by multiple baselines
    (e.g., Skill-GRPO* at 47.5, Skill-SD at 47.8, RLSD at 49.0, SDAR at 49.0) and
    is not the strongest; the claim contradicts the visual data.'
- id: fabbc4a7c393
  severity: writing
  text: 'Figure 1: The y-axis labels (method names) are not explicitly defined in
    the caption or legend, forcing the reader to infer which bars correspond to which
    method groups without a clear key.'
- id: e2d432aa5c96
  severity: science
  text: 'Figure 4: The caption claims OPID ''approaches full-data GRPO performance
    using about 60% of the data,'' but the chart shows OPID at 60% data (~73%) is
    still significantly higher than GRPO at 100% data (~76%), and the red arrow annotation
    points to the gap between OPID at 60% and GRPO at 100% rather than showing convergence.
    The visual evidence does not support the specific claim of ''approaching'' performance
    at that data fraction.'
- id: d54ce7f3ee5d
  severity: writing
  text: "Figure 4: The annotation '\u2248 40% Data' with a downward arrow is ambiguous;\
    \ it is unclear if this refers to the data reduction (100% - 60% = 40%) or a specific\
    \ metric value, and the arrow placement between the curves does not clearly link\
    \ to the x-axis value of 60%."
- id: 5d0164337012
  severity: science
  text: "Figure 6: The y-axis label 'Avg critical steps' contradicts the caption's\
    \ claim that the curve reports 'how many timesteps are selected... in each trajectory'\
    \ (a count per sequence). The y-axis values (~3.0\u20134.0) are too low to represent\
    \ a raw count of steps per trajectory if the x-axis is 'Training step' (1\u2013\
    150), suggesting the metric is an average over multiple trajectories per step,\
    \ but this aggregation is not explained in the caption or axis label."
- id: 0600ce191ced
  severity: writing
  text: 'Figure 6: The annotation ''avg 3.692'' is placed near the end of the plot
    without clarifying whether it represents the global mean across all training steps
    or a local average; the caption does not define this value.'
- id: d27e92c8e04f
  severity: science
  text: "Figure 7: The x-axis is labeled 'Training step' with a range of 1\u2013150,\
    \ but the caption describes 'magnitudes... during OPID training' without specifying\
    \ the unit of the step (e.g., iterations, epochs, or gradient updates). This ambiguity\
    \ makes it impossible to assess the training duration or convergence rate."
- id: ddcc57387f8c
  severity: writing
  text: "Figure 7: The y-axis label for the bottom panel, 'Skill abs advantage(1e-4)',\
    \ uses scientific notation that implies the plotted values are scaled by 10,000.\
    \ However, the axis ticks (1.5\u20134.0) and the caption's description of 'magnitudes'\
    \ suggest these are raw values. If the values are indeed scaled, the caption should\
    \ explicitly state this to avoid misinterpretation of the signal's strength relative\
    \ to the episode advantage."
artifact_hash: ebe41e02149487ccd15d4c76bf5323b1b6f5d76f7c2ba35eb80cabef31288797
artifact_path: projects/PROJ-795-opid-on-policy-skill-distillation-for-ag/paper/metadata.json
backend: dartmouth
feedback: Vision review of 12 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T20:06:56.094617Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

The figure presents a clear bar chart comparing methods across three tasks, but the caption's claim that OPID is 'competitive' on Search-based QA is misleading given that several baselines outperform it. Additionally, the method names on the y-axis lack explicit definition in the caption or legend.

### Figure 2

Figure 2 provides a clear and comprehensive visual overview of the OPID framework, effectively illustrating the three-stage process from skill extraction to routing and self-distillation. The diagram is well-structured with distinct color coding and clear labels that align perfectly with the provided caption, making the complex methodology easy to follow.

### Figure 3

Figure 3 effectively visualizes the training dynamics of OPID and GRPO with clear axes, units, and a legend. The distinction between raw measurements (translucent) and smoothed trends (solid) is explicitly defined in the caption and visually distinct, supporting the claim of improved performance.

### Figure 4

The figure effectively displays the performance gap between OPID and GRPO across data fractions, but the caption's claim about approaching full-data performance at 60% is not strongly supported by the visual gap shown, and the '≈ 40% Data' annotation lacks clear context.

### Figure 5

Figure 5 effectively illustrates the qualitative differences between GRPO and OPID agents on the specified ALFWorld task. The side-by-side trajectory comparison is clear, with distinct annotations highlighting specific failure modes (hallucination, substitution) and successful steps, fully supporting the claims in the caption.

### Figure 6

Figure 6 presents a time-series of critical step counts but mislabels the y-axis as an average when the caption describes per-trajectory counts, and the annotation lacks contextual definition.

### Figure 7

Figure 7 presents two line plots comparing advantage signals, but the x-axis unit is undefined and the y-axis scaling in the bottom panel is ambiguous, hindering accurate interpretation of the training dynamics.

### Figure 8

Figure 8 displays the 'Analyser Prompt' used in the study. The text is legible, and the figure effectively communicates the instructions and JSON schema required for the analyzer component described in the paper.

### Figure 9

Figure 9 presents a clear, step-by-step text trajectory of an agent completing a task in the ALFWorld environment. The layout is readable, the steps are logically ordered, and the content aligns perfectly with the caption's description of a full trajectory.

### Figure 10

Figure 10 presents a clear, text-based qualitative example of an agent trajectory on ALFWorld, consistent with the format of Figure 9 and the caption description. The step-by-step breakdown of observations, reasoning, and actions is legible and effectively illustrates the agent's behavior.

### Figure 11

Figure 11 presents a clear, text-based visualization of a Search-QA agent trajectory, effectively illustrating the step-by-step reasoning and search actions described in the caption. The layout is uncluttered, and the content is fully legible, successfully supporting the claim of showing a full trajectory.

### Figure 12

Figure 12 presents a clear, step-by-step textual log of an agent's trajectory on a Search-QA task. The layout is readable, the reasoning steps are distinct, and the final answer is explicitly marked, fully supporting the caption's description.
