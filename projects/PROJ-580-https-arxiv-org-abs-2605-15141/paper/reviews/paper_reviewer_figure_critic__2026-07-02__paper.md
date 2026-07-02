---
action_items:
- id: 1cc89510075b
  severity: science
  text: 'Figure 1: The caption claims ''causal ODE suffers from scene collapse,''
    but the corresponding images (top row, right) show a coherent scene with a mouse
    and treadmill, contradicting the description of collapse.'
- id: 894136f90a62
  severity: science
  text: "Figure 1: The caption claims 'causal DMD blurs the mouse\u2019s legs into\
    \ a single indistinguishable mass,' but the corresponding images (bottom row,\
    \ right) show distinct legs and clear motion, contradicting the description."
- id: be4b8acbb0f9
  severity: science
  text: 'Figure 2: The caption describes a single action (''moving forward continuously''),
    but the image displays a sequence of 8 distinct video frames. Without a time axis,
    frame indices, or a legend, it is impossible to verify the continuity of motion
    or the temporal resolution of the generation.'
- id: 424a9e654720
  severity: writing
  text: 'Figure 2: The image contains a ''W'' icon and ''A S D'' keyboard keys overlaid
    on the scene. These UI elements are not defined in the caption or legend, making
    it unclear if they represent the input control signal or are artifacts of the
    rendering engine.'
- id: b99b187725c4
  severity: science
  text: 'Figure 3: The ''Before asymmetric DMD'' images show a man in water, while
    the ''After'' images show a snowboarder; the caption claims ''better visual quality''
    but the visual content is completely different, making a direct quality comparison
    impossible.'
- id: 1febce22f18b
  severity: science
  text: 'Figure 3: The bar charts show VBench scores, but the y-axis scales are truncated
    (78-82 and 83-83.5) without a break indicator, exaggerating the performance difference
    between Causal CD and Causal ODE.'
- id: 6fce5d160df3
  severity: science
  text: "Figure 4: The caption claims 'Causal DMD yields lower VBench scores than\
    \ causal CD', but the bar charts compare 'Causal CD' vs 'Causal DMD' (left) and\
    \ 'Causal CD Init.' vs 'Causal DMD Init.' (right). The right chart's legend labels\
    \ ('Causal CD Init.', 'Causal DMD Init.') do not match the caption's description\
    \ of 'used as the initialization for Stage 3' \u2014 it is unclear if these are\
    \ initialization methods or results after Stage 3. This creates ambiguity in interpreting\
    \ the comparison."
- id: 3602c3932a90
  severity: writing
  text: "Figure 4: The y-axis labels on both bar charts lack units or context (e.g.,\
    \ 'VBench score (%)'), making it unclear what the numerical values represent despite\
    \ the x-axis label 'VBench \u2191'."
- id: 46823eb53fe6
  severity: science
  text: 'Figure 5: The caption claims ''Causal Forcing''s causal ODE initialization
    performs well,'' but the figure''s third column is labeled ''DMD after Casual
    Forcing ODE initialization'' (typo: ''Casual'' vs ''Causal'') and the bottom text
    states it ''requires costly data curation,'' which contradicts the caption''s
    claim that it is ''difficult to scale'' due to cost rather than data curation
    requirements.'
- id: 06c85d40d0b2
  severity: writing
  text: 'Figure 5: The bottom text labels contain typos (''Casual'' instead of ''Causal'')
    and the red text ''costly data curation'' is not explicitly defined in the caption,
    creating ambiguity about the specific cost factor.'
- id: d2bd49567366
  severity: writing
  text: 'Figure 6 caption: The phrase ''reduces training cost by 4$$'' contains a
    typo (likely meant ''4x'') that contradicts the ''4x'' label shown in the chart.'
- id: 80ea5b4bbee0
  severity: writing
  text: 'Figure 6 caption: The claim of ''50% lower latency'' is imprecise; the chart
    shows a reduction from 0.6 to 0.27, which is a 55% reduction.'
- id: 2cba19768e01
  severity: writing
  text: 'Figure 7: The label ''Causal Forcing ++ (1-step)'' is visually ambiguous;
    the caption claims the method ''surpasses Causal Forcing'', but the image shows
    the 1-step variant performing worse than the 2-step and 4-step variants, creating
    a potential contradiction between the specific visual evidence and the general
    claim.'
- id: ac9de7c4cd4c
  severity: writing
  text: 'Figure 7: The caption states the figure is a ''Performance comparison'',
    but the image contains no quantitative metrics (e.g., VBench scores, FID, latency
    numbers) or axes; it relies entirely on subjective visual inspection without providing
    the data to support the ''outperforming'' claim.'
artifact_hash: bc6ea3b7abb50e6d2d0c61521fe88f76d18733e7f3e4d74c5eba9d5fe9acb8e6
artifact_path: projects/PROJ-580-https-arxiv-org-abs-2605-15141/paper/metadata.json
backend: dartmouth
feedback: Vision review of 7 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:58:57.270493Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

The figure displays four initialization methods, but the visual evidence in the 'causal ODE' and 'causal DMD' panels directly contradicts the specific failure modes described in the caption.

### Figure 2

The figure displays a sequence of frames for a 'moving forward' action but lacks necessary temporal labels or a legend to interpret the overlaid UI controls (W, A, S, D), making the visualization ambiguous.

### Figure 3

The figure attempts to compare Causal CD and Causal ODE but fails to do so visually by showing completely different video content (water vs. snow) in the 'Before' and 'After' panels, and uses truncated y-axes that exaggerate score differences.

### Figure 4

Figure 4 presents bar charts comparing VBench scores but suffers from ambiguous legend labeling that conflicts with the caption’s description of initialization stages, and lacks explicit units on the y-axis despite referencing a benchmark metric.

### Figure 5

The figure effectively visualizes the degradation of different initialization methods, but contains a significant typo ('Casual' vs 'Causal') in the third column label and bottom text, and the caption's description of the cost factor ('difficult to scale') conflicts with the figure's specific claim of 'costly data curation'.

### Figure 6

Figure 6 effectively visualizes the framework evolution and performance metrics, but the caption contains a typo ('4$$' instead of '4x') and a slightly inaccurate percentage claim regarding latency reduction.

### Figure 7

The figure provides a qualitative visual comparison of video generation methods but lacks the quantitative metrics promised by the caption's 'Performance comparison' description. Additionally, the claim that the method 'surpasses Causal Forcing' is visually contradicted by the 1-step variant shown, which appears inferior to the multi-step variants.
