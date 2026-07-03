---
action_items:
- id: 8ee32c4255a6
  severity: science
  text: 'Figure 1: The caption claims the graph is ''sparse'' and ''disconnected,''
    but the rendered image shows a dense, fully connected web of edges with no visible
    gaps, directly contradicting the textual claim.'
- id: 58963f91fd4e
  severity: writing
  text: 'Figure 1: The central question mark and circle are purely decorative and
    obscure the underlying network structure without adding informational value or
    being defined in the caption.'
- id: 60c198853a5b
  severity: writing
  text: 'Figure 1: The graph is extremely cluttered with overlapping edges and labels
    (e.g., ''DNABERT-2'', ''DNABERT-S'', ''Genomics-FM''), making it difficult to
    trace specific connections or verify the ''fragmented'' claim visually.'
- id: 88c418fe7121
  severity: writing
  text: 'Figure 2: The caption ''Architectural taxonomy of genomic foundation models''
    is too brief for a complex taxonomy diagram; it should define the color-coding
    scheme (orange, green, blue) used to group models and clarify the distinction
    between ''Transformers'' and ''Efficient Alternatives'' branches.'
- id: f8b0b756a423
  severity: science
  text: 'Figure 2: The diagram lists specific model names (e.g., ''mutBERT'', ''Genomics-FM'')
    but provides no visual or textual indication of their architectural differences
    beyond the broad ''Encoder-only'' or ''Decoder-only'' labels, limiting the figure''s
    utility for understanding true architectural diversity.'
- id: 5b2801eee56a
  severity: science
  text: 'Figure 3: The caption states ''Marker size and color both encode macro-MCC'',
    but the legend explicitly defines marker size as encoding ''Model Size'' (10^7,
    10^8, 10^9 params). This contradicts the caption and creates confusion, as size
    is the primary variable on the x-axis.'
- id: cff5eaf02261
  severity: writing
  text: 'Figure 3: The caption text is truncated at the end (''...offset su''), cutting
    off the final sentence.'
- id: 6736a7be8ab1
  severity: writing
  text: 'Figure 4: The x-axis labels (model names) are rotated 45 degrees and overlap
    significantly, making many names illegible (e.g., ''GENERA...-3B'', ''NT-v2-50M-3mer-MS'').
    Consider horizontal spacing or font size adjustment.'
- id: baed895d98f0
  severity: writing
  text: 'Figure 4: The y-axis labels (task groups) are not aligned with the heatmap
    rows, creating ambiguity about which row corresponds to which task (e.g., ''Chromatin
    Acc.'' vs ''Coding/Non-cod.''). Add grid lines or explicit row markers.'
- id: 815f54408a8d
  severity: science
  text: 'Figure 4: The caption states models are ''sorted by overall full-shot macro-average
    MCC'', but the x-axis order does not reflect this sorting (e.g., ''GENERA...-3B''
    appears first despite likely lower aggregate performance than later models). Verify
    sorting logic.'
- id: f554d81d98b5
  severity: writing
  text: 'Figure 5: The caption is truncated mid-sentence at the end (''These profiles
    mo''), suggesting missing text.'
- id: 4ca39beb57f5
  severity: science
  text: 'Figure 5: The legend for the ''Rank 36-40'' subplot includes ''Evo-1-131k'',
    but the caption explicitly identifies this as a ''prokaryotic-only outlier'' (referenced
    in Figure 3''s caption), yet it is included in the general ranking without specific
    exclusion or annotation in the plot itself, potentially confusing the comparison
    of general genomic models.'
- id: 2a0ba456327c
  severity: writing
  text: 'Figure 5: The legend for ''Rank 36-40'' lists ''JanusDNA-72-wo'' and ''JanusDNA-72-w''
    which appear to be very similar model names; ensure these are distinct and correctly
    labeled.'
- id: 7a18ef002bdb
  severity: science
  text: 'Figure 6: The top band displays percentage values (e.g., 65%, 63%) but lacks
    a unit label or explicit definition in the caption clarifying if these represent
    relative performance retention or absolute percentage point drops, creating ambiguity
    in interpreting the ''relative performance drop'' claim.'
- id: f865ff1ba8b7
  severity: writing
  text: 'Figure 6: The x-axis labels for the 40 models are densely packed and rotated,
    causing significant overlap and illegibility for many model names (e.g., ''GENA-LM-Large-T2T'',
    ''NT-v2-50M-MS''), hindering the ability to identify specific data points.'
- id: be9ff004d676
  severity: writing
  text: 'Figure 7: The x-axis label in panel (B) (''Bottom-3 placements'' / ''Top-3
    placements'') is ambiguous regarding the unit of measurement (e.g., raw count
    vs. percentage), which is only clarified by the caption''s mention of ''n = 39
    each''.'
- id: 3aebe6c59e44
  severity: writing
  text: 'Figure 7: Panel (B) uses a diverging bar chart format but lacks a legend
    explicitly mapping the bar colors (orange vs. green) to the ''bottom-3'' and ''top-3''
    categories, relying on the axis labels for interpretation.'
- id: 630ddb1ab67d
  severity: writing
  text: 'Figure 8: The caption is identical to Figure 2''s caption (''Architectural
    taxonomy of genomic foundation models'') and the image filename is ''[fm_models.png]'',
    suggesting this is a duplicate figure rather than a distinct entry.'
- id: 60e337cdde07
  severity: writing
  text: 'Figure 9: The caption contains unrendered LaTeX placeholders (e.g., ''$ =
    MCC_macro - MCC_micro$'', ''$ = 0.988$'', ''$|| = 0.009$'') instead of the variable
    names (likely $\Delta$) or values, making the text difficult to read.'
- id: d7bd5eb4deed
  severity: writing
  text: 'Figure 9: The caption states models are sorted from ''largest negative shift
    to largest positive shift'', but the plot displays them from largest positive
    shift (top) to largest negative shift (bottom), contradicting the description.'
- id: 6b5ad8f8e8b0
  severity: fatal
  text: 'Figure 10: The caption is a placeholder (''Enter Caption'') and does not
    describe the figure content, violating the requirement for a descriptive caption.'
- id: 0575758344f6
  severity: science
  text: 'Figure 10: The figure displays 13 distinct subplots of model performance
    across task categories, but lacks a unifying title or panel labels (e.g., A, B,
    C) to identify them, making it difficult to reference specific categories in the
    text.'
- id: a21d30eadd02
  severity: science
  text: 'Figure 10: The y-axis lists numerous model names (e.g., ''GENERator-Eukaryote-3B'',
    ''Omni-DNA-1B'') that are not defined or explained in the placeholder caption,
    leaving the reader to guess the context of the comparison.'
- id: a4c9b65fc297
  severity: science
  text: 'Figure 11: The ''Coding/Non-cod.'' and ''Chromatin Acc.'' subplots display
    single dots instead of boxplots, contradicting the caption''s claim that ''boxes
    denote the interquartile range'' and ''central lines indicate medians'' for these
    categories.'
- id: 19002dae57fe
  severity: writing
  text: 'Figure 11: The ''Coding/Non-cod.'' subplot lists 15 models but only displays
    14 data points, indicating a missing value or plotting error.'
- id: 040b5a726ebb
  severity: writing
  text: 'Figure 12: The x-axis labels (model names) are rotated 45 degrees and overlap
    significantly, making them difficult to read.'
- id: ad3e9f04024d
  severity: writing
  text: 'Figure 12: The y-axis label ''MCC'' is missing from the individual subplots,
    relying on the user to infer the metric from the caption.'
artifact_hash: 043e93d2fab619e0251c0029f296fc31d53c712bc78a466a1a30d67af8b711e1
artifact_path: projects/PROJ-679-geneb-why-genomic-models-are-hard-to-com/paper/metadata.json
backend: dartmouth
feedback: Vision review of 12 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T13:11:35.784292Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

The figure visually contradicts its caption by depicting a dense, connected network rather than a sparse, disconnected one. Additionally, the central decorative elements obscure the data, and the high density of overlapping edges makes the graph difficult to interpret.

### Figure 2

Figure 2 presents a clear hierarchical taxonomy of genomic foundation models with legible text and logical grouping, but the caption lacks sufficient detail to explain the color-coding and architectural distinctions implied by the diagram.

### Figure 3

The figure is visually clear and effectively communicates the efficiency frontier, but the caption contains a factual contradiction regarding what marker size encodes (stating MCC while the legend indicates parameter count) and ends with a truncated sentence.

### Figure 4

The heatmap effectively conveys task-level heterogeneity but suffers from poor x-axis label readability and ambiguous y-axis row alignment. The claimed sorting by macro-average MCC is not visually evident in the model ordering.

### Figure 5

The figure effectively visualizes category-specific model strengths using radar plots, but the caption is truncated. Additionally, the inclusion of the known outlier 'Evo-1-131k' in the lowest rank subplot without specific annotation may be misleading given the context provided in other figure captions.

### Figure 6

The figure effectively visualizes performance degradation trends across shot regimes, but the top band's percentage values lack clear unit definitions, and the crowded x-axis labels compromise model identification.

### Figure 7

Figure 7 effectively visualizes the relationship between task variance and pretraining data composition. However, the x-axis units in panel (B) are not explicitly labeled on the axis itself, and the color coding for top/bottom placements lacks a dedicated legend.

### Figure 8

The figure is a clear and well-organized taxonomy diagram with no apparent issues in its visual presentation or labeling.

### Figure 9

The figure effectively visualizes the robustness of rankings, but the caption contains unrendered LaTeX placeholders and incorrectly describes the sorting order of the models compared to the visual plot.

### Figure 10

Figure 10 is a collection of boxplots comparing model performance across various genomic tasks, but it is rendered unusable by a placeholder caption and a lack of clear panel labeling or axis definitions.

### Figure 11

The figure effectively visualizes performance distributions across task categories, but the single-task categories (Coding/Non-cod., Chromatin Acc.) display points rather than the boxplots described in the caption, and one data point appears missing in the Coding/Non-cod. subplot.

### Figure 12

The figure effectively displays top-10 model performance across categories, but the x-axis labels are cluttered and overlapping, and the y-axis lacks a direct label on the subplots.
