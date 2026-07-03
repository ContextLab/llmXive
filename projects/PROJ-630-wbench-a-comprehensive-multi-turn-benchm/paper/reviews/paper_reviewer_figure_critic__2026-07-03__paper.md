---
action_items:
- id: b84aa87f06c6
  severity: writing
  text: 'Figure 1: The caption contains multiple instances of missing text where the
    benchmark name should appear (e.g., ''Overview of .'', ''cases in .'', ''covered
    by :''). The figure itself also uses the abbreviation ''PS'' without defining
    it in the caption.'
- id: 59632b435051
  severity: science
  text: 'Figure 1: The radar chart in panel (d) lacks a visible scale or grid values,
    making it impossible to determine the magnitude of the scores for the plotted
    models.'
- id: 258f11d31745
  severity: science
  text: 'Figure 2(c): The heatmap contains values exceeding the theoretical range
    of a Z-score (e.g., +1.9, -1.9), yet the colorbar scale is fixed to [-1.0, 1.0].
    This causes the most extreme values to be clipped to the maximum/minimum colors,
    obscuring the true magnitude of the deviations.'
- id: 8b858546f7fa
  severity: writing
  text: 'Figure 2(c): The y-axis labels are rotated 90 degrees and overlap significantly,
    making them difficult to read; horizontal alignment or increased spacing is needed.'
- id: eb4cb662e1f2
  severity: science
  text: 'Figure 3: The ''Perspective Switching'' panel shows a red ''X'' and a dashed
    line for the ''9 text-driven models'' baseline, but the legend entry for this
    group is a solid black square. This visual mismatch makes the baseline data illegible
    and confusing.'
- id: d54c604acdf6
  severity: writing
  text: 'Figure 3: The caption ''Per-turn performance degradation'' is too brief;
    it should explicitly state that the y-axis represents the evaluation score (e.g.,
    0-100) to clarify the metric being degraded.'
- id: 0b6bad1177e8
  severity: writing
  text: 'Figure 4: The caption contains LaTeX formatting artifacts (''Spearman $$'',
    ''$ 0.94'', ''$ = 1.00'') instead of the symbol ''$\rho$'' or the word ''correlation'',
    making the metric and values unreadable.'
- id: 554daa2db088
  severity: writing
  text: 'Figure 4: The legend at the top is not explicitly labeled as ''Models'' or
    ''Methods'', though the context implies it; adding a label would improve clarity.'
- id: ea016e63da22
  severity: writing
  text: 'Figure 5 caption contains a missing reference: ''all cases in .'' lacks the
    benchmark name (likely ''WBench'').'
- id: 59e7fcad495a
  severity: writing
  text: 'Figure 5 caption is incomplete: ''all cases in .'' should specify the dataset
    or benchmark name.'
- id: 70b22573c8e8
  severity: writing
  text: 'Figure 6: The caption claims ''Two categories per row are presented,'' but
    the layout displays four distinct categories per row (Nature, Urban, Indoor, Workspace
    in the top half; Fantasy, Sports in the bottom half), creating a direct contradiction
    between the text and the visual structure.'
- id: e65d30a52a17
  severity: writing
  text: 'Figure 6: The caption states each category is shown as a ''photorealistic/stylized
    pair,'' yet the ''Nature'' and ''Urban'' rows contain multiple disparate images
    (e.g., penguin, bamboo, city street, neon city) rather than a single paired comparison,
    making the description inaccurate for the majority of the content.'
- id: 087c6f2ecc12
  severity: science
  text: 'Figure 10: The caption claims to showcase ''same-subject switches, multi-subject
    switches, and scope-mode transitions,'' but the image only displays two examples
    (scope-to-FPP and FPP-to-FPP) and lacks the promised variety of sub-types.'
- id: 687c11351b7e
  severity: writing
  text: 'Figure 10: The text labels ''TPP -> FPP'', ''FPP -> FPP'', etc., are rendered
    at a resolution that is difficult to read and may be illegible in smaller formats.'
- id: d280ce74b440
  severity: writing
  text: 'Figure 12: The caption claims the figure shows distributions across ''direction,
    scene type, and control interface'', but the figure only displays distributions
    for ''direction'' (Atomic Distribution) and ''trajectory type'' (Trajectory/Mix
    Distribution). The ''scene type'' and ''control interface'' distributions mentioned
    in the caption are missing from the visual.'
- id: 52b3724819ed
  severity: writing
  text: 'Figure 12: The third subplot is labeled ''(b) Mix Distribution'', but it
    should be labeled ''(c)'' to follow the sequential ordering of (a) and (b) in
    the preceding subplots.'
- id: 1314ce22dee7
  severity: science
  text: 'Figure 12: The ''Atomic Distribution'' chart (a) labels segments with single
    letters (W, S, A, D) and directions (up, down, left, right) but does not explicitly
    state that these represent navigation key presses or actions, which is critical
    context for a ''navigation test case'' distribution.'
artifact_hash: 583182a56bc8cd93d801cd098b02d980b9a48cb375dac6cc8130da68f508615f
artifact_path: projects/PROJ-630-wbench-a-comprehensive-multi-turn-benchm/paper/metadata.json
backend: dartmouth
feedback: Vision review of 12 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T14:05:49.821121Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

Figure 1 provides a clear visual overview of the benchmark's components and taxonomy, but the caption contains significant text omissions (missing benchmark name) and the evaluation radar chart lacks a numerical scale.

### Figure 2

The figure effectively visualizes correlations and deviations, but the Z-score heatmap in panel (c) uses a color scale that clips extreme values, and the y-axis labels are illegible due to overlap.

### Figure 3

The figure effectively visualizes performance trends across turns, but the 'Perspective Switching' panel contains a confusing mismatch between the legend symbol and the plotted baseline data, and the caption lacks specific metric definitions.

### Figure 4

The figure effectively visualizes the correlation between human and automated scores with clear axes and a legend. However, the caption contains significant formatting errors where mathematical symbols and values are rendered as raw LaTeX code, obscuring the reported statistics.

### Figure 5

Figure 5 is a visually clear thumbnail gallery, but its caption is grammatically incomplete and missing the benchmark name after 'in', reducing clarity.

### Figure 6

The figure provides a clear visual gallery of scene types, but the caption is factually inconsistent with the layout, incorrectly describing the number of categories per row and the nature of the image pairs.

### Figure 7

Figure 7 effectively displays representative initial frames for the seven rendering styles listed in the caption (realistic, anime, cartoon, oil painting, ink wash, flat, and pencil sketch). The visual examples are clear, distinct, and directly support the claim of a style gallery.

### Figure 8

Figure 8 effectively illustrates the three perspective categories (disembodied first-person, embodied first-person, and third-person) with clear visual examples. The caption accurately describes the grouping and content, and the image is legible with no missing labels or controls.

### Figure 9

Figure 9 is a clear and well-organized gallery of images categorized by subject type (Human, Animal, Vehicle, Robot, Other). The visual layout effectively demonstrates the diversity of scenes and styles covered by the benchmark, and the caption accurately describes the content shown.

### Figure 10

The figure provides a visual example of perspective switching but fails to deliver the comprehensive taxonomy promised in the caption, showing only two cases instead of the three distinct sub-types described. Additionally, the text labels are somewhat small and could be improved for readability.

### Figure 11

Figure 11 effectively illustrates the navigation action definitions for both first-person and third-person perspectives. The visual mapping of WASD keys and arrow keys to physical camera movements is clear, and the caption provides necessary context regarding the source of the frames.

### Figure 12

The figure presents navigation action and trajectory distributions but fails to visualize the 'scene type' and 'control interface' distributions promised in the caption. Additionally, the third subplot has an incorrect label ('(b)' instead of '(c)'), and the first subplot lacks explicit context linking the labels to navigation controls.
