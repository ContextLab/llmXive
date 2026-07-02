---
action_items:
- id: f32ef6b7374d
  severity: science
  text: 'Figure 1: The caption claims the figure shows ''Iteration speed and peak
    memory'' with ''Left: iteration speed. Right: peak memory,'' but the rendered
    image contains only a single chart showing ''Training Time per Iteration'' (speed).
    The peak memory data is missing.'
- id: 5fdf3e62c431
  severity: science
  text: 'Figure 1: The x-axis label ''Training Video Frames'' (128, 256, 512, 768)
    contradicts the caption''s reference to ''sequence lengths'' and ''long contexts,''
    creating ambiguity about whether the x-axis represents frame count or token sequence
    length.'
- id: d0cf099a682b
  severity: writing
  text: 'Figure 2 caption: The sentence ''With the multi-shot attention sink stabilizes
    shot-level appearance'' is grammatically incorrect and should be rephrased (e.g.,
    ''With the multi-shot attention sink, shot-level appearance is stabilized'').'
- id: 3181591c860a
  severity: science
  text: 'Figure 3: The ''PTQ'' and ''Ours'' rows depict completely different video
    scenes (different furniture, lighting, and background portraits), making a direct
    comparison of ''temporal visual quality'' or facial details scientifically invalid.'
- id: acca77ac507e
  severity: writing
  text: 'Figure 3: The caption states the first column shows the ''initial frame,''
    but the images in the ''Shot 1'' column are visually distinct between the PTQ
    and Ours rows, contradicting the premise of a controlled comparison.'
- id: 0e8228cf0d79
  severity: writing
  text: 'Figure 4: The caption text is truncated at the end (''...various t''), cutting
    off the sentence and likely the citation.'
- id: c560b6eec4a5
  severity: science
  text: 'Figure 4: The label ''DMD on Diffusion Model (with AR mask)'' is visually
    unaligned and appears to be a third category rather than a description of the
    ''Standalone LoRA injection'' row, creating ambiguity about the experimental setup.'
- id: bb275c013984
  severity: science
  text: 'Figure 5: The ''Training Infra'' box shows ''LoRA Few-step'' as a distinct
    input to the final model, but the caption describes LoRA as ''standalone weights''
    derived in parallel. The diagram implies LoRA is a training step added to the
    AR model, whereas the text suggests it is a separate injection for inference,
    creating ambiguity about the training pipeline''s output.'
- id: 542fd5ca6944
  severity: writing
  text: 'Figure 5: The ''Inference Infra'' box lists ''VAE Async Decode'' but does
    not visually connect the VAE to the ''Model'' output in the same way the ''Training
    Infra'' connects components, making the data flow for asynchronous decoding unclear.'
- id: f83e79058099
  severity: writing
  text: 'Figure 6: The legend at the top of the middle panel defines ''Video Seq.''
    and ''Halo'' with specific fill patterns, but the ''Clean Latent Seq.'' and ''Noisy
    Latent Seq.'' entries in the same legend lack the corresponding fill pattern swatches,
    making them visually ambiguous.'
- id: 4f6c82803134
  severity: writing
  text: 'Figure 6: The ''NVFP4 GEMM Speedup 2-4x'' label in the right panel is a floating
    text annotation without a clear visual pointer or bracket indicating exactly which
    components (e.g., DGDRAD, WGRAD, FPROP) constitute the speedup.'
- id: bf2ce3f886d3
  severity: science
  text: 'Figure 7: The ''LongLive 2.0'' column depicts a feedback loop labeled ''DMD''
    and ''LoRA Weights'' on the AR Model, but the caption explicitly claims the method
    ''bypasses... intermediate DMD'' and achieves results by ''injecting standalone
    LoRA weights''. The diagram contradicts the text by showing DMD as part of the
    LongLive 2.0 pipeline rather than a separate pre-training step.'
- id: 8c81bdf03826
  severity: writing
  text: 'Figure 7: The ''LongLive 2.0'' column contains a red arrow and text (''LoRA
    Weights'') that are visually cluttered and overlap with the ''AR Model'' box,
    making the diagram difficult to parse.'
- id: 1e6b1e0b1b67
  severity: science
  text: 'Figure 8: The diagram shows ''LoRA BF16'' modules attached to the Generator
    and Fake Score models, but the caption describes a ''low-precision NVFP4 setup''
    without explaining the presence of BF16 LoRA weights or how they interact with
    the NVFP4 quantization.'
- id: cc43a660263b
  severity: writing
  text: 'Figure 8: The ''update'' arrows and ''Diffusion Loss''/''DMD Loss'' boxes
    are extremely small and low-contrast, making the specific gradient flow paths
    difficult to trace and read.'
- id: 8a03bc2b36f7
  severity: science
  text: "Figure 9: The diagram labels the top row 'NVFP4 KV Cache Window' but the\
    \ text 'Memory 10GB\u2193' is placed ambiguously near the window boundary without\
    \ a clear pointer indicating if it refers to the window size or total memory reduction."
- id: 5e80971b872b
  severity: writing
  text: 'Figure 9: The ''Wait / Idle'' block in the bottom row is unlabeled with a
    chunk index (0-4) like the others, making the timeline alignment slightly ambiguous
    compared to the rest of the sequence.'
- id: c09845e1471b
  severity: science
  text: 'Figure 10: The diagram illustrates the ''Multi-shot Attention Sink'' mechanism
    with visual examples and a heatmap, but it lacks a quantitative plot (e.g., attention
    weights vs. token index) or explicit numerical labels to substantiate the claim
    of ''sink'' behavior or the specific attention distribution.'
- id: 0467f0c87309
  severity: writing
  text: 'Figure 10: The caption is a single phrase (''Multi-shot Attention Sink for
    streaming multi-shot inference'') that merely names the figure rather than explaining
    the visual components (e.g., the meaning of the blue squares, the ''Key''/''Query''
    arrows, or the specific role of the ''Global-level Sink'' vs ''Shot-level Sink'').'
artifact_hash: de9cc7b61426b053f14e2745d8dcacce77bcfbd73c84f2c8e9aae072a3bf9bd1
artifact_path: projects/PROJ-604-https-arxiv-org-abs-2605-18739/paper/metadata.json
backend: dartmouth
feedback: Vision review of 10 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T08:02:57.046396Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

The figure is incomplete as it only displays the iteration speed data while the caption explicitly promises a second chart for peak memory. Additionally, the x-axis label 'Training Video Frames' conflicts with the caption's terminology regarding sequence lengths.

### Figure 2

The figure effectively demonstrates the visual difference between the model with and without the multi-shot attention sink, but the caption contains a grammatical error in the final sentence.

### Figure 3

The figure fails to provide a valid comparison because the PTQ and Ours rows display entirely different video scenes rather than the same content processed by different methods, rendering the visual evidence for the caption's claims invalid.

### Figure 4

The figure effectively visualizes the comparison between the two strategies, but the caption is truncated at the end, and the third text label is positioned ambiguously, potentially confusing the reader about the row definitions.

### Figure 5

The figure provides a high-level overview but contains ambiguities in the training pipeline regarding the role of LoRA and lacks clear data flow connections in the inference section for VAE decoding.

### Figure 6

Figure 6 effectively illustrates the training infrastructure and load balancing concepts, but the legend in the middle panel is incomplete as it omits fill patterns for two entries, and the speedup claim in the right panel lacks a precise visual indicator.

### Figure 7

The figure effectively contrasts the pipeline steps of previous methods with LongLive 2.0, but the diagram for LongLive 2.0 contradicts the caption by including a DMD loop that the text claims is bypassed.

### Figure 8

The figure provides a high-level schematic of the DMD training infrastructure but lacks clarity on the specific data types (BF16 vs NVFP4) used in the LoRA modules and suffers from poor legibility in the loss calculation and update flow annotations.

### Figure 9

The figure effectively illustrates the asynchronous decoding pipeline and memory benefits, but the specific memory reduction claim lacks a precise visual pointer, and the timeline alignment for the initial idle state is slightly inconsistent with subsequent chunks.

### Figure 10

Figure 10 provides a schematic overview of the attention sink mechanism but lacks the quantitative data or detailed annotations necessary to scientifically demonstrate the attention distribution. Additionally, the caption is too brief to explain the specific visual elements shown in the diagram.
