---
action_items:
- id: 1ed0de6d8852
  severity: fatal
  text: 'Figure 1: The caption is explicitly ''(no caption)'', providing no context
    for the plot''s axes, data series, or scientific claim.'
- id: 3dd295d29df4
  severity: science
  text: 'Figure 1: The Y-axis is labeled ''Cosine Similarity'' but the values for
    the ''RCORE'' series drop to -0.79, which is inconsistent with standard cosine
    similarity ranges ([-1, 1]) unless specific normalization is applied, yet no explanation
    is provided.'
- id: e89f49cbf66e
  severity: writing
  text: 'Figure 1: The legend labels ''C2C (Baseline)'' and ''RCORE (Ours)'' are undefined;
    the caption does not explain what these acronyms stand for or the experimental
    setup.'
- id: 42c06d811749
  severity: writing
  text: 'Figure 2: The figure has no caption text (only the filename), making it impossible
    to understand the context, dataset, or specific metrics being plotted.'
- id: f9172ac9dedf
  severity: writing
  text: 'Figure 2: The legend is placed inside the plot area, obscuring the data points
    and trend lines for the ''False Co-occurrence Prediction'' and ''Unseen Accuracy''
    series.'
- id: fa8453117cff
  severity: science
  text: 'Figure 2: The left y-axis (Accuracy) and right y-axis (False Prediction Ratio)
    share the same numerical scale range (0-50 vs 30-70 roughly), but the visual alignment
    of the ticks is ambiguous, potentially misleading the reader about the relative
    magnitude of the ''False Seen Prediction'' vs ''Seen Accuracy''.'
- id: 166adfcc8b4f
  severity: writing
  text: 'Figure 3: The figure lacks a descriptive caption; it is labeled ''(no caption)''
    and only provides a filename, making the specific context of the ''diagnosis''
    unclear.'
- id: cf131e2a3593
  severity: writing
  text: 'Figure 3: The legend entry ''False Co-occurrence Prediction'' is not explicitly
    defined in the caption, leaving the distinction between ''False Seen'' and ''False
    Co-occurrence'' ambiguous to the reader.'
- id: 8cd197d1be41
  severity: writing
  text: 'Figure 4: The provided caption is empty (''no caption''), making it impossible
    to verify if the legends, symbols, or data series (e.g., ''Verb @ Seen Comp.'',
    ''Random Accuracy'') match the authors'' intended description.'
- id: e1a16cb9dfbf
  severity: writing
  text: 'Figure 4: The heatmap legends (e.g., ''Present/Absent'', ''Seen/Unseen'')
    are placed directly above the plots without clear visual separation or titles,
    which may confuse readers regarding which legend applies to which specific grid.'
- id: bfa4066a24f5
  severity: writing
  text: 'Figure 5: The caption is missing; the provided text ''(no caption)'' prevents
    verification of the figure''s content, context, or the meaning of the visual elements.'
- id: a9d10624d1fd
  severity: science
  text: 'Figure 5: The image displays a video frame sequence with a time axis and
    a text label ''(Take, Cup)'', but without a caption, it is unclear what specific
    scientific claim or data this visual evidence supports.'
- id: b0532b966657
  severity: writing
  text: 'Figure 6: The x-axis labels are rotated but still overlap significantly,
    making the text difficult to read; consider increasing spacing or reducing the
    number of labels.'
- id: affd2d9be060
  severity: writing
  text: 'Figure 6: The caption is empty (''no caption''), providing no context for
    the data shown or its relevance to the paper''s claims.'
- id: 1206122f6c32
  severity: writing
  text: 'Figure 7: The caption is missing; the provided text ''(no caption)'' does
    not describe the plot''s content, methods, or significance.'
- id: ed3fb83db005
  severity: writing
  text: 'Figure 7: The legend uses undefined acronyms (''C2C'', ''RCORE'', ''FSP'',
    ''FCP'') without explanation in the caption or figure text.'
- id: 14a8361b7d34
  severity: writing
  text: 'Figure 8: The caption is empty (''no caption''), providing no explanation
    for the complex architecture diagrams, variable definitions (e.g., $L_{TORC}$,
    $L_{CPR}$), or the relationship between the three panels.'
- id: 57c7d021898b
  severity: writing
  text: 'Figure 8: The text ''1 - lambda'' in panel (b) is rendered in a standard
    serif font, while the surrounding mathematical notation uses a sans-serif font,
    creating visual inconsistency.'
- id: 6b4798bf8195
  severity: writing
  text: 'Figure 9: The figure lacks a descriptive caption; the provided metadata ''(no
    caption)'' fails to explain the ''Training Data'', ''Closed-world Evaluation'',
    and ''Open-world Evaluation'' panels or the specific meaning of the hatched, solid,
    and ''X'' marked cells.'
- id: 47bbb1988db8
  severity: writing
  text: 'Figure 9: The legend for the ''Training Data'' panel is incomplete, showing
    only ''Train Pairs'' while omitting definitions for the empty white cells which
    represent unobserved pairs.'
- id: 9967f4ff7333
  severity: writing
  text: 'Figure 11: The caption is missing; the figure contains two complex heatmaps
    defining ''Training Set'' vs ''Test Set'' splits but lacks any text description
    to explain the experimental setup or the significance of the ''Present/Absent''
    and ''Seen/Unseen'' labels.'
- id: 8ff8a4d31afe
  severity: science
  text: 'Figure 11: The ''Test Set'' heatmap uses a ''Seen'' (orange) vs ''Unseen''
    (blue) legend, but the diagonal cells are colored ''Seen'' while the off-diagonals
    are ''Unseen''. This implies a specific compositional split (e.g., seen actions
    on seen objects), but without a caption, the exact definition of the ''Unseen''
    condition (e.g., unseen action-object pairs vs. unseen objects) is ambiguous.'
artifact_hash: f098ae707662ea7ce696ff8b8606006fdddb80c25be82361ec114d13c9a397ed
artifact_path: projects/PROJ-1037-why-can-t-i-open-my-drawer-mitigating-ob/paper/metadata.json
backend: dartmouth
feedback: Vision review of 12 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-11T04:21:12.145487Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

The figure is visually clear but scientifically opaque due to a completely missing caption and undefined acronyms in the legend, making it impossible to interpret the data's significance.

### Figure 2

The figure is visually cluttered due to an internal legend and lacks a descriptive caption, which hinders understanding of the plotted metrics and their significance.

### Figure 3

The figure is visually clear with well-labeled axes and data points, but it lacks a descriptive caption to explain the specific experimental setup or the distinction between the two 'False' prediction metrics.

### Figure 4

The figure contains clear visualizations of learning curves and heatmaps, but the complete absence of a descriptive caption prevents verification of the data and legends shown.

### Figure 5

The figure consists of a visual sequence labeled with an action, but the complete absence of a caption makes it impossible to assess its scientific relevance or verify its content against the paper's claims.

### Figure 6

The bar chart clearly displays the top 30 frequent compositions, but the x-axis labels are crowded and the figure lacks a descriptive caption to explain its significance.

### Figure 7

The figure is visually clear with labeled axes and data points, but it lacks a descriptive caption and relies on undefined acronyms in the legend, hindering standalone interpretation.

### Figure 8

Figure 8 provides a clear visual overview of the model architecture and regularization methods, but the complete absence of a caption makes the specific variables, loss functions, and panel relationships difficult to interpret for the reader.

### Figure 9

Figure 9 effectively visualizes the experimental setup using a grid format, but it is critically hindered by the absence of a descriptive caption and an incomplete legend for the first panel, leaving the specific meaning of the empty cells undefined.

### Figure 10

Figure 10 is a clear and well-structured flowchart that effectively illustrates the evaluation logic for distinguishing between seen and unseen compositions. The visual hierarchy, decision nodes, and resulting metrics are unambiguous and self-explanatory without requiring a detailed caption.

### Figure 11

Figure 11 presents two heatmaps illustrating a dataset split for training and testing, but the complete absence of a caption makes the specific definitions of the 'Seen' and 'Unseen' categories and the experimental goal impossible to verify.

### Figure 12

Figure 12 is a clear, well-structured schematic that effectively communicates the paper's core problem: object-driven shortcuts in zero-shot action recognition. The three panels logically progress from data priors to learning difficulty to the specific failure mode in testing, with all visual elements (icons, arrows, text) being legible and self-explanatory.
