---
action_items:
- id: 4c714b3f0830
  severity: fatal
  text: 'Figure 1 caption is incomplete: ''(a) Comparison between GRPO+OPSD and ;''
    omits the second method name, though the legend shows ''SDAR (Ours)''.'
- id: c51e7ffd190c
  severity: science
  text: Figure 1 caption part (b) 'Overall Performance' is too vague; the plot shows
    'Success Rate' over 'Step' for two methods, not a comprehensive overall performance
    summary.
- id: aad1724379b3
  severity: writing
  text: 'Figure 2: The middle and right panels lack a legend or explicit label identifying
    the blue bars as ''Average teacher-student gap'', relying solely on the caption
    for definition.'
- id: e96dcc23ea28
  severity: science
  text: 'Figure 2: The middle panel''s x-axis (''Turn Step Interval'') has non-uniform
    tick spacing (1, 11, 21...) that does not align with the visual density of the
    bars, potentially misleading the reader about the data distribution.'
- id: ca9e9e7d642a
  severity: writing
  text: 'Figure 3: The caption contains a grammatical error (''Illustrations of framework''
    should be ''Illustration of the framework'') and a dangling comparison in the
    full caption list (''Comparison between GRPO+OPSD and ;'') which suggests missing
    text.'
- id: 627e969d9e4d
  severity: science
  text: 'Figure 3: The ''Self-Teacher'' and ''Self-Student'' icons are identical,
    which may confuse the reader regarding the distinct roles of the teacher and student
    models in the distillation process.'
- id: 169ee40102ed
  severity: writing
  text: 'Figure 4: The left plot''s y-axis label ''Teacher Gap Mean'' is ambiguous;
    the caption specifies ''Average teacher-student gap'', but the negative values
    (ranging from -0.12 to -0.02) are not explained (e.g., is this a difference metric
    where negative implies the student is ahead?).'
- id: e848868cb2ab
  severity: writing
  text: 'Figure 4: The plots lack a legend or explicit line style definitions to distinguish
    the ''Average'' trend line (darker) from the variance/noise band (lighter), relying
    on visual convention rather than explicit labeling.'
- id: 2d56b374bb25
  severity: fatal
  text: 'Figure 5: The rendered image is a line chart of ''Success Rate'' vs ''Step''
    with three metrics (Entropy, SOFT-OR Score, Teacher-Student Gap), but the caption
    describes it as ''Ablations of Token-level Gating''. The content does not match
    the caption, and the figure lacks the necessary ablation curves (e.g., gating
    on/off) to support the title.'
- id: 7c03cc5fa981
  severity: fatal
  text: 'Figure 6: The caption reads ''Ablations of $$'' which is a rendering error
    or placeholder; it fails to define the parameter $\lambda$ shown in the legend.'
- id: 9ca6bc51e2f6
  severity: science
  text: 'Figure 6: The plot lacks error bars or shaded regions for the success rate
    curves, making it impossible to assess the statistical significance of the differences
    between the $\lambda$ values.'
- id: 4dd62389e7e5
  severity: writing
  text: 'Figure 7: The y-axis label ''ALFWorld'', ''WebShop'', and ''Search'' is placed
    only on the far left of the grid, making it ambiguous whether these labels apply
    to the entire row or just the first subplot; explicit row labels or a shared y-axis
    label is needed.'
- id: 3221c2f08b6c
  severity: writing
  text: 'Figure 7: The x-axis label ''Step'' is repeated on the bottom row but missing
    from the top two rows, creating visual inconsistency across the grid.'
- id: 9891564c3ddb
  severity: writing
  text: "Figure 7: The y-axis scales differ significantly between rows (e.g., 0.30\u2013\
    0.50 for ALFWorld vs. 0.175\u20130.375 for Search), but this is not explicitly\
    \ noted in the caption, potentially misleading readers about relative magnitudes."
- id: bb7298e9dea5
  severity: writing
  text: 'Figure 8: The y-axis labels are illegible due to overlapping text and insufficient
    spacing, making it impossible to read the specific numerical values.'
- id: 998240c6345f
  severity: writing
  text: 'Figure 8: The x-axis label ''Step'' is only present on the bottom row; the
    top two rows lack x-axis labels, which is inconsistent with standard multi-panel
    figure formatting.'
- id: ff7b22e337f0
  severity: science
  text: "Figure 9: The y-axis labels (0.010\u20130.070) are inconsistent with the\
    \ caption's claim of 'OPSD Loss'; these values are too low for standard loss curves\
    \ and likely represent a metric like 'Gate Mean' (matching Figure 8) or 'Reward'\
    \ (matching Figure 11). The caption appears to be mislabeled or the plot data\
    \ is incorrect."
- id: a385b0716a6d
  severity: writing
  text: 'Figure 9: The y-axis labels are missing for the middle and top rows of plots;
    only the bottom row (Search) has visible y-axis ticks and values, making it difficult
    to compare magnitudes across the grid.'
- id: 7f0265419caa
  severity: science
  text: 'Figure 10: The y-axis values are negative (ranging from -0.5 to -0.02), but
    the caption describes the metric as ''Teacher-Student Gap''. A ''gap'' is typically
    a non-negative difference; negative values suggest the metric is actually a raw
    score or log-probability difference, not a gap. This contradicts the caption''s
    description.'
- id: dbbff19b03af
  severity: writing
  text: 'Figure 10: The y-axis labels are present but lack units or a clear definition
    of what the negative values represent (e.g., log-probability difference, score
    difference). The caption does not clarify this, making the metric ambiguous.'
- id: fbf1a09c47c7
  severity: writing
  text: 'Figure 10: The x-axis is labeled ''Step'' but does not specify the unit (e.g.,
    training steps, epochs). This is critical for interpreting the training dynamics
    shown.'
- id: b7ed480678c7
  severity: science
  text: 'Figure 11: The caption claims to show training on ''Search-QA'', but the
    y-axis label for the bottom row is ''Search''. This discrepancy creates ambiguity
    about whether the dataset is Search-QA or a different task named ''Search''.'
- id: d1650cca194c
  severity: writing
  text: 'Figure 11: The y-axis label ''Search'' in the bottom row is likely an abbreviation
    for the dataset ''Search-QA'' mentioned in the caption; it should be updated to
    ''Search-QA'' for consistency and clarity.'
artifact_hash: a2fe5096ad1b93f50db064c40f59b84672b255d5a406d9c082d97d449a5f037d
artifact_path: projects/PROJ-579-https-arxiv-org-abs-2605-15155/paper/metadata.json
backend: dartmouth
feedback: Vision review of 11 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:56:45.680638Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

Figure 1 contains critical caption errors: part (a) is grammatically incomplete and part (b) is overly vague relative to the specific data shown. The visual plots themselves are clear but the caption fails to accurately describe them.

### Figure 2

The figure effectively visualizes the teacher-student gap distribution and trends, but the middle and right panels lack explicit internal labels for the bars, and the x-axis in the middle panel has irregular tick spacing that may confuse the reader.

### Figure 3

The figure effectively visualizes the framework's architecture and data flow, but the caption contains grammatical errors and the identical icons for the teacher and student models could be clarified to better distinguish their roles.

### Figure 4

Figure 4 effectively visualizes the training dynamics with clear axes and trends, but the negative values on the y-axis of the left plot are not explicitly explained in the caption, and the distinction between the mean line and the variance band lacks a formal legend.

### Figure 5

The figure content (a performance comparison of three metrics) completely contradicts the provided caption (an ablation study of token-level gating), rendering the figure unusable for its intended purpose.

### Figure 6

The figure displays success rate curves for different lambda values but suffers from a broken caption that fails to define the ablated parameter, and it lacks error bars to support claims of performance differences.

### Figure 7

Figure 7 presents gate active ratio trends across models and tasks but suffers from inconsistent axis labeling and unexplained scale variations that reduce clarity and comparability.

### Figure 8

The figure displays training dynamics across models and tasks, but the y-axis numerical labels are illegible due to overlapping text, and x-axis labels are missing from the top two rows.

### Figure 9

The figure displays training curves for three models across three tasks, but the y-axis labels are missing for the top two rows, and the values shown (0.01–0.07) contradict the caption's claim of 'OPSD Loss', suggesting a potential mislabeling of the metric or the figure itself.

### Figure 10

Figure 10 displays training dynamics with negative y-axis values that contradict the 'Teacher-Student Gap' description in the caption. Additionally, the y-axis lacks units/definition and the x-axis does not specify the step unit, reducing clarity.

### Figure 11

The figure displays reward curves for three models across three tasks, but the bottom row's y-axis label 'Search' conflicts with the caption's 'Search-QA', creating ambiguity about the dataset identity.
