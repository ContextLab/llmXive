---
action_items:
- id: 4af626b74e29
  severity: science
  text: 'Figure 1: The bar chart values (e.g., 18.0 for MimicGen) contradict the pie
    chart legend (18% for MimicGen) and the caption''s claim that the bar chart shows
    ''percentage''. The sum of bar values is ~100, implying the bars show raw counts
    (in 10Ks) rather than percentages, creating a direct conflict with the caption
    and the pie chart''s percentage labels.'
- id: b64c45182588
  severity: writing
  text: 'Figure 2: The caption ''LIBERO-Spatial: bowl from table center to plate''
    is too brief and does not explain the four rows (Current RGB, Current Depth, GT
    Future, Pred Future) or the time steps (T=0 to T=10) shown in the figure.'
- id: 453b15a6b0a3
  severity: science
  text: 'Figure 2: The ''Current RGB'' row shows a top-down view of the scene, while
    the ''Current Depth'' and future rows show a side-view depth map; this perspective
    shift is not explained in the caption and may confuse readers about the spatial
    relationship between views.'
- id: f7e3dd9b0718
  severity: writing
  text: 'Figure 4: The x-axis of the ''Inference Latency'' scatter plot is reversed
    (500 to 5), which is non-standard and potentially confusing.'
- id: fe485cc7cbb8
  severity: writing
  text: 'Figure 4: The x-axis label for the bar chart is misspelled as ''Pertrubed
    Camera'' instead of ''Perturbed Camera''.'
- id: 71e163012411
  severity: writing
  text: 'Figure 4: The title ''Geometric Foundation Model'' is misspelled as ''Geometric
    Foundation Model'' (missing ''r'' in Geometric) in the top left.'
- id: ab93a49e5ebd
  severity: writing
  text: 'Figure 7: The sub-figure labels (a) and (b) in the right column are not defined
    in the caption, which only describes the general setup and ID vs. OOD camera setup
    without mapping these labels to specific camera views.'
- id: d1934562b1f4
  severity: writing
  text: 'Figure 7: The terms ''In-distribution'' and ''Out-of-distribution'' are used
    as labels for the robot end-effector views on the left, but the caption does not
    explicitly define what constitutes the in-distribution versus out-of-distribution
    setup.'
- id: b1c3874a97f7
  severity: science
  text: 'Figure 9: The caption describes ''Attention visualizations of action tokens,''
    but the figure displays a grid of robot manipulation frames with heatmaps overlaid
    on the scene. It is unclear if these heatmaps represent attention over action
    tokens or spatial attention over the image; the visualization does not match the
    description of token-level attention.'
- id: 7c18fa7aebb4
  severity: writing
  text: 'Figure 9: The figure lacks a legend or colorbar to interpret the heatmap
    intensity (e.g., attention weight or probability), making the visualizations unquantifiable.'
- id: adef6f4d345a
  severity: writing
  text: 'Figure 9: The row labels (''Layer 13'', ''Layer 26'', etc.) and column labels
    (''t=1'', ''t=3'', etc.) are present, but there is no explicit legend defining
    what the specific colors in the heatmaps represent.'
- id: 2f847e016af5
  severity: science
  text: 'Figure 10: The caption states that light bars represent in-domain and dark
    bars represent out-of-domain settings, but the bar chart legend identifies the
    colors as ''Ours'', ''$\pi_{0.5}$'', and ''Spatial Forcing''. This creates a direct
    contradiction where the visual encoding (color) conflicts with the textual description
    of the experimental conditions.'
- id: 44ab117ee99a
  severity: science
  text: 'Figure 10: The ''Stack milk and cube'' task shows a 100% success rate for
    ''Ours'' (80+20), yet the ''Pick and Place'' task (a prerequisite skill) shows
    a lower success rate for the same method. The stacked bars imply a breakdown of
    success types (e.g., ID vs OOD) but the caption''s definition of the bars does
    not align with the stacked nature of the data visualization.'
artifact_hash: 2b47a226fbf60e77bf3630e010af6d066f9a3ac0ebb39463048a80ab1f66b524
artifact_path: projects/PROJ-718-geometric-action-model-for-robot-policy/paper/metadata.json
backend: dartmouth
feedback: Vision review of 10 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T21:00:27.748444Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

The figure presents a dataset mixture but contains a critical contradiction: the bar chart values are labeled as percentages in the caption but numerically represent raw counts (scaled by 10,000), which conflicts with the pie chart's percentage labels and the stated axis definition.

### Figure 2

Figure 2 visually demonstrates a robot task progression but lacks sufficient caption detail to explain the multi-view layout and temporal structure, potentially hindering interpretation of the prediction results.

### Figure 3

Figure 3 effectively presents zero-shot robustness results across eight perturbation categories and an average summary. The subplots are clearly labeled, axes are consistent, and the legend is present and readable in each panel, supporting the caption's claims.

### Figure 4

Figure 4 effectively illustrates the GAM pipeline and quantitative advantages, but contains several spelling errors ('Geometric', 'Pertrubed') and uses a reversed x-axis for latency that may confuse readers.

### Figure 5

Figure 5 provides a clear and detailed schematic of the Geometric Action Model (GAM) architecture, effectively illustrating the flow from observation encoding through the causal transformer to action decoding. The diagram is well-organized with distinct color-coded sections and includes a helpful key for the attention mask visualization in panel (b).

### Figure 6

Figure 6 effectively illustrates the architectural differences between Video WAMs, Geometry-aware VLAs, and the proposed GAM. The diagram is clear, well-labeled, and the caption accurately describes the three distinct approaches shown.

### Figure 7

The figure effectively illustrates the experimental setup and camera views, but the sub-figure labels (a) and (b) and the terms 'In-distribution' and 'Out-of-distribution' lack explicit definitions in the caption.

### Figure 8

Figure 8 effectively illustrates four distinct real-world manipulation tasks using a grid of sequential photographs. The visual content aligns perfectly with the caption, and the embedded text labels clearly describe the specific objective for each task.

### Figure 9

Figure 9 presents attention visualizations but fails to provide a legend or colorbar to interpret the heatmap values. Additionally, the visual content (scene heatmaps) appears to contradict the caption's claim of visualizing 'action tokens' specifically, creating ambiguity about what is being shown.

### Figure 10

The figure presents a clear visual layout of robot tasks and results, but the caption's definition of the bar colors (in-domain vs. out-of-domain) directly contradicts the figure's internal legend (Ours vs. Baselines), making the data interpretation impossible without guessing.
