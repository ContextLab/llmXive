---
action_items:
- id: 90c0ae7bfb9c
  severity: writing
  text: "Several figures (e.g., Fig.\u202F1, Fig.\u202F5, Fig.\u202F6, Fig.\u202F\
    9) lack explicit axis labels and units, making it hard to interpret the plotted\
    \ quantities without referring to the main text."
- id: defa81b612de
  severity: writing
  text: "The color schemes (custom blue, gray, and multiple hues) are not verified\
    \ for color\u2011blind accessibility; consider using a palette that is distinguishable\
    \ for deuteranopia/protanopia."
- id: 307c24226ec4
  severity: writing
  text: "Some sub\u2011figures are very small (e.g., the wrap\u2011figure in Fig.\u202F\
    3 and the three\u2011panel Fig.\u202F5) and may become illegible at the final\
    \ print size; increase font sizes and line widths to ensure readability."
- id: fd8ff389eb0c
  severity: writing
  text: "Alt\u2011text or descriptive captions for the PDF are missing; include concise\
    \ descriptions for each figure to aid accessibility and for reviewers using screen\
    \ readers."
- id: 147d764ab902
  severity: writing
  text: "Figure\u202F2 (pipeline schematic) does not label the individual processing\
    \ steps (Hadamard rotation, variance\u2011normalization, RTN) directly on the\
    \ diagram, which would help readers quickly grasp the workflow."
- id: 6cb06c9733ab
  severity: writing
  text: "Figures that compare multiple methods (e.g., Fig.\u202F1b, Fig.\u202F5, Fig.\u202F\
    9) should include a legend within the figure area rather than relying on caption\
    \ text alone, to avoid confusion when printed in grayscale."
- id: cf91b80bb7d9
  severity: writing
  text: "The bar charts (Fig.\u202F6, Fig.\u202F8) lack y\u2011axis tick marks and\
    \ numeric scales; add these to convey the magnitude of the reported overheads\
    \ or errors."
- id: 1792404d2ced
  severity: writing
  text: "Ensure that all figures are referenced in the text with their correct numbers;\
    \ some captions refer to sub\u2011figures using \\ref{fig:scale:a} etc., but the\
    \ surrounding text does not always call them out, which can reduce clarity."
artifact_hash: 41b8c942a61f2cf7279ecdca15cbc48d6d8be293f3b82fe8c5a5b6e8c4e01484
artifact_path: projects/PROJ-657-https-arxiv-org-abs-2606-03458/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-20T04:37:05.459731Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

The manuscript contains a substantial number of figures that are central to the paper’s claims about error accumulation, magnitude‑error decomposition, and the efficacy of the proposed KVarN pipeline. While the visual content is generally relevant, several presentation issues hinder their effectiveness:

1. **Missing Axis Labels and Units** – Figures 1b, 5 (sub‑figures a–c), 6, 9, and the timing bar chart (Fig. 6) plot quantitative data but do not label the axes (e.g., “Error (MAE)”, “Context length (tokens)”, “Runtime (ms)”). Without these labels, readers must infer the meaning from the caption or the main text, which reduces immediate interpretability.

2. **Color‑Blind Accessibility** – The primary color palette (custom blue, gray, and other hues) is not verified for color‑blind safety. Since many readers rely on red‑green discrimination, the current scheme may cause confusion, especially in multi‑line plots such as Fig. 1b and Fig. 5b where several methods are overlaid.

3. **Legibility at Print Scale** – Several sub‑figures are rendered at a small fraction of the column width (e.g., the wrap‑figure in Fig. 3 and the three‑panel Fig. 5). The font size of axis tick labels and legends is borderline for the NeurIPS print format, risking illegibility after compression. Increasing the font size and line thickness would improve readability.

4. **Missing Legends Within Figures** – For multi‑method comparisons (Fig. 1b, Fig. 5, Fig. 9), the legend is placed only in the caption text. Embedding a concise legend directly in the figure area ensures that the plot remains self‑contained, especially when printed in grayscale where line styles or markers become the primary differentiators.

5. **Insufficient Descriptive Captions / Alt‑Text** – The PDF does not contain alt‑text for the included graphics. Adding a short description via the `\includegraphics[...]{...}` optional argument or using the `\caption*{}` mechanism would improve accessibility for screen‑reader users and aid reviewers who rely on text‑only views.

6. **Pipeline Diagram (Fig. 2) Lacks Inline Labels** – The schematic of the KVarN pipeline shows blocks but does not annotate each block with the operation name (e.g., “Hadamard rotation”, “Dual‑scale variance normalization”, “RTN quantization”). Adding these labels would make the figure understandable without constantly referring back to the text.

7. **Bar Charts Without Numeric Scales** – Figures 6 (runtime overhead) and 8 (outlier MSE contribution) present bars but omit y‑axis tick marks or numeric values. Including these scales allows readers to gauge the absolute magnitude of the reported improvements or overheads.

8. **Consistent Figure Referencing** – Some figures are referenced in the text using sub‑figure labels (e.g., “Fig. \ref{fig:scale:a}”) but the surrounding narrative does not always call out the figure explicitly, which can cause the reader to lose the thread. Ensure each figure is introduced with a brief statement of what it demonstrates.

Overall, the figures are essential to the paper’s argument, but their current presentation falls short of NeurIPS standards for clarity, accessibility, and print‑readability. Addressing the points above will significantly improve the manuscript’s visual communication and make the experimental evidence more compelling.
