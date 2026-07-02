---
action_items:
- id: 51b94548ebc4
  severity: science
  text: 'Figure 1: The caption ''Throughput mode'' contradicts the y-axis label ''Latency
    (s)''; the figure displays latency, not throughput.'
- id: 2a2fe0295a36
  severity: writing
  text: 'Figure 1: The legend defines ''Mellum 4B'' and ''Qwen2.5-7B'' but the plot
    contains dozens of unlabeled data points (e.g., ''T:11.6B'', ''A:2.5B'') that
    are not defined in the caption or legend.'
- id: df70c0ced7fc
  severity: writing
  text: 'Figure 1: The x-axis label ''Depth (Layers)'' is ambiguous as the tick marks
    (24, 26, 28...) do not clearly correspond to the specific model configurations
    labeled on the plot.'
- id: 942be7819e1b
  severity: science
  text: 'Figure 2: The caption describes ''Throughput mode (concurrent requests)'',
    but the plot axes are ''Width (Hidden Dimension)'' and ''Depth (Layers)'', and
    the colorbar is ''Latency (s)''. The figure displays a latency contour map, not
    throughput or concurrent request data, contradicting the caption.'
- id: 79a77dc19b61
  severity: science
  text: 'Figure 2: The legend identifies ''Mellum 4B'' and ''Qwen2.5-7B'', but the
    plot contains a dense grid of data points (grey circles) with specific values
    (e.g., ''7.05B'', ''8.62B'') that are not explained in the caption or legend.
    It is unclear if these points represent the models or a parameter sweep.'
- id: 4ebb07675ebe
  severity: science
  text: 'Figure 3: The caption claims to compare ''MoE models'' (plural) with Sliding
    Window Attention, but the plot only explicitly labels one MoE model (''Mellum
    2'') and a group of ''6 other candidate configs'' without specifying if they are
    MoE or their window sizes. This makes the claim of comparing ''MoE models'' (plural)
    unsupported by the visual data.'
- id: aea432eec1ac
  severity: writing
  text: 'Figure 3: The text ''6 other candidate configs'' is rendered in a very light
    gray font that is difficult to read against the white background, reducing legibility.'
- id: cf23c834b2f4
  severity: science
  text: 'Figure 4: The caption ''Qwen2.5-7B (dense)'' is too generic and fails to
    describe the specific comparison shown (Muon vs. AdamW vs. Muon Moonlight) or
    the metric (Validation loss), making the figure''s purpose unclear without external
    context.'
- id: 04dd5a59b0d8
  severity: writing
  text: "Figure 4: The top annotation 'Muon (Megatron defaults) \u2014 diverged ->\
    \ 2.47 at 21B' is rendered in a very small, light orange font that is difficult\
    \ to read against the white background."
- id: 1145ac99684a
  severity: writing
  text: 'Figure 4: The legend labels ''AdamW'' and ''Muon (Moonlight)'' are placed
    directly on the plot area without a distinct legend box or leader lines, which
    can be confusing if the lines were to cross or overlap.'
- id: a7f257e80932
  severity: writing
  text: 'Figure 6: The caption contains raw LaTeX formatting artifacts (''uniform
    $$-bump'' and ''unchanged-$$'') instead of the readable method names (''Uniform
    RoPE base'' and ''Unchanged RoPE base'') shown in the plot labels.'
- id: de75ec70b12a
  severity: writing
  text: 'Figure 6: The caption references ''See for caveats on the absolute scores''
    but lacks the specific figure or section number to which the reader should refer.'
- id: 54d626ab0be8
  severity: writing
  text: 'Figure 7: The caption references ''See for a comment on absolute RULER scores''
    but does not specify which section, figure, or table to consult.'
- id: 1cf02ffa8cd7
  severity: science
  text: 'Figure 7: The x-axis label ''Long-context training tokens (B)'' is ambiguous;
    it is unclear if ''B'' refers to billions of tokens or a specific batch size parameter.'
- id: d40d609a0167
  severity: writing
  text: "Figure 8: The annotation 'RULER plateau (\u224830 B)' is present but lacks\
    \ a definition in the caption or legend explaining what the 'RULER plateau' signifies\
    \ in the context of load-balancing loss."
- id: fa4d575c1196
  severity: science
  text: 'Figure 8: The y-axis label ''Load-balancing loss'' is generic; the caption
    does not specify the exact loss function or metric used (e.g., auxiliary loss
    coefficient, specific MoE load-balancing formula), making it difficult to interpret
    the absolute values.'
- id: 898917619a9f
  severity: writing
  text: 'Figure 10: The caption contains a sentence fragment (''matches the sync latency...'')
    that lacks a subject, failing to explicitly state that ''Mellum 2'' is the model
    being described.'
- id: 3915d295ca25
  severity: science
  text: 'Figure 10: The ''Sync (single request)'' chart displays raw values (193 vs
    192) but does not visually represent the ''matches'' claim in the caption, as
    the bars are distinct in length without error bars to indicate statistical equivalence.'
artifact_hash: cb4466a31e7b640ad51d8c2f8310c27b9827d874fc645a40e58bc959301ab98e
artifact_path: projects/PROJ-647-mellum2-technical-report/paper/metadata.json
backend: dartmouth
feedback: Vision review of 10 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T15:32:49.086099Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

The figure is visually clear but the caption is misleading as it claims to show 'Throughput' while the axis displays 'Latency'. Additionally, the plot is cluttered with numerous unlabeled data points that are not defined in the legend or caption.

### Figure 2

The figure is a latency contour map that contradicts its caption, which claims to show throughput and concurrent requests. Additionally, the data points plotted on the grid are not defined in the caption or legend, making the visualization ambiguous.

### Figure 3

The figure effectively visualizes latency trends but fails to support the caption's claim of comparing multiple MoE models, as the other configs are not explicitly identified as MoE. Additionally, the label for the candidate configs suffers from poor contrast.

### Figure 4

The figure effectively displays the validation loss curves for different optimizers, but the caption is insufficiently descriptive, and the annotation regarding the diverged run is illegible due to poor contrast.

### Figure 5

Figure 5 is a clear and well-structured line plot showing LM loss over training steps. The axes are labeled with units, the three training phases are visually distinguished with background shading and text, and the vertical dashed lines align with phase transitions. The caption accurately describes the figure content.

### Figure 6

The figure is clear and the data presentation is effective, but the caption contains raw LaTeX syntax errors in the method names and a broken cross-reference regarding score caveats.

### Figure 7

The figure clearly displays the relationship between RULER scores and training tokens for three model sizes, but the caption contains an incomplete cross-reference and the x-axis unit is slightly ambiguous.

### Figure 8

The figure clearly displays the load-balancing loss trend over training tokens, but the annotation regarding the 'RULER plateau' is undefined, and the specific loss metric is not detailed in the caption.

### Figure 9

Figure 9 clearly displays training and validation accuracy curves with appropriate axis labels, units, and a legend. The caption accurately describes the visualization, including the smoothed train curve, raw per-step values, and validation sampling frequency.

### Figure 10

The figure effectively presents the benchmark data with clear axes and labels, but the caption contains a grammatical error omitting the subject, and the visual representation of the latency comparison lacks error bars to substantiate the claim of matching performance.
