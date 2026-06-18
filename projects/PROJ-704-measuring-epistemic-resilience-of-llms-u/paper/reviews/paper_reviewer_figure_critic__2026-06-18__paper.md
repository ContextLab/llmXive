---
action_items:
- id: d80f5dc80caa
  severity: writing
  text: "Add descriptive alt\u2011text for every figure (including sub\u2011figures)\
    \ to improve accessibility for screen\u2011reader users."
- id: fd244c829b90
  severity: writing
  text: "Verify that all color schemes used in plots (e.g., Figures\u202F4,\u202F\
    5,\u202F6) are color\u2011blind safe; replace any red/green or similar problematic\
    \ palettes with a palette that is distinguishable for deuteranopia and protanopia."
- id: 569df7700927
  severity: writing
  text: "Increase the font size of axis labels and tick marks in wrapped figures (e.g.,\
    \ Figure\u202F3) to ensure legibility when printed at typical conference sizes\
    \ (column width \u2248 3.25\u202Fin)."
- id: e229ad22d448
  severity: writing
  text: "Ensure every plotted figure includes explicit axis labels with units where\
    \ applicable (e.g., accuracy percentages, attack\u2011success rates) and a legend\
    \ that does not rely solely on color."
- id: b56f0199fb3c
  severity: writing
  text: Provide a brief caption that fully explains the visual content of each figure
    without requiring the reader to refer back to the main text; include definitions
    of any abbreviations used in the figure.
artifact_hash: b321ce34848cd04bd8d899e341b97cc74f8e7595fd9393bb1f9638bbf57b0d10
artifact_path: projects/PROJ-704-measuring-epistemic-resilience-of-llms-u/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-18T21:49:37.696611Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

The manuscript contains seven primary figures (Figures 1–7) plus several supplemental figures in the appendix. Overall, the figures are well‑integrated into the narrative and each is referenced at the appropriate point in the text. Below I evaluate them individually with respect to the figure‑critic lens.

**Figure 1 (Overview diagram)** – The schematic cleanly illustrates the transformation from a clean QA item to a paired resilience test. The components (question, answer options, injection bundle) are labeled, and the flow arrows are unambiguous. However, the diagram relies on a single colour (blue) for all arrows, which can be hard to differentiate for colour‑blind readers. Adding a second hue or varying line style would improve discriminability. No axis is present, which is appropriate.

**Figure 2 (Main example)** – This visual example of a focused false‑context injection is effective: the original question, the correct answer, and the misleading statement are clearly delineated. The caption explains the shift from the correct melanoma‑management answer to the wrong option. The figure lacks alt‑text and the font size of the embedded text is borderline when printed at column width; a slight increase would aid readability.

**Figure 3 (Dataset distribution)** – Implemented as a wrap‑figure, it shows the number of retained items per source dataset. The bar heights are labelled with exact counts, and the x‑axis titles are present. The colour palette (light blues) is acceptable, but the figure is relatively small; the tick labels become cramped at print scale. Enlarging the figure or using a horizontal layout would preserve legibility.

**Figure 4 (Accuracy drop)** – This line plot compares clean accuracy, Type 1 accuracy, and Type 2 accuracy across all models. Axis labels (“Mean Accuracy (%)”) and a legend are present, and the three series are distinguished by colour and line style. The colour palette (blue, orange, green) is generally colour‑blind safe, but the orange line is thin and may be hard to see when printed in grayscale. Adding markers (e.g., circles, squares) would make the series more robust to printing and to readers with colour vision deficiencies.

**Figure 5 (Protocol ASR comparison)** – The bar chart shows Type 1 vs. Type 2 attack‑success rates. Bars are labelled with percentages, and the y‑axis includes a clear “Attack Success Rate (%)” label. The use of a single colour (purple) for both bars could be confusing; a contrasting colour for the two protocol bars would improve immediate visual discrimination. Alt‑text describing the numeric values is missing.

**Figure 6 (Taxonomy ASR)** – This stacked bar chart stratifies ASR by provenance (neutral, patient, authority) and by content‑corruption type. The figure is information‑dense and the colour coding (five distinct hues) is helpful, but the palette includes a red‑green pair that is problematic for deuteranopia. Re‑mapping the colours to a colour‑blind‑friendly palette (e.g., using teal, orange, purple, brown, blue) would resolve this. The legend is placed at the bottom; moving it to the side would free vertical space and avoid overlapping with the bars.

**Figure 7 (Mitigation case study)** – The plot comparing search‑augmented vs. baseline performance on HLE items is clear, with separate markers for each model configuration. Axis labels (“Type 1 ASR”, “Accuracy”) are present, and the legend distinguishes the two settings. The colour scheme (blue for baseline, red for search) again raises a red‑green issue; swapping red for a colour‑blind‑safe hue (e.g., teal) would be advisable.

**Supplemental figures** – The appendix contains additional diagrams (e.g., prompt screenshots, taxonomy tables). These are generally well‑labelled, but many lack explicit axis units (where applicable) and alt‑text. Since the supplemental material is often printed in a reduced format, ensuring sufficient font size and contrast is important.

**General observations**

* **Clarity & legibility** – All figures convey the intended information, but several suffer from small font sizes or thin lines that may become illegible at the typical two‑column conference print size. Increasing font sizes by ~10 % and using thicker line weights would mitigate this risk.

* **Axis labels & units** – Where quantitative axes are present (Figures 4–6, 7), units are correctly indicated as percentages. No missing units were observed.

* **Colour choices** – A few figures employ red/green combinations that are not colour‑blind safe. Switching to a palette verified with tools such as Coblis or ColorBrewer would improve accessibility.

* **Alt‑text** – The manuscript does not provide alt‑text for any figure. For compliance with accessibility standards (e.g., WCAG 2.1), each figure should include a concise description in the PDF metadata or as a caption footnote.

* **Figure justification** – Every figure directly supports a claim made in the text (e.g., Figure 4 substantiates the claim that clean accuracy overstates epistemic resilience). No superfluous figures were identified.

**Verdict** – The figures are fundamentally sound and earn their place in the paper, but the issues noted above (alt‑text, colour‑blind safety, font/line thickness) need to be addressed before publication. Therefore I recommend **minor_revision**.
