---
action_items:
- id: 590444dc5bc5
  severity: writing
  text: 'Figure 1: The caption contains a typo (''capabilitie'' instead of ''capabilities'').'
- id: 93cdc18bb595
  severity: writing
  text: 'Figure 1: The caption text is not fully legible in the rendered image due
    to low resolution.'
- id: d9c625e4616d
  severity: writing
  text: 'Figure 2: The caption text ''new_main_newnane.pdf'' appears to be a filename
    artifact rather than a proper description.'
- id: ee4928435b91
  severity: science
  text: 'Figure 2: The diagram shows ''Mini-Omni3'' and ''SoundStream'' as examples
    but does not clearly distinguish which parts represent the proposed Audio-Interaction
    model versus existing systems being compared.'
- id: 4795615301b9
  severity: science
  text: 'Figure 3: The caption describes a ''training framework'' with ''supervision
    signals'' and ''streaming training strategy,'' but the figure depicts an inference
    pipeline (input audio -> encoder -> adapter -> response generation) without showing
    loss functions, gradients, or training-specific components.'
- id: 1288940d33cd
  severity: writing
  text: "Figure 3: The text 'Audio-Interaction' and 'Adapter' are accompanied by fire\
    \ emojis (\U0001F525) which are undefined in the caption or legend, creating ambiguity\
    \ about whether they denote specific model components, training phases, or are\
    \ merely decorative."
- id: 63cb7dcfd338
  severity: writing
  text: 'Figure 3: The diagram shows specific text inputs (e.g., ''What is your name?'',
    ''Count only upon hearing a dog bark'') but lacks a clear legend explaining the
    color coding of the output blocks (orange vs. green) or the meaning of the ''<Silent>''
    vs ''<Res>'' tokens.'
- id: 5b5a678c9ece
  severity: writing
  text: 'Figure 4: The text ''2.4M source dataitem'' in the Data collection panel
    contains a typo and should be ''data items''.'
- id: 90cf98ab7336
  severity: writing
  text: 'Figure 4: The ''Preprocessing'' panel contains illegible text inside the
    ''ASR checking'' box due to low resolution.'
- id: dea204dcd82a
  severity: science
  text: 'Figure 5: The caption claims to show ''(c) Statistics of source data'', but
    the rendered figure only contains the taxonomy chart (a) and the round distribution/tokens/silence
    plots (b); the source data statistics are missing.'
- id: 35c217eae436
  severity: writing
  text: 'Figure 5: The legend for the top-right line chart (''Rounds distribution'')
    is placed outside the plot area without clear visual grouping, making it difficult
    to associate with the specific data series.'
- id: e1ef16e1d84c
  severity: science
  text: 'Figure 6: The x-axis labels ''Encoder'' and ''Projector'' are positioned
    under the first two data points, but the caption claims ''GPT Layer 0 alone recovers
    most of the continuity.'' The graph shows the massive jump occurs at ''L0'', yet
    the visual grouping of ''Encoder'' and ''Projector'' in the shaded regions suggests
    they are the primary stages, potentially obscuring the specific contribution of
    the projector versus the encoder as described in the text.'
- id: 21ecbc674b4e
  severity: writing
  text: 'Figure 6: The x-axis labels ''Encoder'' and ''Projector'' are rotated 45
    degrees and overlap significantly with the ''L0'' label, reducing legibility.'
- id: 611341ede7d6
  severity: writing
  text: 'Figure 7: The caption describes the plot as showing ''cross-chunk continuity
    ratio'', but the y-axis label reads ''Continuity Ratio (boundary / internal)'',
    which is a specific metric definition not explained in the caption.'
- id: b3526239d683
  severity: writing
  text: 'Figure 7: The x-axis labels ''Encoder'' and ''Projector'' are ambiguous regarding
    the specific layer indices they represent compared to the ''L0'' through ''L35''
    sequence, and the caption does not clarify if these correspond to specific layers
    or blocks.'
- id: 772f0f532d7c
  severity: science
  text: 'Figure 8: The caption claims to report ''end-to-end latency'', but the third
    subplot (right) displays ''Response Trigger Token Acc (%)'' on the y-axis. The
    figure fails to visualize the metric described in the text.'
- id: e66519b83e19
  severity: writing
  text: 'Figure 8: The legend in the rightmost subplot lists ''Ours (w/o Streaming
    Loss)'', whereas the legends in the left and middle subplots list ''Baseline''.
    This inconsistency in naming conventions across the panels is confusing.'
- id: 51e7160aaedd
  severity: science
  text: "Figure 9: The caption claims the second case study shows Audio-Interaction\
    \ handling the 'audio cue directly' while others rely on transcription, but the\
    \ 'Sound Events' row explicitly lists '<Sound effect - Cat> \U0001F431 <End>'\
    \ as a recognized event. This implies the baseline models also have access to\
    \ the audio cue, contradicting the caption's narrative that they only detect the\
    \ cat via transcribed words."
- id: d3dd17eb2719
  severity: writing
  text: 'Figure 9: The ''TRIGGERED / RESPONSE ACC'' column header is ambiguous; it
    is unclear if the two values (e.g., 100.0% / 100.0%) represent Trigger Accuracy
    and Response Accuracy respectively, or if they refer to different metrics entirely.
    A legend or explicit definition is missing.'
- id: d2da8880fcd3
  severity: writing
  text: 'Figure 10: The caption ''Case study: Home'' is insufficient for a complex
    timeline visualization; it should describe the specific scenario (e.g., ''Weekend
    Childcare'') and the model''s multi-modal responses shown.'
- id: 07795c33cad0
  severity: writing
  text: 'Figure 10: The legend at the bottom lists ''Real-time ASR'' and ''Instruction
    Following'' as task categories, but the timeline does not explicitly label any
    segments with these specific tags, creating ambiguity about which interactions
    fall under these definitions.'
- id: 1fd3ad66617b
  severity: fatal
  text: 'Figure 12: The caption is a placeholder (''Enter Caption'') and does not
    describe the figure''s content, making it impossible to verify if the chart supports
    the paper''s claims.'
- id: 01239c5c5583
  severity: science
  text: 'Figure 12: The x-axis labels (e.g., ''Daily Affairs'', ''House Equipment
    States'') do not match the legend categories (e.g., ''Daily Living'', ''Human''),
    creating a disconnect between the data points and their defined groups.'
- id: 4304ae17ea58
  severity: writing
  text: 'Figure 12: The x-axis labels are rotated at a steep angle, causing significant
    overlap and reducing legibility for labels like ''Ecological & Biological Context''.'
artifact_hash: d722b827ffcc42ef33cad3308518a181a01c5d135cbbac51efaf0289e64033d0
artifact_path: projects/PROJ-666-https-arxiv-org-abs-2606-05121/paper/metadata.json
backend: dartmouth
feedback: Vision review of 12 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T00:14:14.198384Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

The figure effectively illustrates the model's capabilities with clear visual examples, but the caption contains a typo and is difficult to read in the provided image.

### Figure 2

Figure 2 effectively illustrates the concept of continuous audio interaction but has a caption filename artifact and could more clearly distinguish between the proposed model and existing systems being compared.

### Figure 3

The figure illustrates an inference pipeline but the caption claims it is a training framework, creating a fundamental mismatch. Additionally, key visual elements like fire emojis and color-coded blocks lack definitions in the caption or legend.

### Figure 4

The figure provides a clear visual overview of the StreamAudio-2M dataset pipeline, but contains minor text quality issues including a typo ('dataitem') and illegible labels in the preprocessing section.

### Figure 5

The figure effectively visualizes the capability taxonomy and task statistics, but it fails to include the source data statistics mentioned in the caption, and the legend for the line chart is somewhat disconnected from the plot.

### Figure 6

The figure effectively visualizes the continuity ratio across stages, but the x-axis labels for the initial stages are cluttered and overlap with the first layer label. Additionally, the caption's claim about the projector's minimal impact is visually supported but the axis labeling makes it slightly difficult to distinguish the exact transition point between the projector and the first GPT layer.

### Figure 7

The figure is visually clear and the legend is well-defined, but the caption fails to explain the specific 'boundary / internal' metric shown on the y-axis and does not clarify the x-axis mapping for the initial components.

### Figure 8

The figure effectively visualizes capability stability for MMAU and Dialogue accuracy, but the third subplot contradicts the caption by showing Response Trigger Token Accuracy instead of the promised end-to-end latency. Additionally, the legend naming is inconsistent across the three subplots.

### Figure 9

The figure presents a clear comparison of model outputs, but the caption's claim that baseline models fail to detect the audio cue directly is contradicted by the 'Sound Events' row which shows the cue was recognized. Additionally, the accuracy column lacks a clear definition for its two distinct percentage values.

### Figure 10

The figure effectively visualizes a complex 30-second audio interaction scenario with clear temporal alignment between audio events and model responses. However, the caption is too brief to stand alone, and the legend includes categories that are not explicitly mapped to specific events in the timeline.

### Figure 11

Figure 11 is a clear and well-structured case study visualization that effectively maps a continuous audio stream to specific user interactions and model responses. The timeline, spectrogram, and task category legend are all legible and consistent with the provided caption.

### Figure 12

The figure displays a bar chart of audio category distribution, but the caption is a placeholder and the x-axis labels are illegible due to rotation and overlap. Furthermore, the specific categories on the x-axis do not align with the broader groups defined in the legend.
