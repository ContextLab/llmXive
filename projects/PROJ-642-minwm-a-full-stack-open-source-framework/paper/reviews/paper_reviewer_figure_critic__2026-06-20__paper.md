---
action_items:
- id: 4244ed5cf647
  severity: writing
  text: "Add concise alt\u2011text descriptions for every figure (including sub\u2011\
    figures) to improve accessibility for screen\u2011reader users."
- id: '706214804911'
  severity: writing
  text: "Ensure that any quantitative plots (e.g., latency table, if rendered as a\
    \ figure) include clearly readable axis labels, units, and tick marks that remain\
    \ legible when printed at 1\u202Fcolumn width."
- id: 0897b179a620
  severity: writing
  text: "Verify that the colour palettes used in the PDF figures are colour\u2011\
    blind safe (e.g., avoid red\u2011green combos) and provide a colour legend where\
    \ multiple curves or categories are shown."
- id: 04dc124e59ed
  severity: writing
  text: "Provide a brief caption note indicating the resolution or scaling factor\
    \ of the visualisations (e.g., \u201CFrames are down\u2011sampled to 480\xD7832\
    \ for display\u201D) so readers understand the visual fidelity."
- id: 3b453ab06017
  severity: writing
  text: "If any figure contains dense visual information (e.g., the main generation\
    \ example), consider adding a higher\u2011resolution version in the supplementary\
    \ material and reference it from the caption."
artifact_hash: 0ee056e55f4c06cb2eab61e5c44334fbdff8ec177adecd2d7f6251ef9b5e9f6a
artifact_path: projects/PROJ-642-minwm-a-full-stack-open-source-framework/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-20T04:34:09.432232Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

The manuscript includes six primary figures (pipeline, main result, and three ablation groups each with three sub‑figures). Overall, the figures are well‑integrated into the narrative and each is referenced at the appropriate point in the text. However, from a pure figure‑centric perspective several improvements are needed to meet the standards of clarity, accessibility, and print‑readability.

**Figure 1 – Pipeline Overview (`Figures/paper_pipeline.pdf`)**  
The diagram effectively conveys the multi‑stage workflow, but the text labels inside the blocks are relatively small and may become illegible when the paper is printed in a single‑column format. Increase the font size of block titles and ensure that arrows are thick enough to be distinguished at reduced scale. Adding a short legend for the colour coding (e.g., “blue = data construction, orange = fine‑tuning”) would aid quick comprehension.

**Figure 2 – Main Generation Result (`Figures/main.pdf`)**  
This qualitative showcase demonstrates camera‑controllable generation. Since the figure is a raster PDF of video frames, the resolution appears adequate on screen, yet at print size the fine details (e.g., texture edges) can blur. Consider providing a higher‑resolution supplemental figure or a zoomed inset highlighting a region where camera motion is evident. The caption correctly emphasizes the preservation of controllability, but an alt‑text such as “Sequence of three frames showing a camera pan across a synthetic indoor scene, with the camera trajectory indicated by arrows” would improve accessibility.

**Figures 3‑5 – Ablation Groups (`Figures/bs-*.pdf`, `Figures/data-*.pdf`, `Figures/steps-*.pdf`)**  
Each group uses three sub‑figures arranged vertically. The captions are descriptive, yet the visualisations themselves lack explicit axis labels or legends. If the PDFs contain plots (e.g., loss curves, quantitative metrics), axis titles, units, and tick labels must be added directly to the figure files. If they are purely qualitative snapshots, a brief annotation (e.g., “batch size = 8”) should be overlaid on each sub‑figure to avoid readers having to cross‑reference the caption. Colour choices appear standard; however, verify that any colour distinctions are colour‑blind safe (e.g., avoid red vs. green for “good” vs. “bad” outcomes). Adding a small colour key in the corner of each sub‑figure would make the visual comparison more immediate.

**General Observations**  
- All figures are included as PDF assets, which is appropriate for vector graphics, but the current PDFs are generated at a size that may not scale down cleanly. Re‑exporting at a higher DPI (e.g., 300 dpi) ensures crispness in the final PDF.  
- The manuscript does not provide explicit alt‑text for any figure, which is a requirement for accessibility compliance.  
- No figure includes a scale bar or unit annotation where spatial dimensions are relevant (e.g., camera trajectory length). Adding such information would help readers quantitatively assess the results.  
- The figure numbering and referencing (`\Figref{fig:pipeline}`, `\Figref{fig:ablation-bs}` etc.) are correct, but the LaTeX macro `\figref` is defined in `math_commands.tex` and may not be recognized by all bibliography styles; ensure the final PDF compiles without undefined references.

**Conclusion**  
The figures convey the core ideas of the minWM pipeline and its ablations, but they require modest refinements to be fully clear, accessible, and printable. Addressing the points above will substantially improve the visual communication of the paper without altering its scientific content.
