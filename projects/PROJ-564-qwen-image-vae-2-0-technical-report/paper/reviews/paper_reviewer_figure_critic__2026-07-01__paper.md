---
action_items:
- id: 412e56d26806
  severity: writing
  text: 'The figures in the Qwen-Image-VAE-2.0 Technical Report generally support
    the narrative of high-fidelity reconstruction and text legibility, but several
    critical issues regarding clarity, labeling, and print-readability must be addressed
    before publication. Figure 1 (OmniDoc-TokenBench): Located in sec/bench.tex, this
    figure serves as the visual introduction to the new benchmark. The current caption
    ("OmniDoc-TokenBench, a curated collection of ~3K text-rich images") is too sparse.
    It fails to de'
artifact_hash: 815458de8568b35ab5a02599bda9f602ed2dc04d545bca014bc4749f57af838e
artifact_path: projects/PROJ-564-qwen-image-vae-2-0-technical-report/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T19:51:32.161211Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

The figures in the Qwen-Image-VAE-2.0 Technical Report generally support the narrative of high-fidelity reconstruction and text legibility, but several critical issues regarding clarity, labeling, and print-readability must be addressed before publication.

**Figure 1 (OmniDoc-TokenBench):** Located in `sec/bench.tex`, this figure serves as the visual introduction to the new benchmark. The current caption ("OmniDoc-TokenBench, a curated collection of ~3K text-rich images") is too sparse. It fails to describe the visual diversity shown in the figure (e.g., specific document types like exam papers vs. financial reports). A reader skimming the paper should be able to understand the benchmark's scope solely from the figure and caption. Please expand the caption to explicitly list the categories of documents depicted.

**Figure 2 (Architecture Ablation):** In `sec/model.tex`, the figure comparing NSC, LSC, and GSC is referenced as showing "reconstruction loss and PSNR performance." However, the provided LaTeX source does not include the actual plot code or image content, only the placeholder. Assuming the final PDF contains the plot, it is imperative that the axes are clearly labeled. The x-axis must indicate the training progression (steps or epochs), and the y-axes must specify units (e.g., "Loss" and "PSNR (dB)"). The legend distinguishing the three connection types must be high-contrast and legible at standard print resolution (300 DPI).

**Figure 3 (Qualitative Text Comparison):** This figure in `sec/experiment.tex` is the primary evidence for the text-rendering claims. While the visual comparison is strong, the figure relies heavily on color (red text) to distinguish the proposed model from baselines. This poses a risk for grayscale printing or color-blind readers. The caption should explicitly state which column corresponds to which model, and the visual distinction should not rely solely on color. Furthermore, the "zoomed-in word" panels lack scale bars or pixel dimensions. Without a reference scale, it is impossible for the reader to judge the absolute size of the text strokes being reconstructed, which is central to the "high compression" argument.

**Figure 4 (Generated Samples):** The generated images in `sec/experiment.tex` are presented as evidence of diffusability. The caption is generic ("Selected image samples..."). To ensure reproducibility and proper evaluation, the caption must include the specific inference parameters used (e.g., "Generated with SiT-XL/2, 80 epochs, CFG scale=7.0"). Without this, the visual quality cannot be fairly compared to other works that might use different guidance scales.

Finally, ensure all figure files (`pics/*.pdf`) are high-resolution vector graphics or 300+ DPI bitmaps to prevent aliasing artifacts in the final print version, particularly for the text-heavy panels in Figure 3.
