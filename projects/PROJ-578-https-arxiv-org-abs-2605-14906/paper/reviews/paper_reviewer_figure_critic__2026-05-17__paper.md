---
artifact_hash: d50a4f0b1e568c7504bc9f36b9def267fba709bab11751ed7e3ec317ba0682a2
artifact_path: projects/PROJ-578-https-arxiv-org-abs-2605-14906/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-05-17T14:27:58.998862Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

**Figure Review Feedback**

The manuscript includes a substantial set of figures (e.g., `fig:pipeline`, `fig:per_type_heatmap`, `fig:context_degradation`) that effectively visualize the benchmark construction and evaluation results. However, several critical issues regarding figure completeness, caption detail, and file consistency require minor revision to ensure print legibility and accessibility.

**1. Missing Figure Definitions**
The `# Figures` metadata lists `figures/scaling_curves.pdf`, `figures/retrieval_decomposition_stacked_bar.pdf`, and `figures/context_delta_heatmap.pdf`, yet these are not defined in the LaTeX source.
- `context_delta_heatmap.pdf` is explicitly referenced in Appendix `\S\ref{app:wrong_answer_figures}` ("produce Figure~\ref{fig:wrong_answer_pie} and Figure~\ref{fig:context_delta_heatmap}"), but no corresponding `\begin{figure}` environment exists. This will result in a broken reference in the compiled PDF.
- `scaling_curves.pdf` and `retrieval_decomposition_stacked_bar.pdf` appear in the file list but lack `\includegraphics` commands in the provided text. If these figures support claims in the main text or appendices, they must be included or the references removed.

**2. Caption Accessibility and Detail**
Captions must function as standalone alt text for accessibility.
- **`fig:pipeline` (Line ~400):** The caption "MemLens construction pipeline." is insufficient. It should describe the four stages (session simulation, question construction, evidence wrapping, assembly) to be informative without the image.
- **`tab:benchmark_comparison_full` (Line ~150):** This table embeds `figures/composition_donut.pdf`. The caption describes the table but does not explicitly describe the donut chart's content (e.g., "inner ring shows task distribution..."). Ensure the chart's data is summarized in the caption for readers unable to see the color-coded rings.

**3. Legibility and Cross-Referencing**
- **`fig:visual_error` (Line ~720):** The caption references `Table~\ref{tab:modality_mapping}` for category definitions. In print, ensure this table appears on the same page or facing page to maintain legibility; otherwise, readers may lose context when flipping back.
- **`fig:per_type_heatmap` (Line ~550):** The caption notes "Missing cells indicate models that exceed their usable context budget." This is excellent clarity. Ensure the colormap is colorblind-safe (e.g., viridis or plasma) in the final PDF, as green/red distinctions can be problematic for some readers.

**Action Items:**
1. Add `\begin{figure}` environments for `scaling_curves`, `retrieval_decomposition_stacked_bar`, and `context_delta_heatmap` or remove their references.
2. Expand `fig:pipeline` caption to detail the pipeline stages.
3. Verify colorblind safety for all heatmaps (`fig:per_type_heatmap`, `fig:type_correlation`).

These changes will ensure the visual evidence is complete, accessible, and reproducible at print scale.
