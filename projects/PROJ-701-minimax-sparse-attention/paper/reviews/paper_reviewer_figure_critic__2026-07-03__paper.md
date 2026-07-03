---
action_items:
- id: 4f52d7d4f5bf
  severity: writing
  text: 'Figure 1: The caption reads ''Overview of .'' with a missing model name or
    subject immediately following ''of'', making the sentence incomplete.'
- id: 54f69d951dfc
  severity: writing
  text: 'Figure 1: The caption contains a broken mathematical expression ''a set $$
    of $k$ key blocks'' where the variable defining the set size is missing between
    the dollar signs.'
- id: ab2a11e6d265
  severity: science
  text: "Figure 2: The caption claims 'four GQA groups' produce 'different long-range\
    \ selection patterns,' but the four subplots (Head 0\u20133) show nearly identical\
    \ diagonal and sink patterns with no visible differentiation in long-range behavior."
- id: ddf368db8876
  severity: writing
  text: 'Figure 2: The y-axis label ''Query Block'' and x-axis label ''Key Block''
    are present, but the colorbar label ''Prob'' is ambiguous without units or context
    (e.g., normalized probability? attention score?).'
- id: 6921207b8fff
  severity: science
  text: 'Figure 4: The title ''Capability Delta Relative to GQA Baseline'' contradicts
    the caption ''Evaluation-score deltas relative to the Full-Attention baseline'';
    the baseline definition must be consistent.'
- id: fc08c61ba872
  severity: science
  text: 'Figure 4: The legend includes ''GQA Baseline'' (dashed line), but the caption
    states the deltas are relative to a ''Full-Attention baseline''; the legend entry
    should match the caption''s baseline definition.'
- id: 3da14fb7f2e7
  severity: science
  text: 'Figure 5: The ''No gradient detach'' (orange) curve in the LM Loss plot terminates
    abruptly around step 2500, while the ''Gradient detach'' (teal) curve continues
    to step 8500. This missing data prevents a full comparison of training stability
    and loss convergence over the entire reported range.'
- id: 7666843786b0
  severity: science
  text: 'Figure 5: The x-axis for the ''Grad Norm'' plot is truncated at ~768 steps,
    whereas the ''LM Loss'' plot extends to 10,000 steps. Since gradient spikes are
    the key phenomenon being illustrated, the short x-axis range makes it impossible
    to verify if spikes persist or recur later in training.'
- id: dc6ac0dec3cf
  severity: writing
  text: 'Figure 7: The y-axis is labeled ''Value'' instead of ''Entropy'', which contradicts
    the figure title and caption.'
- id: b541164ce6c0
  severity: writing
  text: 'Figure 7: The legend defining the teal line (Main Branch) and the dashed
    red line (baseline) is missing from the plot area.'
- id: 157dbc474357
  severity: writing
  text: 'Figure 8: The caption contains a grammatical error (''Evaluation results
    of with and without...'') and fails to specify the model or method being evaluated.'
- id: d4ee1919624b
  severity: writing
  text: 'Figure 8: The x-axis label ''Tokens (Billion)'' is ambiguous; it is unclear
    if this represents total training tokens, context length, or model size.'
- id: 1955a4871b42
  severity: writing
  text: 'Figure 9: The x-axis tick labels (512, 2048, etc.) are present only on the
    bottom row of plots, making the top row (Head 4, Head 5) ambiguous regarding the
    query positions shown.'
- id: 072f7281e0ca
  severity: writing
  text: 'Figure 9: The top row plots (Head 4, Head 5) display only blue bars (''First
    token'') but lack the orange bars (''Learnable sink'') seen in the bottom row,
    which may confuse readers about whether the sink is absent or simply has zero
    value.'
- id: 0603989cfc40
  severity: writing
  text: 'Figure 11: The caption contains a grammatical error (''comparison between
    and a FLOP-matched...''), missing the name of the proposed method (likely ''MiniMax
    Sparse Attention'' or ''MSA'') which is only identifiable via the legend.'
- id: bb340701ed83
  severity: writing
  text: 'Figure 11: The y-axis label ''Perplexity (PPL)'' is redundant; ''Perplexity''
    is sufficient as PPL is the standard abbreviation.'
- id: 2ed6f6151fe3
  severity: writing
  text: 'Figure 12: The caption ''LM loss'' is insufficient; it fails to describe
    the comparison between ''Full Attention'' and ''MSA-PT'' shown in the legend or
    the specific training context.'
- id: 8c52a6c01033
  severity: science
  text: 'Figure 12: The inset plot''s x-axis labels (2.950, 2.975, 3.000) are illegible
    and lack units, making it impossible to verify the scale or the specific range
    of the zoomed-in region.'
artifact_hash: f00725508246b024cf4aa3c534e6f6afc166e2aa03bee30b44dd04e950f05991
artifact_path: projects/PROJ-701-minimax-sparse-attention/paper/metadata.json
backend: dartmouth
feedback: Vision review of 12 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T09:50:21.116512Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

The figure provides a clear visual overview of the architecture with distinct branches and a helpful legend for the attention masks. However, the caption contains significant text errors, including a missing subject and a broken mathematical formula.

### Figure 2

Figure 2 visually fails to support its caption’s claim of distinct long-range patterns across GQA groups, as all four heads show nearly identical attention structures. Axis and colorbar labels are minimally clear but lack contextual precision.

### Figure 3

Figure 3 effectively visualizes the mean attention score on the first token for heads in Layer 4 and Layer 24. The bar charts are clearly labeled with values, axes are defined, and the visualization directly supports the caption's claim of a pervasive attention sink effect.

### Figure 4

The figure is visually clear but contains a critical contradiction between the title/legend (GQA Baseline) and the caption (Full-Attention baseline), which misrepresents the reference point for the reported deltas.

### Figure 5

The figure effectively illustrates the difference in gradient stability between the two methods, but the truncated x-axis on the gradient norm plot and the premature termination of the 'No gradient detach' loss curve limit the ability to assess long-term training behavior.

### Figure 6

Figure 6 effectively communicates the benchmark results with clear axes, units, and a legend distinguishing the two conditions. The four subplots are well-organized, and the visual trend supports the caption's claim that detaching the gradient improves scores.

### Figure 7

The figure effectively visualizes the entropy drop and recovery described in the caption, but the y-axis label 'Value' is generic and incorrect, and the plot lacks a legend to define the plotted lines.

### Figure 8

The figure clearly displays the performance comparison between 'warmup' and 'w/o warmup' across five benchmarks with readable axes and legends. However, the caption contains a grammatical error and lacks specific context regarding the model or method being evaluated.

### Figure 9

The figure effectively visualizes the shift in attention mass between the first token and the learnable sink across different heads. However, the x-axis labels are missing from the top row, and the absence of orange bars in the top plots is visually ambiguous without explicit zero-value indicators.

### Figure 10

Figure 10 is a clear and well-constructed line chart comparing perplexity across four benchmarks. The axes are labeled with units, the legend distinguishes the two methods clearly, and the caption accurately reflects the visual data showing no consistent advantage for the learnable sink.

### Figure 11

The figure effectively compares the proposed method against a sliding-window baseline across six benchmarks, showing consistent perplexity improvements. However, the caption contains a missing subject in the comparison phrase, and the y-axis label is slightly redundant.

### Figure 12

The figure effectively visualizes the training loss curves and includes a helpful inset, but the caption is too brief to stand alone, and the inset's axis labels are too small to read clearly.
