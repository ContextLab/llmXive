---
action_items:
- id: 4308587d3481
  severity: fatal
  text: 'Figure 1: The caption filename ''[Figure2.pdf]'' contradicts the label ''Figure
    1'' and the content, which matches the description of Figure 2 in the provided
    caption list (turning clean QA into resilience tests).'
- id: fcc6721b05e6
  severity: science
  text: 'Figure 1: The ''Injection Sentence'' box contains a specific medical claim
    (''lesions under 1.2 mm require... no lymph node evaluation'') that is not defined
    or sourced in the caption, making the ''Authority'' provenance claim unverifiable.'
- id: a8a2549c5a12
  severity: science
  text: 'Figure 2: The workflow diagram displays numbered steps 1, 2, and 4, but Step
    3 (''Taxonomy Generation & Attack Creation'') is positioned below the main flow
    without a connecting arrow, obscuring the logical sequence of the pipeline.'
- id: ed76dd8e4294
  severity: writing
  text: 'Figure 2: The caption refers to ''Figure1.pdf'' in brackets, which contradicts
    the figure label ''Figure 2'' and suggests a file naming or cross-reference error.'
- id: d4fa4ccab65d
  severity: science
  text: 'Figure 3: The caption claims ''Clean accuracy overstates epistemic resilience''
    and cites a drop to 38.0% under Type 1, but the chart shows Type 1 (red bars)
    varies wildly by model (e.g., 29.9% for Gemini-3.1-pro vs 54.0% for GPT-5.4).
    The 38.0% value is an aggregate mean not explicitly labeled as such on the chart,
    making the claim misleading without a clear ''mean'' bar or annotation for Type
    1.'
- id: 563dc2750be0
  severity: writing
  text: 'Figure 3: The x-axis labels are cluttered and inconsistent; some models have
    sub-labels like ''high'', ''median'', ''low'', ''none'', ''medium'', ''minimal''
    while others do not, and the meaning of these sub-labels is undefined in the caption
    or legend.'
- id: 7d444c840f57
  severity: writing
  text: 'Figure 3: The legend defines ''mean reference'' as a dashed line, but there
    are three horizontal dashed lines (blue, green, red) with no legend entry explaining
    which corresponds to which mean (clean, Type 1, Type 2), despite the caption mentioning
    all three values.'
- id: 3681b444a312
  severity: fatal
  text: 'Figure 4: The caption cites ''Figure5.pdf'' instead of the correct file name
    ''Figure4.pdf''.'
- id: a6edf805c8df
  severity: science
  text: 'Figure 4: The legend defines ''gap'' as a solid line, but the plot uses solid
    lines to connect paired data points (T2/T1) for each model rather than representing
    a ''gap'' metric.'
- id: 53878cd63f24
  severity: writing
  text: 'Figure 4: The legend entry ''T2 all-option ASR'' is ambiguous; the plot shows
    blue circles for T2, but the label does not clarify if this represents the mean
    or individual data points.'
- id: 78260b4bd819
  severity: science
  text: 'Figure 5: The image displays a single case (MEDMISMCQA) with a ''Neutral
    False Statement'' injection, but the caption claims to show ''Rubric A/B controls''
    which are not visible in the provided screenshot.'
- id: 60685d10ebc9
  severity: writing
  text: 'Figure 5: The image is a screenshot of a UI rather than a rendered figure;
    the ''Provenance vehicle'' and ''Misinformation type'' sections appear to be metadata
    definitions rather than the actual ''injected context'' or ''model output'' mentioned
    in the caption.'
- id: 49abe4fbd9ff
  severity: science
  text: 'Figure 6: The x-axis is labeled ''Attack success rate (%)'' but the data
    points for the ''GPT-5.4 generator'' (green circles) are plotted at values (e.g.,
    63.8, 61.5) that are significantly higher than the ''Main generator'' (grey circles,
    e.g., 35.0, 40.6). This contradicts the caption''s claim that ''Type 1 remains
    more damaging'' (implying the new generator should not drastically increase ASR)
    and suggests a potential labeling error or data inversion.'
- id: 60f797c9b28d
  severity: writing
  text: 'Figure 6: The legend at the bottom is split into two disconnected parts (''Main
    generator'' on the left, ''GPT-5.4 generator'' on the right) without a unifying
    title or box, making it slightly ambiguous whether these are mutually exclusive
    categories or separate series.'
artifact_hash: b321ce34848cd04bd8d899e341b97cc74f8e7595fd9393bb1f9638bbf57b0d10
artifact_path: projects/PROJ-704-measuring-epistemic-resilience-of-llms-u/paper/metadata.json
backend: dartmouth
feedback: Vision review of 6 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T00:54:58.539615Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

The figure effectively visualizes the injection process described in the text, but the caption filename is a critical error that contradicts the figure label and the provided caption list. Additionally, the specific medical claim used as the injection is not defined in the caption, obscuring the source of the 'Authority' provenance.

### Figure 2

The figure provides a clear visual overview of the dataset pipeline and attack types, but the workflow logic is slightly obscured by the disconnected placement of Step 3 and the numbering skips from 2 to 4.

### Figure 3

Figure 3 presents a bar chart comparing clean, Type 1, and Type 2 accuracy across models, but fails to clearly link the caption’s aggregate claims (e.g., 38.0% Type 1 mean) to visual elements. The x-axis sub-labels are undefined, and the three dashed ‘mean reference’ lines lack legend differentiation, undermining clarity and scientific rigor.

### Figure 4

The figure effectively visualizes the disparity between Type 1 and Type 2 attack success rates, but the caption contains a critical file reference error ('Figure5.pdf'). Additionally, the legend definition for 'gap' contradicts the visual representation of connecting lines.

### Figure 5

The figure is a UI screenshot that fails to visually demonstrate the 'Rubric A/B controls' mentioned in the caption, and the displayed content appears to be metadata definitions rather than the specific review artifacts described.

### Figure 6

The figure attempts to show generator sensitivity but presents data that contradicts the caption's narrative, as the new generator shows drastically higher attack success rates rather than a consistent pattern. Additionally, the legend layout is disjointed.
