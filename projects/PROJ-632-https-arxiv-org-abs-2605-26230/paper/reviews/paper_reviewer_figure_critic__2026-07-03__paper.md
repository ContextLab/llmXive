---
action_items:
- id: 90359ea00d40
  severity: writing
  text: 'Figure 1: The caption ends abruptly with ''through [fig_architecture_copy_8.pdf]'',
    indicating a broken sentence and a likely copy-paste error where the figure filename
    was pasted instead of the intended text.'
- id: 1e9386d50e4f
  severity: writing
  text: 'Figure 1: The mathematical notation in the caption contains a typo, writing
    the denoiser as ''$S_()$'' instead of ''$S_{\theta}(\cdot)$'' or similar, which
    does not match the label ''$S_{\theta}(\cdot)$'' shown in the diagram.'
- id: 11da73ba5f37
  severity: writing
  text: 'Figure 2: The caption text is truncated at the end (''...restored images
    and consi''), cutting off the sentence and likely the figure filename.'
- id: 3434959df734
  severity: science
  text: 'Figure 2: The diagram labels the input as ''Degraded Images'' and output
    as ''Restored Images & 3D Geometry'', but the caption describes the method as
    operating on ''geometry-aware latent representations'' and restoring ''intermediate
    representations'', creating a disconnect between the visual pipeline and the textual
    description.'
- id: 0bb07803c8a9
  severity: writing
  text: 'Figure 3 caption: The phrase ''provided in Fig. of the supplementary material''
    is incomplete and missing the specific figure number.'
- id: 7e11f8e6d8b3
  severity: science
  text: "Figure 3: The y-axis for the VAE method in panel (b) is broken and scaled\
    \ differently (0.4\u20131.2) than the main plot (17\u201327), which obscures the\
    \ true magnitude of performance differences and makes direct visual comparison\
    \ difficult."
- id: 48d3b9e27f69
  severity: science
  text: 'Figure 4: The caption claims to visualize ''top-down camera trajectories''
    for degraded inputs, but the plots show abstract 2D line graphs with no spatial
    context, axes, or units to verify they represent camera poses or trajectories.'
- id: c39de5b01b43
  severity: writing
  text: 'Figure 4: The legends inside the subplots are illegible due to low resolution,
    making it impossible to distinguish between the ''GARD'' method and the baselines
    mentioned in the caption.'
- id: e9ea984ad1c2
  severity: science
  text: 'Figure 5: The caption claims to visualize ''reconstructed 3D point clouds'',
    but the images display 2D RGB renderings of the scene (e.g., a bedroom and a fruit
    bowl) rather than explicit 3D geometry or point cloud data.'
- id: 94dafde79ded
  severity: writing
  text: 'Figure 5: The labels for the baseline methods (HI-Diff, InstructIR, MoCE-IR,
    Restormer, VRT, FMA-Net, VAE_MVD) are positioned above the image rows, but the
    layout is ambiguous regarding which specific images correspond to which method
    without explicit column headers or grid lines.'
- id: 1a9993713100
  severity: writing
  text: 'Figure 7: The rendered image is a visual collage of results (labeled ''Degraded
    Views & Depths'', ''Degraded 3D Point Cloud'', etc.) rather than a schematic diagram
    of the ''GARD framework'' described in the caption. The caption claims to describe
    the framework''s mechanism (denoising on geometry-aware representations), but
    the figure only shows qualitative before/after examples without illustrating the
    architecture or data flow.'
- id: 48f7b05c8b1b
  severity: science
  text: 'Figure 7: The figure lacks a legend or colorbar for the depth maps shown
    in the ''Degraded Views & Depths'' and ''Restored Views & Depths'' columns, making
    it impossible to interpret the quantitative depth values or verify the ''accurate
    3D scene geometry'' claim visually.'
- id: 6ad173e6620b
  severity: science
  text: 'Figure 8: The caption claims to visualize the effect of attention alignment
    training, but the figure lacks a ''Before'' vs. ''After'' comparison or a baseline
    to demonstrate the specific effect of the training.'
- id: a1581e64f0a3
  severity: writing
  text: 'Figure 8: The figure contains no internal labels, legends, or axis definitions
    to explain what the visual patterns (e.g., heatmaps or point clouds) represent,
    making the visualization unintelligible without external context.'
- id: 53f2eea4202e
  severity: writing
  text: 'Figure 9: The caption text (''Visualization of target correspondence maps'')
    is identical to the caption for Figure 8, suggesting a copy-paste error or missing
    specific description for the target maps shown.'
- id: de77d592462b
  severity: science
  text: 'Figure 9: The heatmap visualizations lack a colorbar or scale legend, making
    it impossible to interpret the magnitude of the correspondence values.'
- id: 7fa8542b1f02
  severity: writing
  text: 'Figure 10: The caption lists ''VAE'', ''DINOv2'', and ''DA3'' as the methods
    being visualized, but the rendered image lacks row labels or a legend to identify
    which row corresponds to which method.'
- id: 7b4dec89395f
  severity: writing
  text: 'Figure 10: The caption mentions ''Cross-view correspondence visualization''
    but does not define the column headers (e.g., ''Reference (query)'', ''View 1'',
    etc.) which are visible in the image but not described in the text.'
- id: 8458cb19bd3e
  severity: science
  text: 'Figure 11: The caption claims to show ''depth estimation results,'' but the
    visualizations use a ''jet'' colormap (blue-to-yellow) that is characteristic
    of normal maps or surface orientation rather than standard depth maps (which typically
    use a linear or log scale from near to far). Without a colorbar or explicit legend,
    the data representation is ambiguous and potentially misleading.'
- id: cbf69651ce81
  severity: writing
  text: 'Figure 11: The caption states ''three selected views out of ten input views,''
    but the figure displays a grid of 11 columns (Input Views, LQ, HI-Diff, InstructIR,
    MoCE-IR, Restormer, VRT, FMA-Net, VAEMVD, GARD (Ours), HQ). The caption fails
    to identify the methods shown in the intermediate columns, making it impossible
    to interpret the comparison.'
- id: b697ab91a629
  severity: writing
  text: 'Figure 12: The caption text is truncated at the end (''...clean HQ repres''),
    cutting off the final word and citation.'
- id: 6791b1dc35f3
  severity: writing
  text: 'Figure 12: The y-axis label ''Cosine Similarity'' is illegible due to low
    resolution.'
- id: ba9525409a28
  severity: science
  text: 'Figure 12: The x-axis label ''Layer Index'' is illegible; the specific layer
    numbers (14-40) are too small to read.'
artifact_hash: 1b009a000ce5ea80de9107001816db5f680b271a1e700e1b78677c55727d55dc
artifact_path: projects/PROJ-632-https-arxiv-org-abs-2605-26230/paper/metadata.json
backend: dartmouth
feedback: Vision review of 12 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T17:41:11.177430Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

The figure provides a clear visual overview of the GARD framework and its components. However, the caption is defective, containing a broken sentence at the end and a typo in the mathematical notation for the denoiser.

### Figure 2

The figure provides a clear visual comparison of two pipelines, but the caption is truncated and the diagram's explicit 'Image' labels slightly contradict the caption's focus on 'latent representation' restoration.

### Figure 3

The figure effectively demonstrates the robustness of the proposed method against degradation, but the caption contains a missing figure reference, and the broken y-axis for the VAE baseline in panel (b) hinders direct visual comparison of performance magnitudes.

### Figure 4

The figure fails to support its caption's claim of visualizing camera trajectories, as the plots appear to be abstract line graphs lacking spatial axes or units. Additionally, the internal legends are illegible, preventing verification of the method comparisons.

### Figure 5

The figure displays 2D image restorations rather than the 3D point clouds described in the caption, creating a mismatch between the visual evidence and the claimed results. Additionally, the method labels are loosely aligned with the image grid, which may cause confusion.

### Figure 6

The figure presents a clear qualitative comparison of image restoration results across multiple methods, including the proposed GARD and a high-quality ground truth. The column headers are legible, and the visual progression from degraded input to restored output effectively supports the caption's claim of high-fidelity recovery.

### Figure 7

The figure serves as a qualitative teaser showing before/after results but fails to visualize the 'GARD framework' architecture described in the caption. Additionally, the depth maps lack a colorbar or scale, hindering the interpretation of the geometric recovery.

### Figure 8

The figure fails to support its caption's claim of visualizing the 'effect' of attention alignment because it lacks a comparative baseline (e.g., before/after) and contains no internal labels or legends to interpret the visual data.

### Figure 9

The figure displays heatmap visualizations but lacks a colorbar to interpret values, and the caption appears to be a duplicate of Figure 8's text, failing to describe the specific target maps shown.

### Figure 10

The figure effectively visualizes correspondence maps for three methods, but the caption fails to explicitly map the method names (VAE, DINOv2, DA3) to the specific rows shown in the image, and omits descriptions for the column headers.

### Figure 11

The figure presents a grid of visualizations that appear to be normal maps rather than depth maps, lacking a colorbar to confirm the metric. Furthermore, the caption fails to define the various method columns (e.g., Restormer, VRT) shown in the grid, rendering the comparison unintelligible.

### Figure 12

The figure effectively visualizes the feature similarity analysis described in the caption, but the image resolution is too low to read the axis labels and tick marks. Additionally, the caption text is truncated at the end.
