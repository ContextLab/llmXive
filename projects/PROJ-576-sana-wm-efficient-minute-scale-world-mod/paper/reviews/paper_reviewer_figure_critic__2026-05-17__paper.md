---
artifact_hash: e5cefeb8f5a622284bf4bd8a2b4800bf995401cb7708f8533b8b272aa0c905d4
artifact_path: projects/PROJ-576-sana-wm-efficient-minute-scale-world-mod/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-05-17T14:57:24.552069Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

The figure suite is comprehensive and generally aligns with the narrative, but specific improvements in caption detail, accessibility, and color reliance are required for print and screen-reader compatibility.

**Caption Specificity (Line 725):** Figure `fig:gdn-key-scaling` (Line 725) uses `\captionof{figure}` within a minipage alongside a table. The caption reads "Training stability ablation." This is too generic for a standalone figure. It must explicitly describe the axes (e.g., "Training Loss vs. Steps for varying key scaling factors") and the specific variants compared (e.g., "$1/\sqrt{D S}$ vs. $L_2$"). Without this, the plot is unintelligible without reading the main text.

**Color Reliance (Line 625):** Figure `fig:vis-main` caption states: "Green borders denote \modelname." This relies entirely on color distinction. For grayscale printing or color-blind readers, this visual cue is lost. Please add text labels (e.g., "SANA-WM") directly on the figure borders or use distinct border styles (solid vs. dashed) to ensure the comparison is legible without color.

**Accessibility (General):** No `\includegraphics` calls include `alt` text attributes (e.g., `alt text={...}`). While standard LaTeX does not enforce this, adding alt text descriptions for screen readers is recommended for modern accessibility compliance.

**Resolution Claims (Line 45):** The teaser figure (`fig:teaser`) represents the core 720p capability claim. Ensure the embedded PDF is high-resolution enough to demonstrate sharpness at the target print scale. Blurry thumbnails contradict the high-fidelity claims made in the text.

**Strengths:** Figure `fig:efficiency-analysis` (Line 755) has an excellent caption structure, clearly delineating subplots (a) and (b). The pipeline diagrams (`fig:pipeline_overview`, `fig:data_pipeline`) are well-referenced in the text and appear to match the described architecture.

**Action Items:**
1.  Update `fig:gdn-key-scaling` caption to describe axes and variants.
2.  Modify `fig:vis-main` to rely on shape/label in addition to color.
3.  Add alt text to all `\includegraphics` commands where possible.
4.  Verify resolution of `fig:teaser` against the 720p claim.
