---
action_items:
- id: 2483247a8ad1
  severity: science
  text: 'Supplementary Figure fig:t-stats-pos references the wrong image file: figs/t_stats_content_only.pdf
    is used for both the content-words and POS ablation plots (supplement.tex, lines
    257-263). This appears to be a copy-paste error; verify the correct file path
    for the POS variant.'
- id: 6169eb6c26df
  severity: writing
  text: No alt text is provided for any of the 5 main figures or 8 supplementary figures.
    Modern accessibility standards require descriptive alt text for screen readers.
    Add alt text to each includegraphics command or provide figure descriptions in
    the caption.
- id: e80e6975a132
  severity: writing
  text: Figure captions mention color-coded author models (e.g., Each color denotes
    a model trained on a single authors work) but do not specify if the color scheme
    is colorblind-accessible. Verify the palette meets WCAG 2.1 contrast requirements
    or add a grayscale-printable alternative.
- id: 1d6048608f5c
  severity: writing
  text: Figure fig:mds and fig:confusion-matrix are referenced as 3D MDS projection
    and heatmap but do not include a colorbar/legend in the caption describing the
    loss scale. Add explicit unit labels (cross-entropy loss, nats or bits) to the
    axis or colorbar.
artifact_hash: 148021f63314c6cbe2b6159eaaaecc4e6c793ec5541ddbe74681664a10cdde19
artifact_path: projects/PROJ-562-a-stylometric-application-of-large-langu/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-11T16:39:35.676073Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

## Figure Review — A Stylometric Application of Large Language Models

I reviewed all 5 main figures (Figs. 1–5) and 8 supplementary figures referenced in the manuscript. Overall, the figures are well-organized and the captions are detailed. However, several issues require attention before publication.

### Accessibility (Critical)

No alt text is provided for any figure in the LaTeX source. This violates modern accessibility standards (e.g., arXiv's 2024 requirements, WCAG 2.1). Each figure command should include a descriptive alternative text for screen readers.

### File Path Error (Science Impact)

In supplement.tex, the POS ablation t-statistic figure (fig:t-stats-pos) references figs/t_stats_content_only.pdf (line 260), which is the same file used for the content-words ablation (line 247). This is likely a copy-paste error that could mislead readers about the ablation results. Verify the correct file path exists and is used.

### Color Accessibility

Multiple figures use color-coded author models (Fig. 1A, Fig. 2A, Fig. 5). The captions state "Each color denotes a model trained on a single author's work" but do not confirm the palette is colorblind-safe. Verify the 8+ color scheme passes WCAG contrast requirements or provide a grayscale-printable version.

### Axis/Unit Clarity

The confusion matrix (Fig. 3) and MDS plot (Fig. 4) reference normalized loss values but do not specify the unit (nats or bits) in the caption. The t-statistic plots (Fig. 2) show a threshold line at p=0.001 but do not label the y-axis as "t-statistic" in the caption text. These should be explicit for reproducibility.

### Figure Density

13 total figures (5 main + 8 supplementary) is reasonable for this scope. The supplementary figures follow a consistent format with the main figures, which aids comprehension.

### Recommendations

Fix the file path error, add alt text to all figures, verify color accessibility, and add explicit unit labels to the loss-based figures.
