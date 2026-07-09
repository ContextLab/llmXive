---
action_items:
- id: ed7b208507c4
  severity: writing
  text: 'Figure 1: The caption text is truncated mid-sentence at the end (''...loss
    c [HiLS-Attn.png]''), leaving the explanation of the gradient flow incomplete.'
- id: b83eb21f0d04
  severity: writing
  text: 'Figure 2: The caption ''NSA kernel [kernel_design_NSA.pdf]'' is a placeholder
    filename rather than a descriptive summary of the diagram''s content.'
- id: 9118e88e26f8
  severity: writing
  text: 'Figure 2: The text inside the green box (''(K,d)-(d,S) Compute m Tensor Core'')
    is extremely small and illegible, making the specific operation unclear.'
- id: d0a0ba5bf908
  severity: science
  text: 'Figure 2: The diagram uses variable names (e.g., ''d'', ''S'', ''G'', ''M'')
    and specific tensor shapes without a legend or axis labels to define their dimensions
    or meaning.'
- id: df99f8788f95
  severity: writing
  text: 'Figure 3 caption: contains broken LaTeX syntax (''Tab. \& Tab.'') and a dangling
    file reference (''[1B_ppl_ruler_combined.pdf]'') that should be removed.'
- id: 855c81f94052
  severity: science
  text: 'Figure 3a: the y-axis label ''Perplexity'' is missing units or a note that
    lower is better, though this is standard, the scale jump to ''>10^2'' is abrupt
    and lacks a clear visual break or annotation style consistency with other values.'
- id: 95eee2eb5210
  severity: writing
  text: "Figure 3b: the y-axis label 'RULER average exact match (%)' is present but\
    \ the legend does not specify what 'Steps' refers to (training steps? inference\
    \ steps?), though context implies training steps \u2014 clarify in caption or\
    \ legend."
- id: be385740ae2f
  severity: writing
  text: 'Figure 4: The caption contains a typo ''at $$16K'' with an extraneous dollar
    sign.'
- id: d2e1449a4137
  severity: writing
  text: 'Figure 4: The x-axis label ''Latency (ms, log scale)'' is missing the ''/token''
    unit for panel (b), which is present in the caption but not the axis label.'
- id: c5b283294e73
  severity: science
  text: 'Figure 5: The left panel''s y-axis is labeled ''Chunk ids (log scale)'' but
    the caption describes it as ''loaded union size''; the axis label should be corrected
    to ''Loaded union size'' to match the description and data.'
- id: e74a73e7f4ca
  severity: writing
  text: 'Figure 5: The right panel''s y-axis label ''Overlap / reuse (%)'' is ambiguous;
    it should be clarified as ''Overlap / reuse fraction (%)'' or similar to distinguish
    between the two metrics being plotted.'
- id: 45663a88ad15
  severity: writing
  text: 'Figure 5: The legend in the right panel uses ''Layer range'' for the shaded
    region, but the caption defines it as ''layer-wise min--max range''; the legend
    should be updated to match the caption''s terminology.'
- id: 1221d98962a6
  severity: science
  text: 'Figure 6: The caption claims to compare ''HiLS-Attention'' vs ''full attention'',
    but the legend labels the baseline as ''Olmo3-CPT (YaRN)''. YaRN is a specific
    extrapolation method, not standard full attention, which misrepresents the comparison
    and the claim of ''strong long-context extrapolation advantages''.'
- id: 243312fc7b03
  severity: writing
  text: 'Figure 6: The y-axis label ''RULER average exact match (%)'' is rotated 90
    degrees and partially cut off at the top, making it difficult to read.'
- id: b63c502ff147
  severity: fatal
  text: 'Figure 7: The caption is explicitly ''(no caption)'', yet the figure contains
    a legend (''Olmo3-CPT (YaRN)'', ''Olmo3-HiLS-Attn'') and specific data points
    that are not defined in the text or other captions.'
- id: 19ab9ecb83e8
  severity: science
  text: 'Figure 7: The x-axis labels (8K, 16K, 32K, 64K, 128K, 256K, 512K, 1M) are
    not evenly spaced visually, but the axis is drawn as a linear scale, which misrepresents
    the exponential growth of context length.'
artifact_hash: c95e527feac1da55ce3c1a4f78a6e7762db38d741afaaaef5a9558e2491c1f16
artifact_path: projects/PROJ-1014-hierarchical-sparse-attention-done-right/paper/metadata.json
backend: dartmouth
feedback: Vision review of 7 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-09T02:56:44.129200Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

The figure provides a clear and well-structured visual overview of the HiLS-Attention mechanism, effectively contrasting it with Naive Block Sparse Attention. However, the figure caption is grammatically incomplete and cuts off abruptly at the end.

### Figure 2

Figure 2 provides a schematic of the NSA kernel but suffers from a placeholder caption and illegible internal text, making the specific computational steps difficult to verify.

### Figure 3

Figure 3 effectively compares Full-Attention RoPE and HiLS-Attention HoPE across training steps with clear annotations and legends, but the caption contains formatting errors and minor ambiguities in axis labeling that should be corrected for clarity.

### Figure 4

The figure effectively communicates the latency comparison and speedup metrics with clear annotations. Minor writing issues include a typo in the caption and a slight inconsistency in the x-axis label for panel (b) regarding the per-token unit.

### Figure 5

Figure 5 is generally clear and supports its claims, but has minor labeling inconsistencies between the axes/legends and the caption that should be corrected for precision.

### Figure 6

The figure effectively visualizes performance degradation but mislabels the baseline method in the legend compared to the caption, and the y-axis label is poorly formatted.

### Figure 7

Figure 7 lacks a descriptive caption, leaving the legend and data unexplained. Additionally, the x-axis uses a linear scale for exponentially increasing context lengths, which distorts the visual representation of the data.
