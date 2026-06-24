---
action_items:
- id: 9f1473981a5f
  severity: writing
  text: "Add explicit axis labels (including units, e.g., meters for trajectory plots)\
    \ to all quantitative figures such as Fig.\u202F4 (verb diversity), Fig.\u202F\
    5 (object diversity), Fig.\u202F7 (pick\u2011and\u2011place success), and Fig.\u202F\
    8 (DROID L2 error)."
- id: 9b7fa6030df8
  severity: writing
  text: "Indicate the log\u2011scale nature of the bar charts (Fig.\u202F4, Fig.\u202F\
    5) directly on the y\u2011axis or in the caption to avoid misinterpretation."
- id: 2813fa615879
  severity: writing
  text: "Replace or supplement current color palettes with a color\u2011blind\u2011\
    friendly scheme (e.g., using ColorBrewer palettes) for all multi\u2011color plots,\
    \ especially the bar charts and the qualitative trajectory visualizations (Fig.\u202F\
    6, Fig.\u202F10)."
- id: 5c41439c1880
  severity: writing
  text: "Provide concise alt\u2011text descriptions for each figure (e.g., \u201C\
    Fig\u202F1: schematic of goal\u2011conditioned 3D point motion forecasting pipeline\u201D\
    ) to improve accessibility for readers using screen readers."
- id: a665bf0d49e3
  severity: writing
  text: "Increase line thickness and marker size in 3D trajectory visualizations (Fig.\u202F\
    6, Fig.\u202F10, Fig.\u202F12) so that details remain legible when printed at\
    \ typical journal column widths."
- id: 7509f2ca33da
  severity: writing
  text: "Ensure that all figures are saved at a minimum of 300\u202Fdpi resolution\
    \ and that vector graphics (PDF) are used for line\u2011drawings to maintain clarity\
    \ in print."
- id: 50535905ef8f
  severity: writing
  text: Verify that figure captions fully describe the content, including what each
    color or symbol represents, and reference any abbreviations used within the figure.
artifact_hash: 43d44b1b7f12aef158eaf0787875484ea72c6860cf8af3c796e4579ec99e55ab
artifact_path: projects/PROJ-741-molmomotion-forecasting-point-trajectori/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-24T15:41:14.340105Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

The manuscript includes a substantial number of figures (≈ 15) that are central to communicating the proposed task, model architecture, data pipeline, and experimental results. Overall the visual material is relevant and generally well‑designed, but several recurring issues affect clarity and reproducibility:

1. **Quantitative plots lack explicit axis labels and units** – The bar charts showing verb and object diversity (Figs. 4 and 5) present counts on a log‑scaled y‑axis but the axis label does not specify the scale or units, which can mislead readers. Similarly, the robot‑transfer plots (Figs. 7 and 8) omit units for the y‑axis (percentage success, L2 error in meters) and sometimes lack a clear label for the x‑axis (training steps). Adding these labels would make the figures self‑contained.

2. **Color choices and accessibility** – Several figures use multiple colors (e.g., the three dataset columns in the diversity bar charts, the different methods in Table 1 visualizations, and the trajectory overlays in Fig. 6). The current palettes are not guaranteed to be distinguishable for color‑blind readers. Switching to a vetted color‑blind‑safe palette or adding patterned fills would improve accessibility.

3. **Legibility at print scale** – Some trajectory visualizations (Fig. 6, Fig. 10, Fig. 12) contain thin lines and small markers that become hard to discern when the figure is reduced to column width. Slightly thicker lines and larger markers, or the use of vector graphics, would preserve detail.

4. **Alt‑text and caption completeness** – The manuscript does not provide alt‑text for figures, which is required for accessibility compliance. Captions are generally informative but could be expanded to explicitly define symbols, colors, and any abbreviations (e.g., “PWT = average percentage within threshold”).

5. **Resolution and format** – All figures are supplied as PDF, which is appropriate for line drawings, but the raster images (e.g., the qualitative video‑generation comparisons) should be confirmed to be ≥ 300 dpi to ensure crisp reproduction in print.

6. **Figure necessity** – Every figure currently serves a purpose (task illustration, model diagram, pipeline overview, dataset statistics, qualitative and quantitative results). No superfluous figures were identified, so the set is justified.

Addressing the above points will make the visual content clearer, more reproducible, and accessible without altering the scientific contributions.
