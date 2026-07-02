---
action_items:
- id: f097ade52793
  severity: writing
  text: 'Figure 1: The caption is missing; the provided text ''(no caption)'' does
    not describe the plot''s content, experimental setup, or the specific model/dataset
    used.'
- id: bf69dcea43ce
  severity: writing
  text: 'Figure 1: The legend at the top is cut off, displaying only the line styles
    and percentages (50%, 90%, 99%) without the corresponding variable name or unit.'
- id: e5d6ee74f6ba
  severity: writing
  text: 'Figure 3: The caption contains a placeholder ''$$'' instead of the actual
    variable name (likely ''gamma'' or ''block size''), making the text incomplete.'
- id: 205bc228c2b5
  severity: writing
  text: "Figure 3: The y-axis label 'Block Efficiency (\u03C4)' uses the symbol '\u03C4\
    ', but the caption refers to 'block efficiency $$', creating a notation mismatch."
- id: c9cdcf9f3d2c
  severity: writing
  text: "Figure 4: The caption contains raw LaTeX syntax ('$$') instead of the actual\
    \ variable name (e.g., '\u03B3' or 'gamma'), making the metric undefined in the\
    \ text."
- id: a5fdab8f7957
  severity: writing
  text: 'Figure 4: The y-axis label ''Block Efficiency (r)'' uses the symbol ''r'',
    which contradicts the caption''s use of ''$$'' and is not defined in the caption
    or legend.'
- id: 77cd69c378c7
  severity: writing
  text: 'Figure 5: The figure lacks a formal caption; the text ''Main figure-1-ver2''
    appears to be a filename artifact rather than a descriptive caption.'
- id: 3a7ca8ff6083
  severity: writing
  text: 'Figure 5: The legend at the top is not enclosed in a box or clearly separated
    from the diagram content, which may cause confusion regarding its scope.'
- id: b25a53204de4
  severity: science
  text: 'Figure 6: The caption states the blue line marks $Speedup_{SD}=1+\epsilon$,
    but the legend explicitly defines it as $Speedup = 1 + \epsilon (\epsilon = 0.05)$.
    The caption fails to define the value of $\epsilon$, making the threshold ambiguous
    without reading the legend.'
- id: 908cf5f2f9c5
  severity: writing
  text: 'Figure 6: The y-axis label ''Batch'' is ambiguous; it likely refers to ''Batch
    Size'' given the range (0-60), but the unit is not specified.'
- id: 71fc76b2674d
  severity: writing
  text: 'Figure 7: The caption contains unrendered LaTeX placeholders (''$$'') instead
    of the variable name (likely ''gamma'' or ''draft length''), making the text unreadable.'
- id: 02b4119eb651
  severity: science
  text: "Figure 7: The red line is annotated with '\u03C4 5.1 -> 5.6 (below thres)',\
    \ but the line is flat at y=5, contradicting the claim that the value increases\
    \ to 5.6."
- id: 8e2b3a431371
  severity: writing
  text: "Figure 7: The y-axis label 'Draft Length \u03B3' uses the Greek letter gamma,\
    \ but the caption uses '$$', creating a disconnect between the visual and the\
    \ description."
- id: ec542fb60c73
  severity: fatal
  text: 'Figure 8: The caption is non-existent (''Qwen3-8B [filename]''), failing
    to describe the plot''s content, axes, or experimental conditions.'
- id: fd0030584eec
  severity: science
  text: 'Figure 8: The legend lists ''No-SD'' and ''EAGLE3'' variants, but the caption
    does not define these terms or explain the experimental setup.'
- id: a8fa26691529
  severity: writing
  text: 'Figure 8: The Y-axis label ''Rollout Generation Time (s)'' is ambiguous;
    it is unclear if this represents total time, per-step time, or time per token.'
- id: 0c0536512696
  severity: science
  text: 'Figure 9: The legend lists ''Qwen2.5-7B (EAGLE3 ours)'' (solid blue) and
    ''Qwen2.5-7B (EAGLE FastRL)'' (solid light blue), but the caption claims ''evaluated
    learned auxiliary drafters remain largely below target-induced quantized drafters.''
    The solid blue line (EAGLE3 ours) is clearly ABOVE the dashed quantized lines
    for most of the plot, directly contradicting the caption''s claim.'
- id: da328cb51818
  severity: writing
  text: 'Figure 9: The legend is cluttered and difficult to read due to the high number
    of entries and similar line colors (e.g., multiple shades of blue and orange),
    making it hard to distinguish between specific model configurations like ''Qwen2.5-7B
    (EAGLE3 ours)'' and ''Qwen2.5-7B (EAGLE FastRL)''.'
- id: bf8ce8bb4e73
  severity: fatal
  text: 'Figure 10: The caption is non-descriptive (''Qwen2.5-7B'') and fails to explain
    the plot''s content, axes, or what the orange line represents, making the figure
    unintelligible.'
- id: 133b21190c84
  severity: science
  text: 'Figure 10: The y-axis label ''Block Efficiency (r)'' uses an undefined symbol
    ''r'' without specifying units or the baseline for comparison.'
- id: 71d1d0aee252
  severity: writing
  text: 'Figure 11: The caption ''Qwen2.5-7B'' is insufficient; it fails to describe
    the plot''s content (Rollout Gen. Time vs. Training Step) or the specific methods
    being compared.'
- id: 3be563fb4f10
  severity: writing
  text: 'Figure 11: The legend is placed outside the plot area at the top, which is
    non-standard and risks being cut off or misaligned in different renderings.'
- id: 2ca8b490909e
  severity: writing
  text: 'Figure 12: The caption ''Qwen2.5-7B'' is insufficient; it fails to describe
    the plot''s content (Reward vs. Training Step) or the specific methods being compared
    (''veRL (AR)'' vs. ''EfficientRollout'').'
- id: 1ec5864dc2a7
  severity: science
  text: 'Figure 12: The legend uses the label ''veRL (AR)'' without defining what
    ''AR'' stands for (e.g., Autoregressive), which is necessary for interpreting
    the baseline comparison.'
artifact_hash: f5cd2bf8ec4b16de31454f2a2486d371422b77f233615f81a71aa09fed433b62
artifact_path: projects/PROJ-738-efficientrollout-system-aware-self-specu/paper/metadata.json
backend: dartmouth
feedback: Vision review of 12 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T16:17:12.564072Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

The figure displays a cumulative completion curve but lacks a descriptive caption and has a truncated legend, making it impossible to understand the context or the specific variable being measured.

### Figure 2

Figure 2 effectively visualizes the inverse relationship between policy entropy and first-token acceptance across three models. The dual y-axes are clearly labeled with units, the Pearson correlation coefficients are explicitly stated, and the caption accurately describes the trends shown.

### Figure 3

The figure clearly visualizes the inverse relationship between policy entropy and block efficiency across three models. However, the caption contains a placeholder '$$' and uses a different symbol for block efficiency than the axis label.

### Figure 4

The figure is visually clear with a readable legend and axes, but the caption contains raw LaTeX syntax ('$$') and the y-axis label uses an undefined symbol ('r') that conflicts with the caption.

### Figure 5

The figure effectively illustrates the KV cache workflow with clear color coding and text annotations, but it lacks a formal descriptive caption and the legend presentation is slightly informal.

### Figure 6

The figure effectively visualizes the validation of the SD toggle policy with clear color mapping and markers. However, the caption is slightly incomplete regarding the definition of the epsilon threshold used for the blue line, and the y-axis label could be more specific.

### Figure 7

The figure is visually clear but the caption contains unrendered LaTeX placeholders ('$$') that obscure the meaning. Additionally, the annotation on the red line contradicts the visual data, claiming a value increase that does not occur.

### Figure 8

The figure displays a line chart of rollout generation time but is critically flawed by a non-existent caption that fails to describe the data, axes, or legend entries.

### Figure 9

The figure contradicts its own caption by showing the 'EAGLE3 ours' line performing better (higher block efficiency) than the quantized baselines, whereas the text claims learned drafters remain below them. Additionally, the legend is overly dense and uses similar colors that reduce readability.

### Figure 10

The figure displays a line plot of block efficiency but is rendered useless by a non-descriptive caption that fails to identify the data series or experimental conditions.

### Figure 11

The figure clearly displays the performance comparison of rollout generation time across different methods, but the caption is merely a model name and lacks a descriptive summary of the data shown.

### Figure 12

The figure clearly displays reward curves for two methods, but the caption is non-descriptive and the legend contains an undefined acronym ('AR') that obscures the baseline definition.
