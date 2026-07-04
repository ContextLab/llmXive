---
action_items:
- id: c34864bd06bc
  severity: writing
  text: 'Figure 1: The legend entry ''Ours'' is not defined in the caption; the caption
    only defines ''DFlash(n)'' but does not explicitly name the proposed method.'
- id: 11f64bfa2f2d
  severity: writing
  text: "Figure 1: The y-axis label 'SpeedUp (\xD7)' is ambiguous; it should clarify\
    \ whether this is relative to a baseline (e.g., 'relative to EAGLE-3' or 'vs.\
    \ baseline')."
- id: 0e2f334c3677
  severity: science
  text: 'Figure 1: No error bars or confidence intervals are shown despite multiple
    models and settings; this limits assessment of statistical significance of the
    reported speedups.'
- id: 6343f8d58002
  severity: science
  text: "Figure 2: The y-axis is labeled 'Proportion' (0 to 1), but the bars for each\
    \ group (e.g., GSM8K: 0.34 + 0.66 = 1.0) sum to 1.0, implying they represent the\
    \ full distribution of a binary outcome. However, the caption states 'Proportion\
    \ of samples with B* matching or mismatching B', which is ambiguous. It is unclear\
    \ if the blue bars represent 'matching' and orange 'mismatching', or vice versa.\
    \ The legend at the top defines B* = B (blue) and B* \u2260 B (orange), but this\
    \ legend is not clearly linked to"
- id: 24af4747b0c0
  severity: writing
  text: "Figure 2: The legend at the top uses colored squares to denote B* = B (blue)\
    \ and B* \u2260 B (orange), but these colors are not explicitly stated in the\
    \ caption. While the colors match the bars, the caption should clarify that blue\
    \ represents 'B* = B' and orange represents 'B* \u2260 B' for readers who may\
    \ not immediately associate the legend with the bars."
artifact_hash: d1adb033922809cc3a6775315ab50696e09aef30604df9967080e20f9c9fc5f8
artifact_path: projects/PROJ-849-blockpilot-instance-adaptive-policy-lear/paper/metadata.json
backend: dartmouth
feedback: Vision review of 3 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-04T02:14:19.773495Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

Figure 1 presents a clear bar chart comparing speedups across models, but the legend entry 'Ours' is undefined in the caption, the y-axis lacks baseline context, and no uncertainty measures are provided.

### Figure 2

Figure 2 presents a clear bar chart comparing proportions, but the legend's connection to the bar colors is implicit rather than explicit, and the caption could be more precise in defining what each color represents to avoid ambiguity.

### Figure 3

Figure 3 provides a clear and well-structured schematic of the BlockPilot inference pipeline. The visual flow from input sequences through the LLM Target Model, Block Predictor, and dLLM Draft Model is logical and easy to follow. The caption accurately describes the process shown, and all components are clearly labeled.
