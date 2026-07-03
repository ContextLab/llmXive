---
action_items:
- id: ae77bce05ebe
  severity: fatal
  text: 'Figure 1: The caption is explicitly ''(no caption)'', leaving the plot''s
    context, the definition of ''Mag.'', and the experimental setup undefined.'
- id: f93a06948c95
  severity: science
  text: 'Figure 1: The y-axis label ''Error fraction due to Mag.'' is ambiguous; it
    is unclear if this represents the fraction of total error or the fraction of magnitude,
    and the baseline (dashed line) is not defined.'
- id: 12240403eb02
  severity: writing
  text: 'Figure 2: The caption contains multiple placeholders (e.g., ''Schematic layout
    of .'', ''VarN($$)'', ''see e.g. Tab. .'') where the method name ''KVarN'' and
    specific table references should be, making the text incomplete.'
- id: a88b611ac6cb
  severity: writing
  text: 'Figure 2: The caption states ''We store... a second scale'' but does not
    explicitly define the symbol ''$s_2$'' shown in the diagram, relying on the reader
    to infer its meaning from the visual context.'
- id: 7c3cba4c0050
  severity: writing
  text: 'Figure 3: The caption contains a missing method name in the sentence ''is
    designed to operate in this regime''.'
- id: f4c65b71c5e4
  severity: writing
  text: 'Figure 3: The caption contains a missing reference in the sentence ''see
    e.g. Tab. .''.'
- id: 1bec77c2365d
  severity: science
  text: 'Figure 4: The y-axis label ''MAE(attention-output)'' is ambiguous; the caption
    refers to ''reconstruction error'' but does not specify if this is the error of
    the quantized cache against the original, or the error in the attention output
    itself, which are distinct metrics.'
- id: f997c8cc291c
  severity: writing
  text: 'Figure 4: The caption is a bare filename (''sinkh_only_l1_pooled_abs_Qwen_Qwen3-4B_ctx32768_B64_N8_K500000.pdf'')
    and lacks a descriptive sentence explaining the experimental setup, model, or
    context length (32k) shown in the filename.'
- id: 3b326e64d1e0
  severity: writing
  text: 'Figure 4: The x-axis label ''Context length (kTokens)'' is slightly non-standard;
    ''k'' usually implies 1000, but ''kTokens'' is not a standard unit abbreviation
    (e.g., ''k tokens'' or ''thousands of tokens'' is preferred).'
- id: 7f936fd21903
  severity: writing
  text: 'Figure 5: The x-axis labels (''VarN(.) all layers'', ''128-token generation'')
    are rotated and overlap, making them difficult to read; consider horizontal alignment
    or better spacing.'
- id: 6f3ca3085955
  severity: science
  text: 'Figure 5: The y-axis scales differ significantly across the three subplots
    (0-1200, 0-4000, 0-7000 ms), which visually exaggerates the relative overhead
    of variance normalization; using a consistent scale or normalizing the data would
    improve comparability.'
- id: 5cd0c44edcef
  severity: writing
  text: 'Figure 6: The caption is incomplete, containing only the title ''Arrangement
    of Hadamard transforms...'' and a filename, but lacks the explanatory text found
    in other captions (e.g., Figure 2) that describes the specific operations (e.g.,
    ''Every token is Hadamard-rotated...'').'
- id: ff2a03de8e70
  severity: science
  text: 'Figure 6: The diagram shows a Hadamard transform ($H$) applied to the $W_v$
    path, but the $W_q$ and $W_k$ paths show $H$ applied *after* RoPE. This contradicts
    the standard ''pre-RoPE'' rotation logic implied by the $W_q$/$W_k$ flow and the
    caption''s claim of a specific ''arrangement'' without explaining the discrepancy.'
- id: c7b44b24dfb0
  severity: science
  text: 'Figure 7: The caption claims ''KIVI and ablations of our method have substantial
    off-diagonals,'' but the ''HK'' and ''VarN(K)'' subplots show tight diagonal alignment
    with minimal off-diagonal spread, contradicting the text.'
- id: 25a412763906
  severity: writing
  text: 'Figure 7: The caption contains a missing subject in the phrase ''tightly
    controls token scales'' (likely ''KVarN''), making the sentence grammatically
    incomplete.'
- id: b075e90ff1b8
  severity: writing
  text: 'Figure 8 caption contains incomplete cross-references: ''complement Fig.
    .'' and ''see e.g. Tab. .'' lack specific figure/table numbers.'
- id: f996936ce1e5
  severity: writing
  text: 'Figure 8 caption has a grammatical error: ''It shows much MSE remains'' should
    be ''It shows how much MSE remains'' or ''It shows the remaining MSE''.'
- id: 9a19db04aac8
  severity: science
  text: Figure 8 caption claims to show MSE when replacing top k% errors, but the
    x-axis labels ('fix top 1%', 'fix bottom 99%', etc.) are ambiguous about whether
    bars represent MSE of the replaced portion or the remaining error.
- id: a0357904c15f
  severity: science
  text: Figure 8 lacks a legend explaining the blue vs. orange bar colors, which appear
    to represent different conditions not defined in the caption.
- id: bf8878c4dc60
  severity: science
  text: Figure 8 y-axis label 'MSE(fp16, variant)' is unclear about what 'variant'
    refers to; the caption does not specify which quantization method or baseline
    is being measured.
- id: 2c50d56326d7
  severity: writing
  text: 'Figure 9 caption: The phrase ''KIVI vs. under Static'' is grammatically incomplete;
    the second method name is missing (likely ''KVarN'' based on the paper title).'
- id: 7bccf1480e93
  severity: science
  text: 'Figure 9: The x-axis labels (3, 6, 9, 12, 16, 19, 22, 25, 28, 31) are non-uniformly
    spaced but plotted on a linear grid, which visually distorts the density of data
    points at higher context lengths.'
artifact_hash: 41b8c942a61f2cf7279ecdca15cbc48d6d8be293f3b82fe8c5a5b6e8c4e01484
artifact_path: projects/PROJ-657-https-arxiv-org-abs-2606-03458/paper/metadata.json
backend: dartmouth
feedback: Vision review of 10 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T01:21:04.718304Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

The figure is a bar chart with clear axes but lacks a functional caption, making the metric 'Error fraction due to Mag.' and the significance of the dashed baseline impossible to interpret.

### Figure 2

The figure provides a clear visual schematic of the KVarN pipeline, but the caption is marred by missing text placeholders for the method name and table references, and it fails to explicitly define the '$s_2$' symbol shown in the diagram.

### Figure 3

The figure effectively illustrates the proposed pseudo-decode setting and error accumulation mechanism. However, the caption contains two instances of missing text where the method name and a table reference should be.

### Figure 4

The figure clearly displays the performance curves for KIVI and KVarN, but the caption is insufficient as it merely lists a filename without describing the experiment, and the y-axis label lacks specific definition regarding the error metric.

### Figure 5

Figure 5 presents timing data clearly with labeled bars, but the overlapping x-axis labels reduce readability, and the inconsistent y-axis scales across subplots may mislead interpretation of the overhead magnitude.

### Figure 6

The figure provides a clear schematic of the attention layer, but the caption is incomplete and lacks the descriptive detail found in other figures. Additionally, the placement of the Hadamard transform relative to RoPE differs between the query/key and value paths without explanation.

### Figure 7

The figure effectively visualizes the joint distributions, but the caption contains a grammatical error and makes a claim about 'ablations' having off-diagonals that is not supported by the visual evidence in the HK and VarN(K) subplots.

### Figure 8

Figure 8's bar chart is visually clear but suffers from multiple caption issues including incomplete cross-references, grammatical errors, and insufficient explanation of the plotted data and color coding.

### Figure 9

The figure effectively visualizes the Needle-in-a-Haystack results with a clear legend, but the caption contains a grammatical error omitting the second method's name, and the x-axis uses non-uniform spacing on a linear scale.

### Figure 10

Figure 10 is a clear and well-constructed bar chart that effectively communicates the median dequantization time for KIVI and KVarN across different context lengths. The axes are labeled with appropriate units, the legend is distinct, and the specific values are annotated directly on the bars, making the data easily interpretable and consistent with the caption.
