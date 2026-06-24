---
action_items:
- id: 1465eb7dbe4a
  severity: writing
  text: "Add descriptive alt\u2011text for every figure (e.g., \u201CFigure\u202F\
    3 shows three diagnostic plots of forward magnitude, gradient magnitude, and cosine\
    \ similarity versus transformer block index\u201D) to improve accessibility and\
    \ comply with publication standards."
- id: 8754addcf9f5
  severity: writing
  text: "Ensure all plots include clear axis labels with units where appropriate (e.g.,\
    \ training\u2011iteration count (K) on the x\u2011axis and FID (lower\u2011better)\
    \ on the y\u2011axis in Figure\u202F2; timesteps on the x\u2011axis and source\u2011\
    mixing importance on the y\u2011axis in Figure\u202F4)."
- id: f2f4905bef53
  severity: writing
  text: "Add colorbars or legends to heat\u2011map style figures (Figures\u202F4 and\u202F\
    7) that explain the meaning of the color scale (e.g., importance weight, speedup\
    \ factor, memory\u2011saving percentage)."
- id: f5aa7c9571db
  severity: writing
  text: "Check that line styles, markers, and text remain legible when the figures\
    \ are printed at typical conference column width (\u22483.25\u202Fin). Increase\
    \ line thickness or marker size if necessary."
- id: 769469df3689
  severity: writing
  text: "For multi\u2011panel figures (e.g., Figure\u202F1 and Figure\u202F2), provide\
    \ sub\u2011figure labels (a), (b), \u2026 in the caption and ensure each sub\u2011\
    figure is referenced correctly in the main text."
- id: c732393cfd9e
  severity: writing
  text: "Verify that any quantitative axes (e.g., latency speedup in Figure\u202F\
    7 left) include the scale (e.g., \u201C\xD7 speedup\u201D) and that the range\
    \ of values is appropriate for the plotted data."
artifact_hash: 7a4bc7e64a39662319f7490ada4c2be57d6c20dd18ca5f1225c2e0b697bf14b3
artifact_path: projects/PROJ-625-https-arxiv-org-abs-2605-20708/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-24T18:01:39.981509Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

The manuscript contains several informative figures, but many of them lack essential accessibility and clarity elements.  

**Figure 1 (PAGE1.pdf)** – a visual comparison for DMD. The caption describes the purpose, yet no alt‑text is supplied, and the figure is a raster image without any annotation of what is being compared. Adding a concise alt‑text and, if possible, overlaying brief labels on the compared images would help readers quickly grasp the differences.  

**Figure 2 (fid_training_curve.pdf)** – training FID curves. The caption mentions “Training FID curves”, but the figure does not explicitly label the x‑axis (training iterations) or y‑axis (FID). Units (e.g., “K iterations”) are missing, and the line thickness is thin, which may become illegible in print. A legend distinguishing ODE vs. SDE curves (if both are present) is also absent.  

**Figure 3 (symptoms.pdf)** – diagnostic symptoms across depth. The plot likely shows three curves versus block index, but the axes are not described in the caption. It is unclear whether the y‑axis is RMS magnitude, gradient magnitude, or cosine similarity, and the units (e.g., “RMS value”) are omitted. Adding axis titles and a legend for the three symptoms would make the figure self‑contained.  

**Figure 4 (fig_baseline_vs_attnres_source_mixing.pdf)** – source‑mixing heatmaps. The caption explains the methodology, yet the figure lacks a colorbar indicating the scale of the importance weights or routing weights, and the axes (timestep vs. source index) are not labeled. Without a legend, readers cannot interpret the magnitude of the values.  

**Figure 5 (DAR.pdf)** – schematic overview of the proposed routing. While the diagram is useful, it contains several small text labels that may be too fine for a two‑column layout. Increasing line weight and ensuring all component names are legible at print size is recommended. Alt‑text summarizing the flow (e.g., “Diagram showing query‑key attention over previous layer outputs to compute the aggregated hidden state”) should be added.  

**Figure 6 (fig_t_decode_agg_only_paper.pdf)** – linear‑probe R² results. The plot presumably has depth on the x‑axis and R² on the y‑axis, but the axes are not explicitly labeled, and the range of R² values (0–1) is not indicated. Adding axis titles and a brief caption note about the baseline (raw latents) would improve interpretability.  

**Figure 7 (infra_benchmark.pdf)** – infrastructure benchmark. The left panel shows latency speedup versus number of routed sources N, but the y‑axis label (“Speedup (×)”) is missing, and the right panel shows memory saving without a clear unit (percentage). Both panels need legends or color indicators for dynamic/static variants and forward/backward passes.  

Overall, the figures convey the core experimental findings, but the lack of axis labels, units, legends, and alt‑text hampers readability, reproducibility, and accessibility. Addressing these issues will make the visual evidence clearer and ensure the figures meet standard conference formatting requirements.
