---
action_items:
- id: 32ecdae931c4
  severity: writing
  text: Simplify the teaser figure caption (Fig. 1) by moving detailed metric comparisons
    (e.g., 2.15x speedup) to the main text or a dedicated table to improve readability
    at print scale.
- id: 685a19f7add3
  severity: writing
  text: Ensure internal legends and axis labels in composite figures (e.g., Fig. A.1,
    Fig. A.5) are legible at 100% zoom; consider increasing font size for sub-figure
    annotations.
artifact_hash: 6191ec14b8389b89c96572533c3f6f5e9333a3f73e89fe363432c3a9d7429fb8
artifact_path: projects/PROJ-604-https-arxiv-org-abs-2605-18739/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-04T19:10:49.208400Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

The figure suite effectively communicates the system architecture and performance gains, but several figures require refinement for optimal legibility and accessibility.

Figure 1 (teaser) is central to the paper's narrative but suffers from caption density. The current caption mixes high-level descriptions with specific numerical results (e.g., "2.15$\times$ faster training"). For print legibility, move these specific metrics to Section 5 or a dedicated table, leaving the caption to describe the visual content. This reduces cognitive load when scanning the figure.

In the appendix, composite figures like Figure A.1 (Fig. interactive_ar_parallel_scaling) and Figure A.5 (Fig. shot_level_sink_ablation) contain multiple panels. Ensure that internal labels (e.g., "SP", "TP", "DP") are sufficiently large to remain readable when the PDF is viewed at 100% zoom. Small text in minipages often renders poorly on standard displays. Additionally, verify that color contrasts (e.g., `DeepRed` vs. black text) meet accessibility standards for colorblind readers, particularly in Figure A.1 where performance differences are highlighted by color.

Figure 3 (sp-training) and Figure 4 (clean-pipeline) are well-structured and clearly delineate the proposed method against baselines. The visual distinction between "Traditional SP" and "Balanced SP" is intuitive. However, Figure 5 (dmd_training) is quite small (`\begin{figure}[t]`). Consider expanding its width or ensuring the diagram complexity matches the allocated space to avoid clutter.

Figure 6 (async_inference) and Figure 7 (shot-level-sink) are critical for understanding the inference pipeline. Ensure that the flow arrows in Figure 6 are distinct enough to be traced without confusion, especially given the technical density of the asynchronous pipeline description.

Finally, while LaTeX does not enforce alt text, adding descriptive alternative text to `\includegraphics` commands (using the `alt` key in `graphicx` or `caption` package) would improve accessibility for screen readers. This is particularly relevant for the qualitative ablation figures (Fig. A.5, Fig. A.6) where visual evidence is the primary claim.

Overall, the figures earn their place by illustrating complex infrastructure co-design. Addressing the caption density and ensuring print-scale legibility for small annotations will elevate the presentation quality.
