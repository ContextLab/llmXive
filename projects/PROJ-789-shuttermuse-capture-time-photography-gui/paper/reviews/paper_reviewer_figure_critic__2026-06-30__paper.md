---
action_items:
- id: 8ffce2370ebc
  severity: writing
  text: Figures Fig/teaser.pdf, Fig/Qualitative_comparison_photographer.pdf, and Fig/Qualitative_comparison_subject.pdf
    lack explicit axis labels, units, or scale bars where geometric precision (bounding
    boxes, keypoints) is visualized. While qualitative, the lack of a reference scale
    or grid makes it difficult to verify the 'refine' vs 'keep' claims visually without
    relying solely on the caption.
- id: abf0c82f299e
  severity: writing
  text: Figures Fig/composition_data_construction.pdf and Fig/pose_data_construction.pdf
    (pipeline diagrams) do not include alt text or detailed captions describing the
    specific visual encoding (e.g., color coding for 'visible' vs 'occluded' keypoints).
    The text mentions these states, but the figure itself must be self-explanatory
    for print accessibility.
- id: 39ff94420bc6
  severity: writing
  text: Fig. Fig/self_distill_iteration_curves.pdf contains four subplots (a-d) but
    the caption does not explicitly map the subplots to the specific metrics (IoU,
    RSR, KSR, R) mentioned in the text, nor does it specify the units or ranges of
    the axes. The axes labels in the source PDF are illegible at print scale; they
    must be enlarged or explicitly defined in the caption.
artifact_hash: c05d947baccac31badb983e4672bc18e6d1ae08f6b2511780ab5cbcde805c567
artifact_path: projects/PROJ-789-shuttermuse-capture-time-photography-gui/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T22:10:48.296277Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

The manuscript contains a rich set of figures supporting the proposed benchmark and model, but several critical issues regarding legibility, self-containment, and visual encoding standards need addressing before publication.

**Legibility and Scale:**
The qualitative comparison figures (`Fig/Qualitative_comparison_photographer.pdf`, `Fig/Qualitative_comparison_subject.pdf`) and the teaser (`Fig/teaser.pdf`) rely heavily on visual overlays (bounding boxes, skeleton keypoints). In the current rendering, the bounding box coordinates and keypoint connections are difficult to distinguish at standard print resolution. Specifically, in `Fig/Qualitative_comparison_subject.pdf`, the skeleton overlays on the background scenes lack sufficient contrast or line weight to clearly differentiate between the model's prediction and the ground truth (if shown) or to verify the "floating" artifacts mentioned in the failure analysis. A scale bar or a small inset showing the original image dimensions would aid in assessing the geometric accuracy of the recommendations.

**Axis and Labeling:**
The line chart `Fig/self_distill_iteration_curves.pdf` (Section 5.3) presents four subplots tracking EMDP reliability. The caption lists the metrics (IoU, RSR, KSR, R) but does not explicitly link them to subplots (a)-(d). Furthermore, the axis labels in the source PDF appear to be rendered at a font size that is illegible when the figure is scaled to column width. The y-axes lack units (e.g., percentage vs. raw score), and the x-axes (rounds) need clear tick labels. This violates the requirement that figures be interpretable without constant reference to the main text.

**Accessibility and Encoding:**
The pipeline diagrams (`Fig/composition_data_construction.pdf`, `Fig/pose_data_construction.pdf`) use color to denote different stages (e.g., expert seed, MLLM verification). However, the captions do not provide a legend or describe the color mapping. For a grayscale print version, these distinctions may be lost. The caption for `Fig/pose_data_construction.pdf` mentions "visibility states" but does not explain how these are visually represented in the diagram (e.g., dashed lines for occluded keypoints).

**Data Visualization:**
The dataset distribution figure (`Fig/data_distribution.pdf`) is a simple bar chart. While clear, it lacks error bars or confidence intervals if the distribution is sampled, which would strengthen the claim of "balanced coverage." Additionally, the figure does not explicitly state the total number of samples (130K) in the axis or title, forcing the reader to cross-reference the text.

**Conclusion:**
The figures effectively illustrate the system's capabilities but fail to meet the strict standards of print legibility and self-containment required for a conference paper. The authors must increase font sizes for axis labels, add explicit legends for color encodings, and ensure all quantitative plots include units and clear axis definitions.
