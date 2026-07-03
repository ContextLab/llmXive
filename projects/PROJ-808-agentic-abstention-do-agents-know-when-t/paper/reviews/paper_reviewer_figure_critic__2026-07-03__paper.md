---
action_items:
- id: ce365b8c0ed1
  severity: writing
  text: 'Figure 1: The provided caption text is fragmented and does not match the
    visual content; it discusses ''web shopping, terminal interactions, and question
    answering'' generally, whereas the figure specifically illustrates a single ''Missing
    Target Task'' scenario with a timeline of agent actions.'
- id: 167ee145853e
  severity: writing
  text: 'Figure 1: The caption contains raw LaTeX formatting artifacts (e.g., ''%'',
    ''[overview.pdf]'') and disjointed sentence fragments that should be cleaned up
    for the final version.'
- id: e0e8c2122fbf
  severity: writing
  text: 'Figure 3: The legend at the top lists 10 models, but the ''Terminal'' subplot
    only displays 4 distinct lines, making it impossible to identify which models
    are missing or which lines correspond to the unlisted models.'
- id: 38f574b9cf9d
  severity: writing
  text: 'Figure 3: The legend uses identical green diamond markers and similar green
    line colors for both ''gpt-oss-120b'' and ''Terminus 2'', creating ambiguity in
    distinguishing these two series.'
- id: e84ed3ada04a
  severity: fatal
  text: 'Figure 4: The caption describes a multi-row layout (''From top to bottom,
    the rows show Web, Terminal, and QA results''), but the rendered image displays
    four horizontally arranged panels labeled ''Missing Target'', ''Subjective Preference'',
    ''Underspecified Intent'', and ''False Premises'' with no row structure or scenario
    labels.'
- id: d467df158b33
  severity: science
  text: 'Figure 4: The caption claims to show results across Web, Terminal, and QA
    scenarios, but the figure lacks any visual indicators (e.g., panel titles, axis
    labels, or legends) identifying which data corresponds to which scenario.'
- id: 3db69d18819a
  severity: writing
  text: 'Figure 4: The x-axis label ''K'' is present, but the y-axis label ''Abstention
    Recall'' is only visible on the leftmost panel; the other three panels lack y-axis
    labels, reducing clarity.'
- id: 297e20de98b8
  severity: science
  text: 'Figure 5: The caption claims ''Missing Target... is the hardest case for
    all models,'' but the ''Missing Target'' panel shows Llama-3.3-70B achieving ~0.62
    AbsRec@1, whereas ''False Premises'' shows the same model at ~0.95. The ''hardest''
    category (lowest recall) is actually ''Missing Target'' only for the lower-performing
    models, while the top model finds it relatively easy compared to other categories;
    the caption''s absolute claim contradicts the visual data for the best-performing
    model.'
- id: 7d433937960b
  severity: writing
  text: 'Figure 5: The y-axis label ''Abstention Recall'' is present, but the caption
    uses the notation ''$AbsRec@K$'' without explicitly defining that the y-axis represents
    this specific metric, though it is implied.'
- id: f67dd5792c8e
  severity: science
  text: 'Figure 6: The x-axis label ''K'' is positioned only under the rightmost subplot,
    leaving the x-axes of the left and middle subplots unlabeled.'
- id: 045b9b30ef9f
  severity: writing
  text: 'Figure 6: The legend is placed outside the plot area at the bottom center,
    which is ambiguous regarding which subplot it applies to; it should be placed
    inside or clearly associated with the specific panel.'
- id: 11b4193c4d80
  severity: fatal
  text: 'Figure 7: The figure has no caption provided (labeled ''(no caption)''),
    making it impossible to verify what the plotted data represents or to interpret
    the specific models and metrics shown.'
- id: 46970f9f9766
  severity: science
  text: 'Figure 7: The legend lists ''GPT-5.4-mini'' variants, but the y-axis is ''Over-Abstention
    Rate'' while the paper''s other figures (e.g., Fig 3, 4) focus on ''Abstention
    Recall''; the metric definition and its relationship to the paper''s core claims
    are unclear without a caption.'
- id: 8ed59b03556c
  severity: writing
  text: 'Figure 7: The legend is placed outside the plot area without a border or
    background, which can be visually confusing and makes it harder to associate the
    symbols with the lines compared to an inset legend.'
- id: 01f76b89d001
  severity: fatal
  text: 'Figure 8: The rendered image displays four panels labeled ''Missing Target'',
    ''Subjective Preference'', ''Underspecified Intent'', and ''False Premises'',
    but the caption describes a triptych of ''Web, Terminal, and QA scenarios'' with
    rows. The visual content does not match the caption''s description of the layout
    or the specific scenarios presented.'
- id: 440f0999ccc2
  severity: science
  text: 'Figure 8: The caption claims to show results for ''Missing Prerequisite in
    Terminal'', but the rendered panels do not contain a ''Missing Prerequisite''
    category or a ''Terminal'' scenario label, creating a disconnect between the text
    and the data shown.'
- id: f34ea7860d02
  severity: fatal
  text: 'Figure 9: The rendered image displays four panels labeled ''Missing Target'',
    ''Subjective Preference'', ''Underspecified Intent'', and ''False Premises'',
    but the caption describes a triptych of ''Web, Terminal, and QA scenarios'' and
    mentions ''Missing Prerequisite'' in Terminal, which is not shown. The figure
    content does not match the caption.'
- id: e0c249c0ef7a
  severity: science
  text: 'Figure 9: The y-axis is labeled ''Abstention Recall'' but the caption refers
    to ''$AbsRec@K$''. While likely the same metric, the axis label should explicitly
    match the caption''s notation or define the relationship to avoid ambiguity.'
- id: e9104c3cf58c
  severity: writing
  text: 'Figure 10: The caption references panels (b) and (c) and a missing Figure
    number (''shown in Figure .''), but the provided image contains only panel (a).'
- id: a4f06a2a3178
  severity: science
  text: 'Figure 10: The histogram bars are overlapping rather than side-by-side or
    transparent, making it difficult to compare the ''Original'' and ''Rewritten''
    distributions at specific token lengths.'
- id: 9232049c831b
  severity: fatal
  text: 'Figure 11: The caption describes three panels (a, b, c), but the rendered
    image only shows panel (a) ''Token Length Distribution''; panels (b) and (c) are
    missing.'
- id: 8a171f144541
  severity: science
  text: 'Figure 11: The caption claims ''similar token counts'' between original and
    rewritten instructions, but the histogram shows a clear shift where ''Rewritten''
    (orange) has a longer tail and higher values than ''Original'' (blue).'
- id: c3c9917091dd
  severity: writing
  text: 'Figure 11: The caption contains an incomplete cross-reference: ''shown in
    Figure .'' lacks the specific figure number.'
- id: b499afe37c66
  severity: science
  text: 'Figure 12: The plot displays two distinct colors (blue and orange) for data
    points, but the caption and plot lack a legend defining what these colors represent
    (e.g., original vs. rewritten instructions).'
- id: af4a93fb4aeb
  severity: writing
  text: 'Figure 12: The title ''(a) Subjective Preference'' suggests this is a sub-panel,
    yet the caption describes the figure as containing visualizations for three categories
    (''Subjective Preference, Underspecified Intent, and False Premise or Contradiction''),
    creating a mismatch between the single panel shown and the multi-category description.'
artifact_hash: 38d0e8e4fb458c680aadb1d4bcdffd2c4f641f3bec33db525a174585bed1f06b
artifact_path: projects/PROJ-808-agentic-abstention-do-agents-know-when-t/paper/metadata.json
backend: dartmouth
feedback: Vision review of 12 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T01:32:17.805510Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

The figure effectively visualizes a specific 'Missing Target' abstention scenario with clear action timelines, but the provided caption is fragmented, contains raw formatting artifacts, and fails to accurately describe the specific content shown.

### Figure 2

Figure 2 effectively illustrates the task components and instruction rewriting process. The diagram in (a) clearly labels the four core components, and the examples in (b) provide concrete instances of the two abstention scenarios described in the caption.

### Figure 3

The figure effectively illustrates the claim that abstention recall increases with K, but the legend is poorly designed with duplicate markers/colors for different models, and the 'Terminal' subplot fails to display all models listed in the legend.

### Figure 4

Figure 4 fails to match its caption's description of a multi-row layout across scenarios; instead, it shows four unlabeled horizontal panels without scenario identification, and y-axis labels are missing from three of the four plots.

### Figure 5

The figure effectively displays Abstention Recall across four categories, but the caption's claim that 'Missing Target' is the hardest case for all models is contradicted by the data for the top-performing model (Llama-3.3-70B), which achieves significantly higher recall in that category than in others.

### Figure 6

The figure displays three panels of Abstention Recall vs K, but the x-axis label is missing for the first two panels, and the legend placement is ambiguous.

### Figure 7

Figure 7 is critically flawed because it lacks a caption, preventing verification of the data and metrics. Additionally, the metric 'Over-Abstention Rate' is not defined in the context of the paper's main 'Abstention Recall' focus, and the legend placement is suboptimal.

### Figure 8

The figure is fundamentally broken as the rendered image (four specific abstention categories) contradicts the caption's description (three scenarios: Web, Terminal, QA). The visual content does not support the claims made in the caption regarding the layout or the specific scenarios analyzed.

### Figure 9

The figure is severely mismatched with its caption; the image shows four specific abstention categories while the caption describes a comparison across three different scenarios (Web, Terminal, QA) and mentions a category ('Missing Prerequisite') not present in the plot.

### Figure 10

The figure is incomplete, showing only panel (a) while the caption describes panels (b) and (c) and contains a broken cross-reference. Additionally, the overlapping bars in the histogram obscure direct comparison between the two distributions.

### Figure 11

The figure is incomplete, displaying only panel (a) despite the caption describing three panels (a, b, c). Additionally, the visual data in panel (a) contradicts the caption's claim of similar token counts, and the caption contains a broken cross-reference.

### Figure 12

The figure is a t-SNE plot with a specific title for 'Subjective Preference', but it lacks a legend to explain the color coding of the points. Additionally, the caption implies the figure covers three categories, while the image only shows one labeled panel.
