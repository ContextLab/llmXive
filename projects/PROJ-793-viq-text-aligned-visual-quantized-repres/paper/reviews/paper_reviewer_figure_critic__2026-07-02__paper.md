---
action_items:
- id: 6dab2d467a8c
  severity: writing
  text: 'Figure 1: The text labels inside the ''Position-Aware FSQ'' matrix (e.g.,
    ''9'', ''863'', ''25'', ''358'') are extremely small and illegible, making the
    specific quantization values unreadable.'
- id: b56ef324c805
  severity: science
  text: 'Figure 1: The bar charts on the right lack explicit axis titles (e.g., ''Score''
    or ''FID'') and the y-axis tick labels are too small to read, hindering verification
    of the ''state-of-the-art'' claim.'
- id: e41110b45a38
  severity: writing
  text: 'Figure 2: The legend in Stage 2-2 uses the term ''LoRA'' (Low-Rank Adaptation),
    but the diagram does not explicitly show where LoRA modules are applied to the
    frozen components, making the legend''s relevance to the visual flow unclear.'
- id: 8c53cb10f11d
  severity: writing
  text: 'Figure 2: The bottom row of diagrams appears to be a duplicate or slightly
    modified version of the top row without a clear distinction in the caption explaining
    the difference between the two rows.'
- id: c1464b8e5f10
  severity: science
  text: 'Figure 3: The legend defines ''4K Speed-up ratio'' and ''16K Speed-up ratio''
    as lines, but the bars are labeled with specific values (e.g., 12.94, 15.67) that
    do not match the right y-axis scale (0-100%) or the line trends, creating ambiguity
    about what the bar values represent.'
- id: da1a37594bd2
  severity: writing
  text: 'Figure 3: The caption states the figure compares ''Training Efficiency'',
    but the y-axis is labeled ''Time (s)'' and ''Speed-up Ratio (%)'', which are metrics
    of inference or forward pass efficiency, not training efficiency, creating a contradiction
    between the caption and the data shown.'
- id: 94d9a784197b
  severity: writing
  text: 'Figure 3: The legend includes ''ViQ Offline Code Extraction'' and ''MLLM
    w/ ViQ'' as separate entries, but the bars appear stacked or grouped in a way
    that makes it unclear which specific bar segment corresponds to which legend item
    without explicit visual distinction (e.g., hatching vs solid) matching the legend
    keys.'
- id: 0e3a26f7a457
  severity: writing
  text: 'Figure 4: The x-axis label ''JPEG(Q=0.08)'' is visually identical to the
    ''ViQ-Codes'' label, yet the bar chart shows ''JPEG(Q=0.08)'' at 0.08 MB and ''ViQ-Codes''
    at 0.07 MB. The visual reconstruction images above the ''ViQ-Codes'' label appear
    to correspond to the ''JPEG(Q=0.08)'' quality level (highly compressed artifacts),
    while the ''JPEG(Q=0.85)'' label is missing its corresponding image column, creating
    a mismatch between the visual examples and the quantitative data.'
- id: 880f65ba8e00
  severity: science
  text: 'Figure 4: The bar chart compares ''Raw'' (7.37 MB) against ''ViQ-Codes''
    (0.07 MB) to claim a 96x compression ratio. However, the ''Raw'' image is likely
    uncompressed (e.g., PNG or raw sensor data), whereas ''ViQ-Codes'' represents
    a compressed representation. A fair comparison for ''image compression'' should
    typically be against a standard baseline like JPEG at a similar quality level
    or a standard raw format specification, as comparing against a potentially inflated
    ''Raw'' size exaggerates the compressi'
- id: 5afce3c9efb4
  severity: science
  text: 'Figure 5: The caption states ''Left or above is the original image,'' but
    the visual layout (2x4 grid) and image content suggest these are side-by-side
    comparisons of original vs. reconstructed images. The ''above'' descriptor is
    confusing for a grid layout, and the lack of explicit ''Original'' vs. ''Reconstructed''
    labels makes it difficult to verify the reconstruction quality claim.'
- id: d27da130662d
  severity: writing
  text: 'Figure 5: The caption is ambiguous regarding the spatial arrangement of the
    comparison pairs. It should explicitly state ''Left column is original, right
    column is reconstructed'' (or similar) to match the visual evidence, rather than
    using ''Left or above'' which implies a different layout structure.'
artifact_hash: b0d13f79598805d86a50b3ae742d6ff735642238ad128fe0a6c96ca6ef0ec5e0
artifact_path: projects/PROJ-793-viq-text-aligned-visual-quantized-repres/paper/metadata.json
backend: dartmouth
feedback: Vision review of 5 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T21:10:12.816814Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

Figure 1 effectively illustrates the ViQ architecture and performance claims, but the text within the quantization matrix is illegible, and the bar charts lack clear axis labels and readable tick values.

### Figure 2

The figure provides a clear visual breakdown of the three-stage ViQ training pipeline. However, the legend entry for 'LoRA' is not visually mapped to specific components in the diagram, and the purpose of the second row of diagrams is not explained in the caption.

### Figure 3

The figure presents efficiency data but contradicts its own caption by labeling the y-axis as 'Time' and 'Speed-up Ratio' while the caption claims to show 'Training Efficiency'. Additionally, the bar values and legend definitions are ambiguous relative to the dual y-axes.

### Figure 4

Figure 4 effectively demonstrates ViQ's compression capabilities but suffers from a confusing layout where the visual reconstruction examples do not clearly align with the specific JPEG quality factors listed on the x-axis, and the baseline 'Raw' size used for the 96x compression claim lacks context regarding the file format.

### Figure 5

The figure displays a grid of image pairs that appear to be original vs. reconstructed samples, but the caption's description of the layout ('Left or above') is ambiguous and does not clearly map to the visual grid structure, making it difficult to distinguish the input from the output.
