---
action_items:
- id: 8d8a7a0d12ff
  severity: writing
  text: Convert figures/teaser.png to vector format (.pdf/.eps) for print quality.
- id: 4f102a8745d9
  severity: writing
  text: Move main_dl3dv_mesh_render.pdf and main_dl3dv_textured_mesh.pdf to sections/04_experiments.tex.
- id: 9a5a094f8f68
  severity: writing
  text: Ensure axis labels are present on the pipeline2.pdf bubble chart, not just
    in caption.
- id: e67f2b315feb
  severity: writing
  text: Add sub-figure labels (a, b, c) to grouped appendix figures.
artifact_hash: 375d837bf9b63242d32116a8a2f6433796abb291136cadef4ae07e469b227763
artifact_path: projects/PROJ-627-trisplat-simulation-ready-feed-forward-3/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-02T07:53:14.716230Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

The figure presentation generally supports the simulation-ready narrative, but several technical issues regarding format, placement, and accessibility require correction before publication. These changes are necessary to meet standard conference journal requirements for print quality and standalone readability.

First, `figures/teaser.png` (main.tex, line 67) is provided as a raster image. For print-quality proceedings, all figures, especially the prominent teaser, must be vector-based (`.pdf` or `.eps`) to prevent pixelation at high DPI. Convert this to a vector format to ensure sharpness in the final PDF.

Second, figures `main_dl3dv_mesh_render.pdf` and `main_dl3dv_textured_mesh.pdf` are currently embedded in `sections/03_method.tex` (lines 170, 176). These represent experimental results and comparisons. They should be moved to `sections/04_experiments.tex` to maintain the logical flow between methodology description and evaluation results.

Third, Figure 1 (`figures/pipeline2.pdf`) describes a bubble chart in the caption ("mesh-rendering PSNR versus mesh geometry F1"). Ensure these axes are explicitly labeled *on the figure itself*, not just in the caption, to ensure standalone legibility for readers who view the figure without the surrounding text.

Fourth, grouped appendix figures like `supp_nvs_re10k_mesh_render_01.pdf` contain multiple images. Add explicit sub-figure labels (e.g., (a), (b), (c)) in the caption and ensure they correspond to visual markers in the image. This is critical for referencing specific rows or scenes in the text. Additionally, for simulation sequences (e.g., `supp_sim_unity_character.pdf`), ensure frame timestamps ($t=1$ to $t=4$) are visible within the image frames themselves.

Finally, verify color choices for grayscale legibility. Many comparison figures rely on color differences to distinguish methods; ensure contrast remains distinguishable if printed in black-and-white or viewed by colorblind readers. Ensure font sizes within figures match the paper's typography to maintain visual consistency.

These changes will ensure figures meet publication standards for clarity, accessibility, and professional presentation.
