---
action_items:
- id: a85c1f28d27e
  severity: writing
  text: "Add clear axis labels (including units) and legends to all quantitative plots\
    \ (e.g., Fig\u202F2\u202F(data_scaling.pdf), Fig\u202F3\u202F(model_training.pdf),\
    \ Fig\u202F4\u202F(data.pdf)). This will make the figures interpretable without\
    \ referring to the main text."
- id: 16a50c38bfee
  severity: writing
  text: "Provide descriptive alt\u2011text for each figure in the LaTeX source (using\
    \ \\caption[...]{...} optional argument) to improve accessibility and aid reviewers\
    \ reading the PDF in grayscale."
- id: be1bf1a0fbae
  severity: writing
  text: "Replace or recolor the current color schemes in multi\u2011color figures\
    \ (e.g., Fig\u202F1\u202F(teaser.pdf), Fig\u202F2\u202F(pipeline.pdf), Fig\u202F\
    5\u202F(ablation.pdf)) with a color\u2011blind\u2011friendly palette (e.g., using\
    \ ColorBrewer\u2019s \u2018Set2\u2019 or similar) and ensure sufficient contrast\
    \ for print."
- id: 6456cf4f72d5
  severity: writing
  text: "Increase the font size of axis tick labels and legend text in all plots so\
    \ they remain legible when the figure is printed at typical journal column width\
    \ (\u22483.25\u202Fin)."
- id: 822b7b7c72ca
  severity: writing
  text: "For the bubble\u2011plot in Fig\u202F2\u202F(diversity.pdf), add a legend\
    \ explaining the meaning of bubble size and axes (gstd, log\u2011volume) and include\
    \ grid lines or reference markers to aid quantitative reading."
- id: fff2b97a2219
  severity: writing
  text: "In Fig\u202F6\u202F(accurate.pdf) showing inference latency, annotate the\
    \ bars with exact latency values (ms) and indicate the hardware configuration\
    \ directly in the caption."
- id: f8865c0991f3
  severity: writing
  text: Ensure that all figures are embedded as vector graphics (PDF/EPS) rather than
    rasterized images where possible, to avoid loss of detail at high resolution.
artifact_hash: 11a83a092083d485002512d3e56d130e02aef8501fdca7259786be2bc34086fd
artifact_path: projects/PROJ-658-humanoid-gpt-scaling-data-and-structure/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-23T13:00:29.435337Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

The manuscript contains a substantial number of figures that are central to its claims about scaling, diversity, and real‑world performance. Overall the visual material is relevant, but several recurring issues hinder clarity and reproducibility:

1. **Missing or ambiguous axis labels** – Figures that present quantitative trends (e.g., the data‑scaling curve, model‑scaling comparison, and the HME diversity bubble) lack explicit axis titles and units. Readers must infer the meaning from the caption or the surrounding text, which is error‑prone.

2. **Insufficient legend information** – In the bubble‑plot (Fig 2 diversity.pdf) the size of each bubble encodes the number of motion clips, yet there is no legend or scale bar to interpret the relative sizes. Similarly, the latency comparison (Fig 5 accurate.pdf) shows bars without numeric values, making it hard to gauge the magnitude of improvement.

3. **Color choices and accessibility** – Several multi‑color figures (pipeline, ablation, teaser) use palettes that are not optimized for color‑blind readers (e.g., reds and greens together). The contrast between some lines and the background is low, especially when printed in grayscale.

4. **Readability at print scale** – Tick labels, legend text, and annotation fonts are small; when the figures are reduced to column width they become difficult to read. This is especially problematic for the t‑SNE and feature‑distribution plots where dense point clouds are shown.

5. **Lack of alt‑text / descriptive captions** – The LaTeX source does not provide optional short captions for accessibility, and the main captions sometimes omit key details (e.g., hardware used for latency measurements, exact meaning of “SR” in the scaling table).

6. **Raster vs. vector graphics** – Some figures (e.g., the real‑world robot photos) are raster images, which is appropriate, but the plots appear to be rasterized PDFs. Using true vector graphics would preserve crispness for line plots and axis markings.

7. **Consistency of figure numbering and references** – The manuscript sometimes refers to figures by name (e.g., “Fig \ref{fig:pipeline}”) but the numbering in the compiled PDF may shift if supplementary figures are added. Ensuring stable labels will help reviewers locate the correct visual evidence.

Addressing these points will make the figures self‑contained, improve accessibility, and ensure that the visual evidence robustly supports the paper’s scaling claims. No fundamental scientific flaws are identified in the figures themselves; the concerns are primarily about presentation and clarity.
