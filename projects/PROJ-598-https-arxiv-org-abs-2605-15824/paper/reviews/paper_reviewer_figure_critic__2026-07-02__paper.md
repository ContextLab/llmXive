---
action_items:
- id: 951a2c921300
  severity: writing
  text: 'Figure 1: The caption contains a grammatical error (''Overall pipeline of
    :'') where the model name is missing, likely due to a formatting placeholder.'
- id: b660503c34bb
  severity: writing
  text: 'Figure 1: The ''Legends'' box uses icons (flame, snowflake) that are not
    explicitly defined in the legend text itself, relying on the viewer to infer ''Trainable''
    and ''Frozen'' from the icons alone.'
- id: b0a3b8f81a48
  severity: writing
  text: 'Figure 2: The right panel''s x-axis labels (''Reference'', ''Garment'', ''History'')
    are ambiguous and do not match the caption''s description of ''historical and
    conditional KV''; clarify what each block represents.'
- id: '693429032252'
  severity: science
  text: "Figure 2: The right panel's colorbar scale (0.000\u20130.0003) is extremely\
    \ low and lacks context; without normalization or comparison to baseline attention\
    \ values, the claim that 'the model attends more to historical KV' is not visually\
    \ substantiated."
- id: 4b1183ca4252
  severity: writing
  text: 'Figure 3: The column headers use inconsistent naming conventions, mixing
    method names with parameter counts (e.g., ''Ours(5B)'', ''Edit(20B)+I2V(5B)'',
    ''Phantom(1.3B)'') without defining what the numbers in parentheses represent
    in the caption or figure.'
- id: 8c0052f3bee8
  severity: writing
  text: 'Figure 3: The caption states ''Qualitative comparison of our with other baselines''
    but contains a grammatical error (''of our'') and fails to explicitly name the
    proposed method (''FashionChameleon'') in the text.'
- id: b3f9aac9ffc4
  severity: science
  text: 'Figure 5: The top row (Native DMD vs. Gradient-Reweighted DMD) shows a static
    scene with no motion, contradicting the caption''s claim that Gradient-Reweighted
    DMD ''alleviates motion collapse during extrapolation''; the visual evidence does
    not support the stated ablation claim.'
- id: e1455e3b7fa2
  severity: writing
  text: 'Figure 5: The bottom row labels (''Random Reference'', ''Reference KV w/o
    Disentangle'', ''Reference KV Disentangle'') are not clearly aligned with the
    image columns, making it difficult to distinguish which method corresponds to
    which result.'
- id: 92e11c123761
  severity: writing
  text: 'Figure 6: The caption contains a placeholder ''of .'' instead of the paper
    title ''FashionChameleon''.'
- id: f1e9b5960721
  severity: writing
  text: 'Figure 6: The top-left section lists filtering criteria (e.g., ''Transition
    Abruptly'', ''No Human'') but lacks a legend or label explicitly identifying this
    block as Stage 1, unlike the other three stages which have clear titles.'
- id: 37ff1443bf0b
  severity: writing
  text: 'Figure 7: The caption for (c) states that each sample comprises a reference
    image, a garment image, and an input prompt, but the rendered image only shows
    the images; the input prompt text is missing from the visual layout.'
- id: de29999c0fec
  severity: writing
  text: 'Figure 7: The bar chart in (b) displays percentage values (e.g., ''29.6%'')
    on top of the bars, but the y-axis is labeled ''Count'', creating a contradiction
    between the axis label and the data labels.'
- id: ea3308b468e5
  severity: science
  text: 'Figure 8: The stacked bars sum to 100% but the caption claims they show ''human
    preference rates'' without clarifying if this is a ''win rate'' in pairwise comparisons
    or a normalized distribution; the lack of a y-axis scale or total count makes
    the statistical significance of the ''superior'' rates (e.g., 44%) ambiguous.'
- id: 7d280a676b3a
  severity: writing
  text: 'Figure 8: The legend at the top is cluttered and uses inconsistent formatting
    for model names (e.g., ''Edit(20B)+I2V(5B)'' vs ''Phantom-1.3b''), and the color
    mapping for ''Phantom-1.3b'' (light blue) is visually indistinguishable from ''Edit(20B)+I2V(5B)''
    (darker blue) in the bars, risking misinterpretation.'
artifact_hash: 8ac732f80d31fee19845b13e35eb49deeae5414cb6cb993b15f1b25017de2aa1
artifact_path: projects/PROJ-598-https-arxiv-org-abs-2605-15824/paper/metadata.json
backend: dartmouth
feedback: Vision review of 8 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T02:02:51.813219Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

Figure 1 provides a clear and comprehensive visual overview of the three main pipeline components. However, the caption contains a missing model name, and the legend relies on icons without explicit text definitions for the symbols.

### Figure 2

Figure 2 effectively illustrates garment switching but the attention map on the right suffers from ambiguous axis labels and a color scale that is too low to meaningfully support the caption's claim about attention distribution.

### Figure 3

The figure effectively displays qualitative results comparing the proposed method against several baselines, but the column headers are inconsistently formatted with undefined parameter counts, and the caption contains a grammatical error and omits the method's name.

### Figure 4

Figure 4 effectively demonstrates the model's capabilities in long-video extrapolation and interactive multi-garment customization. The visual layout is clear, with distinct rows for different tasks and explicit 'Switch' indicators that align perfectly with the caption's description.

### Figure 5

The figure presents a qualitative ablation but fails to visually demonstrate the claimed 'motion collapse' in the top row, and the bottom row labels are ambiguously aligned with the results.

### Figure 6

The figure effectively visualizes the four-stage data curation pipeline with clear icons and flow, but the caption contains a placeholder error ('of .') and the first stage lacks an explicit title label compared to the others.

### Figure 7

Figure 7 effectively visualizes data diversity and distribution, but the bar chart contains a labeling contradiction between the 'Count' y-axis and percentage data labels, and the representative sample panel omits the input prompt text described in the caption.

### Figure 8

Figure 8 presents a stacked bar chart of human evaluation results, but the lack of a y-axis and ambiguous definition of 'preference rates' obscures the statistical context. Additionally, the legend's color coding for similar blue shades is difficult to distinguish in the bars.
