---
action_items:
- id: 7d07ac906216
  severity: writing
  text: "Figure~\ref{fig:training_curves} lacks visible axis labels and units. The\
    \ x-axis (training steps/epochs) and y-axis (reward score) are not explicitly\
    \ labeled in the subplots, making the curves ambiguous without reading the caption.\
    \ Add 'Steps' and 'Reward' labels to all six subplots."
- id: 202c3c7aa90a
  severity: writing
  text: "The track-completion figures (Figs.~\ref{fig:track_completion_androidworld_qwen},\
    \ \ref{fig:track_completion_mobileworld_qwen}, \ref{fig:track_completion_mobileworld_guiowl})\
    \ are high-resolution PNGs but lack visual annotations (e.g., bounding boxes,\
    \ arrows, or text overlays) to highlight the specific UI elements where the base\
    \ model failed and the adapted model succeeded. The captions describe the failure,\
    \ but the visual evidence is not self-explanatory at print scale."
- id: fdd8458db28b
  severity: writing
  text: "The teaser figure (Fig.~\ref{fig:mobileforge-teaser}) is referenced in the\
    \ Introduction but its content is not visible in the provided LaTeX chunks. Ensure\
    \ the final PDF includes a high-contrast, legible diagram that clearly distinguishes\
    \ the 'Existing' vs. 'MobileForge' pipelines, as this is the primary visual hook\
    \ for the paper."
artifact_hash: eb6909e8c26be542682832f5d7b13c92b92b728f8b94fb6c9612acad1621be79
artifact_path: projects/PROJ-782-mobileforge-annotation-free-adaptation-f/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T20:16:07.284776Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

The manuscript relies heavily on visual evidence to demonstrate the efficacy of the MobileForge framework, yet several figures suffer from legibility and annotation issues that hinder immediate comprehension.

First, **Figure~\ref{fig:training_curves}** (Section 3) presents six subplots showing reward convergence. While the caption explains the metrics, the individual subplots lack explicit axis labels. The x-axis (presumably training steps or iterations) and y-axis (reward value) are missing tick labels and titles. In a print context, a reader cannot determine the scale or the specific metric being optimized (overall vs. action type vs. arguments) without cross-referencing the caption. All subplots must include clear axis labels (e.g., "Training Steps", "Reward Score") and a legend if multiple lines are present.

Second, the **track-completion case studies** (Figures~\ref{fig:track_completion_androidworld_qwen}, \ref{fig:track_completion_mobileworld_qwen}, and \ref{fig:track_completion_mobileworld_guiowl}) display side-by-side screenshots of base vs. adapted models. While the file sizes suggest high resolution, the images themselves lack visual annotations. The captions describe the failure modes (e.g., "repeated scrolling," "underspecified semester"), but the images do not visually highlight these specific errors. To earn their place, these figures should include bounding boxes, arrows, or semi-transparent overlays pointing to the exact UI elements where the base model erred and the adapted model succeeded. Without these annotations, the visual comparison is weak and requires the reader to mentally map the text description to the pixel data.

Finally, the **teaser figure** (Figure~\ref{fig:mobileforge-teaser}) is critical for the Introduction but its content is not fully rendered in the provided snippets. Assuming it exists in the final PDF, it must be designed to be self-explanatory. It should clearly contrast the "sparse-reward rollouts" of existing methods with the "hierarchical feedback" of MobileForge using distinct visual metaphors (e.g., color-coded feedback loops). If the current version relies on dense text blocks, it should be simplified to a flowchart with minimal text to ensure legibility at standard conference column width.

Addressing these annotation and labeling gaps is essential for the figures to effectively support the paper's claims.
