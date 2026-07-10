---
action_items:
- id: 0313551ccad5
  severity: writing
  text: 'Figure 1: The caption contains a grammatical error and missing subject (''generated
    by . can produce...''), likely due to a missing model name placeholder.'
- id: 77629989e87d
  severity: writing
  text: 'Figure 1: The caption claims to show ''Text-to-Video'' samples, but the rendered
    image is a static collage of still images with no indication of motion or video
    frames.'
- id: 37ce56ea2b3d
  severity: writing
  text: 'Figure 2: The legend in the top-right corner defines ''Routed Expert'' and
    ''Shared Expert'' but does not define the purple ''Attention'' block or the pink
    ''Gate'' block, which are distinct components in the diagram.'
- id: 990dfc443d7e
  severity: writing
  text: 'Figure 2: The ''Time Embedding'' label is placed at the bottom of the diagram,
    but the arrows originating from it are not explicitly drawn to the specific modulation
    points (the ''C'' circles) in the main block diagram, making the connection implicit
    rather than explicit.'
- id: f02bead036a0
  severity: writing
  text: 'Figure 3: The caption ''Training loss'' is too generic to describe the specific
    comparison of MoE expert scales (7B, 13B, 25B) shown in the legend; it should
    explicitly state the figure compares training loss across different MoE configurations.'
- id: fd69a478f17c
  severity: writing
  text: 'Figure 3: The x-axis label ''Training Steps'' uses ''k'' notation (10k, 20k)
    without explicitly defining ''k'' as 1,000 in the caption or axis text, which
    is a minor clarity issue.'
- id: e61726f8bae6
  severity: writing
  text: 'Figure 4: The caption ''Training loss'' is insufficient; it fails to define
    the two model variants (MoE 13B-A1.4B-E128 vs MoE 13B-A1.5B-E64) shown in the
    legend or explain the specific ''active capacity'' ablation being compared.'
- id: c4581a2eb527
  severity: science
  text: "Figure 4: The y-axis lacks a zero baseline and uses a truncated scale (0.15\u2013\
    0.17), which visually exaggerates the performance difference between the two models."
- id: 914dfdf968a9
  severity: science
  text: 'Figure 5: The caption states ''validation curves are unsmoothed'', but the
    right panel shows perfectly smooth curves with no noise, which is inconsistent
    with raw logged losses. The left panel shows raw data in the background, but the
    right panel does not, contradicting the description.'
- id: 382f1d94a07d
  severity: writing
  text: 'Figure 5: The x-axis tick labels (5k, 20k, 40k, 60k) are non-uniformly spaced
    relative to the axis ticks, making it difficult to accurately read the step count
    for specific points on the curve.'
- id: 1e29bedf4fc2
  severity: science
  text: 'Figure 6: The inset ''Long-run zoom'' shows curves extending to 80k steps,
    but the main plot''s x-axis stops at 60k. This creates a disconnect where the
    inset displays data not present in the main view, and the main plot''s x-axis
    scale (10k-60k) does not align with the inset''s (20k-80k), making it difficult
    to correlate the two views.'
- id: 9c7644b7b9a9
  severity: writing
  text: 'Figure 6: The legend is placed inside the plot area and partially obscures
    the curves, particularly the ''MoE 13B-A1.4B'' and ''MoE 30B-A3B'' lines. Moving
    the legend outside or using a more compact layout would improve readability.'
- id: 904f9767a72d
  severity: writing
  text: 'Figure 7: The caption describes the content as ''video generation'' and ''refined
    video generation'', but the rendered image displays static frames (likely keyframes)
    without any indication of motion or temporal progression, which is misleading
    for a video paper.'
- id: c7ac653d4a94
  severity: writing
  text: 'Figure 7: The caption claims the robot''s name is ''AURORA'' and the prompt
    includes this detail, but the image shows the text ''AURORA'' on the robot''s
    chest; however, the caption does not explicitly point out that the text rendering
    is a specific success metric being demonstrated, making the connection implicit.'
- id: 80510d834063
  severity: writing
  text: 'Figure 9: The JSON object on the left is rendered at a very small font size,
    making the specific keys and values difficult to read and verify against the caption''s
    description of ''structured tags''.'
- id: ee70eaaf3191
  severity: writing
  text: 'Figure 9: The ''Long-tail distribution'' panel contains bar charts with no
    axis labels, units, or numerical scales, rendering the data purely illustrative
    rather than informative.'
- id: 295fc6e06aee
  severity: science
  text: 'Figure 10: The top ''Image'' stream shows a retention rate of 27% at Stage
    3, but the band width visually narrows to near zero by Stage 5, implying total
    elimination, yet the caption states percentages are relative to the initial pool
    without clarifying if the stream is fully dropped or just reduced further.'
- id: a7871ed75e5d
  severity: writing
  text: 'Figure 10: The ''192p'', ''480p'', and ''1080p'' labels at the top are not
    defined in the caption or legend; it is unclear if these refer to resolution thresholds,
    data quality tiers, or sampling criteria.'
- id: d3540dbf8130
  severity: science
  text: 'Figure 11: The caption claims to demonstrate improvements in ''blurred or
    incorrect text rendering,'' but the provided image contains no text elements (e.g.,
    signs, labels, or typography) to support this specific claim.'
- id: 58b1741dd428
  severity: science
  text: 'Figure 11: The caption claims to show ''structural object deformation'' resolution,
    yet the ''Original'' images (e.g., the excavator and motorcyclist) appear structurally
    sound and do not exhibit the deformation described.'
artifact_hash: 9ee70f69980a19ab6b09b1ef85c408bba9d6c20db5c959c0faf89cac5e30112c
artifact_path: projects/PROJ-1026-scaling-mixture-of-experts-video-pretrai/paper/metadata.json
backend: dartmouth
feedback: Vision review of 12 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-10T03:04:43.076518Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

The figure serves as a visual teaser with high-quality samples, but the caption contains a grammatical error with a missing subject and fails to distinguish between the static images shown and the claimed video generation capabilities.

### Figure 2

The figure provides a clear overview of the architecture, but the legend is incomplete as it omits definitions for the 'Attention' and 'Gate' blocks shown in the diagram. Additionally, the connection between the 'Time Embedding' and the modulation points is implied by proximity rather than explicit arrows.

### Figure 3

The figure clearly displays training loss curves for three MoE configurations with appropriate legends and error shading, but the caption is overly generic and fails to describe the specific experimental comparison being visualized.

### Figure 4

The figure presents a training loss comparison but suffers from a generic caption that fails to define the specific models or ablation parameters, and the truncated y-axis scale exaggerates the visual difference between the curves.

### Figure 5

The figure effectively compares the two models, but the caption's claim that validation curves are 'unsmoothed' contradicts the visual evidence of perfectly smooth lines in the right panel. Additionally, the non-uniform x-axis tick spacing reduces readability.

### Figure 6

Figure 6 presents training loss curves for dense and sparse models with a zoomed-in inset, but the x-axis misalignment between main and inset plots and the legend's placement within the plot area reduce clarity and hinder direct comparison.

### Figure 7

The figure effectively demonstrates visual fidelity improvements between base and refiner generations for both human and robot subjects. However, the caption's reference to 'video generation' is slightly misleading as the figure only presents static frames, and it fails to explicitly highlight the successful text rendering of 'AURORA' as a key result.

### Figure 8

Figure 8 effectively visualizes the Data Profiling Engine workflow described in the caption. The diagram clearly maps input media types to five annotated dimensions with specific examples, and the layout is uncluttered and easy to follow.

### Figure 9

Figure 9 effectively visualizes the hierarchical structure of the World-Knowledge Topological Graph and the feedback loop for data curation. However, the text in the JSON annotation block is too small to read comfortably, and the distribution charts lack necessary axis labels and scales.

### Figure 10

The Sankey diagram effectively visualizes the data curriculum flow, but lacks definitions for the resolution labels (192p, 480p, etc.) and the visual representation of the image stream's final retention is ambiguous relative to the stated percentages.

### Figure 11

The figure provides a clear visual comparison of video quality before and after post-training, but the caption makes specific claims about text rendering and object deformation that are not supported by the visual evidence in the provided image.

### Figure 12

Figure 12 effectively demonstrates qualitative improvements in embodied scenarios by comparing 'Original' and 'Post-training' results across four distinct tasks. The visual evidence clearly supports the caption's claims regarding the resolution of artifacts like structural distortion and non-physical penetration.
