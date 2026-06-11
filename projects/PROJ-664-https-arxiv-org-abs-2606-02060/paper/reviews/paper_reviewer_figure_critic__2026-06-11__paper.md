---
action_items:
- id: 5ff0a02e226e
  severity: writing
  text: Add explicit color legend mapping to captions for Figure 4 (performance) and
    Figure 5 (further-analysis) specifying which color corresponds to each model family.
- id: 2c3b6a50aae2
  severity: writing
  text: Include alt text descriptions for all 11 figures to meet accessibility requirements
    for print and screen-reader users.
- id: 0074c7faa1be
  severity: writing
  text: Convert Figure 7 (annotation_ui_screenshot.png) from PNG screenshot to vector
    format (PDF/SVG) for print-scale legibility.
- id: a16e85d0995c
  severity: writing
  text: Expand Figure 4 caption to explain what bars/lines represent and how to interpret
    the macro-F1 comparison.
- id: b774f41444b5
  severity: writing
  text: Clarify piecewise-compressed y-axis behavior in Figure 10 (effort_profiles)
    caption or add visual annotation.
artifact_hash: 35ded812a75ceef1f48d0fbc3a809a8b976c23d29d82ed40e43751cfcaadee3e
artifact_path: projects/PROJ-664-https-arxiv-org-abs-2606-02060/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-11T08:09:07.643835Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

## Figure Review — Where Do Deep-Research Agents Go Wrong?

This review examines all 11 figures across the main text and appendix for clarity, labeling, color choices, print legibility, and whether each figure earns its place.

### Strengths

- **Figure 2 (mechanism_analysis)**: Effectively uses 8 subfigures to show complementary views of error patterns; the multi-panel design is appropriate for the complexity of the data.
- **Figure 3 (DRIFT overview)**: Clearly illustrates the claim-centric workflow; this is essential for understanding the method and justifies its main-text placement.
- **Figure 5 (further-analysis)**: Uses 4 subfigures to show ablation, scale sensitivity, and efficiency trade-offs; the Pareto frontier visualization is well-chosen.

### Issues Requiring Revision

1. **Color Encoding Ambiguity (Figures 4, 5)**: Multiple figures use color to distinguish model families and frameworks, but captions do not explicitly map colors to entities. For example, Figure 5 caption states "Colors denote model families" but does not specify which color corresponds to GPT-5.4, DeepSeek, etc. This forces readers to cross-reference the text or legend within the image, which may not render clearly at print scale.

2. **Missing Accessibility Descriptions**: None of the 11 figures include alt text or accessibility annotations. For publication compliance and screen-reader accessibility, each figure needs a brief text description of what the visualization shows.

3. **Raster Screenshot Legibility (Figure 7)**: The annotation interface (`figure/annotation_ui_screenshot.png`) is a PNG screenshot rather than a vector graphic. At print scale, small UI elements and text may become illegible. Convert to PDF/SVG or provide a higher-resolution export.

4. **Oversimplified Captions (Figure 4)**: The caption "Overall macro-F1 on TELBench" provides no guidance on how to interpret the bars or what comparisons are being made. Expand to explain axes, grouping, and what constitutes a meaningful difference.

5. **Unexplained Axis Behavior (Figure 10)**: The caption mentions "piecewise-compressed above 400 steps, 20 spans, and 100 tool calls" but does not explain why this compression was necessary or how to read values in compressed regions. Add visual annotation or clarify in caption.

6. **Inconsistent Subfigure Spacing (Figure 5)**: The LaTeX code uses varying `\vspace` values (-6pt, -4pt) across subfigure pairs, which may cause uneven visual alignment in the compiled PDF.

### Recommendations

- Add explicit color keys to all multi-series figures.
- Provide alt text for each figure in LaTeX comments or as caption additions.
- Recast Figure 7 as vector graphics or provide a zoomed-in detail inset for small UI elements.
- Standardize subfigure spacing for visual consistency.

These are writing-level fixes that do not require re-running experiments.
