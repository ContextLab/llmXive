---
action_items:
- id: 174cee66e11a
  severity: writing
  text: Figures in `Figures_tex/ablation.tex` lack visible axis labels or scale bars.
    Ensure source PDFs are high-resolution enough to resolve fine artifacts like 'antler
    separation' at print scale.
- id: c01e459cb395
  severity: writing
  text: Figure 3 (`Figures_tex/causal-cd.tex`) subfigure (b) claims efficiency gains
    but lacks y-axis units (e.g., GPU Hours). Explicitly label axes to validate the
    4x speedup claim visually.
- id: 4cefe3f63bfc
  severity: writing
  text: Figure 5 (`Figures_tex/performance_comparison.tex`) claims superiority over
    baselines but lacks quantitative overlays or clear axis labels if it is a chart.
    Add metrics or labels to substantiate the 'surpassing' claim.
artifact_hash: bc6ea3b7abb50e6d2d0c61521fe88f76d18733e7f3e4d74c5eba9d5fe9acb8e6
artifact_path: projects/PROJ-580-https-arxiv-org-abs-2605-15141/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T21:06:21.113568Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

The figures in this manuscript generally serve the narrative well, but several critical issues regarding legibility, labeling, and the "earning their place" criteria require attention before publication.

**Clarity and Legibility:**
In `Figures_tex/ablation.tex` (Figure 1), the subfigures compare initialization methods (1-step, 2-step, 4-step). The captions describe specific visual failures (e.g., "mouse's legs into a single indistinguishable mass," "antler separation artifacts"). However, the provided LaTeX code does not include any visual indicators of resolution or scale. Given the claim of "high visual quality," the source images (`Figures/ablation_step1.pdf`, etc.) must be rendered at a resolution where these fine-grained artifacts are clearly visible to the reader. If the PDF compilation results in blurry thumbnails, the figure fails to prove the claim. Additionally, there are no axis labels or units in any of the quantitative plots (e.g., `Figures_tex/causal-cd.tex`, `Figures_tex/dmd-is-worse-than-cd.tex`). While the text describes the metrics, the figures themselves must be self-contained.

**Axis Labels and Units:**
Figure 3 (`Figures_tex/causal-cd.tex`) contains a bar chart in subfigure (b) regarding "Training-efficiency." The caption states it "dramatically reduces training time," but the y-axis is not labeled in the LaTeX source. Without explicit units (e.g., "GPU Hours" or "Seconds") and a clear scale, the reader cannot verify the magnitude of the claimed 4x speedup. Similarly, Figure 4 (`Figures_tex/dmd-is-worse-than-cd.tex`) subfigure (b) attempts to visualize "history shift" with a schematic. The axes are undefined, making the "shift" interpretation purely speculative without visual anchors.

**Color Choices and Alt Text:**
The color schemes in `Figures_tex/performance_comparison.tex` and `Figures_tex/ablation.tex` appear to use standard distinct colors, but the contrast ratios for the text overlays (if any) are not specified. More importantly, the manuscript lacks alt text for these figures. For accessibility and reproducibility, a textual description of the visual trends (e.g., "Bar chart showing Causal CD at 2900 GPU hours vs. Causal ODE at 11600 GPU hours") should be included in the figure environment or the caption.

**Earning Their Place:**
Figure 2 (`Figures_tex/action.tex`) shows action-conditioned generation. While visually interesting, it lacks quantitative context. Does the "tilt" action result in a specific camera angle change? A small overlay indicating the camera pose or a reference frame would strengthen the claim of "interactive generation." Figure 5 (`Figures_tex/performance_comparison.tex`) is a single image claiming superiority over multiple baselines. If this is a grid of video frames, it is a weak form of evidence without accompanying metrics overlaid on the images. If it is a chart, the missing axis labels render it useless.

**Conclusion:**
The figures are currently too dependent on the text for interpretation. They require explicit axis labels, units, and higher-resolution rendering to ensure the specific artifacts mentioned in the captions are visible. The quantitative plots must be self-explanatory.
