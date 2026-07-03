---
action_items:
- id: b08410a91f18
  severity: writing
  text: 'Figure 1: The caption contains multiple grammatical errors and missing nouns,
    reading ''Overview of .'' and ''The resulting can take...'', which obscures the
    subject (Humanoid-GPT).'
- id: 7a18cd062597
  severity: writing
  text: 'Figure 1: The caption describes ''keypoint-level rewards'' for stage (b),
    but the diagram only labels the loop as ''RL'' without specifying the reward type.'
- id: 2e90ee5ddd22
  severity: science
  text: 'Figure 2: The top x-axis is labeled ''Geometric-std'' but the caption defines
    the horizontal axis as ''gstd''; the label should be updated to match the caption''s
    terminology.'
- id: e25c52ea0a7b
  severity: writing
  text: 'Figure 2: The text ''Our Training data'' is placed below the large brown
    bubble rather than inside it or connected by a leader line, which creates ambiguity
    about whether the label refers to the bubble or the empty space below.'
- id: e40eaecf0a87
  severity: writing
  text: 'Figure 3: The caption contains a grammatical error and missing noun (''Overview
    of .'', ''Real-world experiments for our .''), likely due to a missing model name
    placeholder.'
- id: 110ebc5336a0
  severity: writing
  text: 'Figure 3: The text labels for specific tasks (e.g., ''Sit on sofa'', ''Play
    with cat'') are rendered in a low-contrast light blue font that is difficult to
    read against the background.'
- id: b20ca2c5cf07
  severity: science
  text: 'Figure 4: The claim ''5 times faster'' is unsupported by the data shown;
    the fastest method (C++ COMM, 0.39 ms) is only ~8.5x faster than TWIST (3.32 ms),
    while the labeled ''final optimization'' (TensorRT & Cache, 0.58 ms) is only ~5.7x
    faster. The comparison baseline (TWIST) is separated by a dashed line and not
    grouped with the optimization methods, making the direct comparison ambiguous.'
- id: 663487133a85
  severity: writing
  text: 'Figure 4: The y-axis labels are cluttered and inconsistent; ''C++ COMM''
    and ''TWIST CPU ONNX'' are split across two lines while others are not, and the
    dashed line separating TWIST is not explained in the caption.'
- id: 8d5ebd5b5929
  severity: science
  text: 'Figure 6: The y-axis label ''Zero-Shot MPJPE'' is present, but the caption
    ''Data Scaling up Curve on Zero-shot Performance'' is vague; it should explicitly
    state that lower MPJPE indicates better performance to ensure the downward trend
    is interpreted correctly.'
- id: f99e222e8f5e
  severity: writing
  text: 'Figure 6: The y-axis has a break symbol (zigzag) but no numerical scale or
    tick marks are provided, making it impossible to verify the magnitude of the improvement
    or the spacing between data points.'
- id: e8438c924cc2
  severity: science
  text: 'Figure 7: The plot displays ''Training Loss'' on the y-axis, but the caption
    describes it as a ''Model Scalability Comparison''. Scalability comparisons typically
    show performance metrics (e.g., accuracy, success rate) or efficiency metrics
    (e.g., FLOPs, latency) against model size or parameter count, not training loss
    curves.'
- id: 6af1a6a46b58
  severity: science
  text: 'Figure 7: The x-axis is labeled ''Training Steps'' (50K to 200K), which measures
    training duration rather than model scale (e.g., number of parameters). This contradicts
    the caption''s claim of a ''Model Scalability Comparison''.'
- id: fef70a33b232
  severity: writing
  text: 'Figure 7: The y-axis label ''Training Loss'' is split across two lines (''Training''
    and ''Loss'') with excessive vertical spacing, making it difficult to read as
    a single unit.'
- id: ed4e2a8cc1e6
  severity: science
  text: 'Figure 8: The pie chart displays percentages (68%, 18%, 9%, 4%) that sum
    to 99%, implying a missing 1% slice or rounding error, yet no ''Other'' category
    is shown to account for the discrepancy.'
- id: 9671b288b8d7
  severity: writing
  text: 'Figure 8: The caption ''Data distribution visualization'' is too vague; it
    fails to specify what the categories (PHUMA, Inhouse, etc.) represent (e.g., source
    of motion data, dataset split) or the total number of samples.'
- id: 51a7a894da87
  severity: writing
  text: 'Figure 8: The label ''Motion Million'' is ambiguous and likely a typo or
    truncated name; it is unclear if this refers to a specific dataset or a category
    of motion.'
- id: 928743ce43db
  severity: science
  text: 'Figure 9: The figure displays three bar charts showing ''Success Rate'' vs.
    ''Cluster Num'', ''History Length'', and ''Envs Num'', but the caption only states
    ''Ablation studies for Humanoid-GPT'' without specifying what is being ablated
    or what the baseline is. The charts show parameter sweeps rather than ablation
    of specific model components.'
- id: 45cf6304dc01
  severity: writing
  text: 'Figure 9: The y-axis lacks a scale or tick marks, making it impossible to
    judge the magnitude of differences between bars beyond the labeled values. The
    x-axis labels are rotated and partially illegible in the rendered image.'
- id: 0b99b7cf36d8
  severity: science
  text: 'Figure 9: No error bars or confidence intervals are shown despite presenting
    experimental results, which limits the ability to assess statistical significance
    of the observed differences.'
- id: a22c91831e5b
  severity: fatal
  text: 'Figure 10: The figure has no caption, making it impossible to interpret the
    axes, the meaning of the ''Blue'', ''Brown'', and ''Light blue'' labels, or the
    nature of the visualization (e.g., t-SNE, UMAP, or raw data).'
- id: 56c9c72cfa57
  severity: science
  text: 'Figure 10: The plot lacks axis labels and units, preventing any assessment
    of the feature space dimensions or scale.'
- id: 8c3200bffefd
  severity: science
  text: 'Figure 10: The legend is ambiguous; ''Light blue: All'' suggests an overlay
    of the other two categories, but the visualization does not clearly distinguish
    the specific contributions of ''AMASS'' and ''LAFAN'' versus the combined set.'
artifact_hash: 11a83a092083d485002512d3e56d130e02aef8501fdca7259786be2bc34086fd
artifact_path: projects/PROJ-658-humanoid-gpt-scaling-data-and-structure/paper/metadata.json
backend: dartmouth
feedback: Vision review of 10 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T13:30:11.653480Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

Figure 1 provides a clear visual overview of the pipeline stages, but the caption is marred by grammatical errors where the subject is missing, and it references specific reward types not explicitly labeled in the diagram.

### Figure 2

The figure effectively visualizes dataset diversity with clear axes and annotations, but the top x-axis label 'Geometric-std' conflicts with the caption's 'gstd', and the label for the largest bubble is ambiguously positioned.

### Figure 3

The figure effectively demonstrates the robot's zero-shot capabilities through clear visual examples of various tasks. However, the caption contains grammatical errors with missing nouns, and the task labels on the image suffer from poor contrast.

### Figure 4

The bar chart effectively visualizes latency differences but the caption's claim of '5 times faster' is imprecise relative to the specific data points shown, and the separation of the TWIST baseline by a dashed line without explanation creates ambiguity in the comparison.

### Figure 5

Figure 5 effectively demonstrates the system's zero-shot generalization capabilities through a grid of real-world video frames showing the humanoid tracking diverse human motions. The visual evidence aligns perfectly with the caption's claim of handling complex and high-dynamic tasks, including specific dance styles.

### Figure 6

Figure 6 effectively visualizes the trend of performance improvement with data scaling, but the y-axis lacks a numerical scale and tick marks, relying solely on data labels which limits the ability to assess the magnitude of change.

### Figure 7

The figure displays training loss curves over training steps, which contradicts the caption's claim of a 'Model Scalability Comparison' that should typically relate performance to model size or parameters. Additionally, the y-axis label formatting is poor.

### Figure 8

The figure presents a pie chart of data sources but suffers from a mathematical inconsistency where the percentages sum to 99% without an 'Other' category. Additionally, the caption is insufficiently descriptive, failing to define the categories or the total dataset size.

### Figure 9

Figure 9 presents parameter sensitivity analyses rather than clear ablation studies, lacks y-axis scaling, and omits error bars, reducing its scientific rigor and interpretability.

### Figure 10

Figure 10 is a scatter plot with a legend but no caption or axis labels, rendering the visualization scientifically unintelligible and impossible to verify against the paper's claims.
