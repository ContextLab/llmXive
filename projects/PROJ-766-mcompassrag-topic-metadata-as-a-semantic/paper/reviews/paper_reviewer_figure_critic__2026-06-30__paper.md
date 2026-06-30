---
action_items:
- id: 9ae4c529bef0
  severity: writing
  text: Figure 1 (main-teaser) subfigure (a) and (b) lack axis labels and units. Subfigure
    (b) plots 'Performance' vs 'Latency' but the axes are not explicitly labeled with
    metric names (e.g., 'Avg. F1', 'ms') or units in the image itself, relying solely
    on the caption. This violates print legibility standards.
- id: aaee99f3a2b4
  severity: writing
  text: Figure 2 (CompassRAG-pipeline_v2) contains no caption text describing the
    specific icons (fire/snowflake) or the flow of data between the 'Metadata Bank'
    and 'Student Retriever'. The visual complexity requires a more descriptive caption
    to be self-contained.
- id: 9a22a570f1be
  severity: writing
  text: Figure 4 (student_teacher_ie_plots) and Figure 5 (tsne_qualitative_new) lack
    explicit axis labels and legends within the image files. Figure 4's x-axis (number
    of topics) and y-axis (IE) are not labeled on the plot, and Figure 5's t-SNE axes
    are unlabeled. These must be added for standalone readability.
- id: 2230bb58075c
  severity: writing
  text: Figure 3 (CompassRAG_qualitative_comparison) uses color coding (teal, red)
    to distinguish chunks but lacks a legend or explicit text labels within the figure
    indicating which color corresponds to 'Gold Chunk' vs 'Distractor'. The caption
    explains it, but the figure itself is ambiguous without reading the text.
artifact_hash: 5e7163c1713464843d620f2c37705ca96ededa7c235cfa3e5a0986f0a19b0aa7
artifact_path: projects/PROJ-766-mcompassrag-topic-metadata-as-a-semantic/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T15:14:52.337040Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

The manuscript contains several figures that fail to meet the standard of being self-contained and legible at print scale without relying heavily on the surrounding text or caption.

**Figure 1 (main-teaser):** While the concept is clear, subfigure (b) is a scatter plot comparing performance and latency. The axes are completely devoid of labels and units within the image. The x-axis represents latency (ms) and the y-axis represents performance (F1), but a reader viewing the figure in isolation (e.g., in a poster or slide) would not know the units or specific metrics. The caption provides this, but the figure itself should include axis titles.

**Figure 2 (CompassRAG-pipeline_v2):** This architectural diagram is dense. While the flow is logical, the legend for the icons (fire for trained, snowflake for frozen) is not explicitly defined in the caption with sufficient detail to be immediately obvious to a non-expert. Furthermore, the text labels inside the diagram are quite small; ensuring they are legible at 100% zoom is critical.

**Figure 3 (CompassRAG_qualitative_comparison):** This figure uses color to distinguish the "Gold Chunk" from distractors. However, there is no legend within the figure itself. The caption explains the colors, but standard practice dictates that the figure should include a small legend or direct labels (e.g., "Gold", "Distractor") on the visual elements to ensure accessibility and immediate comprehension.

**Figure 4 (student_teacher_ie_plots) & Figure 5 (tsne_qualitative_new):** Both figures suffer from missing axis labels. Figure 4 plots Information Efficiency against the number of topics, but the axes are not labeled. Figure 5 is a t-SNE plot; t-SNE axes are arbitrary, but the plot must still indicate what the points represent (e.g., a legend for the colors/shapes representing different chunks or the query). Without these, the figures are not interpretable in isolation.

**General:** The use of `resizebox` on tables and figures (e.g., Table 1, Figure 1) often leads to inconsistent font sizes that can become illegible when printed. While not strictly a figure content error, the visual balance of Figure 1 (subfigure widths 0.60 vs 0.36) creates an awkward aspect ratio that might be better balanced.

All figures require minor revisions to add internal axis labels, legends, and ensure text legibility independent of the caption.
