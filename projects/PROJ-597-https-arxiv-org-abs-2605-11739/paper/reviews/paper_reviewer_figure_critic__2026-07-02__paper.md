---
action_items:
- id: eb3b33b3cf8a
  severity: science
  text: 'Figure 2: The caption claims the figure compares ''RL and OPD'', but the
    legends in all subplots explicitly label the orange curves as ''PPO'', ''GRPO'',
    or ''DAPO'' (specific distillation methods) rather than the generic ''RL'' category
    mentioned in the text.'
- id: e66784d178fe
  severity: science
  text: 'Figure 2: The x-axis label ''Update Norm of ||alpha Delta W||_F'' in panel
    (a) includes a scaling factor alpha, but the caption describes the analysis as
    ''updates scaled to the same norm'' without clarifying if alpha represents the
    scaling factor or a hyperparameter, creating ambiguity in the axis definition.'
- id: e77c03f1e052
  severity: science
  text: 'Figure 3: The caption states panel (b) shows ''OPD reasoning accuracy'' (line),
    but the legend explicitly labels the line series as ''MLP Accuracy'' and ''Attn
    Accuracy'', creating a direct contradiction between the text description and the
    visual legend.'
- id: 7f55a1f524cd
  severity: science
  text: 'Figure 3: Panel (b) displays ''RL Extra Update'' and ''OPD Effective update''
    in the legend, but the caption claims the bars represent ''RL/OPD-trained'' models
    without specifying which color corresponds to which method, making the comparison
    ambiguous.'
- id: f3b7db09f447
  severity: science
  text: 'Figure 4: The caption claims panel (b) shows ''RL incurs significantly larger
    norm cost'', but the legend in the rendered image labels the orange line as ''GRPO''
    (in the middle plot) and ''DAPO'' (in the right plot), not ''RL''. This contradicts
    the caption''s claim and makes the comparison to RL impossible to verify visually.'
- id: 5bd9ef57f12d
  severity: writing
  text: 'Figure 4: The x-axis label in panel (b) reads ''Rank Percentage of $\Delta
    W_{bottom-k}$ (%)'', but the tick marks range from 0 to 50. The caption describes
    this as ''Bottom-$k\%$ subspace'', implying the x-axis represents the percentage
    of the bottom subspace, yet the label syntax is slightly ambiguous compared to
    panel (a).'
- id: 6579d55b9c21
  severity: science
  text: 'Figure 5: The caption describes panel (a) as a ''t-SNE visualization of Top-1
    subspace evolution'', but the plot is a 2D line chart with axes labeled ''Dim
    1'' and ''Dim 2'' showing trajectories. This contradicts the standard definition
    of t-SNE (which is a scatter plot of high-dimensional points) and mislabels the
    visualization type.'
- id: f26cb9892b5e
  severity: science
  text: 'Figure 5: Panel (c) displays ''Accuracy (%)'' on the left y-axis (0-60 range)
    and ''KL Loss'' on the right y-axis (0.0-1.0 range). However, the orange line
    (''Scaled Acc'') and blue line (''Original Acc'') track the right axis values
    (0.8-1.0) rather than the left axis (0-60), making the left axis misleading and
    the data interpretation confusing.'
- id: 8b846b9d5f0a
  severity: writing
  text: 'Figure 5: The legend in panel (c) uses the term ''Scaled Acc'' and ''Scaled
    KL'', but the caption refers to ''Changes in Accuracy and KL''. The legend should
    explicitly state ''Scaled Accuracy'' and ''Scaled KL'' for clarity, or the caption
    should match the legend terminology.'
- id: cc88e1ba7d8d
  severity: writing
  text: 'Figure 6: The caption is too generic (''Performance comparison...'') and
    fails to define the specific symbols used in the plots, such as the star markers
    which likely denote best performance or specific checkpoints.'
- id: dadafbe8b71d
  severity: writing
  text: 'Figure 6: The x-axis label ''Training Steps'' is missing from the top row
    of subplots, creating visual inconsistency with the bottom row.'
- id: a5ce9f4b94d2
  severity: science
  text: 'Figure 7: The legend in panel (a) lists ''lr = 1e-6 (EffOPD)'' but the other
    four entries are labeled ''(OPD)''. Since the figure caption states this panel
    shows the ''Effect of different learning rates'' for the proposed method, the
    legend should consistently label all entries as ''EffOPD'' (or the specific variant)
    to avoid implying a comparison with the base OPD method which is not the variable
    being tested here.'
- id: 4b93760d1fbf
  severity: writing
  text: 'Figure 7: The x-axis label in panel (c) is ''Time (s)'', but the tick marks
    (10000, 20000, etc.) suggest the unit is likely milliseconds or the label is missing
    a multiplier (e.g., ''Time (ms)'') given typical training durations for LLMs;
    clarify the unit to ensure accurate interpretation of the efficiency gains.'
- id: 8e8c80648710
  severity: science
  text: 'Figure 8: The caption claims a comparison between ''RL and OPD'', but the
    legends in all subplots explicitly label the orange line as ''PPO'', ''GRPO'',
    or ''DAPO''. While these are RL methods, the caption should explicitly name the
    specific baselines shown (e.g., ''PPO, GRPO, and DAPO'') rather than using the
    generic term ''RL'' to avoid ambiguity.'
- id: de9fa6245b31
  severity: writing
  text: "Figure 8: The x-axis label 'Update Norm of ||\u03B1\u0394W||_F Based on the\
    \ Final Checkpoint' is cluttered and difficult to read due to the mathematical\
    \ notation and length; consider simplifying the phrasing or moving the 'Based\
    \ on...' qualifier to the caption."
- id: 6093382d9fb6
  severity: science
  text: 'Figure 9: The caption claims to compare ''RL and OPD'', but the legends in
    all four subplots explicitly label the orange line as ''DAPO'' or ''GRPO'' rather
    than ''RL''. This contradicts the caption''s assertion that the figure analyzes
    RL dynamics.'
- id: 1e7844596b5f
  severity: science
  text: "Figure 9: The x-axis label 'Update Norm of ||\u0394W||_F during Different\
    \ Training Checkpoints' is ambiguous; it is unclear if the norm is cumulative\
    \ (total distance from initialization) or instantaneous (step size), which is\
    \ critical for interpreting the 'efficiency' claim."
- id: 92434a50a4a1
  severity: science
  text: 'Figure 10: The caption describes panel (a) as showing the ''Effect of embedding
    layer replacement on MATH500'', but the x-axis labels clearly indicate ''Qwen2.5-7B-PPO'',
    ''Qwen3-8B-PPO'', and ''Qwen3-8B-DAPO'', which are different model architectures
    or training setups, not embedding layer replacement experiments.'
- id: 523508595b86
  severity: science
  text: 'Figure 10: Panel (a) legend includes ''Base'', ''OPD'', ''RL'', ''OPD w/
    Base Emb'', and ''RL w/ Base Emb'', but the bars for ''Qwen2.5-7B-PPO'' and ''Qwen3-8B-PPO''
    groups do not include the ''Base'' condition (purple bar), making the comparison
    incomplete and inconsistent with the third group.'
- id: 37bbf14af745
  severity: writing
  text: 'Figure 10: Panel (b) legend lists ''OPD Effective update (MLP)'', ''OPD Effective
    update (Attn)'', ''RL Extra Update (MLP)'', ''RL Extra Update (Attn)'', and two
    accuracy lines, but the bar colors in the plot do not clearly distinguish between
    MLP and Attn components for each method, risking misinterpretation.'
- id: 11a7e0b66f40
  severity: science
  text: 'Figure 11: The caption states that red and green lines indicate shifts from
    Base to RL and Base to OPD, respectively, but the plot legend and markers use
    red triangles for RL and green squares for OPD. The lines in the plot connect
    Base points to RL/OPD points, but the legend does not explicitly define the lines,
    only the markers, creating ambiguity about whether the lines represent the shift
    vectors or just connections.'
- id: c2e5fbb43a0a
  severity: writing
  text: 'Figure 11: The legend uses colored circles for ''Base'' but the plot shows
    colored circles for Base points; however, the red and green lines are not defined
    in the legend, only in the caption, which may confuse readers scanning the figure
    without reading the caption.'
- id: 7ca74597afc8
  severity: science
  text: 'Figure 12: The caption claims to show cosine similarity of $U_1$ (first and
    last steps), but the x-axis labels (''down'', ''gate'', ''up'', ''k'', ''o'',
    ''q'', ''v'') correspond to specific MLP/Attention sub-modules, not the full $U_1$
    matrix. This creates a mismatch between the caption''s claim and the granular
    data shown.'
- id: d5f29789e5a9
  severity: writing
  text: 'Figure 12: The x-axis label ''Component Type'' is generic, but the specific
    components (down, gate, up, k, o, q, v) are not defined in the caption or figure,
    making it unclear which architectural parts are being analyzed.'
artifact_hash: 86f3dbb1aa547b2619e2d0068122fd6e86cb21c5f6980bdd3810b1ffe64d94e9
artifact_path: projects/PROJ-597-https-arxiv-org-abs-2605-11739/paper/metadata.json
backend: dartmouth
feedback: Vision review of 12 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T02:01:29.609533Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

Figure 1 effectively communicates the core concepts of foresight, module allocation, and update direction alignment through clear schematic illustrations and a supporting line plot. The visual metaphors (mountains) and color-coded diagrams are well-labeled and directly support the claims made in the caption regarding OPD's efficiency and the motivation for EffOPD.

### Figure 2

The figure effectively visualizes the performance gap between OPD and other methods, but the caption's use of the generic term 'RL' contradicts the specific method names (PPO, GRPO, DAPO) shown in the legends, and the x-axis scaling factor alpha is not explicitly defined in the caption.

### Figure 3

The figure presents data on update norms and accuracy, but the caption for panel (b) contradicts the legend by referring to 'OPD reasoning accuracy' when the legend clearly labels the lines as 'MLP Accuracy' and 'Attn Accuracy'. Additionally, the bar colors in panel (b) are not explicitly mapped to RL or OPD in the caption.

### Figure 4

The figure presents low-rank subspace analysis, but panel (b) contains a critical discrepancy where the legend labels methods as GRPO/DAPO while the caption claims to compare against RL, undermining the stated scientific claim. Additionally, the x-axis labeling in panel (b) is slightly ambiguous regarding the subspace definition.

### Figure 5

Figure 5 contains significant labeling inconsistencies: panel (a) is misidentified as a t-SNE visualization when it is a trajectory plot, and panel (c) has a confusing dual-axis setup where the accuracy lines appear to follow the KL loss scale rather than the accuracy scale.

### Figure 6

The figure effectively displays performance curves across multiple datasets, but the caption is insufficiently descriptive regarding the plotted symbols, and the top-row x-axis labels are missing.

### Figure 7

Figure 7 presents ablation studies clearly, but the legend in panel (a) inconsistently labels the learning rate variants as 'OPD' instead of 'EffOPD', and the time unit in panel (c) may be ambiguous or incorrect for the scale shown.

### Figure 8

The figure effectively visualizes the scaling analysis of update norms versus accuracy, supporting the claim that OPD is more efficient. However, the caption's use of the generic term 'RL' contradicts the specific algorithm names (PPO, GRPO, DAPO) shown in the legends, and the x-axis label is overly cluttered.

### Figure 9

The figure presents scaling analysis of update norms versus accuracy, but the legends (DAPO/GRPO) contradict the caption's claim of comparing RL and OPD. Additionally, the x-axis definition of 'update norm' lacks clarity regarding whether it is cumulative or instantaneous.

### Figure 10

Figure 10 contains significant mismatches between the caption and the actual content in panel (a), where the x-axis labels contradict the described experiment. Additionally, panel (a) omits the 'Base' condition in two of three groups, and panel (b) has ambiguous color coding for component types.

### Figure 11

Figure 11 effectively visualizes token embedding shifts but has a minor inconsistency between the legend (which defines markers) and the caption (which defines lines), potentially causing confusion about the meaning of the connecting lines.

### Figure 12

The figure presents a clear heatmap of cosine similarities, but the caption's reference to '$U_1$' conflicts with the specific sub-component labels on the x-axis, and the specific components are not defined in the text.
