---
action_items:
- id: 190b9458d4bc
  severity: fatal
  text: 'Figure 1: The caption and chart legends contain a placeholder ''.'' instead
    of the method''s name (likely ''RTPurbo'' based on the legend), rendering the
    figure''s subject undefined.'
- id: 27fe2c62b737
  severity: science
  text: 'Figure 1: The right panel''s x-axis labels (128K, 192K, 256K, 360K, 512K)
    do not align with the left panel''s labels (32K, 64K, 128K, 256K, 512K, 1M), making
    direct comparison of efficiency and accuracy at specific context lengths difficult.'
- id: 53d161a9ad09
  severity: writing
  text: 'Figure 1: The right panel''s y-axis label ''Accuracy (%)'' is present, but
    the bars are not explicitly labeled as accuracy values in the legend or caption,
    relying on the reader to infer the metric from the axis.'
- id: f122fdb95d15
  severity: writing
  text: 'Figure 2: The y-axis label ''Head Index'' is ambiguous; the caption mentions
    ''query heads'', but the axis includes indices up to 31, which may exceed the
    number of query heads per layer in the model, or implies a flattened index without
    explanation.'
- id: 5fd0836144e1
  severity: writing
  text: "Figure 2: The x-axis label 'Layer' and tick labels (0\u201347) suggest 48\
    \ layers, but the model name 'Qwen3-Coder-30B-A3B' does not clarify if this matches\
    \ the actual architecture; a note on layer count or model specs would improve\
    \ clarity."
- id: bd71c076473d
  severity: science
  text: 'Figure 2: No statistical context (e.g., averaging method, number of samples,
    or variance) is provided for the ''retrieval scores''; without this, the heatmap
    values lack interpretability regarding reliability or significance.'
- id: 3ab8c8b2bcaf
  severity: writing
  text: 'Figure 3: The x-axis label ''train/global_step'' is rendered as a grey text
    overlay on the plot area rather than a formal axis label, and the y-axis lacks
    a descriptive label (e.g., ''Loss'').'
- id: d5125f8b56e3
  severity: writing
  text: 'Figure 3: The plot contains a single data series but lacks a legend to explicitly
    identify the curve, relying solely on the caption for context.'
- id: d75682360083
  severity: writing
  text: 'Figure 4: The caption contains a missing subject (e.g., ''Unlike baselines
    that collapse..., [METHOD NAME] sustains robust accuracy...''). The figure shows
    ''RTPurbo'' in the legend, so the caption should explicitly name it.'
- id: fc96f0482d09
  severity: writing
  text: 'Figure 4: The right y-axis label ''Sparsity (%)'' is ambiguous; the line
    values (94-98%) represent the percentage of tokens *kept* (or sparsity ratio),
    but ''Sparsity'' usually implies the percentage of tokens *dropped*. Clarify if
    this is ''Retention Rate'' or ''Sparsity''.'
- id: e542b43a363a
  severity: writing
  text: 'Figure 5: The caption contains a missing subject (e.g., ''Sparse decoding
    speedup of [Model Name]''), making it grammatically incomplete and unclear.'
- id: c3e2ae028a12
  severity: science
  text: 'Figure 5: The y-axis labels ''Ours (Fused)'' and ''Full Attn (FA2)'' are
    not explicitly defined in the legend; the legend only lists specific kernel components
    (e.g., ''D16 Score + Top-p''), requiring the reader to infer the grouping.'
- id: 6fc6c05862e4
  severity: writing
  text: "Figure 5: The x-axis label 'Latency (\xB5s)' is repeated for all three subplots,\
    \ which is redundant and could be consolidated into a single label for the entire\
    \ figure."
- id: 3c9c09e210a2
  severity: fatal
  text: 'Figure 6: The caption reads ''Overall architecture of .'' with a missing
    model name, and the diagram contains multiple instances of the same missing name
    (e.g., ''sustains robust accuracy'' in Figure 4 caption context), indicating incomplete
    text rendering or copy-paste errors.'
- id: 13373559394d
  severity: science
  text: 'Figure 6: The ''Dynamic Top-p Selector'' inset shows a cumulative curve with
    p=0.9 but lacks axis labels for the curve itself (e.g., what is plotted on y-axis
    vs x-axis beyond ''Cumulative'' and ''p''), making the selection rule ambiguous.'
- id: d547d7424d60
  severity: writing
  text: 'Figure 7: The caption contains a missing model name (''Overview of the hardware-aware
    decoding kernel in .''), likely due to a placeholder or formatting error.'
- id: 82e18c98b68d
  severity: writing
  text: 'Figure 7: The legend items ''Sort-free top-p'' and ''Bandwidth-optimized''
    are not explicitly defined in the caption, though their association with the red
    and green boxes is visually clear.'
- id: 3528996eb868
  severity: science
  text: 'Figure 8: The figure displays abstract blocks labeled ''A'', ''B'', ''C''
    and a bar chart, but lacks the actual text passage or attention heatmap required
    to demonstrate ''semantic relatedness'' or ''similar patterns'' as claimed in
    the caption.'
- id: ed753837281d
  severity: science
  text: 'Figure 8: The orange arrows indicate a mapping from the first three blocks
    to the last three, but the middle section is obscured by ''......'', making it
    impossible to verify the ''long-range'' or ''far away'' context claim.'
- id: f582a3d61578
  severity: writing
  text: 'Figure 8: The bar chart below the blocks has no axes, units, or legend to
    explain what the bar heights represent or the difference between orange and teal
    colors.'
- id: 8a6f45b14809
  severity: writing
  text: 'Figure 9: The top panel''s x-axis label ''Token position'' is not aligned
    with the tick marks, and the top-right y-axis label ''Attn mass'' lacks a clear
    scale or unit definition in the caption.'
- id: f3678b489ab7
  severity: science
  text: 'Figure 9: The red curve in the bottom-left plot is labeled ''Retrieval head''
    but no corresponding legend entry exists for the gray ''Uniform'' line, making
    comparison ambiguous without external context.'
artifact_hash: 898687640cf9d8b6eab95a3e688a2f4f6333ec4f1546846934c46563afd8ae37
artifact_path: projects/PROJ-617-full-attention-strikes-back-transferring/paper/metadata.json
backend: dartmouth
feedback: Vision review of 9 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-04T02:00:37.081757Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

The figure effectively visualizes performance gains but is critically flawed by a missing method name in the caption and legends, and the x-axis scales between the two panels are inconsistent, hindering direct comparison.

### Figure 2

Figure 2 presents a clear heatmap of retrieval scores across layers and head indices, but lacks clarification on head indexing, model layer count alignment, and statistical grounding of the scores, which limits interpretability and scientific rigor.

### Figure 3

The figure displays a standard training loss curve with clear axes ticks, but it lacks formal axis labels and a legend, relying on the caption for context.

### Figure 4

The figure effectively displays accuracy and sparsity trends across sequence lengths with clear data labels. However, the caption is grammatically incomplete due to a missing subject, and the right y-axis label could be more precise regarding the definition of the sparsity metric.

### Figure 5

The figure effectively communicates latency comparisons across different sequence lengths, but the caption is grammatically incomplete with a missing subject, and the y-axis categories are not explicitly defined in the legend.

### Figure 6

Figure 6 provides a clear architectural overview but suffers from critical text omissions in the caption and diagram labels, and the Dynamic Top-p Selector lacks sufficient axis detail to interpret the selection mechanism.

### Figure 7

The figure provides a clear and well-structured overview of the hardware-aware decoding kernel workflow. However, the caption contains a grammatical error with a missing model name, and the legend keys are not explicitly defined in the text.

### Figure 8

The figure fails to substantiate its caption's claim about semantic retrieval because it uses abstract placeholders instead of actual text or attention maps, and the accompanying bar chart lacks necessary labels and axes.

### Figure 9

Figure 9 effectively illustrates diffuse retrieval but suffers from minor labeling inconsistencies and an incomplete legend that may confuse readers unfamiliar with the baseline.
