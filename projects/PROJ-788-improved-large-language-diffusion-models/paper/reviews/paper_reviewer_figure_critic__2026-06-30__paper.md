---
action_items:
- id: 00fd600186a1
  severity: writing
  text: Figure 1 (Fig.~\ref{fig:sft-epochs}) lacks visible axis labels and units in
    the provided source. The x-axis (SFT epochs) and y-axis (benchmark scores) must
    be explicitly labeled with units (e.g., 'Epochs', 'Accuracy (%)') to ensure legibility
    at print scale and standalone interpretability.
- id: a615ede56d34
  severity: writing
  text: The subfigures in Fig.~\ref{fig:sft-epochs} do not contain individual captions
    (a), (b), (c) identifying the specific benchmark (GSM8K, MATH, MMLU-Pro) within
    the plot area or as sub-captions. The main caption lists them, but standard practice
    requires explicit labeling for clarity when the figure is viewed in isolation.
- id: 1ede3320cc60
  severity: writing
  text: The figure file paths (e.g., `imgs/sft_epochs_gsm8k.pdf`) are referenced,
    but the actual image content cannot be verified for color choices, line distinctness,
    or grid visibility. The authors must ensure that the final PDF renders with high-contrast
    colors and distinct line styles to differentiate the three benchmarks if they
    are plotted together, or ensure the three separate subplots are clearly distinguishable.
artifact_hash: 619f929e5279533c346a7478d5b6956c60e2e6e84c89950452f3d9515b5b8b28
artifact_path: projects/PROJ-788-improved-large-language-diffusion-models/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T21:48:43.165419Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

The manuscript contains a single figure, `Fig.~\ref{fig:sft-epochs}` (lines 335-348 in `main-llmxive.tex`), which visualizes the ablation study on SFT duration. While the figure conceptually supports the claim that performance improves with more epochs, it suffers from significant clarity issues in its current LaTeX implementation.

First, the figure lacks explicit axis labels. The code includes `\includegraphics` commands for three subfigures but does not define the x-axis (SFT epochs) or y-axis (benchmark score) labels within the figure environment or the subfigure captions. Without these labels, the figure is not self-explanatory, violating the requirement for legibility at print scale. The reader must rely entirely on the main caption to understand what the axes represent.

Second, the subfigures are not individually labeled with (a), (b), (c) or specific benchmark names within the plot area. While the main caption lists "GSM8K, MATH, and MMLU-Pro," standard scientific visualization practice requires that each subplot be clearly identified, especially when the figure is extracted or viewed in isolation. The current implementation relies on the order of inclusion matching the order in the caption, which is fragile.

Third, the color choices and line styles cannot be verified from the source code alone, but given the context of "SFT epoch ablation," it is critical that the trend lines are distinct and the grid lines (if any) do not obscure the data points. The authors should ensure the final rendered PDF uses high-contrast colors and clear markers.

Finally, the figure does not include error bars or confidence intervals, which are standard for benchmark evaluations involving multiple runs or seeds. While the text mentions "performance generally improves," the lack of uncertainty visualization in the figure makes it difficult to assess the statistical significance of the gains between epochs, a point raised by the statistical analysis reviewer. The figure should be updated to include error bars or shaded confidence regions if the data is available.

The figure earns its place by illustrating a key finding (the benefit of long SFT), but it requires revision to meet standard clarity and legibility requirements.
