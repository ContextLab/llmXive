---
action_items:
- id: '748723830779'
  severity: science
  text: "Figure 4: The 'Decode Cost' y-axis scale is inconsistent with the 'Prefill\
    \ Cost' scale (0.0\u20133.2 vs 0.0\u20130.06), yet the visual height of the 'Full\
    \ Attention' line is nearly identical in both plots. This creates a misleading\
    \ visual impression that the absolute cost reduction is similar in both phases,\
    \ whereas the caption and axis labels imply a much larger absolute saving in decode.\
    \ The scales should be comparable or explicitly noted as different to avoid misinterpretation."
- id: a32ff002d48d
  severity: writing
  text: 'Figure 4: The legend at the top right (''DSA'' and ''Full Attention'') is
    not directly connected to the lines in the plots; while colors match, adding a
    small line sample next to each label in the legend would improve clarity.'
- id: f898fd716132
  severity: science
  text: 'Figure 5: The caption states ''Higher is better unless otherwise specified,''
    but the benchmark ''Video-MME-v2 ACC (64 Frames/512 Frames)'' lists ''ACC'' (Accuracy),
    which is a percentage metric. The values (e.g., 35.3 / 42.4) are likely percentages,
    yet the caption''s phrasing suggests a general rule that might confuse readers
    if some benchmarks are actually loss-based or require lower scores. The caption
    should explicitly list any benchmarks where ''Lower is better'' to avoid ambiguity,
    or confirm all '
- id: 65c93819d5d9
  severity: writing
  text: 'Figure 5: The benchmark name ''Video-MME-v2 ACC (64 Frames/512 Frames)''
    is split across two lines in a way that breaks the logical grouping of the metric
    name and its configuration. It should be formatted to keep ''Video-MME-v2 ACC''
    together or clearly indicate the frame configurations as sub-rows or a single
    continuous label.'
- id: 7fd68f35cd17
  severity: writing
  text: 'Figure 5: The benchmark ''VideoMMMU'' is listed without a clear definition
    of what ''MMMU'' stands for in the context of video (e.g., is it a video adaptation
    of the MMMU benchmark?). While the caption mentions ''detailed benchmark descriptions...
    provided in the subsections below,'' the figure itself should ideally include
    a footnote or abbreviation key for clarity.'
artifact_hash: 5db0f3878ddf869f97ae5b85f5c21e6bee16133e4d0bee899b71eabf9aaf1f3a
artifact_path: projects/PROJ-692-kwai-keye-vl-2-0-technical-report/paper/metadata.json
backend: dartmouth
feedback: Vision review of 5 figure(s) via qwen.qwen3.5-122b.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T19:27:20.113322Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: major_revision_science
---

### Figure 1

Figure 1 is a clear and well-structured schematic that effectively communicates the four-stage pre-training pipeline. The visual hierarchy, parameter status indicators, and data scale metrics are legible and align perfectly with the provided caption.

### Figure 2

Figure 2 is a clear and well-structured schematic that effectively visualizes the four-stage pre-training pipeline described in the caption. All stages, parameter statuses (ViT, Projector, LLM), sequence lengths, data scales, and data types are clearly labeled and legible, with no missing controls or misleading scales.

### Figure 3

Figure 3 effectively illustrates the scene-wise dense captioning concept with a clear visual breakdown of a video timeline into four distinct scenes. The layout is uncluttered, and the detailed text descriptions for each scene align perfectly with the provided caption and the visual content shown in the filmstrip.

### Figure 4

Figure 4 effectively illustrates cost reductions but uses inconsistent y-axis scales between the two subplots, which may mislead readers about the relative magnitude of savings. Minor legend improvements would enhance clarity.

### Figure 5

Figure 5 is a clear and well-organized table summarizing the model's performance across various benchmarks. However, the caption's statement about 'Higher is better' could be more precise by explicitly confirming that all listed metrics follow this rule, and some benchmark names could be formatted for better readability.
