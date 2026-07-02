---
action_items:
- id: 9c026e40c976
  severity: science
  text: 'Figure 1(c): The legend lists ''Ours'' (purple dashed line), but the caption
    describes the plot as ''pass@$k$'' (implying a variable k). However, the y-axis
    is labeled ''Avg. Pass@1 of Branches'' and the x-axis shows dataset sizes (1,
    2, 4...), not k values. This contradicts the caption''s claim of showing pass@$k$.'
- id: 38dc5bed639f
  severity: science
  text: 'Figure 1(c): The radar chart legend includes ''GRPO'', ''GIGPO'', ''ARPO'',
    and ''Ours (APPO)'', but the caption text only mentions ''performance comparison
    between APPO and others'' without specifying these baselines, creating a disconnect
    between the visual legend and the textual description.'
- id: 51dbc1d277c1
  severity: writing
  text: 'Figure 1(b.1): The text annotation ''Entropy does not always work ..'' is
    informal and unprofessional for a scientific figure; it should be rephrased to
    a formal statement or removed.'
- id: e3828421cb5f
  severity: science
  text: 'Figure 2: The ''Dual-Group Advantage Calculation'' panel depicts a ''Future''
    term (purple box) being added to the advantage calculation, but the diagram does
    not visually link this term to the ''Branching Score'' or ''Entropy'' components
    shown in the ''Rollout Branching'' panel, making the ''future-aware'' mechanism
    described in the caption opaque.'
- id: cec2e4432d0c
  severity: writing
  text: 'Figure 2: The legend at the bottom is incomplete; it defines symbols for
    ''Query'', ''Reasoning Tokens'', ''Procedures'', ''Tool-calls (Python)'', and
    ''Tool-calls (WebSearch)'', but does not define the symbols for ''Entropy'', ''Branching
    Score'', or the ''Future'' term used in the main diagram.'
- id: d60f1a4f89f3
  severity: science
  text: 'Figure 3: The legend is cropped and illegible; the text labels for the purple
    and teal patterns are cut off, making it impossible to verify which color corresponds
    to ARPO and which to APPO.'
- id: 3d66a972c0d0
  severity: writing
  text: 'Figure 3: The y-axis of subplot (c) ''WebWalkerQA'' has a truncated scale
    (40-70) that is inconsistent with the other subplots (40-65 or 10-25), which may
    mislead the reader regarding the relative magnitude of performance differences.'
- id: 87b932ede2bb
  severity: science
  text: "Figure 4: The caption describes 'training dynamics' but does not define the\
    \ y-axes. The left plots show values 0.0\u20130.6 (likely entropy or probability)\
    \ and the right plots show 150\u2013400 (likely token count or cost), yet neither\
    \ metric is labeled on the axes, making the 'dynamics' uninterpretable."
- id: 702abb6ceebb
  severity: writing
  text: 'Figure 4: The legend is split across the top of the subplots (two separate
    legends for two model families) rather than being unified or clearly associated
    with the specific subplots, which creates visual clutter and potential confusion.'
- id: 304a5822d97b
  severity: science
  text: 'Figure 5: The caption claims to show ''alternative designs of the BS metric,''
    but the sub-captions (a)-(d) do not define which specific metric design corresponds
    to each panel, making the comparison impossible to interpret.'
- id: 68c3e1e39fdf
  severity: writing
  text: 'Figure 5: Sub-captions (a), (b), and (c) contain mathematical notation (''Weight=(0.5,
    0.5)'', etc.) that is undefined; the caption fails to explain what these weights
    represent or which components of the BS metric they modify.'
artifact_hash: 3a43673385ee45c44ff0ac04e7e12a654dbb1cefe913b5676a26e486f2c9fad4
artifact_path: projects/PROJ-707-appo-agentic-procedural-policy-optimizat/paper/metadata.json
backend: dartmouth
feedback: Vision review of 5 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T09:36:57.595367Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

Figure 1 presents a comprehensive overview but contains a significant contradiction in panel (c) where the caption claims to show pass@$k$ results, yet the axes display Pass@1 accuracy against dataset sizes. Additionally, the informal text annotation in panel (b.1) detracts from the scientific tone.

### Figure 2

Figure 2 provides a clear high-level overview of the APPO workflow, but the specific mechanism for 'future-aware' advantage estimation is visually disconnected from the branching logic, and the legend fails to define key symbols used in the diagram.

### Figure 3

The figure presents a clear comparison of Pass@k metrics across four datasets, but the legend is visually cropped and illegible, preventing verification of the model-to-color mapping. Additionally, the inconsistent y-axis scaling in subplot (c) warrants adjustment for visual consistency.

### Figure 4

The figure presents training curves for two models but fails to label the y-axes, rendering the specific metrics (entropy vs. token count) ambiguous despite the caption's claim of showing 'training dynamics'.

### Figure 5

The figure presents four word clouds but fails to define the specific metric variations shown in the sub-captions, rendering the comparison of 'alternative designs' unintelligible.
