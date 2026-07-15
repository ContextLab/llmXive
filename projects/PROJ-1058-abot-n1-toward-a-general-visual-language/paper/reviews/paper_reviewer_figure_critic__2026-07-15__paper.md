---
action_items:
- id: 72c685829889
  severity: science
  text: 'Figure 1: The caption states that Stage 3 uses ''A* on MoGe-V2-derived 2D
    occupancy grids'', but the diagram explicitly labels the grid generation step
    as ''MoGe-V2 Normal Prior'' and does not visually depict the occupancy grid or
    the A* algorithm, creating a disconnect between the text description and the visual
    pipeline.'
- id: 685df9de0085
  severity: writing
  text: 'Figure 1: The ''Stage 3'' section contains a floating label ''MoGe-V2 Normal
    Prior'' pointing to a pyramid icon without a connecting box or clear definition
    of its role in the ''Traversability-Aware Sampling'' flow, making the diagram''s
    logic harder to follow.'
- id: 56ac222fb31f
  severity: writing
  text: 'Figure 2: The caption describes the content as ''Four segments of a long-range
    outdoor episode,'' but the figure itself is a composite of four distinct sub-figures
    (Seg1-Seg4) without a unifying visual frame or explicit labels connecting the
    segments into a single continuous narrative.'
- id: 51d78c3b6421
  severity: science
  text: 'Figure 2: The ''Slow System Reasoning'' panels display ''Affordance Pixel''
    markers (green dots) on the ground, but the corresponding ''VLA'' and ''Third-View''
    panels below them do not show these markers, making it difficult to verify if
    the visual guidance aligns with the agent''s actual perception or trajectory.'
- id: 2d46c61ac4ca
  severity: science
  text: 'Figure 4: The caption claims ''slope navigation and staircase avoidance''
    for the Luckin Coffee case, but the visual evidence shows the robot navigating
    a flat sidewalk and avoiding a red barrier; no slope or staircase is visible.'
- id: b1d7d28ab0bd
  severity: writing
  text: 'Figure 4: The ''Slow System Reasoning'' row contains red, blue, and green
    bounding boxes, but no legend or caption text explains what these specific colors
    signify (e.g., confidence levels, specific reasoning steps, or error types).'
- id: 6bc063b50cdd
  severity: science
  text: 'Figure 5: The ''Target Pixel'' (red star) is shown in the final ''bar approach''
    panel but is absent from the first three ''Slow System Reasoning'' panels despite
    the caption claiming ''target pixel visualizations'' are present at all four critical
    moments.'
- id: fe44f9f36969
  severity: writing
  text: 'Figure 5: The legend in the ''bar approach'' panel labels the red star as
    ''Target Pixel'' and the green dot as ''Affordance Pixel'', but the ''Slow System
    Reasoning'' panels for stair descent, gym entry, and gym exit only show the green
    dot without a legend, creating ambiguity about the red star''s absence.'
- id: 187d3748ae61
  severity: science
  text: 'Figure 7: The caption claims evaluation on ''EVT-Bench'', but the radar chart
    legend and axis labels only show ''ABoT-N1'', ''Previous BOTA'', ''NavFoM'', ''Uni-NavVid'',
    and ''Qwen-VLA'', with no explicit reference to EVT-Bench or its specific metrics.'
- id: e51a908cc81a
  severity: writing
  text: 'Figure 7: The legend for the radar chart is extremely small and illegible,
    making it difficult to distinguish between the different model lines (e.g., ''Previous
    BOTA'' vs ''NavFoM'').'
- id: d5d75c877d51
  severity: writing
  text: 'Figure 8: The caption text is truncated at the end (''predict continuo''),
    cutting off the description of the MLP output.'
- id: b269fac16789
  severity: science
  text: 'Figure 8: The ''Slow System'' block contains a purple hourglass icon and
    fire emojis, but the caption does not define these symbols or explain their significance
    (e.g., latency, compute intensity).'
- id: c1c0ec617be9
  severity: science
  text: 'Figure 8: The ''Fast System'' block contains a lightning bolt icon and a
    fire emoji, which are undefined in the caption and lack a legend.'
- id: fc9dd1275ac7
  severity: science
  text: 'Figure 9: The inner ring of the main donut chart contains a segment labeled
    ''Object Goal 0.1M'' that is visually indistinguishable from the adjacent ''POI
    Goal 3.0M'' segment due to identical coloring and lack of a visible boundary line,
    making the chart unreadable.'
- id: 0b374447ae81
  severity: science
  text: 'Figure 9: The ''TOTAL 30M'' label in the center of the main donut chart is
    mathematically inconsistent with the sum of the visible segment labels (6.2+2.4+2.7+3.0+0.1+0.1+5.1+6.8+3.4
    = 29.8M), suggesting a rounding error or missing data.'
- id: ff91730b767f
  severity: writing
  text: 'Figure 9: The text labels for the inner ring segments (e.g., ''Point Goal'',
    ''Person Following'') are rotated and difficult to read, reducing the clarity
    of the data breakdown.'
- id: cd84124bc89d
  severity: writing
  text: 'Figure 10: The caption describes the ''Right'' panel as having ''affordance
    pixel annotation'', but the image labels the green dot as ''Affordance Pixel''
    and the red dot as ''Target''/''Perturbed Target'' without explicitly defining
    the distinction in the caption text.'
- id: 42b5459bc36a
  severity: writing
  text: 'Figure 10: The ''Structured Sample'' panel includes a ''Mission'' text block
    with coordinates, but the caption does not explain the coordinate system or the
    meaning of the values.'
- id: cba81bfa76bd
  severity: science
  text: 'Figure 11: The caption describes a ''three-stage pipeline'' and ''generates
    and verifies affordance and target pixels,'' but the visual diagram only shows
    ''VLM Instruction Decomposition'' and ''VLM Annotation-Align'' without explicitly
    depicting the verification step or the generation of target pixels (which are
    listed as empty in the sample).'
- id: 6028751130ab
  severity: writing
  text: 'Figure 11: The ''Structured Sample'' on the right lists ''Target Pixel: left:[],
    front: [], right[]'' as empty, which contradicts the caption''s claim that the
    sample shows ''pixel-level annotations for affordance and target''.'
- id: 6aabcdef2c1c
  severity: science
  text: 'Figure 12: The caption claims the pipeline uses ''A* consistency filtering'',
    but the diagram labels the filter simply as ''Consistency Filter'' without explicitly
    showing or labeling the A* algorithm component.'
- id: 2e67d71d00fb
  severity: writing
  text: 'Figure 12: The ''Structured Sample'' text block contains raw JSON-like syntax
    (e.g., ''left: [], front: [542, 698]'') which is difficult to read and visually
    cluttered compared to the rest of the figure.'
artifact_hash: f88378b8f34f2b343e5f44980e669d21b209180df8e509a6c35972c8ebfdc6e7
artifact_path: projects/PROJ-1058-abot-n1-toward-a-general-visual-language/paper/metadata.json
backend: dartmouth
feedback: Vision review of 12 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-15T03:53:06.902877Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

The figure provides a clear overview of the dataset statistics and pipeline stages, but the visual representation of Stage 3 omits the occupancy grid and A* algorithm mentioned in the caption, relying instead on a 'Normal Prior' label that is not fully integrated into the flow.

### Figure 2

Figure 2 effectively illustrates the four key segments of the point-goal deployment with clear visual examples. However, the connection between the 'Slow System Reasoning' outputs and the agent's actual execution in the VLA/Third-View panels is not explicitly visualized, and the composite nature of the figure could be better structured to emphasize the continuous episode.

### Figure 3

Figure 3 effectively illustrates three object-goal deployment cases (outdoor bench, indoor chair with bottle, fire extinguisher) with clear visual overlays for CoT reasoning, affordance pixels, and target pixels. The layout is organized, the text is legible, and the caption accurately describes the content shown.

### Figure 4

The figure effectively visualizes the robot's navigation in three distinct POI scenarios with clear tri-view overlays, but the caption's description of the third case (Luckin Coffee) contradicts the visual content by mentioning obstacles not present in the image.

### Figure 5

Figure 5 effectively illustrates the slow-system reasoning process with clear visualizations of affordance pixels and CoT. However, the target pixel visualization is inconsistently applied across the four critical moments, appearing only in the final panel despite the caption's claim, and the legend is missing from the first three panels.

### Figure 6

Figure 6 effectively visualizes the person-following deployment across outdoor and indoor scenarios. The figure clearly distinguishes between raw observations and model outputs (Target Pixel, Affordance Pixel) using consistent color coding and labels, and the caption accurately describes the depicted tasks.

### Figure 7

The figure provides a clear visual overview of the ABot-N1 architecture and performance, but the caption mentions 'EVT-Bench' which is not explicitly labeled in the radar chart, and the radar chart legend is too small to read clearly.

### Figure 8

The figure effectively visualizes the dual-system architecture with clear data flow, but the caption is truncated at the end. Additionally, several icons (hourglass, lightning, fire emojis) are used without definition in the caption or a legend.

### Figure 9

The figure effectively visualizes the data pipeline and composition, but the main donut chart suffers from poor legibility due to rotated text and a confusing inner ring where the 'Object Goal' segment is visually merged with its neighbor. Additionally, the total count in the center does not match the sum of the labeled segments.

### Figure 10

The figure effectively visualizes the data pipeline and a sample output, but the caption lacks specific definitions for the coordinate values shown in the sample and could be more precise about the target pixel annotations.

### Figure 11

The figure effectively visualizes the instruction decomposition and alignment process, but the example sample on the right fails to show the target pixel annotations mentioned in the caption, and the verification stage described in the text is not explicitly illustrated in the diagram.

### Figure 12

The figure effectively visualizes the data pipeline and sample structure, but the caption's specific claim about A* filtering is not explicitly labeled in the diagram, and the structured sample text is cluttered with raw coordinate syntax.
