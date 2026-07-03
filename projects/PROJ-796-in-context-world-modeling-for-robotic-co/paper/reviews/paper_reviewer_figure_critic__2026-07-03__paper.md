---
action_items:
- id: 43804683338d
  severity: writing
  text: 'Figure 1: The ''OOD Viewpoint Shifts'' bar chart lacks a Y-axis label defining
    the metric (e.g., Success Rate), making the quantitative claims ambiguous.'
- id: 194b17e2a552
  severity: writing
  text: 'Figure 1: The ''Real World Experiments'' panel contains a text label ''6
    OOD Viewpoint'' that is not defined in the caption or legend.'
- id: b415caf1e6f7
  severity: science
  text: 'Figure 3: The caption claims the tasks are ''evaluated across six distinct
    camera viewpoints,'' but the figure only displays a ''Multi-Cam View'' and a ''Single
    Camera View'' without showing or labeling the six specific viewpoints mentioned.'
- id: bda44b999b12
  severity: writing
  text: 'Figure 3: The bottom section of the figure is partially obscured by large
    white blocks, cutting off the ''Single Camera View'' label and the associated
    image sequence, making the figure incomplete.'
- id: 1bbcd797c966
  severity: science
  text: 'Figure 4: The ''LONG'' subplot shows ''UNSEEN'' performance for MV, EXP,
    and ICWM that is higher than their ''SEEN'' performance, which contradicts the
    definition of ''Unseen (OOD)'' as a harder domain; verify if the x-axis labels
    are swapped or if the data is mislabeled.'
- id: 19c7af1b0c19
  severity: writing
  text: 'Figure 4: The ''LONG'' subplot''s ''UNSEEN'' group lacks the small baseline
    bars (pi-FAST, pi-0.5, NORA) visible in other subplots, making it unclear if they
    are zero or missing data.'
- id: be13b8a81fa7
  severity: writing
  text: 'Figure 5: The caption references items (a) and (b), but the figure uses numeric
    labels ''1'' and ''2'' instead; update the caption to match the figure or vice
    versa.'
- id: dda68700d132
  severity: writing
  text: 'Figure 5: The text ''Base:'' appears in the lower-left white space without
    any corresponding image or explanation, creating confusion.'
- id: 58e6572ee5b4
  severity: fatal
  text: 'Figure 6: The figure has no caption provided (''(no caption)''), making it
    impossible to verify what the t-SNE plots represent or what the numerical labels
    (e.g., 45, 135) signify.'
- id: d1855f5de188
  severity: science
  text: 'Figure 6: The x-axis scales differ between the ''Spatial'' (-75 to 75) and
    ''Object'' (-100 to 100) plots, which may mislead readers regarding the relative
    spread of the clusters without explicit normalization context.'
- id: 3c663a05bc0b
  severity: writing
  text: 'Figure 7: The caption ''Semantic perturbations'' is too vague and does not
    describe the specific experiments, metrics, or conditions shown in the bar charts.'
- id: 6b929b3a3fee
  severity: science
  text: 'Figure 7: The bar charts lack axis labels and units, making it impossible
    to determine what metric is being measured (e.g., success rate, error) or the
    scale of the values.'
- id: fac8e8b03290
  severity: science
  text: "Figure 7: The 'Morphology' section shows images of a robot with 'adding rigid\
    \ spacers' but the corresponding chart labels refer to '\u0394L' (length change),\
    \ creating a disconnect between the visual modification and the quantitative data."
- id: 8ca934d88147
  severity: writing
  text: 'Figure 8: The caption contains a grammatical error (''different setting''
    should be ''different settings'') and lacks specific details about the experimental
    conditions (e.g., hardware, model size) shown in the chart.'
- id: 22f4a229947c
  severity: science
  text: 'Figure 8: The x-axis label ''Inference Time Cost Per-step'' is ambiguous;
    it is unclear if the values represent wall-clock time or computational cost, and
    the unit ''s'' (seconds) is only shown inside the bars rather than on the axis.'
- id: 01932d2d1994
  severity: writing
  text: 'Figure 10: The caption lists percentages as ''100%, 90%, 80%, 70%'', but
    the image labels show ''Original Length'', ''70% Length'', ''90% Length'', and
    ''80% Length''. The order and inclusion of ''Original'' (vs 100%) are inconsistent
    between the text and the visual labels.'
- id: a802cfae1942
  severity: writing
  text: 'Figure 10: The caption contains a formatting artifact ''\100\%'' which should
    be corrected to ''100%'' for proper typesetting.'
- id: 36511f87c2ad
  severity: science
  text: 'Figure 11: The caption claims to illustrate ''robustness against object disturbances,''
    but the visualized trajectories show clean, successful executions without any
    visible perturbations or disturbances to the objects.'
- id: 3391aed99d39
  severity: writing
  text: 'Figure 11: The image contains three distinct task sequences (lifting, pick-and-place,
    stacking) labeled 1, 2, and 3, but the caption does not explicitly map these numbers
    to the specific tasks shown.'
- id: 3def8c001d53
  severity: fatal
  text: 'Figure 12: The caption is a placeholder (''Enter Caption'') and does not
    describe the content, making the figure''s purpose and the meaning of the labels
    ($o^s$, $o^e$) impossible to interpret.'
- id: 55349d3b270c
  severity: science
  text: 'Figure 12: The image consists of a grid of robot interaction pairs labeled
    $o^s$ and $o^e$ without any explanatory text or context, failing to communicate
    the scientific claim or comparison being illustrated.'
artifact_hash: 1607b7a56c94fa04d6447f07acdf09cff37e83d8d846355c78db174b7f1d3ac9
artifact_path: projects/PROJ-796-in-context-world-modeling-for-robotic-co/paper/metadata.json
backend: dartmouth
feedback: Vision review of 12 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T20:12:11.185312Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

Figure 1 effectively illustrates the conceptual framework of ICWM and the training pipeline, but the embedded quantitative charts lack necessary axis labels and definitions to fully support the visualized performance claims.

### Figure 2

Figure 2 provides a clear and well-structured overview of the ICWM training and inference pipeline. The diagram effectively visualizes the flow from self-exploration to the Pretrained VLM, with distinct sections for training and inference that align perfectly with the provided caption.

### Figure 3

The figure illustrates the task suite but is visually incomplete due to white blocks obscuring the bottom section. Additionally, the caption's claim of six distinct viewpoints is not visually supported by the provided panels.

### Figure 4

The figure is visually clear but contains a likely data labeling error in the 'LONG' subplot where unseen performance exceeds seen performance, and missing baseline data points for the 'UNSEEN' group in that same subplot.

### Figure 5

The figure effectively illustrates the qualitative differences between the baseline and the proposed method, but the caption's use of (a)/(b) does not match the figure's numeric labels (1/2), and there is unexplained text ('Base:') in the empty space below.

### Figure 6

The figure displays t-SNE visualizations but lacks a caption entirely, preventing verification of the data source or the meaning of the labels. Additionally, the differing axis scales between the two subplots could be misleading without further explanation.

### Figure 7

Figure 7 presents bar charts comparing methods under different conditions but fails to label axes or units, and the caption is insufficient to explain the semantic perturbations or the specific metrics being evaluated.

### Figure 8

The bar chart clearly displays inference times for different shot settings, but the caption is grammatically incorrect and lacks necessary experimental context, while the axis labeling is slightly ambiguous regarding units.

### Figure 9

Figure 9 effectively visualizes four distinct robotic manipulation tasks in simulation, with clear panel labels and descriptive titles for each sequence. The images are legible, and the caption accurately reflects the content shown, supporting the claim of successful multi-stage execution.

### Figure 10

The figure effectively visualizes the morphological changes, but the caption text is inconsistent with the image labels regarding the specific percentage values and their order, and contains a minor LaTeX formatting artifact.

### Figure 11

The figure displays successful real-robot trajectories for three tasks, but the claim of demonstrating robustness against object disturbances is unsupported by the visual evidence, which shows no perturbations.

### Figure 12

The figure displays a grid of robot interaction pairs but is rendered useless by a placeholder caption ('Enter Caption') that fails to explain the content or the meaning of the labels.
