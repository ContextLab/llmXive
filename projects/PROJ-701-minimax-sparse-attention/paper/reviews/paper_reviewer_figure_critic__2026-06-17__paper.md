---
action_items:
- id: f9cfb115d0f8
  severity: writing
  text: "Figure\u202F1 (msa_arch.png) is dense and uses several colors without a legend;\
    \ add a clear legend or annotate the color coding directly on the diagram, and\
    \ ensure all block arrows are labelled with their dimensions or purpose."
- id: cfd0bcff7f88
  severity: writing
  text: "Figures showing evaluation curves (e.g., idx_grad_1.png, msa_curves_reproduce.png,\
    \ training_lm_loss_fromscratch_vs_full.pdf) lack axis titles, units, and tick\
    \ label fonts that are legible at print scale; add explicit axis labels (e.g.,\
    \ \u201CTraining steps (\xD710\u2076)\u201D, \u201C\u0394\u202FScore (%)\u201D\
    ) and increase font size."
- id: e122520bd39b
  severity: writing
  text: "The heat\u2011map visualizations (vis_analysis_2.png, vis_analysis_3.png,\
    \ plot_sink_v2.png, learnable_sink_vis.png) do not include colorbars or scale\
    \ legends, making it impossible to interpret the magnitude of probabilities; include\
    \ a colorbar with quantitative tick marks."
- id: 3cb1b68f72cf
  severity: writing
  text: "Sub\u2011figures in the Appendix (e.g., the two\u2011panel Figure\u202F\r\
    ef{fig:vis-selection}) are placed side\u2011by\u2011side without consistent sizing\
    \ or labeling of (a) and (b) in the caption; ensure each sub\u2011figure is labeled\
    \ and referenced uniformly."
- id: 6644b934d470
  severity: writing
  text: Several PDF figures (efficiency_gqa_vs_msa.pdf, training_* .pdf) contain thin
    lines and small markers that become unreadable when printed; redesign with thicker
    lines or larger markers and consider vector graphics for crispness.
- id: 762668ab87bc
  severity: writing
  text: "Alt\u2011text descriptions are missing for all raster images; provide concise\
    \ alt\u2011text in the LaTeX source (e.g., \\includegraphics[...]{...}\\caption[Alt\u2011\
    text]{Full caption}) to improve accessibility."
- id: 922c922340a7
  severity: writing
  text: "Table\u202F\ref{tab:topk_latency} is presented as a figure file rather than\
    \ a proper LaTeX table, which reduces clarity; replace the image with a native\
    \ tabular environment."
- id: abfa54765246
  severity: writing
  text: "The \u201CTraining dynamics\u201D figures (Fig\u202F\ref{fig:training-dynamics-pt}\
    \ and Fig\u202F\ref{fig:training-dynamics-cpt}) mix multiple curves without a\
    \ legend distinguishing Full\u2011Attention vs. MSA; add a legend or use distinct\
    \ line styles."
artifact_hash: f00725508246b024cf4aa3c534e6f6afc166e2aa03bee30b44dd04e950f05991
artifact_path: projects/PROJ-701-minimax-sparse-attention/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-17T16:28:06.339076Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

The manuscript contains a substantial number of figures that are central to demonstrating the MiniMax Sparse Attention (MSA) design and its empirical benefits. While the overall selection of visualizations is appropriate, several recurring issues hinder their effectiveness.

**Clarity and labeling** – Many plots (e.g., the evaluation‑score delta heatmap, the training‑loss curves, and the efficiency graphs) omit explicit axis titles and units. Readers cannot readily infer the meaning of the horizontal “step” axis or the vertical “score” axis, and tick labels are often too small for print. Adding clear axis descriptors such as “Training steps (×10⁶)”, “Per‑token FLOPs (×10⁹)”, or “Δ Score (%)” would resolve this.

**Legends and color scales** – Heat‑map figures that display selection probabilities or sink attention (vis_analysis_2/3, plot_sink_v2, learnable_sink_vis) lack colorbars. Without a quantitative scale, the intensity of colors is ambiguous. Including a colorbar with numeric tick marks (e.g., 0.0 – 1.0) is essential. Similarly, the performance‑comparison plots overlay multiple curves (Full‑Attention, MSA‑PT, MSA‑CPT) but provide no legend; distinct line styles or a legend should be added.

**Sub‑figure organization** – In the Appendix, the two‑panel visualization of Index Branch selections (Fig \ref{fig:vis-selection}) presents the panels side‑by‑side but does not consistently label them as (a) and (b) within the caption. Uniform labeling improves navigability, especially when the figure is referenced in the text.

**Readability at print scale** – Several PDF figures use thin lines and small markers that become indistinct when the paper is printed or viewed at reduced size. Switching to thicker strokes, larger markers, or vector‑based graphics will ensure the figures remain legible in both digital and print formats.

**Accessibility** – The manuscript does not supply alt‑text for raster images. Providing concise alternative descriptions in the LaTeX source (using the optional argument of \\caption) will make the paper more accessible to screen‑reader users.

**Formatting consistency** – The latency comparison (Table \ref{tab:topk_latency}) appears as an image rather than a native LaTeX table, which reduces typographic quality and makes it harder to edit. Converting it to a proper tabular environment will align it with the rest of the paper’s style.

Addressing these issues will markedly improve the interpretability of the visual evidence and ensure that the figures fully support the paper’s claims.
