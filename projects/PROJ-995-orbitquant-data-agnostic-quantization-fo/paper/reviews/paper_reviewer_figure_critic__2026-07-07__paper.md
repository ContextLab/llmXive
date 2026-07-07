---
action_items:
- id: 63da0bf2413c
  severity: science
  text: "Figure 1: The mathematical notation in the central panel ($W' \tilde{x}'\
    \ \approx (W \Pi_d^\top)(\Pi_d x) = Wx$) is missing the rotation matrix $\Pi_d$\
    \ in the final equality term shown in the caption ($W'x' Wx$), creating a visual\
    \ disconnect between the diagram's logic and the caption's claim that the rotation\
    \ 'cancels'."
- id: aca0ec634415
  severity: writing
  text: 'Figure 1: The 3D surface plots in Panel 1 lack visible axis tick labels and
    units, making it impossible to verify the magnitude of the ''drift'' described
    in the caption.'
- id: 805d32cdb088
  severity: science
  text: 'Figure 4: The legend defines four methods (OrbitQuant, SmoothQuant, QuaRot,
    ViDiT-Q), but the right panel (Video) only displays three data points (OrbitQuant,
    SmoothQuant, ViDiT-Q). The QuaRot data point is missing, preventing a complete
    comparison for the video task.'
- id: 714144851d97
  severity: writing
  text: 'Figure 4: The x-axis label ''Latency (s/img)'' for the left panel implies
    a per-image metric, but the x-axis values (25-35) are unusually high for a single
    image inference step on modern hardware, suggesting the unit might be ''ms/img''
    or the metric is ''time per batch''. This ambiguity makes the performance claims
    difficult to verify.'
- id: ecb783f7e6ee
  severity: science
  text: 'Figure 5: The left panel''s x-axis labels (''BF16'', ''W4'', ''W3'', ''W2'')
    contradict the caption''s claim that ''AdaLN activations in BF16'' are fixed;
    the labels imply the activations are being quantized alongside the weights.'
- id: 2a3081560c6d
  severity: writing
  text: 'Figure 5: The right panel''s y-axis label ''Compression ratio'' is ambiguous;
    the caption clarifies it is ''model compression'', but the axis label alone does
    not specify if this is total model size or just the AdaLN component.'
artifact_hash: d056dc4f21ae1b95e98f52ede135ede40ce7ffad195ba83894f4cf9d35e33f1a
artifact_path: projects/PROJ-995-orbitquant-data-agnostic-quantization-fo/paper/metadata.json
backend: dartmouth
feedback: Vision review of 5 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-07T04:53:19.121170Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

Figure 1 effectively communicates the high-level workflow of OrbitQuant, but the 3D plots lack axis labels for verification, and the mathematical notation in the central panel is slightly inconsistent with the caption's description of the rotation cancellation.

### Figure 2

Figure 2 effectively visualizes the distribution of activation tokens across different rotation methods (Raw, Haar, RPBH) for two projection dimensions. The caption clearly defines all visual elements, including the dashed target curve, the KS distance insets, and the red codebook bin edges, ensuring the figure is self-contained and easy to interpret.

### Figure 3

Figure 3 effectively presents a qualitative comparison of image and video generation across different quantization methods. The layout is clear, with distinct rows for models and columns for methods, and the captions provide sufficient context to interpret the visual results without ambiguity.

### Figure 4

The figure effectively visualizes the trade-off between latency and memory, but the right panel is incomplete as it omits the QuaRot data point defined in the legend. Additionally, the latency units on the x-axis appear potentially incorrect or ambiguous, which hinders accurate interpretation of the performance gains.

### Figure 5

The figure effectively communicates the ablation results, but the left panel's x-axis labels conflict with the caption's description of fixed activation precision, and the right panel's axis label lacks specificity regarding the compression scope.
