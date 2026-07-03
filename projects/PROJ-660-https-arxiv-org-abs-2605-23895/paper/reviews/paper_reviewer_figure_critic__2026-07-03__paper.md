---
action_items:
- id: 77882f693ff1
  severity: science
  text: 'Figure 3: The caption describes the figure as showing ''regions discovered
    by BrainCause'' and ''regions discovered by an activation-based method'' (implying
    brain maps), but the rendered image displays generated images (e.g., ''Market
    to mountains'', ''Pizza'') with numerical scores. The visual content does not
    match the caption''s description of the data type.'
- id: e76af51e9c9a
  severity: science
  text: 'Figure 3: The caption states the figure shows ''high activation'' and ''lower
    activation'', but the image displays numerical values (e.g., +1.72, -0.26) without
    specifying the metric (e.g., correlation, z-score, log-odds) or units, making
    the magnitude of ''activation'' uninterpretable.'
- id: c81f5c582ae9
  severity: writing
  text: 'Figure 3: The ''Semantic negatives'' row in the top section contains images
    (e.g., sleeping person, office desk) that do not visually correspond to the ''Market
    to mountains'' or ''Party to empty room'' causal edit pairs above them, making
    the relationship between the positive and negative examples unclear.'
- id: 33a18fcdb9b6
  severity: science
  text: 'Figure 4: The caption claims the figure shows ''Causal ranking reduces false
    discoveries'' and compares BrainCause to activation-based methods, but the plot
    axes are labeled ''Activation Train Score'' and ''Causality Train Score'' (training
    metrics) rather than evaluation metrics. Furthermore, the plot displays raw scatter
    points without any ''ranking'' visualization (e.g., a curve or threshold line)
    to demonstrate the reduction of false positives.'
- id: 066e51121b2a
  severity: writing
  text: 'Figure 4: The x-axis label in panel (a) is ''Activation Train Score'' while
    panel (b) is ''Causality Train Score'', yet the y-axis is ''Causality Eval Score''
    for both. This inconsistency in axis labeling (Train vs Eval) makes it unclear
    if the comparison is between training performance or evaluation performance.'
- id: 8a44b9c40629
  severity: writing
  text: 'Figure 5: The caption states ''three example concepts'' are shown, but the
    image displays three columns labeled ''Animal Face'', ''Food'', and ''Tool'' without
    explicitly defining these as the specific concepts in the text.'
- id: 6f05c24ce314
  severity: writing
  text: 'Figure 5: The caption mentions ''warmer colors indicate higher concept-specific
    causal evidence'', but no colorbar or scale is provided to quantify the causal
    score values.'
- id: afcd87be0d46
  severity: writing
  text: 'Figure 6: The figure displays six brain maps corresponding to six concepts
    (Human Leg, Human Hand, Human Face, Symbolic Signs, Logo, Handwritten Text), but
    the caption only lists the concepts in text without explicitly mapping them to
    the specific panels (Left vs. Right) or providing a clear legend linking the top
    images to the bottom maps.'
- id: '625745895794'
  severity: writing
  text: 'Figure 6: The brain maps lack a colorbar or legend indicating the scale of
    the ''causal scores'' or activation levels, making it impossible to determine
    the magnitude of the colored regions relative to the background.'
- id: 1ea352f32e7a
  severity: writing
  text: 'Figure 7: The text labels for the visual regions (e.g., ''OPA'', ''EBA'',
    ''VWFA-1'') are extremely small and low-contrast against the background, making
    them illegible in the rendered image.'
- id: 19fcfb211702
  severity: writing
  text: 'Figure 7: The colorbar or scale indicating the specific range of ''causal
    scores'' is missing; the caption describes warmer colors as higher evidence but
    provides no quantitative reference.'
- id: 20d9805d4d3a
  severity: writing
  text: 'Figure 8: The row labels ''Activation Score'' and ''Causal Score'' are rotated
    90 degrees and placed outside the plot area, making them difficult to read and
    visually disconnected from the data rows.'
- id: a699a76d50b0
  severity: writing
  text: 'Figure 8: The brain flatmaps contain numerous small text labels (e.g., ''OPA'',
    ''EBA'', ''VWFA-1'') that are illegible at the current resolution, hindering the
    ability to verify the caption''s claim about specific region suppression.'
- id: 418678f3dc6b
  severity: writing
  text: 'Figure 9: The top histogram''s x-axis label (''# Positive Examples per Target
    Concept'') and the bottom-left''s (''# Negative Examples per Target Concept'')
    are ambiguous; the caption states these counts are ''For each target concept,''
    implying the x-axis should represent the count value (bin) and the y-axis the
    number of concepts, but the labels could be misread as the x-axis being the concepts
    themselves. Clarify axis labels to ''Count of Examples'' (x) and ''# of Target
    Concepts'' (y) for precision.'
- id: 5c25c87a2add
  severity: writing
  text: 'Figure 9: The bottom-right plot''s x-axis label (''# Successfully Retrieved
    Images per Semantic-Negative'') is slightly confusing given the y-axis is ''#
    Semantic Negatives''; it implies the x-axis is the number of images retrieved
    for a single negative, but the caption says ''for each target--negative pair''.
    While likely correct, the label could be clearer, e.g., ''# Retrieved Images per
    Pair''.'
- id: 9d691564214a
  severity: science
  text: 'Figure 10: The caption claims these are ''semantic negatives'' that failed
    to exclude the target concept, but the images shown (e.g., ''Sky'', ''Reflection'')
    appear to be standard, high-quality photographs of the target concepts themselves
    rather than generated images containing artifacts or failures. It is unclear if
    these are the ''generated'' images or the ''positive'' ground truth used for comparison,
    making the ''failure'' claim visually unsubstantiated.'
- id: 7ea90c92bed3
  severity: writing
  text: 'Figure 10: The row labels (''Image with lighting contrast'', ''Sky'', ''Image
    with reflection'') are rotated 90 degrees and placed on the far left, which is
    a poor layout choice that makes them difficult to read and visually disconnected
    from the specific images they describe.'
- id: f482aa72d41f
  severity: science
  text: 'Figure 11: The caption claims histograms show p-values for ''five validation
    criteria,'' but only five subplots are shown without labels identifying which
    criterion corresponds to which plot, making it impossible to verify the claim
    or interpret the results.'
- id: 6f341c07e49c
  severity: writing
  text: 'Figure 11: The y-axis label ''# Concepts'' is present on the first subplot
    but missing from the other four, creating visual inconsistency and potential confusion
    about whether all plots share the same metric.'
- id: a7b182315cb3
  severity: science
  text: 'Figure 12: The maps lack a colorbar or legend defining the binary scale (e.g.,
    0 vs 1 or ''negative'' vs ''positive''), making it impossible to distinguish the
    background from the active voxels without relying on the caption.'
- id: 770ac36f3bc5
  severity: science
  text: 'Figure 12: The brain maps are unlabeled; there are no axis ticks, anatomical
    landmarks, or ROI outlines (unlike Figure 5) to identify the specific cortical
    regions shown.'
artifact_hash: 3e7821bc4196322444417ea380054aced908f7d581b2fd2f7cbee1140a5fd1b0
artifact_path: projects/PROJ-660-https-arxiv-org-abs-2605-23895/paper/metadata.json
backend: dartmouth
feedback: Vision review of 12 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T16:29:01.887846Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

Figure 1 effectively communicates the conceptual difference between prior activation-based methods and the proposed BrainCause approach. The visual flow from counterfactual generation to causal evaluation is clear, and the caption accurately describes the logic of distinguishing false positives from true causal regions.

### Figure 2

Figure 2 is a clear and well-structured pipeline diagram that effectively visualizes the data generation process described in the caption. All components, including the specific models used (Gemma, Flux, Qwen) and the three stimulus categories, are explicitly labeled and easy to follow.

### Figure 3

The figure content (generated images with scores) fundamentally contradicts the caption's description (brain regions/activation maps). Additionally, the specific metric for the displayed numerical scores is undefined, and the semantic negative examples lack clear visual correspondence to their paired positive stimuli.

### Figure 4

The figure displays scatter plots of training scores versus evaluation scores but fails to visually demonstrate the 'ranking' or 'reduction of false discoveries' claimed in the caption. Additionally, the axis labels are inconsistent between panels and do not clearly support the evaluation-focused claim.

### Figure 5

The figure effectively visualizes concept-specific causal scores on brain flatmaps with clear ROI outlines, but it lacks a colorbar to quantify the score values and the specific concept names are only implied by column headers rather than explicitly defined in the caption.

### Figure 6

The figure effectively visualizes distinct voxel patterns for body and text concepts, but it lacks a colorbar to quantify the displayed scores and the caption does not explicitly link the specific concept images to their corresponding brain map panels.

### Figure 7

The figure effectively demonstrates cross-subject consistency with clear layout and representative images, but the internal anatomical labels are illegible and the absence of a color scale prevents quantitative interpretation of the causal scores.

### Figure 8

The figure effectively illustrates the contrast between broad activation patterns and selective causal maps, but the rotated row labels and illegible ROI text annotations significantly reduce readability and interpretability.

### Figure 9

Figure 9 effectively visualizes the dataset coverage with clear histograms, but the x-axis labels on the top and bottom-left plots are slightly ambiguous regarding whether they represent the count value or the concept identifier, and the bottom-right x-axis label could be more precise about the 'pair' unit.

### Figure 10

The figure attempts to show failure cases in semantic-negative generation but lacks visual evidence of generation artifacts, presenting what appear to be standard photographs instead. Additionally, the rotated row labels on the left margin are difficult to read and poorly integrated with the image grid.

### Figure 11

Figure 11 presents five p-value histograms as described, but fails to label which of the five 'validation criteria' each subplot represents, undermining interpretability. Additionally, the y-axis label is inconsistently applied across subplots.

### Figure 12

The figure illustrates distinct spatial patterns for action concepts but lacks essential annotation, including a legend for the binary maps and anatomical labels for the brain regions.
