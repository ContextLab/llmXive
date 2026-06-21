---
action_items:
- id: bf1ade7fc785
  severity: writing
  text: "Add explicit axis labels and units to Figure\u202F2 (Inference cost) \u2013\
    \ the current plot shows only a curve with no indication of what the y\u2011axis\
    \ represents (e.g., $$/hour, latency) or the x\u2011axis scaling (tokens, seconds)."
- id: 5d309e0cec27
  severity: writing
  text: "Replace the default colormap in Figure\u202F1 (Performance Comparison) with\
    \ a color\u2011blind\u2011friendly palette and ensure that the legend uses distinct\
    \ patterns or shapes for open\u2011source vs. closed\u2011source models."
- id: 031470d82f86
  severity: writing
  text: "Provide concise alt\u2011text descriptions for all case\u2011study figures\
    \ (Figures\u202F4\u20118) so that screen\u2011reader users can understand the\
    \ content without seeing the images."
- id: b483da835103
  severity: writing
  text: "Increase the line\u2011weight and font size of axis tick labels in the PDF\
    \ figures (e.g., keye_inference_cost.pdf) to guarantee legibility when printed\
    \ at 80\u202F% scale."
- id: ceaeb77d0912
  severity: writing
  text: "Ensure every figure is referenced in the main text before its first appearance;\
    \ currently Figure\u202F5 (dense caption example) is introduced only in the appendix."
artifact_hash: 5db0f3878ddf869f97ae5b85f5c21e6bee16133e4d0bee899b71eabf9aaf1f3a
artifact_path: projects/PROJ-692-kwai-keye-vl-2-0-technical-report/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-21T09:53:48.319692Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

The manuscript includes a substantial set of visual elements (Figures 1, 2, 3, 4‑8) that are central to the claimed performance gains and case‑study demonstrations. Overall, the figures are well‑integrated and the captions are informative, but several presentation issues hinder their effectiveness.

**Figure 1 (Performance Comparison)** – The caption clearly states the benchmarks, but the color scheme uses similar shades of blue and red that are difficult to differentiate for color‑blind readers. Adding patterned fills or a palette such as ColorBrewer’s “Set2” would improve accessibility. The axis labels are present, yet the units (e.g., “% accuracy”) are omitted; this should be added for clarity.

**Figure 2 (Inference cost)** – This is the most critical figure for the paper’s claim of cost efficiency. However, the plot lacks any axis labels or units, making it impossible to interpret the magnitude of the reported savings. The legend is also small and may become illegible when the PDF is printed. Adding explicit labels (e.g., “Cost ($/hour) vs. Context Length (tokens)”) and increasing font sizes will resolve this.

**Figure 3 (Dense caption example)** – The figure is a full‑width PDF showing timestamped captions. While the visual layout is clear, the font size of timestamps is borderline for print. A slight up‑scaling of the text and a brief alt‑text (e.g., “Scene‑wise dense caption table with timestamps and concise descriptions”) would aid accessibility.

**Case‑study figures (Figures 4‑8)** – These are rendered as PNGs of varying resolution. The heart‑circulation diagram (Figure 4) is high‑resolution, but the room‑layout and video‑preview images are compressed, leading to pixelation when zoomed. Providing vector‑based PDFs or higher‑resolution PNGs (≥300 dpi) would improve readability. Moreover, the manuscript does not include alt‑text for these figures, which is required for compliance with accessibility standards.

**General layout** – Across all figures, the line weight of plotted curves is thin, and tick labels are sometimes cramped. Consistently using a minimum line width of 1 pt and a font size of at least 9 pt for tick labels will ensure legibility at typical conference print scales (e.g., 80 % of the original size). Finally, each figure should be cited in the main body before its first appearance; a few case‑study figures are only mentioned in the appendix, which can confuse readers.

Addressing these issues will make the visual evidence much clearer, more accessible, and better aligned with the paper’s narrative.
