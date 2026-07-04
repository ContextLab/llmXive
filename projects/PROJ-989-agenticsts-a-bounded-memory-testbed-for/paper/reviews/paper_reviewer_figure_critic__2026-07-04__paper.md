---
action_items:
- id: 4b7a283e518e
  severity: writing
  text: 'Figure 1: The caption contains a broken cross-reference (''are given in --'')
    instead of citing the specific figure or section containing the exact numbers
    and caveats.'
- id: 0c1aee3ccb36
  severity: writing
  text: 'Figure 1: The ''L1 protocol'' through ''L5 skills'' labels in the bottom-left
    panel are not defined in the caption, leaving the specific meaning of these layers
    ambiguous to the reader.'
- id: 894d081dd82d
  severity: writing
  text: 'Figure 2: The caption states that summary labels (e.g., ''no trade-off'',
    token-efficiency, score-gap figures) are illustrative, but the figure itself displays
    these specific claims as definitive facts (e.g., ''90%+ fewer tokens'', ''+52.4
    vs best public'') without visual distinction, potentially misleading readers about
    the data''s status.'
- id: 3ce673a8f254
  severity: science
  text: 'Figure 2: Panel (c) presents a box plot for ''Ours +L5 scaffold'' with n=30,
    while other groups (AGI-Eval GPT-5.4, Opus 4.7) have n=9; the caption notes sample
    size differences but does not explicitly warn that the visual comparison of distributions
    across these disparate sample sizes is statistically limited.'
- id: a10879f69339
  severity: writing
  text: 'Figure 3: The legend in panel (a) displays the formula as ''1/4 O(c^2)'',
    but the caption describes the counterfactual as ''1/4 of naive O(c^2) growth''
    with a specific median token formula; the legend notation is ambiguous and should
    explicitly state it represents the total cumulative growth curve to match the
    y-axis.'
- id: 9e5d871b4d90
  severity: writing
  text: 'Figure 3: The x-axis label ''strategic decisions c'' is present, but the
    caption refers to ''ten fixed-A0 runs'' and ''two per cell'' without explicitly
    defining what the specific x-axis values (0 to 140) represent in the context of
    the ''Per-run growth'' panel (e.g., is it the max decisions reached in a run?).'
- id: 49c34a4b8596
  severity: science
  text: 'Figure 4: The diagram labels the transition from ''mode-a'' to ''mode-b''
    as ''swap L5 source'', but the visual content shows ''L5 human'' (mode-a) changing
    to ''L5 agent'' (mode-b). The caption defines the comparison as isolating ''L5
    source'', yet the diagram does not explicitly label ''human'' and ''agent'' as
    the specific sources being swapped, creating ambiguity about the ablation axis.'
- id: f9fb1d04fa06
  severity: writing
  text: 'Figure 4: The caption states ''adjacent bars are organized by a named ablation
    axis'', but the figure is a schematic flowchart of configuration states, not a
    bar chart. This terminology mismatch between the caption and the visual representation
    is confusing.'
- id: f404c7b26f4b
  severity: science
  text: "Figure 5: The x-axis labels 'A2', 'A3', 'A4', 'A5', 'A7', 'A8' are undefined;\
    \ the caption does not explain what these codes represent or how they relate to\
    \ the named conditions (e.g., 'baseline-strict', 'Mode B').\n  - severity: science\n\
    \    text:"
- id: 01699e065fc8
  severity: science
  text: 'Figure 5: The ''Mode B'' and ''full+postrun'' groups lack sample size (n)
    labels, whereas all other groups explicitly state ''(n=...)'', preventing assessment
    of statistical reliability for these key conditions.

    summary:'
- id: 8a2afdf5326f
  severity: writing
  text: 'Figure 6: The caption ends abruptly with ''e [fig_cmp_strips.pdf]'', cutting
    off the explanation of the token convention (likely ''estimated'') and leaving
    the sentence incomplete.'
- id: a7edd25c099c
  severity: science
  text: 'Figure 6: The y-axis for (c) Cost is labeled ''Fresh tokens / score pt''
    with a log scale, but the data labels (e.g., ''570.7k'') are placed directly on
    the plot without a clear visual mapping to the axis ticks, making it difficult
    to verify the values against the scale.'
- id: e9923788ee59
  severity: science
  text: 'Figure 7: The x-axis extends to 1000+ decisions, but the caption states the
    AgenticSTS runs make ''~100 strategic calls'' and the x-extent is ''not comparable''.
    Plotting the bounded contract (dashed line) on the same x-axis as the unbounded
    competitors implies a direct comparison of growth over the same run length, which
    the caption explicitly denies, creating a misleading visual comparison.'
- id: 922320bae9cc
  severity: writing
  text: 'Figure 7: The legend entry ''AgenticSTS bounded contract (~5k/call, est.)''
    is ambiguous regarding the y-axis unit. The caption clarifies this is ''strategic
    user-message median'' excluding the ''constant cached system prefix'', but the
    y-axis label is ''Prompt tokens per LLM call''. This discrepancy (partial vs.
    full prompt) is not visually distinguished in the legend or axis, potentially
    confusing the reader about what is being measured.'
- id: b01a7b67c430
  severity: writing
  text: 'Figure 8: The legend labels ''AgenticSTS (full-frozen)'' and ''AgenticSTS
    (baseline-strict)'' are not defined in the figure caption, which only refers to
    them generically as ''our cells''.'
- id: 7fd1d5597d99
  severity: science
  text: 'Figure 8: The x-axis label ''Fresh LLM tokens per run'' is ambiguous because
    the legend explicitly states that the diamond markers (AgenticSTS) use ''estimated''
    tokens based on a convention, whereas the competitor markers use ''measured''
    tokens; the axis label should reflect this mixed data source.'
- id: e871fc790c05
  severity: science
  text: 'Figure 9: The caption claims the figure shows ''combat planning (left) and
    shop planning (right)'', but the rendered image is a single screenshot of a combat
    encounter with no right-side panel or shop interface visible.'
- id: a6d4db63a5fc
  severity: science
  text: 'Figure 9: The image displays a game UI (Slay the Spire) rather than the ''decision
    states used in the prompt'' (e.g., text logs or structured data) described in
    the caption.'
artifact_hash: 199901d5e4144b007deca7b5b20bcc2b010b84ade5616f6bb7430db503358c9f
artifact_path: projects/PROJ-989-agenticsts-a-bounded-memory-testbed-for/paper/metadata.json
backend: dartmouth
feedback: Vision review of 9 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-04T21:54:53.972753Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

The figure provides a clear visual overview of the proposed memory contract and testbed. However, the caption contains a broken cross-reference and fails to define the specific 'L1-L5' layers shown in the diagram.

### Figure 2

Figure 2 effectively visualizes the proposed architecture and comparative scores, but it presents illustrative summary labels as definitive facts and compares distributions across significantly different sample sizes without sufficient visual or textual caveats in the panel itself.

### Figure 3

The figure effectively visualizes the token audit and counterfactual growth, but the legend notation in panel (a) is slightly ambiguous regarding the formula representation, and the x-axis definition could be more explicit in the context of the caption's description of run mechanics.

### Figure 4

The figure effectively visualizes the ablation surface configuration states, but the caption's reference to 'adjacent bars' contradicts the flowchart format, and the 'L5 source' swap is not explicitly labeled in the diagram.

### Figure 5

The figure presents ascension data but fails to define the 'A#' labels on the x-axis or the orange/green bar colors in the legend. Additionally, the omission of sample sizes for the final two conditions makes it impossible to evaluate the robustness of those results.

### Figure 6

The figure effectively visualizes the competitor comparison across effect, speed, and cost, but the caption contains a significant truncation error at the end, and the cost axis labels could be clearer.

### Figure 7

The figure effectively visualizes the context growth difference between bounded and unbounded agents, but the x-axis comparison is misleading given the caption's disclaimer that run lengths are not comparable. Additionally, the legend and y-axis label do not fully align with the caption's definition of the AgenticSTS metric (partial vs. full prompt).

### Figure 8

The figure effectively visualizes the cost-effect frontier, but the legend uses specific method names not defined in the caption, and the x-axis label fails to distinguish between estimated and measured token counts.

### Figure 9

The figure fails to match its caption; it shows a single combat screenshot instead of the promised side-by-side comparison of combat and shop planning states, and it displays a game UI rather than the prompt data described.
