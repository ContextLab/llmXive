---
action_items:
- id: 6edc120f187e
  severity: writing
  text: "Add clear axis labels, scale bars, and unit annotations to all quantitative\
    \ figures (e.g., Fig.\u202F5 radar chart, Fig.\u202F6 continent coverage, and\
    \ any plots showing performance metrics)."
- id: 452f759a418f
  severity: writing
  text: "Provide high\u2011resolution versions of raster images (e.g., Fig.\u202F\
    2 data pipeline, Fig.\u202F3 data sources) and ensure that line widths and text\
    \ remain legible when the figure is printed at 1\u202Fcolumn width."
- id: 21468795c4c9
  severity: writing
  text: "Include concise alt\u2011text descriptions for each figure in the LaTeX source\
    \ (using \\caption[Alt\u2011text]{...}) to improve accessibility."
- id: 8cf99960d34f
  severity: writing
  text: "For multi\u2011panel figures (e.g., Fig.\u202F9 comparing Google Earth vs.\
    \ ABot\u2011Earth), add consistent visual markers (e.g., scale bars, compass roses)\
    \ and annotate the geographic region in each panel to avoid ambiguity."
- id: beedeedc1119
  severity: writing
  text: "Ensure that color palettes used in heat\u2011maps or coverage maps are color\u2011\
    blind friendly and include a legend explaining the color scale."
- id: cb91cd67c910
  severity: writing
  text: "Replace low\u2011contrast or overly saturated colors in the teaser figure\
    \ (Fig.\u202F1) with a palette that retains visual impact but does not wash out\
    \ when printed in grayscale."
artifact_hash: 889d5a8e39acbdaa7baa4d1b8f93a551383f0dbc1ede3c36f50fc7a5e7bb8167
artifact_path: projects/PROJ-693-abot-earth-0-5-generative-3d-earth-model/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-17T06:19:14.486990Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

The manuscript contains a substantial number of figures that are central to its claims about planetary‑scale 3D generation, data pipelines, and system‑level comparisons. While the visual material is generally relevant, several recurring issues affect clarity and reproducibility.

1. **Figure 1 (Teaser)** – The image is visually striking but lacks any scale indicator or reference to the geographic extent being shown. The caption does not specify the resolution or the area covered, making it difficult for readers to gauge the model’s scope. Moreover, the color palette includes very bright yellows that may become indistinguishable when printed in grayscale.

2. **Figures 2–3 (Data Pipeline & Data Sources)** – Both are dense block diagrams rendered as JPEG/PNG images. Text within the boxes is small, and line thickness is thin; at the typical two‑column print size, many labels become illegible. No axis or scale is required, but a legend for the icons (e.g., satellite, aerial, urban) would improve interpretability. The figures also lack alt‑text for accessibility.

3. **Figure 4 (Quantitative Comparison – Table 5)** – Though presented as a table, the accompanying figure (radar chart) is embedded as a PDF image without axis labels. The radar axes are not annotated with the metric names (e.g., “Coverage”, “Timeliness”, “Visual Quality”), forcing readers to refer back to the caption. The chart also uses a red‑green color scheme that is not color‑blind safe.

4. **Figure 5 (Continental Coverage)** – The continent‑level map uses a sequential color gradient but provides no legend or numeric values. Readers cannot discern what the colors represent (e.g., percentage of area covered). Adding a color bar with explicit values is essential.

5. **Figure 6 (System Comparison – Multi‑panel)** – The side‑by‑side comparison of Google Earth and ABot‑Earth (sub‑figures a–f) lacks consistent annotations. Only the panels for New Zealand and Japan show a viewpoint description in the caption; the Ireland panel does not indicate that Google Earth is showing a flat map. Adding a small inset or annotation (“No 3D data”) would clarify the contrast. Additionally, the image dimensions differ slightly between Google and ABot‑Earth panels, leading to a visual mismatch.

6. **Figure 7 (Production Pipeline – CutBlock & LODTiles)** – The two sub‑figures are of different aspect ratios, causing an uneven visual balance. The figure captions do not explain the meaning of the arrows or the meaning of the “zoom levels”. Adding a brief legend and ensuring both sub‑figures share the same width would improve readability.

7. **Figure 8 (Rendered LOD Visualization)** – This figure demonstrates the final rendering but does not include any scale bar or viewpoint metadata (camera altitude, FOV). Without these, the claim of “real‑time interactive rendering” cannot be independently assessed.

8. **Figure 9 (Landmark Integration)** – The composite images are high‑resolution PDFs, yet the caption does not indicate the source of the landmark reconstructions or the coordinate alignment method. Adding a small overlay showing the bounding box or a coordinate grid would help readers understand how the landmarks are fused.

9. **General Issues** – Across all raster figures, the PDF files are embedded at a resolution that appears sufficient on screen but may degrade when printed. The manuscript does not provide alt‑text for any figure, which is required for accessibility. Color choices in several figures (e.g., radar chart, coverage maps) are not verified for color‑blind safety, and no legends are provided for multi‑color plots.

**Recommendations**  
- Standardize figure sizes to fit within a single column (≈3.25 in) or double‑column width where appropriate, ensuring that all textual elements remain legible after scaling.  
- For every quantitative plot, include axis labels with units (e.g., “Coverage (%)”, “Generation time (min/km²)”).  
- Add legends or color bars to all heat‑maps, coverage maps, and radar charts, and verify that the palettes are color‑blind friendly (e.g., using ColorBrewer palettes).  
- Provide concise alt‑text for each figure using the optional argument of \\caption, which will also aid screen‑reader users.  
- Where geographic regions are shown, include a scale bar (e.g., “1 km”) and optionally a north arrow.  
- Ensure that multi‑panel figures maintain consistent dimensions and include panel labels (a), (b), … directly on the images to avoid reliance on caption ordering.

Addressing these points will considerably improve the clarity, reproducibility, and accessibility of the visual components, allowing the figures to fully support the paper’s claims.
