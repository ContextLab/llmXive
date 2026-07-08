---
action_items:
- id: ed10ef374d7b
  severity: writing
  text: 'Figure 1: The x-axis timeline is cluttered and inconsistent; the ''2014''
    label is merged with ''2015 - 2019'', and the ''2020'' label is merged with ''2020
    - 2023'', making the specific year boundaries difficult to parse.'
- id: b258e35adb73
  severity: writing
  text: 'Figure 1: The x-axis labels ''2014'' and ''2020'' are visually merged with
    adjacent time ranges (e.g., ''2014 2015 - 2019''), creating ambiguity about the
    start of the ''Stage II'' and ''Stage III'' periods.'
- id: 3272c0544c8a
  severity: writing
  text: 'Figure 2: The top-left ''Iterations'' arrow points to the S0 block but lacks
    a clear label or connection to the ''Training Iteration t'' box, creating ambiguity
    about the temporal flow.'
- id: d4770b1c82f6
  severity: writing
  text: 'Figure 2: The ''Transformer Blocks'' section lists ''Self-Attn'' and ''MLP
    / FFN weights'' but does not explicitly link these to the ''trainable parameter
    groups'' arrow feeding into S0, which could confuse readers about the source of
    gradients.'
- id: 79ac2d8c806f
  severity: science
  text: 'Figure 7: The caption states ''stars mark frontier members,'' but the left
    plot shows ''Lion'' (green star) and ''GaLore'' (red star) as stars, while ''APOLLO''
    (purple star) is also a star. However, ''Lion'' is clearly dominated by ''GaLore''
    and ''APOLLO'' in both PPL and time/memory, so it should not be on the Pareto
    frontier. This misrepresents the frontier definition.'
- id: 87844513e167
  severity: writing
  text: "Figure 7: The x-axis label 'Per-step time (ms)' on the left plot and 'Optimizer-state\
    \ memory (GB)' on the right plot are clear, but the y-axis label 'C4 val PPL (1B)'\
    \ is repeated identically on both plots without clarifying that the left is time\
    \ and right is memory \u2014 though this is minor since the x-axes differ."
- id: 632e9901c9f3
  severity: science
  text: 'Figure 8: The colorbar legend is inverted relative to the data and caption.
    The caption states ''Green is favorable'' (lower PPL/Time/Memory), but the colorbar
    labels ''better than AdamW'' at the top (green) and ''worse than AdamW'' at the
    bottom (red). However, the data shows AdamW (PPL 14.48) is colored green, while
    methods with better PPL (e.g., Adan 14.35) are also green, and methods with worse
    PPL (e.g., AdaBelief 16.79) are red. The issue is that the colorbar labels ''Time/Mem
    baseline'' and ''same'
- id: fb2a69e8af1b
  severity: writing
  text: 'Figure 8: The colorbar legend has ambiguous labels. The top label ''Time/Mem
    baseline'' is unclear because the heatmap includes three metrics (PPL, Time, Memory),
    but the label suggests the baseline applies only to Time and Memory. The middle
    label ''same as AdamW'' is placed on the colorbar, but it is not clear if this
    refers to the color value or the metric value. The bottom label ''worse than AdamW''
    is clear, but the overall legend design is confusing. The colorbar should be relabeled
    to explicitl'
- id: 28abe67339b1
  severity: writing
  text: 'Figure 9 caption: states ''hatch = architecture'' for panel (c), but the
    rendered plot uses color intensity (opacity) to represent architecture, not hatching
    patterns.'
- id: 5ba61b3df0a5
  severity: science
  text: 'Figure 9: The y-axis in panels (a) and (b) is inverted (1 at top, 12 at bottom)
    to indicate ''1 = best'', but the axis labels are not explicitly marked as inverted
    or ''best at top'', which can be confusing for standard plot reading.'
- id: 404992225ef7
  severity: writing
  text: 'Figure 9: The x-axis labels in panels (a) and (b) are stacked vertically
    (e.g., ''Tr++'' over ''340M''), which is readable but could be improved by rotating
    or spacing them to avoid crowding.'
- id: be9fc50178d9
  severity: writing
  text: 'Figure 9: The legend in panel (b) is placed inside the plot area and partially
    obscures the data lines; moving it outside or making it semi-transparent would
    improve readability.'
- id: 2d36aefba52d
  severity: writing
  text: 'Figure 9: The x-axis labels in panel (c) are rotated at an angle, which is
    good for readability, but some labels (e.g., ''MARS-Shampoo'') are still slightly
    cut off or hard to read at the edges.'
- id: 3d7213668900
  severity: writing
  text: 'Figure 9: The caption mentions ''hatch = architecture'' for panel (c), but
    the plot uses color intensity (opacity) instead of hatching, creating a mismatch
    between description and visual representation.'
- id: 4a30974bffbc
  severity: science
  text: "Figure 10: The heatmap cells display raw GNormCV values (e.g., 111, 161)\
    \ while the colorbar scale is normalized (0.3\u2013111.6), creating a misleading\
    \ visual mapping where the highest numerical value (161) is colored identically\
    \ to the scale's maximum (111.6)."
- id: 14145cfeaa38
  severity: writing
  text: 'Figure 10: The x-axis labels (''340m'', ''1b'') are ambiguous and do not
    specify the architecture or scale they represent, which is critical for interpreting
    the ''across architectures'' claim in the caption.'
- id: 8bf7cf8e03aa
  severity: writing
  text: 'Figure 11: The caption defines the sensitivity score as ''$s_LR$'', but the
    panels display ''$s$''; align the notation in the caption with the figure labels.'
- id: bb2ea5b5b7fc
  severity: writing
  text: "Figure 11: The legend uses the symbol '\u2605' for 'Best LR', but the caption\
    \ states 'The star marks the tuned learning rate'; clarify if 'Best LR' and 'tuned\
    \ learning rate' are synonymous."
- id: 68956bfc976d
  severity: science
  text: "Figure 12: The caption states the profile covers objectives O1\u2013O6, but\
    \ the heatmap only displays five columns (Performance, Efficiency, Stability,\
    \ Robustness, Generalization). The mapping between these labels and the O1\u2013\
    O6 objectives is not provided in the caption or the figure, making it impossible\
    \ to verify the data against the claimed metrics."
- id: 5b0f777b0ca7
  severity: science
  text: 'Figure 12: The colorbar indicates that green is ''best'' and red is ''worst'',
    but the underlying data values are not normalized or defined. For example, ''Performance''
    shows 14.35 (green) while ''Robustness'' shows 23.0 (red); without knowing if
    lower or higher is better for each specific metric, the color mapping appears
    arbitrary and potentially misleading.'
artifact_hash: dbc48f30e617ac30caed20a396534de7c2a315d3d80c0dacd34ca49ae13f2258
artifact_path: projects/PROJ-1007-omniopt-taxonomy-geometry-and-benchmarki/paper/metadata.json
backend: dartmouth
feedback: Vision review of 12 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-08T03:15:13.069153Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

The figure effectively visualizes the taxonomy and timeline of optimizer evolution, but the x-axis typography is cluttered, with specific year labels merging into time ranges, which reduces readability.

### Figure 2

Figure 2 effectively illustrates the universal meta-pipeline for an optimizer step with clear stage progression and internal operations. Minor improvements could be made to clarify the temporal iteration flow and the explicit connection between transformer components and trainable parameter groups.

### Figure 3

Figure 3 is a clear and well-organized taxonomy diagram that effectively visualizes the relationships between various T1 optimizer variants. The use of color-coded sections, directional arrows, and detailed text boxes for specific algorithms (like AdamW and AdEMAMix) makes the mechanism overview easy to follow and consistent with the caption's description.

### Figure 4

Figure 4 is a clear and well-organized taxonomy schematic that effectively visualizes the three T2 matrix-level routes (Spectral Orthogonalization, Kronecker-Factored Preconditioning, Low-Rank Subspace Projection) and their constituent methods. The color-coding, hierarchical layout, and internal annotations (S1-S5) are legible and align perfectly with the provided caption.

### Figure 5

Figure 5 is a clear and well-organized taxonomy schematic that effectively categorizes T4 optimizers by their memory reduction mechanisms. The visual hierarchy, color-coding, and internal text descriptions (S1-S5) align perfectly with the caption's description of the four sub-groups.

### Figure 6

Figure 6 is a clear and well-organized taxonomy schematic that effectively categorizes T5 curvature-aware and geometric regularization methods into four distinct sub-groups. The visual hierarchy, color-coding, and internal text descriptions (S1-S5) are legible and align perfectly with the caption's description of the intervention points.

### Figure 7

The figure visually presents Pareto frontiers with color-coded families and star-marked frontier members, but incorrectly labels non-frontier methods (e.g., Lion) as frontier members, contradicting the definition of Pareto optimality. Axis labels are clear but slightly redundant.

### Figure 8

Figure 8 presents a clear heatmap of optimizer metrics, but the colorbar legend is ambiguously labeled. The 'Time/Mem baseline' label is misleading because the color scheme applies to PPL as well, and the legend does not explicitly state that green indicates better performance (lower values) for all three metrics relative to AdamW. This could lead to misinterpretation of the data.

### Figure 9

Figure 9 presents rank stability data clearly, but the caption incorrectly describes the use of 'hatching' for architecture in panel (c) when the plot actually uses color intensity/opacity. Additionally, the inverted y-axis in panels (a) and (b) lacks explicit annotation to indicate that lower rank numbers (better performance) are at the top.

### Figure 10

The figure presents a heatmap of gradient-norm stability but suffers from a mismatch between the raw numerical values in the cells and the normalized colorbar scale, alongside ambiguous x-axis labels that fail to define the specific architectures tested.

### Figure 11

The figure effectively visualizes learning-rate robustness across optimizers with clear color coding and data points. However, there is a minor notation inconsistency between the caption ($s_LR$) and the panel labels ($s$), and the legend symbol description could be better aligned with the caption's terminology.

### Figure 12

The figure presents a family-level summary heatmap but fails to map the displayed columns to the O1–O6 objectives mentioned in the caption. Additionally, the lack of defined units or directionality (higher/lower is better) for the specific metrics makes the color-coded 'best/worst' interpretation ambiguous.
