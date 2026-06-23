---
action_items:
- id: 3f98a1473613
  severity: writing
  text: "Add explicit axis labels (including units) to all line\u2011plot figures\
    \ (e.g., Fig.\u202F2, Fig.\u202F3, Fig.\u202F4, Fig.\u202F5, and the appendix\
    \ dynamics plots)."
- id: 7ee091c3312a
  severity: writing
  text: "Replace the current red\u2011green colour scheme in Fig.\u202F2 and Fig.\u202F\
    4 with a colour\u2011blind\u2011safe palette or add distinct line styles/markers."
- id: 3fb1c9f5edde
  severity: writing
  text: "Provide concise alt\u2011text descriptions for each figure in the PDF (e.g.,\
    \ via \\caption[Alt\u2011text]{...}) to improve accessibility."
- id: 27764b3bc667
  severity: writing
  text: "Ensure that the high\u2011resolution conceptual diagram (figure_high_concept.png)\
    \ includes a legend explaining all symbols and arrows; currently some symbols\
    \ are undocumented."
- id: 66171abcabec
  severity: writing
  text: "In Fig.\u202F5 (qualitative examples), increase the font size of the overlaid\
    \ text (e.g., \u2018Candidate\u202FA\u2019, \u2018Student\u2019s BCQ rollout\u2019\
    ) so it remains legible when printed at 80\u202F% scale."
- id: 74914efd6b6c
  severity: writing
  text: "For the teacher\u2011scale plot (figure_teacher_scale.pdf), add a grid or\
    \ tick marks on both axes and label the x\u2011axis with \u2018Teacher size (B\
    \ parameters)\u2019 and the y\u2011axis with \u2018\u0394\u202Faccuracy (pp)\u2019\
    . This will make the trend easier to read."
artifact_hash: 0fd8fa2b8ede4e304df4503c08bd0823fb3038495b7a89b759c4ee4216df60db
artifact_path: projects/PROJ-731-zone-of-proximal-policy-optimization-tea/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-23T13:03:50.891048Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

The manuscript contains a substantial set of figures (Fig. 1–5, a high‑concept illustration, teacher‑scale plot, and several appendix plots) that are central to the claimed performance gains of ZPPO. Overall the visualizations are well‑integrated with the text, but several recurring issues hinder their clarity and reproducibility.

**Axis labeling and units** – Many line‑charts (e.g., the buffer‑composition dynamics in Fig. 2, the training‑step curves in Fig. 3, and the multi‑scale dynamics in Fig. 4) lack explicit axis titles and units. Readers must infer from the caption that the x‑axis is “training step” and the y‑axis is “rollout accuracy” or “positive‑advantage fraction”, but this is not guaranteed. Adding clear labels (including the unit “%” where appropriate) will eliminate ambiguity.

**Colour choices** – The primary colour palette pairs red and green to distinguish baseline vs. ZPPO curves. This combination is problematic for colour‑blind readers. A safer alternative is to use a colour‑blind‑friendly palette (e.g., blue/orange) or to differentiate curves with distinct line styles (dashed vs. solid) and markers. The same issue appears in the teacher‑scale plot (figure_teacher_scale.pdf).

**Legibility at print scale** – The qualitative example figures (Fig. 5 and the appendix “airplane”/“coat” images) embed small text annotations inside the image panels. When the PDF is printed or viewed on a reduced screen, these annotations become unreadable. Increasing the font size or moving the annotations to the caption area would preserve readability.

**Legends and symbols** – The high‑concept schematic (figure_high_concept.png) introduces several custom symbols (e.g., a “zone” oval, arrows labelled “BCQ”, “NCQ”) but the caption does not define them. Adding a small legend within the figure or expanding the caption to describe each symbol will aid comprehension, especially for reviewers unfamiliar with the terminology.

**Alt‑text / accessibility** – The PDF currently provides no alternative text for figures, which limits accessibility for screen‑reader users. Supplying concise alt‑text via the optional argument of \\caption (e.g., \\caption[Alt‑text]{Full caption}) will satisfy accessibility guidelines.

**Gridlines and tick marks** – Some plots (e.g., the teacher‑scale curve) omit gridlines and have sparse tick marks, making it difficult to gauge exact values. Adding light gridlines and ensuring evenly spaced ticks will improve interpretability without cluttering the visual.

Addressing these points will make the figures self‑contained, accessible, and easier to interpret, thereby strengthening the overall presentation of the experimental results.
