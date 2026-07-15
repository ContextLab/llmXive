---
action_items:
- id: 5604827e86a4
  severity: science
  text: 'Figure 1: The caption claims to show two panels (''Left: R1-Distill...''
    and ''Right: Nemotron...''), but the rendered image displays only a single plot
    titled ''JustRL overlap dynamics'' containing both transfer pairs. The figure
    fails to visually separate the two distinct teacher-student pairs as described.'
- id: 64fe9acbf35d
  severity: writing
  text: 'Figure 1: The legend labels ''JustRL -> R1-7B'' and ''JustRL -> Qwen3-1.7B''
    do not match the caption''s description of the ''Left'' pair (''R1-Distill-1.5B
    -> JustRL-1.5B''). The axis label ''Student top-k overlap ratio'' is also inconsistent
    with the caption''s ''Teacher--student top-k overlap''.'
- id: 6a38e5219da0
  severity: science
  text: 'Figure 2: The top-left subplot is titled ''Qwen3-1.7B'' but the caption identifies
    the first column as ''student entropy''. Since the student is Qwen3-1.7B, the
    title is redundant and potentially confusing; it should explicitly label the metric
    (e.g., ''Student Entropy'') to match the caption''s description of the columns.'
- id: 7aa4cfb19d11
  severity: writing
  text: 'Figure 2: The y-axis tick labels on the top row (0.225, 0.300, 0.375, 0.450)
    are rendered in a font size that is significantly smaller and less legible than
    the x-axis labels or subplot titles, reducing readability.'
- id: 1ca60f9734a7
  severity: writing
  text: 'Figure 3: The y-axis label ''AIME 2024/2025'' is illegible due to vertical
    rotation and small font size, making it difficult to read the metric name.'
- id: '532496392899'
  severity: writing
  text: 'Figure 3: The y-axis label ''avg. accuracy (ave@32)'' is rotated 90 degrees
    and compressed, reducing readability.'
- id: f7c29b31cf42
  severity: fatal
  text: 'Figure 4: The provided caption is truncated mid-sentence (''...actors tra''),
    failing to describe the middle and right panels shown in the image.'
- id: 770e7f5716c0
  severity: science
  text: 'Figure 4: The legend defines ''6k fixed KL1'' (pink), but the middle panel''s
    pink curve remains flat at 0 while the caption implies all actors should show
    drift; the legend does not explain this baseline behavior.'
- id: bc0925b53005
  severity: writing
  text: 'Figure 4: The mathematical definition of the cumulative gap $G_T$ in the
    caption contains a typo (''=_t T g_t'') and is missing the summation symbol and
    index range.'
- id: ac9484145b92
  severity: science
  text: 'Figure 5: The top row y-axis label ''AIME 2024/2025'' contradicts the caption''s
    claim that the plot shows ''AIME 2024/2025 validation accuracy (ave@32)''; the
    axis label implies a single metric combining both years, while the caption suggests
    the plot represents the average of the two. This ambiguity makes it unclear if
    the data is an aggregate or a specific year.'
- id: 9d2145c3971a
  severity: writing
  text: 'Figure 5: The legend in the top row is split across three separate panels
    with inconsistent entries (e.g., ''KL 0.8'' only in the right panel), which is
    redundant and cluttered. A single unified legend or consistent labeling across
    all subplots would improve readability.'
- id: 1dda9cdc1e30
  severity: writing
  text: 'Figure 6: The caption contains a broken cross-reference (''Together with
    Figure , this shows...'') where the figure number is missing.'
- id: c6c8dd06a2cf
  severity: science
  text: 'Figure 6: The plot titles (''Qwen3-1.7B'', ''QuestA teacher'', ''QuestA teacher
    ref'', ''QuestA delta'') do not explicitly label the y-axis units (entropy bits)
    or confirm the metric is entropy, relying entirely on the caption for context.'
- id: 782a146842d4
  severity: science
  text: 'Figure 7: The legend defines ''QuestA -> R1-7B'' and ''QuestA -> Qwen3-1.7B'',
    but the plot titles are ''R1-Distill-7B'' and ''Qwen3-1.7B''. The legend label
    ''R1-7B'' is an inconsistent abbreviation that does not match the full model name
    in the title.'
- id: 5f3e8a65745d
  severity: science
  text: 'Figure 7: The legend entry ''Initial'' corresponds to a dashed line, but
    the legend does not specify the numerical value of this baseline, forcing the
    reader to estimate it from the y-axis.'
- id: c67ebe6bdb39
  severity: writing
  text: 'Figure 8: The caption contains multiple grammatical fragments and missing
    terms (e.g., ''transfers RL-induced...'', ''showing that is not specific...''),
    making the text difficult to read.'
- id: 7d46f3386387
  severity: science
  text: 'Figure 8: The legend defines ''Initial Student'' as a dashed line, but the
    plots contain multiple horizontal lines (dashed, dotted, and solid) representing
    baselines (e.g., ''JustRL 0.512''), creating ambiguity about which line corresponds
    to the legend entry.'
- id: 5cf85f59ead4
  severity: writing
  text: 'Figure 8: The y-axis label ''AIME 2024 Accuracy (ave@32)'' is repeated for
    the top row, but the bottom row y-axis label is ''AIME 2025 Accuracy (ave@32)'';
    however, the caption text ''evaluated on AIME 2024 and AIME 2025'' is vague about
    which specific subplot corresponds to which year without explicit row headers.'
- id: f6a4aa6155ba
  severity: science
  text: 'Figure 9: The legend defines ''T1500'' (orange line) but the caption text
    is truncated (''...short transf''), failing to define what T1500 represents or
    how it relates to the ''T$N$'' notation described.'
- id: 5051f8319394
  severity: science
  text: 'Figure 9: The rightmost subplot (''Qwen3 nonthinking: AIME 2025'') contains
    a dashed blue line labeled ''0.635'' but lacks a corresponding legend entry or
    caption definition explaining what this baseline represents.'
- id: 9dc7e13d78ca
  severity: writing
  text: 'Figure 9: The caption text is truncated at the end (''...short transf''),
    cutting off the description of the wall-clock time calculation for the transfer
    points.'
- id: 688d124ea921
  severity: science
  text: "Figure 10: The caption states the figure contains 'Left: trajectories...\
    \ Right: endpoint scores', but the rendered image displays only a single plot\
    \ of trajectories (steps 0\u2013600) and lacks the promised 'Right' panel showing\
    \ endpoint scores."
- id: 56bc7b642ee9
  severity: writing
  text: 'Figure 10: The title ''Qwen3-1.7B: JustRL then QuestA policy-shift transfer''
    and the vertical dashed line at step 300 labeled ''Switch to QuestA'' are not
    explicitly defined in the figure''s own caption, which only describes the signals
    generally.'
- id: e69fb9627689
  severity: science
  text: 'Figure 11(a): The caption claims the blue curve ''transfers the JustRL-1.5B
    - R1-Distill-1.5B policy shift,'' but the legend labels it ''Direct-OPD.'' This
    contradicts the paper''s distinction between ''vanilla OPD'' (red) and the proposed
    method, creating ambiguity about whether the blue curve represents the proposed
    method or a different baseline.'
- id: 0c98c71990a8
  severity: writing
  text: 'Figure 11(a): The y-axis label ''AIME 24 ave@32'' is truncated and difficult
    to read due to tight spacing; expand the label or increase font size for clarity.'
- id: 9188128b934e
  severity: writing
  text: 'Figure 11(b): The bar chart lacks explicit y-axis tick labels (only gridlines
    are visible), making it hard to verify the exact values of the bars and the ''Teacher''
    reference line.'
artifact_hash: fe03c20c23e17e66c41241fcf88a5ad32b5f8c89483ca27ec649ff3d3b355988
artifact_path: projects/PROJ-1059-weak-to-strong-generalization-via-direct/paper/metadata.json
backend: dartmouth
feedback: Vision review of 11 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-15T02:41:35.570580Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

The figure fails to match its caption, which describes two separate panels for different teacher pairs, whereas the image shows a single combined plot. Additionally, the legend labels and axis text contradict the specific model pairs and metrics defined in the caption.

### Figure 2

The figure effectively visualizes the entropy diagnostics described in the caption, showing the expected trends of non-collapsing actor entropy and narrowing teacher/reference gaps. However, the top-left subplot title is redundant rather than descriptive, and the y-axis tick labels on the top row are rendered too small for comfortable reading.

### Figure 3

The figure effectively displays the response-length sweep results with clear legends and gridlines, but the y-axis labels are rotated and rendered in a font size that is difficult to read.

### Figure 4

The figure is visually clear with a legend, but the provided caption is truncated and contains a typo in the mathematical definition. Additionally, the legend includes a '6k' condition that appears to behave as a static baseline in the middle panel without explanation.

### Figure 5

The figure effectively demonstrates the impact of KL coefficients and adaptive KL on validation accuracy and token reward. However, the top row y-axis label is ambiguous regarding the 'AIME 2024/2025' metric, and the split legends across subplots are redundant.

### Figure 6

The figure presents four entropy diagnostic plots with clear titles and axes, but the caption contains a broken cross-reference to a missing figure number, and the plot titles lack explicit unit labels.

### Figure 7

The figure presents transfer curves for the QuestA setting on AIME 2025, but the legend uses inconsistent abbreviations ('R1-7B' vs 'R1-Distill-7B') and fails to explicitly state the numerical value of the 'Initial' baseline.

### Figure 8

The figure effectively displays transfer learning results across different models, but the caption contains significant grammatical errors and missing words. Additionally, the legend definition for 'Initial Student' is ambiguous given the presence of multiple baseline lines in the plots.

### Figure 9

Figure 9 presents a compelling comparison of training efficiency, but the caption is truncated and the legend for the rightmost subplot is incomplete, leaving the meaning of the '0.635' baseline undefined.

### Figure 10

The figure is partially rendered, missing the 'Right' panel of endpoint scores described in the caption. Additionally, specific labels like the 'Switch to QuestA' annotation and the figure title are not defined in the caption text.

### Figure 11

Figure 11 effectively illustrates the performance gains of the proposed method over vanilla OPD, but the legend in panel (a) mislabels the proposed method as 'Direct-OPD' (contradicting the caption), and panel (b) lacks clear y-axis tick labels for precise value reading.
