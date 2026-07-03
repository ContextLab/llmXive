---
action_items:
- id: e8110b32b3e8
  severity: science
  text: 'Figure 1: The bar chart on the right shows ''Accept length'' for EAGLE3 (4.86)
    and Domino (4.70) as higher than DFlash (4.03), yet the ''Speedup'' for EAGLE3
    (3.28) and Domino (3.84) is lower than DFlash (3.42). This contradicts the caption''s
    claim that speedup is evaluated on GSM8K, as higher acceptance length should generally
    correlate with higher speedup, suggesting a potential data labeling or calculation
    error.'
- id: 7dadc5fdfbc4
  severity: writing
  text: 'Figure 1: The legend for the left panel uses five distinct shades of blue
    to represent ''verify'', ''draft'', ''LM Head'', ''DHead'', and ''Tree'', but
    the ''verify'' and ''draft'' bars are identical in color to the first two legend
    entries, while the remaining three categories are represented by progressively
    lighter shades that are difficult to distinguish visually, especially in the ''EAGLE3''
    bar where multiple small segments are present.'
- id: 07ee845e6853
  severity: science
  text: 'Figure 2: The legend includes ''DART'' (yellow bars), but the caption only
    lists ''Domino, DFlash, and EAGLE-3''. The figure presents data for an unlisted
    method, creating a mismatch between the visual content and the description.'
- id: 22e1bcd15b63
  severity: science
  text: 'Figure 2: The x-axis labels (e.g., GSM8K, MATH) represent specific datasets,
    but the caption describes the figure as a general ''Speedup comparison... on Qwen3-8B''
    without explicitly stating that the comparison is broken down by these specific
    benchmarks.'
- id: f6c310087718
  severity: science
  text: 'Figure 3: The diagram shows the ''Domino Head'' receiving hidden states $h_0,
    h_1, h_2$ as inputs to the MLPs, but the caption states the head updates causal
    state from ''previously sampled draft tokens'' ($d_i$). The visual flow contradicts
    the textual description of the mechanism.'
- id: ea345967e34e
  severity: writing
  text: 'Figure 3: The legend defines ''Draft token'' as a gray box, but the diagram
    uses gray boxes for $d_0, d_1$ (inputs to the head) and $d_0, d_1, \dots, d_N$
    (outputs), creating ambiguity about whether the gray boxes represent the input
    to the MLP or the final sampled token.'
artifact_hash: ac9b2293924c2f0c1f04178796bb698ee01d07baef5d80d5250c3c91d8a5b9a5
artifact_path: projects/PROJ-654-https-arxiv-org-abs-2605-29707/paper/metadata.json
backend: dartmouth
feedback: Vision review of 4 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T15:23:14.487356Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

Figure 1 presents latency breakdowns and performance metrics, but the right panel's data appears inconsistent (higher acceptance length does not yield higher speedup), and the left panel's legend uses overly similar colors for distinct categories, reducing clarity.

### Figure 2

The figure is visually clear with data labels, but the legend includes a method ('DART') that is not mentioned in the caption, and the caption fails to explicitly identify the x-axis categories as specific datasets.

### Figure 3

The figure provides a clear visual overview of the Domino architecture, but there is a discrepancy between the diagram's data flow (using hidden states $h_i$ as inputs) and the caption's description (using sampled draft tokens). Additionally, the legend's definition of 'Draft token' is ambiguous regarding its role in the diagram.

### Figure 4

Figure 4 effectively presents the training strategy ablation results. The left panel clearly contrasts the parallel backbone loss with and without the curriculum, while the right panel accurately displays average acceptance lengths for the three strategies against the DFlash reference line, with all necessary labels and legends present.
