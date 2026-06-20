---
action_items:
- id: a1ba7d368ba3
  severity: writing
  text: "Add concise, descriptive alt\u2011text for every figure (e.g., Fig.\u202F\
    1\u20137) so that screen\u2011reader users can understand the visualized metrics\
    \ such as step size\u202F\u03B4\u207D\u02B3\u207E, angular change\u202Fcos\u202F\
    \u03B8\u207D\u02B3\u207E, effective rank, KL\u2011divergences, etc."
- id: 3efe05693c29
  severity: writing
  text: Verify that all axes in the plotted figures have explicit labels (including
    units where applicable) and that legends are large enough to be legible when the
    figure is printed at column width.
- id: e2719701bf42
  severity: writing
  text: "Replace or augment the current colour\u2011only encodings with colour\u2011\
    blind\u2011safe palettes or add hatch/marker patterns, especially in heat\u2011\
    map figures (e.g., Fig.\u202F3 and Fig.\u202F4) where red\u2011green contrasts\
    \ are used."
- id: 4a65b60e2616
  severity: writing
  text: "Ensure that every caption fully defines all symbols and abbreviations used\
    \ in the figure (e.g.,\u202F\u03A9\u207D\u02B3\u207E,\u202F\u0394p\u207D\u02B3\
    \u207E,\u202Fg\u0304\u207D\u02B3\u207E,\u202FD_KL\u207D\u02B3\u207E) so that the\
    \ figure can be understood without referring back to the main text."
- id: 74e84fca1380
  severity: writing
  text: "Provide high\u2011resolution (300\u202Fdpi) PDF/PNG versions of all figures\
    \ for the final camera\u2011ready version to avoid loss of detail in print, and\
    \ check that line widths remain distinguishable at the final scale."
artifact_hash: a7ef470bc19c88e059a2cbeeef65085c1b552dfdce4bd956e635196d664635f0
artifact_path: projects/PROJ-733-loopcoder-v2-only-loop-once-for-efficien/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-20T21:33:23.204961Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

The manuscript contains a rich set of visualisations (Figures 1–7) that are central to the paper’s gain–cost analysis of Parallel Loop Transformers. Overall the figures are well‑chosen and support the narrative, but several presentation issues limit their clarity and accessibility.

**Clarity & Axis Labels**  
The plots (e.g., Fig. 1 “Step size δ⁽ʳ⁾ …”, Fig. 2 “Intrinsic offset cost Ω⁽ʳ⁾ …”) lack explicit axis titles in the source description. It is essential that the x‑axis (loop index r) and y‑axis (metric value) be labelled with units or scale (e.g., “δ⁽ʳ⁾ (‖·‖₂)”, “cos θ⁽ʳ⁾ (unitless)”). Legends for multiple series (PLT₂/₃/₄) should be large enough to read at column width.

**Colour Choices & Accessibility**  
Figures such as the attention‑heat‑map (Fig. 3) and the head‑similarity matrix (Fig. 4) rely on colour gradients that may be indistinguishable for colour‑blind readers. Introducing a colour‑blind‑safe palette (e.g., blue‑orange) or adding hatch patterns will improve interpretability. The same applies to line plots where red/green are used to differentiate curves.

**Legibility at Print Scale**  
Some captions reference small markers (e.g., “shaded bands are 95 % CIs over 500 samples (often narrower than the markers)”). When printed, these markers can become invisible. Increasing marker size or using thicker lines for confidence bands will ensure the visual information survives scaling.

**Alt‑Text & Captions**  
The current captions describe the high‑level trend but do not define every symbol (Ω⁽ʳ⁾, Δp⁽ʳ⁾, ḡ⁽ʳ⁾, D_KL⁽ʳ⁾). Adding a brief definition of each symbol within the caption, or providing a separate alt‑text block, will make the figures self‑contained and improve accessibility for readers using assistive technologies.

**Resolution & Print Quality**  
All figures are supplied as PDF files, which is appropriate, but the source PDFs should be generated at a minimum of 300 dpi. Verify that line widths and point markers remain distinguishable after the final typesetting shrinkage.

**Overall Assessment**  
The figures convincingly illustrate the paper’s core claim that loop 2 provides the primary refinement while later loops incur a fixed CLP offset cost. Addressing the above presentation concerns will make the visual evidence clearer, more reproducible, and accessible, thereby strengthening the manuscript.
