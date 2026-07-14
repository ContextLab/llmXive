---
action_items:
- id: 289875bdc578
  severity: writing
  text: 'Figure 1 caption: The phrase ''GPTQ, GPTAQ, and on LLaMA-2-13B'' is grammatically
    incomplete; it omits the third method name before the model list, though the legend
    identifies KronQ.'
- id: ba9f53338664
  severity: writing
  text: 'Figure 1 caption: The list of methods ''GPTQ, GPTAQ, and KronQ'' is grammatically
    incomplete; it omits the third method name before the model list, though the legend
    identifies KronQ.'
- id: a6a2c5aa2467
  severity: writing
  text: Figure 2(a) caption contains a typo '$$-incoherence' instead of the symbol
    '$\mu$-incoherence' shown on the plot axis.
- id: 0088aed88fe3
  severity: science
  text: Figure 2(b) y-axis labels (0, 1024, 2048, 3072, 4096) are inverted (0 at top,
    4096 at bottom), which contradicts the standard convention for matrix visualization
    where row 0 is typically at the top.
- id: 36d2d3f4bf36
  severity: writing
  text: 'Figure 3: The y-axis labels use single letters (o, k, q, v) which are ambiguous
    without a legend or explicit definition in the caption stating they correspond
    to the output, key, query, and value projections.'
- id: d5e2308992b1
  severity: writing
  text: 'Figure 3: The labels ''#4 o'', ''#5 k'', etc., are rendered with a vertical
    bar artifact (e.g., ''k|'', ''q|'') likely due to a font rendering error, making
    them look like ''k|'' or ''q|'' instead of just the letter.'
- id: 1901741b13f8
  severity: science
  text: 'Figure 4: The x-axis labels (2.0, 2.17, 2.29, 2.43, 2.57, 3.0) are non-uniform
    and do not correspond to the visual spacing of the data points, making the ''Average
    Bit-width'' scale misleading and difficult to interpret.'
- id: 53f147e725f7
  severity: writing
  text: 'Figure 4: The inset plot''s x-axis is labeled only with ''3.0'', failing
    to show the full range of bit-widths for the zoomed-in region, which limits the
    utility of the inset for comparing the methods at that specific scale.'
- id: b9c051e6307b
  severity: science
  text: 'Figure 5: The caption states the data is ''relative to the bf16 baseline,''
    but the y-axes are labeled with absolute units (''Peak VRAM (GB)'' and ''TPOT
    (ms/token)'') and the bars show absolute values (e.g., ~100 GB) rather than relative
    ratios. This contradicts the caption''s description of the data presentation.'
- id: b6037a7df0e8
  severity: writing
  text: 'Figure 5: The legend in panel (a) includes ''W2'', but the corresponding
    dark blue bars are not visible in the chart, likely obscured by the ''W4'' bars
    or missing entirely, making the data for W2 unreadable.'
- id: e6c7cbafaadd
  severity: writing
  text: 'Figure 6: The caption is explicitly ''(no caption)'', leaving the plot unexplained
    and failing to define the context (e.g., model size) or the specific methods being
    compared.'
- id: dad68d191f14
  severity: science
  text: 'Figure 6: The inset plot''s x-axis is labeled ''3.0'' without a range or
    tick marks, making it impossible to determine the bit-width scale or the specific
    data points being highlighted.'
- id: 6b8eac1d0d82
  severity: writing
  text: 'Figure 6: The x-axis label ''Average Bit-width'' is present, but the axis
    ticks (2.0, 2.17, etc.) are rotated and crowded, reducing readability.'
- id: da10eb5ca526
  severity: writing
  text: 'Figure 7: The provided image is a 3-panel plot showing ''Original'', ''$H_X$
    only'', and ''$H_X + H_G$'' weight distributions with $CV_{in/out}$ metrics, which
    matches the content of Figure 2(b) in the paper, not Figure 7. The caption ''Weight
    distributions of LLaMA-2-70B'' does not match the visual content shown.'
- id: c83f5593a61b
  severity: science
  text: 'Figure 7: The figure displays data for LLaMA-2-7B (inferred from the 8192
    channel dimension and similarity to Figure 2), but the caption claims it shows
    LLaMA-2-70B. This is a factual mismatch between the visual data and the caption.'
artifact_hash: 6bdf7827fba12b0d8bdf1afc2ca37e869d5688f3fbc4e54d47c586b30e10b890
artifact_path: projects/PROJ-1045-kronq-llm-quantization-via-kronecker-fac/paper/metadata.json
backend: dartmouth
feedback: Vision review of 7 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-14T04:02:05.993460Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

The figure is visually clear and effectively communicates the data, but the caption contains a grammatical error where the third method (KronQ) is omitted from the text list, leaving the sentence incomplete.

### Figure 2

The figure effectively visualizes the incoherence and weight distribution changes, but the caption contains a typo regarding the incoherence symbol, and the matrix plots in panel (b) use an inverted y-axis that may confuse readers.

### Figure 3

The figure effectively visualizes the sensitivity rankings described in the caption, but the y-axis labels use ambiguous single-letter abbreviations without a legend, and some labels suffer from a rendering artifact that adds a vertical bar.

### Figure 4

The figure effectively compares perplexity across methods, but the non-uniform x-axis scale is misleading, and the inset plot lacks a complete x-axis scale for the zoomed-in data points.

### Figure 5

The figure presents absolute values on the axes while the caption claims the data is relative to a baseline, creating a contradiction. Additionally, the W2 data series defined in the legend is not visible in the chart.

### Figure 6

The figure presents a perplexity vs. bit-width comparison but lacks a descriptive caption to identify the model or methods. Additionally, the inset plot's x-axis is poorly defined, and the main axis labels are cluttered.

### Figure 7

The figure content appears to be a duplicate of Figure 2(b) (showing LLaMA-2-7B weight distributions) rather than the LLaMA-2-70B data described in the caption. The visual data (8192 channels) contradicts the caption's claim of 70B model data.
