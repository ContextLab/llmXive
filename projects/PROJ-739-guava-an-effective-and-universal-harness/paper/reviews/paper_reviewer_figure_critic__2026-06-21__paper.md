---
action_items:
- id: ac2d6757a6af
  severity: writing
  text: "Add descriptive alt\u2011text for every figure (e.g., using the \\includegraphics[alt=...]\
    \ option or a surrounding \\caption) to improve accessibility for screen\u2011\
    reader users."
- id: aa64cb292e59
  severity: writing
  text: "Ensure that all quantitative plots (e.g., the three sub\u2011figures in Fig.\u202F\
    2 and the bar charts in Fig.\u202F3, Fig.\u202F4, Fig.\u202F5) include clear axis\
    \ labels, units, and tick marks; the current LaTeX source only supplies a caption\
    \ without explicit axis titles."
- id: 1a389a19de29
  severity: writing
  text: "Verify that the color palettes used in the plots are color\u2011blind friendly\
    \ (e.g., avoid red/green pairs) and provide sufficient contrast when printed in\
    \ grayscale; consider adding patterned fills or distinct line styles for critical\
    \ series."
- id: cd681b8608a7
  severity: writing
  text: "For multi\u2011panel figures (e.g., Fig.\u202F2, Fig.\u202F3, Fig.\u202F\
    5), add panel labels (a), (b), (c) directly on the sub\u2011figures and reference\
    \ them consistently in the caption to aid readers when the figure is reproduced\
    \ at smaller scales."
- id: affdb7cfbc19
  severity: writing
  text: "Check that the resolution of raster images (e.g., realworld_qualitative.pdf,\
    \ push_example.pdf) is high enough for print; low\u2011resolution PDFs can become\
    \ blurry when the paper is printed in journal format."
- id: be72c0d6769a
  severity: writing
  text: Include a brief description of the data shown in each plot within the caption
    (e.g., number of trials, confidence intervals) so that the figure can stand alone
    without requiring the reader to search the main text.
artifact_hash: 305fa4e0caf5509b3ff951ed539855921f525d3dfdda7d54d245e51eb00f86f3
artifact_path: projects/PROJ-739-guava-an-effective-and-universal-harness/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-21T00:46:00.072042Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

The manuscript contains a substantial number of figures (over a dozen), most of which are essential for illustrating the Guava harness, experimental pipelines, and qualitative robot roll‑outs. Overall the figures are well‑placed and referenced, but several presentation issues limit their clarity and accessibility.

**Clarity & Labels**  
Figures that present quantitative results (e.g., Fig. 2 “Impact of harness design”, Fig. 3 “Data generation engine”, Fig. 4 “Real‑world performance”, Fig. 5 “RL improves performance”) are included as PDFs without explicit axis titles in the source. The captions describe the overall trend but do not specify the units or meaning of the axes (e.g., success rate % vs. task type). Adding clear X‑ and Y‑axis labels, tick marks, and legends directly on the plots would make the figures self‑contained and easier to interpret, especially when reproduced at reduced size.

**Color Choices**  
The plots use a palette of soft greens, blues, and reds. While aesthetically pleasing, the red/green contrast may be problematic for readers with red‑green color‑blindness. Introducing patterned fills or distinct line styles (solid, dashed, dotted) for each series would improve discriminability in both color and grayscale print. The multi‑panel figures (Fig. 2, Fig. 3) lack explicit panel identifiers (a), (b), (c) on the sub‑figures; adding these labels would help readers follow the discussion in the text.

**Legibility at Print Scale**  
Some raster‑based PDFs (e.g., realworld_qualitative.pdf, push_example.pdf) are relatively large in file size, suggesting high resolution, but the compiled PDF’s visual quality should be verified at the journal’s column width. If the images become blurry when scaled down, consider providing higher‑resolution versions or vector‑based alternatives where possible.

**Alt Text & Accessibility**  
The LaTeX source does not include alt‑text for any figure. Modern accessibility guidelines recommend providing concise descriptions (e.g., “Fig. 2a: bar chart comparing iterative vs. single‑turn workflows across six tasks”). Adding alt‑text via the `\includegraphics[alt=...]` option or a surrounding description will make the paper more inclusive.

**Figure Necessity**  
All figures appear to support key claims (e.g., the effectiveness of iterative loops, the data‑generation pipeline, and the performance gap between SFT and RL). No superfluous figures are identified, so the figure set is justified.

In summary, the figures are conceptually appropriate but would benefit from improved labeling, color accessibility, panel annotations, higher‑resolution assets, and alt‑text for accessibility. Addressing these points will enhance readability and ensure the figures convey their intended information independently of the main text.
