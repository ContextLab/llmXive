---
action_items:
- id: 7c9b83ef2a42
  severity: science
  text: 'Figure 1: The caption describes a comparison between passive retrieval and
    active reconstruction, but the figure displays four distinct panels (Passive Retrieval,
    Flat Memory, Active Reconstruction, Associative Memory). The caption fails to
    define or explain the ''Flat Memory'' and ''Associative Memory'' panels, leaving
    the reader to guess their relationship to the main comparison.'
- id: f3d6fff29b6b
  severity: writing
  text: 'Figure 1: The figure contains no axis labels, units, or data scales, which
    is acceptable for a conceptual diagram, but the lack of a formal legend defining
    the icons (brain vs. robot) and symbols (red X vs. green check) makes the visual
    encoding ambiguous without external context.'
- id: 35509a470fc2
  severity: writing
  text: 'Figure 2: The diagram contains three distinct panels (left, middle, right)
    illustrating a progression, but the figure lacks explicit labels (e.g., (a), (b),
    (c)) to reference these specific stages in the text or caption.'
- id: a90656fe99a1
  severity: writing
  text: 'Figure 2: The caption describes the figure as comparing ''passive retrieval''
    and ''active reconstruction'', but the visual labels use ''1-hop Neighbors'' and
    ''LLM Reasoning'', creating a terminology mismatch between the text and the diagram.'
- id: cbe9b965f277
  severity: science
  text: 'Figure 4: The x-axis labels ''CE'', ''CTE'', and ''CTC'' in the ''No Reasoning''
    section are undefined; the caption mentions ''Ablation results'' but does not
    specify what these acronyms represent, making the comparison against ''MRAgent''
    incomprehensible.'
- id: 511def241e08
  severity: writing
  text: 'Figure 4: The legend at the top is cut off on the right side, obscuring the
    label for the final bar category.'
- id: d52d90ff530f
  severity: science
  text: 'Figure 5: The legend labels (''Multi-hop'', ''Temporal'', ''Open Domain'',
    ''Single hop'') do not match the y-axis metric ''Cumulative Recall (%)'', which
    implies a cumulative sum over turns; these categories likely represent distinct
    datasets or query types, but the caption fails to define what the lines represent
    or how they relate to the ''multi-turn reasoning'' analysis.'
- id: 9396a8ae3de2
  severity: writing
  text: 'Figure 5: The legend is presented as a separate color bar below the plot
    rather than an integrated key, and the colors in the legend do not explicitly
    map to the specific lines in the plot (e.g., which color corresponds to ''Multi-hop''
    vs ''Single hop'' is ambiguous without direct visual alignment).'
- id: 20d8149e9705
  severity: science
  text: 'Figure 6: The label ''Second Rejectipn'' contains a spelling error (''Rejectipn''
    instead of ''Rejection''), which appears in both the node label and the bottom
    axis.'
- id: 3ad70bb8f696
  severity: science
  text: 'Figure 6: The diagram lacks explicit connecting lines or arrows between the
    nodes (e.g., between ''First screenplay Submission'' and ''First Rejection''),
    making the ''reasoning trajectory'' and graph structure visually ambiguous.'
- id: 57c26c93f757
  severity: writing
  text: 'Figure 6: The bottom axis labels (''First screenplay'', ''Second screenplay'',
    etc.) are crowded and difficult to read due to the lack of spacing or line breaks.'
- id: 58fb84f3c9fd
  severity: writing
  text: 'Figure 7: The caption ''Active Memory Reconstruction'' is too brief and generic;
    it fails to describe the specific ''Nate'' example, the step-by-step reasoning
    process, or the timeline visualization shown in the figure.'
- id: 8515e5bf4924
  severity: science
  text: 'Figure 7: The timeline in the third panel displays dates (01-14, 05-27, 09-29)
    that do not align with the textual evidence in the second panel (e1: ''last week'',
    e3: ''just won'', e4: ''last week''), creating a logical contradiction in the
    example''s narrative.'
- id: 91da08c81e2c
  severity: writing
  text: 'Figure 7: The final panel references ''e5'' in the text (''Reference: [e4,
    e5]''), but the event ''e5'' is never defined or shown in the preceding panels
    of the figure.'
- id: dfbe0bf41560
  severity: science
  text: 'Figure 8: The x-axis labels (''call2'', ''call4'', ''call8'') do not match
    the caption''s description of ''per-round retrieval budget (K)''; the axis should
    be labeled with the specific values of K (e.g., 2, 4, 8) or the labels should
    be defined in the caption.'
- id: 291675cd0f1e
  severity: writing
  text: 'Figure 8: The y-axis labels (''turn2'', ''turn4'', ''turn8'') are ambiguous;
    the caption defines ''number of reasoning turns (T)'', so the axis should explicitly
    state the values of T (e.g., 2, 4, 8) rather than using a ''turn'' prefix that
    could be confused with a unit or category.'
- id: 6f77e7ff0686
  severity: science
  text: 'Figure 9: The text inside the bottom-left panel is truncated (''buted cortical
    reinst...''), making the label illegible and obscuring the comparison to the MRAgent
    architecture.'
- id: 544237d2baa2
  severity: science
  text: 'Figure 9: The diagram lacks a legend or explicit labels defining the specific
    icons (eye, ear, robot, question marks) and their functional mapping between the
    biological and computational domains.'
artifact_hash: b428847249c815694ce34a179b14e661a1c8a1e001ab2124c52ead974dee57ea
artifact_path: projects/PROJ-706-memory-is-reconstructed-not-retrieved-gr/paper/metadata.json
backend: dartmouth
feedback: Vision review of 9 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T20:14:39.418073Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

The figure conceptually illustrates the difference between retrieval and reconstruction but is poorly captioned; it fails to account for the four distinct panels shown, specifically omitting definitions for the 'Flat Memory' and 'Associative Memory' quadrants.

### Figure 2

The figure effectively illustrates the conceptual difference between passive retrieval and active reconstruction using a clear visual flow. However, the lack of panel labels (a, b, c) and the terminology mismatch between the caption ('passive retrieval') and the diagram ('1-hop Neighbors') reduce its precision for academic reference.

### Figure 3

Figure 3 effectively illustrates the MRAgent architecture with clear visual separation between the associative memory system (a) and the active reconstruction process (b). The diagram is well-organized, with distinct components, logical flow arrows, and readable text that aligns with the caption's description of Cue-Tag-Content structures and LLM-driven reasoning.

### Figure 4

The figure presents ablation data but fails to define the baseline methods (CE, CTE, CTC) on the x-axis, rendering the comparison invalid. Additionally, the top legend is partially cropped.

### Figure 5

The figure displays cumulative recall across turns for four categories, but the caption fails to define what these categories represent or how they relate to the analysis of multi-turn reasoning. Additionally, the legend is poorly integrated, making it difficult to associate specific colors with the labeled categories.

### Figure 6

The figure illustrates the reasoning trajectory but suffers from a spelling error in the labels ('Rejectipn') and lacks explicit connecting lines to visualize the graph structure described in the caption.

### Figure 7

The figure illustrates a step-by-step reasoning process but suffers from a generic caption that lacks necessary context. Additionally, there are internal logical inconsistencies regarding the timeline dates and a reference to an undefined event 'e5' in the final answer.

### Figure 8

The heatmap effectively visualizes performance trends, but the axis labels ('call' and 'turn' prefixes) are inconsistent with the caption's variable definitions ($K$ and $T$), creating ambiguity about the specific parameter values represented.

### Figure 9

The figure attempts to draw a functional correspondence between human and agent memory but suffers from illegible, truncated text in the bottom-left panel and lacks a legend to define the symbolic icons used in the diagram.
