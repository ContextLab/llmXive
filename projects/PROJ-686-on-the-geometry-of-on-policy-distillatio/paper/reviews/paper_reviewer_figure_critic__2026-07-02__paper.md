---
action_items:
- id: 7fbb560ca6f5
  severity: science
  text: 'Figure 1: The inset line plot in panel (b) shows ''Stable Rank'' on the y-axis,
    but the legend defines the lines as SFT, OPD, and RLVR without specifying the
    x-axis variable (e.g., training steps or epochs), making the ''rapidly enters''
    claim in the caption difficult to verify quantitatively.'
- id: f23bdac44f70
  severity: writing
  text: 'Figure 1: The x-axis label in the inset plot of panel (b) reads ''Training
    Progress (%)'', but the tick marks (20, 40, 60, 80, 100) lack a ''%'' symbol,
    creating a minor inconsistency between the label and the axis values.'
- id: 38b9c815f161
  severity: writing
  text: 'Figure 2: The x-axis label ''Rank index k'' is used in the left two columns,
    but the caption does not define ''k'' (e.g., as rank index, layer index, or training
    iteration), creating ambiguity.'
- id: e65c9a91edb0
  severity: writing
  text: 'Figure 2: The y-axis label ''NSS'' in the rightmost column is undefined in
    the caption; the acronym should be spelled out or explained.'
- id: 4ffb5c92f440
  severity: writing
  text: 'Figure 2: The ''Max Principal Angle (all-layer)'' plots use ''Weight matrix
    index'' on the x-axis, but the caption does not clarify what this index represents
    (e.g., layer number, parameter block).'
- id: cc3e0c7c4f7d
  severity: science
  text: 'Figure 3: The ''Global'' row contains three line plots with different y-axis
    scales (0-100, 0-50, 0-100) but no explicit axis labels or units are provided
    on the plots themselves, making it impossible to verify the ''Global'' metric
    values against the heatmap percentages without guessing.'
- id: 07abbda81837
  severity: writing
  text: 'Figure 3: The ''Global'' row plots lack y-axis labels; while the caption
    mentions ''update-mask localization'', the specific metric being plotted (e.g.,
    ''Overlap %'', ''Density'') is not explicitly labeled on the axes, relying on
    the reader to infer from the heatmaps above.'
- id: 53c05fad27c4
  severity: science
  text: 'Figure 3: The ''Global'' row plots show single points with error bars (or
    shaded regions) but do not specify what the error bars represent (e.g., std dev,
    confidence interval) in the caption or on the plot, which is critical for interpreting
    the ''robustness'' claim.'
- id: d3631ccc0d12
  severity: writing
  text: 'Figure 4: The x-axis label ''Training progress (%)'' is ambiguous; the caption
    refers to tracking cumulative updates $W_t$ over time, but it is unclear if the
    x-axis represents training steps, epochs, or percentage of total budget.'
- id: d5db9596b319
  severity: writing
  text: 'Figure 4: Panel (a) contains a text annotation ''OPD band'' pointing to the
    blue line, but this specific term is not defined in the caption or legend, making
    the annotation''s purpose unclear.'
- id: d6fc226439a2
  severity: writing
  text: 'Figure 5: The provided caption is a raw LaTeX comment block (starting with
    %) rather than a rendered description, making it difficult to read and unprofessional.'
- id: 3e997ced59c5
  severity: writing
  text: 'Figure 5: The y-axis label ''Sim_16(t, t_final)'' uses subscript notation
    that is not explicitly defined in the caption, which only vaguely mentions ''Top-16
    subspace similarity''.'
- id: bda08fbcdbbd
  severity: science
  text: 'Figure 6: The caption claims ''Rank-16 projection leaves OPD intact but degrades
    SFT'', but the plot shows ''plain'' (OPD) performance dropping significantly after
    the projection start (dashed line), while ''K16'' (SFT) performance improves.
    The visual data directly contradicts the caption''s claim.'
- id: 8236dbeab3cc
  severity: writing
  text: 'Figure 6: The legend labels ''plain'' and ''K16'' are not defined in the
    caption, making it impossible to identify which method corresponds to OPD or SFT
    without external context.'
- id: 06e6afcfc6b9
  severity: science
  text: 'Figure 7: The caption claims OPD ''locks onto its final update channel earlier''
    than SFT and RLVR, but the plot shows OPD starting with higher similarity and
    rising monotonically without a distinct ''lock'' or plateau phase that would demonstrate
    early locking compared to the other methods.'
- id: 67a0444b2b47
  severity: writing
  text: "Figure 7: The y-axis label 'Sim(\u03B8, \u03B8_final)' is ambiguous; the\
    \ caption specifies 'Top-16 subspace similarity', but the axis label does not\
    \ explicitly state this metric, potentially confusing readers about whether it\
    \ is parameter similarity or subspace similarity."
- id: f2cc0a74c99b
  severity: science
  text: 'Figure 8: The caption claims ''Rank-16 projection leaves OPD intact but degrades
    SFT,'' but the plot shows the ''plain'' (OPD) line dropping significantly at 100%
    training, while the ''K16'' (projection) line remains stable. The visual data
    contradicts the claim that OPD is ''intact'' at the end of training.'
- id: c5946e573464
  severity: writing
  text: 'Figure 8: The legend in panel (a) defines ''plain'', ''K16'', and ''shared
    resume'', but panel (b) lacks a legend, forcing the reader to assume the same
    mapping applies without explicit confirmation.'
- id: 4622277e397c
  severity: science
  text: 'Figure 9: The caption claims the figure shows ''Runtime perturbations'' and
    ''objective-level interpolation'', but the legend labels these as ''Top-KL'',
    ''Random'', and ''Objective mixing'' (alpha values). The connection between the
    legend terms and the caption''s conceptual categories is not explicit, making
    it difficult to verify the claim that ''Runtime perturbations'' (likely Top-KL/Random)
    preserve the trajectory without external inference.'
- id: 63fb90753b6f
  severity: writing
  text: "Figure 9: The legend in panel (c) uses the symbol 'a' for the parameter alpha\
    \ (e.g., 'a=0.25'), which is non-standard and potentially confusing compared to\
    \ the Greek letter $\alpha$ used in the caption text."
- id: 22257b941ebd
  severity: science
  text: 'Figure 10: The legend defines ''K16'' (orange squares) and ''plain'' (blue
    circles), but the caption claims to compare ''unconstrained training'' and ''rank-16
    projected training''. The legend fails to explicitly label the orange line as
    the ''rank-16 projected'' condition, creating ambiguity between the legend text
    and the caption''s description.'
- id: 402127c2188d
  severity: writing
  text: 'Figure 10: The y-axis labels use abbreviated metrics (e.g., ''avg@32 (%)'',
    ''avg@4 (%)'') without defining what ''avg'' refers to (e.g., average accuracy,
    average score) in the caption or axis text.'
- id: 0619ca0cb453
  severity: writing
  text: 'Figure 11 caption contains a broken cross-reference: ''analyzed in Figure
    .'' is missing the figure number.'
- id: 5fc0484a14f3
  severity: science
  text: 'Figure 11: The legend in the bottom-left panel defines ''a=0.75'' through
    ''a=0.01'' and ''a=0.01'' (red dashed), but the caption does not define what ''a''
    represents (e.g., interpolation coefficient), making the ''objective interpolation''
    claim ambiguous.'
artifact_hash: 131dbc2ce86fd7fa8c00d7dd55a7501ac648ec7bf3f89711e549ef82e5ed9b1b
artifact_path: projects/PROJ-686-on-the-geometry-of-on-policy-distillatio/paper/metadata.json
backend: dartmouth
feedback: Vision review of 11 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T21:34:48.857036Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

Figure 1 effectively communicates the conceptual geometry of OPD through clear visual metaphors and a consistent color scheme. However, the quantitative inset in panel (b) lacks a clear x-axis definition in the legend, and the axis label formatting is slightly inconsistent.

### Figure 2

Figure 2 presents clear comparative plots of spectral geometry across methods, but key axis labels ('k', 'NSS', 'Weight matrix index') lack definitions in the caption, reducing interpretability for readers unfamiliar with the notation.

### Figure 3

Figure 3 effectively visualizes update-mask localization with clear heatmaps and a colorbar, but the 'Global' row plots lack explicit y-axis labels and error bar definitions, hindering full interpretation of the quantitative claims.

### Figure 4

The figure effectively visualizes the three metrics described in the caption, but the x-axis label is ambiguous regarding the training unit, and the 'OPD band' annotation in panel (a) lacks a definition in the text.

### Figure 5

The figure is visually clear and effectively demonstrates the claim that OPD locks onto its final update channel earlier than SFT and RLVR. However, the caption is unrendered LaTeX code, and the y-axis notation lacks a precise definition in the text.

### Figure 6

The figure's visual data contradicts the caption's claim that OPD remains intact while SFT degrades under rank-16 projection. Additionally, the legend labels 'plain' and 'K16' are undefined in the caption, obscuring method identification.

### Figure 7

The figure displays subspace similarity trends but fails to visually demonstrate the 'locking' behavior described in the caption, and the y-axis label lacks the specificity found in the caption text.

### Figure 8

The figure contains a contradiction between the caption's claim that OPD is 'intact' and the visual data showing a performance drop for the 'plain' method at 100% training. Additionally, panel (b) lacks a legend to define its series.

### Figure 9

The figure effectively visualizes the stability of the OPD trajectory under different conditions, but the mapping between the legend labels (Top-KL, Random) and the caption's categories (Runtime perturbations) is implicit rather than explicit, and the use of 'a' instead of $lpha$ in the legend is a minor notation inconsistency.

### Figure 10

The figure effectively visualizes the performance of OPD versus SFT under rank constraints across benchmarks, but the legend labels ('plain', 'K16') do not explicitly match the caption's terminology ('unconstrained', 'rank-16 projected'), and the y-axis metric definitions are abbreviated.

### Figure 11

The figure displays the intended metrics clearly, but the caption contains a broken cross-reference to a missing figure number, and the variable 'a' used in the legend is not defined in the text.
