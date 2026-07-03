---
action_items:
- id: e71016281e3a
  severity: writing
  text: 'Figure 1: The legend at the top (Memory Represent. & Storage, Memory Extraction,
    etc.) uses colored boxes that do not match the shapes or colors used in the diagrams
    below (e.g., ''Memory Extraction'' is a green box in the legend but green hexagons
    in the figure). This creates ambiguity about which components belong to which
    category.'
- id: 143ecb64c088
  severity: writing
  text: 'Figure 1: The legend labels are truncated (e.g., ''Represent. & Storage''
    instead of ''Representation & Storage''), reducing clarity and professionalism.'
- id: 8dce624963cf
  severity: science
  text: "Figure 1: In panel (a), the 'Reflection (LLM)' and 'Planner (LLM)' components\
    \ are gray hexagons, but they are not defined in the legend or caption \u2014\
    \ it\u2019s unclear whether they fall under 'Memory Retrieval / Routing' or another\
    \ category."
- id: e019da5f54ed
  severity: writing
  text: 'Figure 2: The caption is marked ''(to be refined)'' and lacks specific details
    about the datasets, metrics, or experimental conditions shown in the plot.'
- id: f4bd86da640b
  severity: science
  text: 'Figure 2: The x-axis uses a logarithmic scale (1, 3, 10, 30, 100, 300) but
    lacks explicit tick labels or grid alignment for intermediate values, making precise
    reading of runtime difficult.'
- id: 673814cce994
  severity: writing
  text: 'Figure 2: The legend ''Double-outline = Pareto-optimal'' is present, but
    the term ''Pareto-optimal'' is not defined in the caption, leaving the criteria
    for optimality ambiguous.'
- id: 21f048dc93fa
  severity: fatal
  text: 'Figure 3: The caption describes a two-panel figure ((a) comparison, (b) trending),
    but the image shows only a single scatter plot.'
- id: 2480a9dd7c07
  severity: science
  text: 'Figure 3: The x-axis label ''Sum of Mean Build+Query Runtime Across 3 Tasks
    (s)'' is ambiguous; it is unclear if the values represent the sum of means or
    the mean of sums.'
- id: 6648492616f1
  severity: writing
  text: 'Figure 3: The legend ''Double-outline = Pareto-optimal'' is a text box rather
    than a standard legend, and the term ''Pareto-optimal'' is not defined in the
    caption.'
- id: 7dabe9d418ac
  severity: science
  text: 'Figure 9: The x-axis labels in subplots (a)-(d) are rotated 45 degrees, causing
    the text to be illegible and unreadable.'
- id: c740c90530f9
  severity: science
  text: 'Figure 9: Subplots (a)-(d) lack a y-axis title (e.g., ''Score'' or ''Percentage''),
    making the metric units ambiguous despite the caption.'
- id: 460e8f100a01
  severity: science
  text: 'Figure 9: The legend at the top (''Reference Baselines'', ''Sequential Context'',
    etc.) does not map to the specific x-axis categories (e.g., ''Mem0'', ''Cognee'')
    shown in the plots, leaving the grouping logic unclear.'
- id: 3316c6586f4d
  severity: science
  text: 'Figure 10: The legend lists ''Zep Local'' (red square), but the bar chart
    in panel (a) labels the corresponding red bars as ''Zep MemTree'', creating a
    direct contradiction between the legend and the chart labels.'
- id: d7457269d6ab
  severity: science
  text: 'Figure 10: Panel (a) bar chart x-axis labels are cluttered and overlapping
    (e.g., ''Zep MemTree'', ''LightMem SimpleMem''), making it difficult to distinguish
    which bar belongs to which method.'
- id: 15ebc72ec1d1
  severity: writing
  text: 'Figure 10: The legend in panel (b) uses inconsistent line styles (solid,
    dashed, dotted, dash-dot) and markers that are difficult to distinguish visually
    in the plot, reducing readability.'
- id: b1abee19d198
  severity: science
  text: 'Figure 11: The x-axis labels (''Emb. RAG'', ''LightMem'', ''MemOS'', ''MemTree'',
    ''A-MEM'') describe specific memory systems, but the caption states the figure
    is an ''Ablation of Backbones''. This indicates a mismatch between the figure
    content and its caption, suggesting the wrong plot was rendered or the caption
    is incorrect.'
- id: d83d3153bbed
  severity: writing
  text: 'Figure 11: The numerical data labels on top of the bars are extremely small
    and illegible, making it impossible to read the precise values without zooming
    in significantly.'
- id: 695440afeef5
  severity: science
  text: 'Figure 12: The legend in panel (b) lists 12 methods, but the x-axis only
    has 4 bins. The lines are extremely cluttered and overlapping, making it impossible
    to distinguish individual method trends or verify the ''growth'' claim for specific
    systems.'
- id: 5b0cb00ad3ae
  severity: writing
  text: 'Figure 12: Panel (a) x-axis labels are split across multiple lines (e.g.,
    ''Long Ctx'', ''Embed RAG''), which is visually cluttered and reduces readability
    compared to a single-line label.'
- id: 9108fc614541
  severity: science
  text: 'Figure 12: Panel (c) y-axis is ''Answer F1 (%)'' while panel (b) is ''ROUGE-L
    F1 (%)''. The caption describes (c) as ''Temporal evidence-distance drift'' but
    does not clarify if the metric change is intentional or if it should be consistent
    with (b) for comparison.'
artifact_hash: 6dff6a8b182c59d170af29ed51dc0ec9fc4ff0bcf02876363e01c2d0e0fdd424
artifact_path: projects/PROJ-792-are-we-ready-for-an-agent-native-memory/paper/metadata.json
backend: dartmouth
feedback: Vision review of 12 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T14:19:02.041383Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

Figure 1 presents four workflow diagrams with a legend that mismatches the visual encoding in the panels, uses truncated labels, and omits definitions for key components like 'Reflection' and 'Planner', reducing interpretability.

### Figure 2

Figure 2 presents a scatter plot comparing memory methods but suffers from an unrefined caption and a logarithmic x-axis that lacks clear intermediate tick labels, hindering precise data interpretation.

### Figure 3

The figure is a single scatter plot that contradicts the caption's description of a two-panel layout. Additionally, the x-axis label is ambiguous regarding the aggregation of runtime data.

### Figure 4

Figure 4 effectively illustrates three distinct memory representation methods (Token-Level, Graph & Tree-Based, and Heterogeneous Composite) with clear visual diagrams and labels. The internal structure of each method is well-defined, and the caption accurately reflects the content shown.

### Figure 5

Figure 5 effectively illustrates three distinct memory storage architectures (Transient In-Context Register, Specialized Single-Engine, and Heterogeneous Multi-Engine) using clear diagrams and labels. The visual distinction between the 'No External Store', 'Single-Specialized Store', and 'Multi-Distributed Store' approaches is intuitive and aligns well with the caption 'Memory Storage Methods'.

### Figure 6

Figure 6 effectively illustrates three distinct memory extraction methods (Raw Sequence Concatenation, Schema-Free Semantic Extraction, and Schema-Constrained Structured Extraction) using clear diagrams and text examples. The visual layout is uncluttered, and the caption accurately describes the content shown.

### Figure 7

Figure 7 effectively visualizes five distinct memory retrieval methods with clear, labeled diagrams and a consistent visual style. The figure is self-contained, and the caption accurately reflects the content shown.

### Figure 8

Figure 8 effectively illustrates four distinct memory maintenance methods using clear diagrams and labeled sub-panels. The visual hierarchy and text are legible, and the content aligns well with the caption 'Memory Maintenance Methods'.

### Figure 9

Figure 9 presents a comprehensive comparison across multiple benchmarks, but the x-axis labels are rotated to the point of illegibility, and the legend fails to clarify how the specific methods are categorized into the four color groups.

### Figure 10

Figure 10 presents retrieval results but suffers from a contradiction between the legend and bar chart labels in panel (a) regarding 'Zep Local' vs 'Zep MemTree'. Additionally, the x-axis labels in the bar chart are cluttered, and the line styles in the line chart are hard to distinguish.

### Figure 11

The figure displays performance metrics for various memory systems rather than a backbone ablation study as claimed in the caption, creating a significant content mismatch. Additionally, the data labels on the bars are too small to be legible.

### Figure 12

Figure 12 presents three panels evaluating memory system stability, but panel (b) suffers from severe visual clutter due to overlapping lines and a dense legend, hindering interpretation. Additionally, inconsistent y-axis metrics between panels (b) and (c) and split x-axis labels in panel (a) reduce clarity.
