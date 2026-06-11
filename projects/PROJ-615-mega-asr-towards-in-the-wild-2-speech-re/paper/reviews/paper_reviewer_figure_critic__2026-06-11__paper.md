---
action_items:
- id: 5053112208a2
  severity: writing
  text: Reduce Figure 1 width from 1.1 textwidth to 0.95 textwidth to prevent margin
    overflow in standard proceedings.
- id: 4b0ae5d2c283
  severity: writing
  text: Clarify y-axis labels in Figure 3. Accuracy is ambiguous in ASR. Specify if
    this is 1-WER or token accuracy.
- id: bb317a490918
  severity: writing
  text: Ensure all figures are legible in grayscale. Verify distinct line styles or
    markers for Figure 1 radar plot.
- id: 68897d05c82f
  severity: writing
  text: Increase font size in Figure 5 (inference-routing) as it is constrained to
    0.41 linewidth within a minipage.
artifact_hash: b76830428db6f31ab0213200b5916231003e882ec498765fb220acf8020a5333
artifact_path: projects/PROJ-615-mega-asr-towards-in-the-wild-2-speech-re/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-11T02:24:35.932162Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

The manuscript includes a comprehensive set of figures that generally support the narrative regarding the Mega-ASR framework and the Voices-in-the-wild-2M dataset. However, several technical and legibility issues require attention to meet publication standards for figure quality.

**Figure 1 (fig:radar_comparison):** The inclusion width is set to 1.1 textwidth. This will cause overflow in standard two-column conference templates and risks cutting off axis labels or legends during print. Reduce to 0.95 textwidth or 0.9 textwidth. Additionally, radar charts can be difficult to interpret precisely. Ensure the legend is external or clearly placed, and verify that the color palette remains distinguishable when printed in grayscale, as many journals require monochrome compatibility.

**Figure 3 (fig:robustness_sampling_combined):** The caption references SFT accuracy curves. In ASR research, Word Error Rate (WER) is the standard metric, where lower is better. If the y-axis plots Accuracy, it must be explicitly defined (e.g., 100 minus WER). Ambiguity here confuses the reader regarding performance directionality. Ensure axis units are explicitly labeled (e.g., percent WER or percent Accuracy).

**Figure 5 (fig:inference-routing):** This figure is embedded within a minipage of 0.41 linewidth. At this reduced width, any text labels inside the diagram (e.g., model names, routing thresholds) risk becoming illegible. Increase the internal font size of the figure source or restructure the layout to utilize more horizontal space.

**Figure 6 (fig:study):** The case study displays transcriptions. Ensure the text overlays are high-contrast against the waveform background. If this figure relies on color coding to distinguish models (Gemini vs. Qwen vs. Mega-ASR), provide pattern fills or distinct line styles for accessibility.

Overall, the figures are informative but require scaling and labeling adjustments to ensure data integrity and readability across different output formats.
