---
action_items:
- id: 25a384b505a5
  severity: science
  text: 'Figure 1: The caption states ''Colored cells report the per-domain ranking'',
    but the heatmap contains both colored cells with numbers and black cells with
    dots. The caption fails to define the meaning of the black cells (e.g., whether
    they represent ''not ranked'', ''did not run'', or ''no data''), making the visualization
    ambiguous.'
- id: f9b068c0c8b9
  severity: writing
  text: 'Figure 1: The top legend bar uses colored blocks to group methods (e.g.,
    blue for VGGT, green for DA3), but the specific method names in the header are
    not clearly aligned with these color blocks, and the legend does not explicitly
    map the colors to the method names below them.'
- id: 7a990b7385ae
  severity: writing
  text: 'Figure 2: The caption states ''Colored cells report the per-domain ranking'',
    but the image shows a single large table with no visual distinction or separation
    for the ''Sparse'' regime mentioned in the title; it appears identical to the
    dense regime table, making the specific ''Sparse'' context unverifiable.'
- id: b77affe9de41
  severity: writing
  text: 'Figure 2: The top legend bar contains colored blocks for methods (e.g., VGGT,
    DA3-Giant) but lacks text labels directly under the blocks, relying on the user
    to map colors to the column headers below, which is visually cluttered and indirect.'
- id: 0052fa7eed46
  severity: writing
  text: 'Figure 3: The top legend bar contains colored blocks for methods (e.g., VGGT,
    DA3-Giant) but lacks text labels directly under the blocks; the method names are
    only visible in the first row of the grid, making the legend incomplete on its
    own.'
- id: a929cd1d7c06
  severity: writing
  text: 'Figure 3: The caption states ''Colored cells report the per-domain ranking'',
    but the cells contain numbers (1-9) without a legend or colorbar explaining the
    ranking scale (e.g., does 1 mean best or worst?).'
- id: e0f765b38f40
  severity: science
  text: "Figure 4: The caption states 'Empty cells indicate that the method runs out\
    \ of memory', but the figure shows empty cells (e.g., in the 'G1 \u2014 INDOOR'\
    \ section) containing dashed outlines or dots, which contradicts the definition\
    \ of 'empty' and makes it unclear if these are OOM failures or missing data."
- id: fc7db493c6ef
  severity: writing
  text: 'Figure 4: The top legend labels (e.g., ''VGCT'', ''DA3-Giant'') are extremely
    small and blurry, making them illegible and difficult to map to the corresponding
    columns.'
- id: f48ba4ba2419
  severity: science
  text: 'Figure 5: The caption claims to show ''depth/camera metrics'' for the scenes,
    but the rendered image contains no numerical metrics, tables, or text annotations
    reporting these values.'
- id: 889e3194ee81
  severity: science
  text: 'Figure 5: The ''GT Point Cloud'' for the second scene (outdoor driving) is
    labeled ''N/A'', yet the caption describes this as a ''dense outdoor driving''
    case, implying a ground truth should be available for comparison.'
- id: c4dc69ad8c97
  severity: science
  text: 'Figure 6: The caption claims to visualize ''DA3-Giant'', but the bar charts
    label the method as ''DA3-Giant (w/ Cam)'', while the 3D visualizations are labeled
    simply ''DA3''. This creates ambiguity about whether the visualized results include
    the depth prior mentioned in the caption.'
- id: 665787b84c66
  severity: writing
  text: 'Figure 6: The dataset titles in the right-hand bar charts (e.g., ''robotwin_franka-panda-1_stack_blocks_two_episode44_sparse'')
    are truncated or poorly formatted, making it difficult to identify the specific
    scenes being evaluated.'
- id: 54db3e263a2e
  severity: science
  text: 'Figure 7: The caption claims to show ''DA3-Giant'', but the bar charts list
    ''DA3'' (and ''DA3-Giant'' in other figures), creating ambiguity about whether
    the specific ''Giant'' variant is being evaluated or if the label is truncated.'
- id: fcbbd1c1cfa7
  severity: writing
  text: 'Figure 7: The ''Multi-view Input'' column is unlabeled; while the caption
    mentions ''input views'', the column header is missing, making the layout less
    self-explanatory compared to the method columns.'
- id: '410154549989'
  severity: science
  text: 'Figure 8: The caption claims to show ''DA3-Giant, MapAnything, OmniVGGT,
    Pi3, and WorldMirror'', but the visualizations only show DA3, MapAnything, OmniVGGT,
    Pi3-X, and WorldMirror. The ''Giant'' variant is missing from the visual grid.'
- id: a5a230ad73d8
  severity: science
  text: 'Figure 8: The rightmost bar chart for the bottom scene (''lingbot...'') only
    displays ''depth abs_rel'' metrics. The caption states that the right panel reports
    both ''depth AbsRel and camera AUC@30'', but the camera metric is missing for
    this specific case.'
- id: 9bda98bf9e86
  severity: writing
  text: 'Figure 8: The title of the bottom-right bar chart is split across two lines
    (''lingbot_RobbyReal_00009_07_overpass_passage_si'' / ''ngle''), making the scene
    identifier difficult to read.'
- id: 5f881ab07624
  severity: science
  text: 'Figure 9: The caption claims to visualize failure cases of MapAnything, WorldMirror,
    and OmniVGGT, but the rendered image displays a grid of successful reconstructions
    (MapAnything, WorldMirror, OmniVGGT) compared against ''Ground Truth Point Cloud''
    across three scenes, contradicting the ''Failure Cases'' title.'
- id: 052a18a2d06b
  severity: writing
  text: 'Figure 9: The image contains no figure number or title text; the caption
    ''Figure 9: Failure Cases...'' is external to the rendered image, making the figure
    standalone ambiguous.'
- id: 43238d9b56dc
  severity: science
  text: 'Figure 10: The caption claims to compare ''annotations from OmniWorld'' against
    ''reconstructed point clouds'', but the ''OmniWorld'' column displays sparse,
    noisy point clouds that visually resemble the ''DA-Next-5M w/ Init Cam Poses''
    output rather than clean ground-truth annotations, making the comparison misleading.'
- id: 65b07e6e8e96
  severity: writing
  text: 'Figure 10: The column headers ''DA-Next-5M w/ Init Cam Poses'' and ''DA-Next-5M
    w/ Refined Cam Poses'' are repetitive and cluttered; consider using a shared row
    label or a cleaner legend to distinguish the methods.'
- id: 45ae92cecf0f
  severity: writing
  text: 'Figure 11: The caption ''DROID Gallery 1'' is insufficient for a standalone
    figure; it fails to describe the content (e.g., input views, 3D reconstructions,
    timestamps) or the specific scenes shown, making the figure unintelligible without
    external context.'
- id: 093eb2f7e7df
  severity: science
  text: 'Figure 11: The figure displays eight distinct scenes with timestamps but
    lacks any quantitative metrics, error bars, or comparative baselines, rendering
    it purely illustrative and unable to support scientific claims about model performance.'
- id: 553465cf12fe
  severity: writing
  text: 'Figure 12: The caption ''DROID Gallery 2'' is insufficient for a standalone
    figure; it fails to describe the visual content (e.g., input views, segmentation
    masks, 3D point clouds) or the specific scenes shown, making the figure unintelligible
    without the main text.'
- id: 4e8e3347cfcd
  severity: science
  text: 'Figure 12: The figure displays eight distinct scene examples (labeled 9-16)
    but lacks any visual legend or colorbar to explain the meaning of the colors in
    the segmentation masks or the point cloud reconstructions.'
artifact_hash: 306c5e78aff3c136de96c4c6956084c3af89239f10c2fba4682734d1809d3475
artifact_path: projects/PROJ-634-https-arxiv-org-abs-2605-27367/paper/metadata.json
backend: dartmouth
feedback: Vision review of 12 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T21:44:04.411802Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

The figure presents a comprehensive ranking heatmap, but the caption fails to explain the black cells containing dots, leaving the reader unsure if they represent missing data or a specific ranking status. Additionally, the color-coding in the top legend is not explicitly mapped to the method names in the header.

### Figure 2

The figure presents a comprehensive dataset coverage matrix, but the caption's claim of a 'Sparse' regime is not visually distinguished from the dense regime shown in the image, and the top legend lacks direct text labels for the method colors.

### Figure 3

The figure presents a clear matrix of rankings and coverage, but the top legend lacks method labels, and the caption fails to define the ranking scale (1-9) or the color mapping used in the cells.

### Figure 4

The figure presents a dense heatmap of rankings and coverage, but the top column labels are illegible due to low resolution. Additionally, the visual representation of 'empty' cells (dashed boxes/dots) contradicts the caption's definition that empty cells indicate out-of-memory errors.

### Figure 5

The figure provides a clear visual comparison of point cloud reconstructions across four scenes, but it fails to deliver the specific 'depth/camera metrics' promised in the caption, and one ground truth comparison is missing.

### Figure 6

The figure effectively visualizes reconstruction quality and metrics, but the labeling of methods in the charts ('DA3-Giant (w/ Cam)') conflicts with the visualization labels ('DA3') and the caption's claim of using both camera and depth priors. Additionally, the dataset titles are cluttered and hard to read.

### Figure 7

The figure effectively visualizes reconstruction quality and metrics, but the column labeling is inconsistent (missing 'Multi-view Input' header) and the method name 'DA3' in the charts conflicts with the caption's 'DA3-Giant' claim.

### Figure 8

Figure 8 provides a useful qualitative comparison of depth-prior enhanced models, but it omits the 'Giant' variant mentioned in the caption and fails to display the camera metric for the final scene, contradicting the caption's description of the right panel.

### Figure 9

The figure contradicts its caption by showing successful reconstructions rather than failure cases, and it lacks an internal title or figure number.

### Figure 10

The figure effectively visualizes the progression from initial to refined poses, but the 'OmniWorld' column appears to show a noisy reconstruction rather than the clean annotations claimed in the caption, which undermines the validity of the comparison.

### Figure 11

Figure 11 is a visual gallery of eight scenes with timestamps but lacks a descriptive caption and quantitative metrics, making it purely illustrative and insufficient for scientific evaluation.

### Figure 12

The figure presents a gallery of qualitative results but suffers from a lack of descriptive context in the caption and missing legends to interpret the visual data.
