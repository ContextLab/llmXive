---
action_items:
- id: 0d9e8bf5776b
  severity: writing
  text: Figure 1c (Performance) overlaps significantly with Table 1 (Main Results).
    Consider removing Fig 1c or replacing it with a visualization that highlights
    the 'Attribution Hallucination' gap (Ans. vs SAA) specifically, rather than repeating
    the full table data.
- id: f5164afe9b85
  severity: writing
  text: Radar charts in Fig 5 (citevqa_ability_radar.pdf) and Appendix Fig (citevqa_domain_radar.pdf)
    are difficult to read with multiple models. Suggest switching to grouped bar charts
    or heatmaps for better comparison of SAA scores across question types.
- id: 50c101f5c8a7
  severity: writing
  text: Figure 3 (pdf_statistics.pdf) and Figure 4 (question_statistics.pdf) lack
    explicit axis labels for units (e.g., 'Count', '%', 'Pages'). Ensure all axes
    are clearly labeled for print legibility.
- id: 6745a71357aa
  severity: writing
  text: Case study figures (Simple_Case.pdf, Case_Study1.pdf, Case_Study2.pdf) have
    small text in crops. Verify legibility at standard print scale (e.g., 10pt font
    equivalent). Add arrows or bounding boxes to explicitly highlight cited regions.
- id: 00df9bc44ba8
  severity: writing
  text: Files 'shlab.png' and 'OpenDataLab_blue_no_words.pdf' are listed in the figures
    directory but not referenced in the LaTeX source. Remove unused assets to reduce
    repository clutter.
- id: 5ea0d86cd128
  severity: writing
  text: Caption for Figure 7 (Simple_Case.pdf) is generic ('A Typical Example.').
    Expand to describe the specific failure mode illustrated (e.g., 'Qwen3-VL-235B
    answers correctly but cites blank regions').
artifact_hash: 343bba3cbfbb16bee3f79c8a33c3a51555292623f2cdbd016ca7ae51e6fbc39c
artifact_path: projects/PROJ-601-https-arxiv-org-abs-2605-12882/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-05T21:46:37.594554Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

**Figure Review — CiteVQA**

This review evaluates the clarity, legibility, and efficacy of the visual elements in the manuscript. The figures generally support the narrative, but several presentational issues require attention to ensure accessibility and clarity at print scale.

**1. Redundancy and Visual Focus**
*   **Figure 1c vs. Table 1:** Figure 1c displays model performance (SAA, Ans.) which is duplicated in Table 1 (Main Results). This redundancy consumes valuable figure space. I recommend replacing Figure 1c with a dedicated visualization of the "Attribution Hallucination" gap (e.g., a scatter plot of Ans. vs. SAA for all models) to visually reinforce the core finding without repeating tabular data.
*   **Figure 1b:** Dataset statistics (docs, pages) are also summarized in Table 3. Ensure Figure 1b adds unique value (e.g., highlighting the distribution balance) rather than just listing numbers.

**2. Chart Selection and Readability**
*   **Radar Charts (Fig 5 & Appendix):** The radar charts (`citevqa_ability_radar.pdf`, `citevqa_domain_radar.pdf`) are difficult to interpret when comparing multiple models simultaneously due to overlapping polygons. For quantitative comparisons of SAA scores, grouped bar charts or heatmaps would provide clearer differentiation between models and question/document types.
*   **Axis Labels:** Figures 3 (`pdf_statistics.pdf`) and 4 (`question_statistics.pdf`) require explicit axis labels. The y-axes should specify "Count" or "Percentage," and the x-axes should clarify units (e.g., "Page Number," "Evidence Source").

**3. Legibility and Detail**
*   **Case Studies (Figs 7, Appendix Figs):** The case study images (`Simple_Case.pdf`, `Case_Study1.pdf`, `Case_Study2.pdf`) contain text crops that may be illegible at standard print resolution. Ensure text within crops is large enough to be read without zooming. Additionally, explicitly mark the cited bounding boxes with colored outlines or arrows to guide the reader to the evidence.
*   **Captions:** Some captions are too brief. For instance, Figure 7's caption ("A Typical Example.") does not explain *why* it is typical. Expand captions to describe the specific phenomenon (e.g., "Correct answer with incorrect evidence attribution").

**4. Repository Hygiene**
*   **Unused Assets:** The files `shlab.png` and `OpenDataLab_blue_no_words.pdf` appear in the figure list but are not referenced in the LaTeX source (`\includegraphics`). These should be removed to maintain a clean artifact directory.

**Conclusion**
The figures are functional but could be optimized for better data communication and accessibility. Addressing the redundancy, chart types, and legibility will strengthen the visual argument.
