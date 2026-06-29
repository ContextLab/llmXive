---
action_items:
- id: 5acec32c2436
  severity: writing
  text: "Figure\u202F1 (chaotic_models.png) lacks a legend explaining what node colors\
    \ or edge styles represent; add a concise legend and ensure the caption explicitly\
    \ defines nodes\u202F=\u202Fmodels and edges\u202F=\u202Fexplicit baselines."
- id: cb5a9c99ab80
  severity: writing
  text: "Several heatmaps (e.g., Fig\u202F3 main_hitmap.png, Fig\u202F4 category_summary.png,\
    \ Fig\u202F6 high\u2011variance tasks) use a red\u2011to\u2011green color map\
    \ without a color\u2011blind\u2011safe palette; switch to a palette such as viridis\
    \ or cividis and include a color bar with numeric MCC values."
- id: cedd1dc62fa4
  severity: writing
  text: "Axis labels and units are missing or ambiguous on many plots (e.g., Fig\u202F\
    2 image_per_size_v2.png lacks a label for the x\u2011axis \u2018Parameter count\
    \ (M)\u2019 and y\u2011axis \u2018Macro\u2011MCC\u2019); add clear axis titles\
    \ with units where applicable."
- id: 54db47fd86bb
  severity: writing
  text: "Font sizes in heatmaps and line plots are too small to be legible when printed\
    \ (e.g., model names and task labels in Fig\u202F3 and Fig\u202F5 are cramped);\
    \ increase label font size and consider rotating tick labels for readability."
- id: 400597a47fb8
  severity: writing
  text: "Captions for multi\u2011panel figures (e.g., Fig\u202F6 high\u2011variance\
    \ tasks) do not describe each panel (A) and (B) in sufficient detail; expand captions\
    \ to serve as alt text for accessibility."
- id: 03068ba1bc21
  severity: writing
  text: "Figure\u202F5 (few\u2011shot performance degradation) plots MCC values for\
    \ 40 models but does not include a legend indicating which line corresponds to\
    \ which model; add a legend or annotate key models directly on the plot."
- id: 1385a2fa4c65
  severity: writing
  text: "The Pareto frontier figures (e.g., Fig\u202F2, Fig\u202F7, and many category\u2011\
    specific pareto plots) often omit axis tick marks for parameter count (log\u2011\
    scale) making it hard to gauge model sizes; ensure tick marks and gridlines are\
    \ present."
- id: 8d95ab84a1cb
  severity: writing
  text: "Some figures are stored as compressed PNGs with noticeable artifacts (e.g.,\
    \ heatmap images in the zip archive); provide high\u2011resolution vector PDFs\
    \ for all figures to avoid loss of detail."
artifact_hash: 043e93d2fab619e0251c0029f296fc31d53c712bc78a466a1a30d67af8b711e1
artifact_path: projects/PROJ-679-geneb-why-genomic-models-are-hard-to-com/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T02:53:51.702593Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

The manuscript includes a large number of figures (over 30), each intended to convey critical benchmark insights. While the overall visual strategy is sound, several recurring issues undermine clarity and accessibility:

1. **Legends and Annotations** – The network diagram in Figure 1 (chaotic_models.png) shows nodes and edges but provides no legend; readers cannot infer the meaning of node colors or edge thicknesses without consulting the text. Similar omissions appear in heatmaps (Figures 3, 4, 6) where the color scale is shown but the mapping to MCC values is not labeled.

2. **Color Choices** – Many figures employ a red‑to‑green gradient that is not optimal for color‑blind readers. Switching to a perceptually uniform, color‑blind‑safe palette (e.g., viridis, cividis) would improve interpretability across the entire suite.

3. **Axis Labels & Units** – Figures that plot quantitative relationships (e.g., Figure 2 image_per_size_v2.png, Figure 5 avg_mcc_fewshot.png) lack explicit axis titles and units. Adding “Parameter count (M)” on the x‑axis and “Macro‑MCC” on the y‑axis would make the plots self‑contained.

4. **Readability at Print Scale** – Model names, task identifiers, and tick labels are rendered in very small fonts, especially in dense heatmaps. When printed, these become illegible. Increasing font sizes, using bold for key labels, and rotating long tick labels would preserve legibility.

5. **Captions as Alt Text** – Multi‑panel figures (e.g., Figure 6 high‑variance tasks) have brief captions that do not describe each sub‑figure. Expanding captions to include a short description of panels (A) and (B) would serve both as alt text for accessibility and as a quick reference for readers.

6. **Legends for Multi‑Line Plots** – The few‑shot degradation plot (Figure 5) overlays 40 model curves without a legend, making it impossible to identify individual models. Either a legend with distinct line styles or direct annotation of the most relevant models is needed.

7. **Axis Tick Marks on Log Scales** – Pareto frontier plots often omit tick marks on the log‑scaled parameter axis, obscuring the exact model sizes. Adding clear tick marks and optional gridlines would aid quantitative interpretation.

8. **Resolution and File Formats** – Several figures are supplied as compressed PNGs, leading to visible artifacts in fine details (e.g., heatmap cell boundaries). Providing vector‑based PDFs or high‑resolution PNGs (≥300 dpi) would ensure crisp reproduction in both digital and print formats.

Addressing these points will significantly enhance the figures’ clarity, reproducibility, and accessibility, allowing the benchmark results to be interpreted without ambiguity.
