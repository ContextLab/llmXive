---
action_items:
- id: 5c70a407853c
  severity: writing
  text: Fig. 1 (teaser) and Fig. 2 (pipeline) lack explicit axis labels or scale bars
    where spatial dimensions are implied. The '64-GPU training' and 'single-GPU inference'
    claims in captions are text-heavy; consider moving these to the main text and
    using a small inset icon or schematic for hardware scale to improve visual clarity
    at print resolution.
- id: 1ffed5e96dcb
  severity: writing
  text: Fig. 4 (efficiency-analysis) sub-figure (b) shows 'OOM' for all-softmax but
    lacks a clear y-axis label for memory (GB) and x-axis for sequence length (frames/seconds).
    The 'scaled for readability' note in the caption for sub-figure (a) is insufficient;
    the bars must have explicit numerical tick marks or a secondary axis to allow
    quantitative comparison of latency.
- id: f3c37284adb8
  severity: writing
  text: Fig. 5 (train-stability) combines a table and a line plot. The line plot (loss-vs-scale)
    has no visible axis labels or units in the provided source context. Ensure the
    y-axis clearly indicates 'Loss' or 'Gradient Norm' and the x-axis indicates 'Training
    Steps' with appropriate scaling to verify the 'NaN events' claim visually.
- id: 23996062a440
  severity: writing
  text: Qualitative figures (Fig. 6, Fig. 7, Fig. 12) rely on 'Green borders' and
    'transparent overlays' for comparison. At standard print resolution (300 DPI),
    these overlays may be illegible. Verify that the 'Zoom in for details' instruction
    is supported by sufficient resolution in the PDF and that the green border contrast
    is high enough for grayscale printing.
artifact_hash: e5cefeb8f5a622284bf4bd8a2b4800bf995401cb7708f8533b8b272aa0c905d4
artifact_path: projects/PROJ-576-sana-wm-efficient-minute-scale-world-mod/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T20:48:05.999891Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

The figure suite in SANA-WM is generally well-structured to support the paper's claims of efficiency and quality, but several critical visual elements lack the necessary annotation for standalone interpretability, particularly regarding quantitative axes and print-scale legibility.

**Clarity and Axis Labels:**
Figures 4 (`efficiency-latency-gpu.pdf`) and 5 (`loss-vs-scale.pdf`) are the most problematic. In Fig. 4(b), the claim that the all-softmax variant "OOMs" (Out of Memory) is central to the efficiency argument, yet the y-axis (presumably Memory in GB) and x-axis (Sequence Length) are not explicitly labeled in the provided LaTeX context. Without clear tick marks and units, the reader cannot verify the magnitude of the memory savings or the exact point of failure. Similarly, Fig. 4(a) mentions bars are "scaled for readability," which is a red flag for quantitative figures; the axes must display actual values (e.g., seconds, GB) to validate the "36x throughput" claim. Fig. 5's line plot lacks axis labels entirely, making it impossible to visually confirm the "immediate gradient instability" or the specific step count where NaNs occur without cross-referencing the text.

**Legibility and Color Choices:**
The qualitative comparison figures (Fig. 6 `vis-main`, Fig. 7 `vis-appendix`, and Fig. 12 `vis_refiner`) rely heavily on "Green borders" and "transparent action overlays" to distinguish the proposed method from baselines. While effective on high-resolution screens, these visual cues often fail in grayscale print or at reduced sizes. The "transparent overlays" in the bottom-left corners may become indistinguishable from the video content if the contrast is low. The authors should ensure the green border is thick enough and high-contrast enough to be visible in black-and-white reproduction, or consider using distinct patterns (e.g., dashed vs. solid lines) in addition to color.

**Figure Placement and Content:**
Fig. 1 (Teaser) and Fig. 2 (Pipeline) are dense. The caption for Fig. 1 packs significant quantitative claims ("64-GPU training", "single-GPU inference") into the text. While the figure itself is a teaser, the visual representation of the hardware scale is missing. A small schematic icon or a simplified hardware diagram inset would make the efficiency claim more immediate. Additionally, Fig. 3 (`benchmark_trajectories`) uses a minipage layout that might cause alignment issues in the final two-column PDF; ensuring the BEV paths are large enough to distinguish the "Simple" vs. "Hard" trajectory complexity is crucial.

**Alt Text and Accessibility:**
The LaTeX source does not include `alt` text or `description` fields for the figures. For a paper claiming "high-fidelity" and "precise control," the figures must be accessible to screen readers. The current captions describe the content but do not provide the necessary alternative text for visually impaired readers to understand the data trends in the efficiency plots or the qualitative differences in the video frames.

**Conclusion:**
The figures effectively illustrate the architecture and results but require minor revisions to ensure they are self-contained, quantitatively precise, and legible in print. Adding explicit axis labels, units, and verifying color contrast for grayscale printing are essential steps before acceptance.
