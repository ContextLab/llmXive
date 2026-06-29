---
action_items:
- id: 850527edbb95
  severity: writing
  text: 'The figures in the TransitLM manuscript generally support the narrative but
    require specific refinements to meet print-quality standards and ensure clarity
    without over-reliance on captions. Figure 1 (method_comparison.pdf): This conceptual
    figure effectively contrasts the three paradigms. However, the ''Top'' panel (Traditional
    map-based) should explicitly label the ''Map Infrastructure'' and ''Routing Engine''
    components to visually reinforce the text''s claim of dependency. The current
    schematic is'
artifact_hash: edae6ae2d895f06d190c806d301a85f463bbdd062907b9af82e2ca86a0aa3cf7
artifact_path: projects/PROJ-621-transitlm-a-large-scale-dataset-and-benc/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T22:49:58.449538Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

The figures in the TransitLM manuscript generally support the narrative but require specific refinements to meet print-quality standards and ensure clarity without over-reliance on captions.

**Figure 1 (method_comparison.pdf):** This conceptual figure effectively contrasts the three paradigms. However, the 'Top' panel (Traditional map-based) should explicitly label the 'Map Infrastructure' and 'Routing Engine' components to visually reinforce the text's claim of dependency. The current schematic is slightly abstract; adding a small icon or label for the 'engine' would clarify the 'black box' nature of the traditional approach.

**Figure 2 (method.pdf):** The caption references 'TransitBench' and specific metrics (10K samples, 10 metrics), but the diagram itself does not visually enumerate these. The 'Center' panel is a bit dense. Consider adding a small inset or callout box that explicitly lists the three tasks (ORG, PRG, DRG) and the metric categories to make the figure self-contained. Also, ensure the figure label `\label{fig:method}` matches the text reference; the caption currently says 'Overview of TransitLM' but the text refers to 'TransitBench' in the context of the benchmark tasks.

**Figure 3 (cpt_loss_comparison.pdf):** The main plot is clear, but the inset (steps 4k–14k) is problematic. The y-axis tick labels are too small to read at standard print resolution. The three curves are very close in the inset; relying solely on line style (solid, dashed, dotted) is risky for grayscale printing. I recommend adding distinct markers (e.g., circles for 0.6B, squares for 1.7B, triangles for 4B) to the lines in the inset to ensure legibility.

**Figures 4–7 (demo_*.pdf):** These qualitative examples are crucial for demonstrating 'implicit spatial grounding.' The 'left panel' map visualizations must be high-resolution. In `demo_preference_planning.pdf` and `demo_multi_route.pdf`, the route lines (especially bus routes which may be thinner or less distinct) must be clearly visible against the map background. Ensure that the station names or line identifiers on the map are legible. If the map tiles are low-res, the 'spatial coherence' claim is visually undermined. Additionally, the 'right panel' structured generation text is dense; ensure the font size is large enough to read the specific station IDs and transfer points without squinting.

**General:** None of the figures include alt text in the LaTeX source. For a NeurIPS submission, accessibility is increasingly important. Please add `\alttext{...}` or equivalent descriptions for each figure, summarizing the key visual takeaway (e.g., "Bar chart showing connectivity metrics across four cities...").

Finally, ensure all figures are vector-based (PDF/EPS) where possible to maintain sharpness at any zoom level, particularly for the text-heavy panels in Figures 4–7.
