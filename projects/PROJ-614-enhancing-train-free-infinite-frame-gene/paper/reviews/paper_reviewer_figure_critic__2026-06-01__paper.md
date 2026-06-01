---
action_items:
- id: e610e649a446
  severity: writing
  text: Revise Figure 1 caption (line ~130) to clarify that static images represent
    keyframes from videos, not the videos themselves.
- id: 7eb1aa3ee923
  severity: writing
  text: Add accessibility alt-text descriptions for all figures using the accessibility
    package or descriptive captions to support screen readers.
- id: b4f8e5dd61c2
  severity: writing
  text: Ensure axis labels in ablation charts (Fig 5, Fig 6) are legible at print
    scale; verify font sizes are >= 8pt.
artifact_hash: 2fc45fd89cfd8c3cc27102ad20713af6a66d4f721af1c258a0cd318f7ea682b3
artifact_path: projects/PROJ-614-enhancing-train-free-infinite-frame-gene/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-01T11:08:57.070268Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

**Figure Review Feedback**

The manuscript includes a comprehensive set of figures that generally support the technical narrative. Figure 1 (line ~130) effectively showcases the long-video capability, though the caption states "We present three long videos." Since the PDF is a static medium, this is technically inaccurate. Please revise to "We present keyframes from three long videos" to maintain precision.

Figure 2 (line ~230) and Figure A1 (line ~1000) provide clear schematic overviews of the TTA and DCE mechanisms. The use of color coding in Figure 2 (a vs b) is distinct, but ensure the legend or caption explicitly defines the color mapping for colorblind accessibility.

Ablation figures (Fig 5 at line ~550, Fig 6 at line ~560) present quantitative trends. While the data is clear, standard practice for conference proceedings requires axis labels to be legible when printed at 100% scale. Verify that tick labels and axis titles in `ab_threshold.pdf` and `ab_phase2_steps_bar.pdf` are not too small (recommend >= 8pt font).

Regarding accessibility, the LaTeX source does not utilize the `accessibility` or `alttext` packages. While not strictly required for all venues, adding `alt` descriptions to `\includegraphics` commands or ensuring captions are sufficiently descriptive for screen readers is recommended for broader inclusivity.

Figure 4 (line ~350) uses yellow and red bounding boxes to highlight noise and inconsistency. The caption explains these colors, which is good practice. However, ensure the contrast is sufficient for grayscale printing, as some reviewers may print in black and white.

Overall, the figures are well-integrated and the visual evidence aligns with the quantitative claims. Addressing the caption precision and accessibility notes will bring the visual presentation to a higher standard.
