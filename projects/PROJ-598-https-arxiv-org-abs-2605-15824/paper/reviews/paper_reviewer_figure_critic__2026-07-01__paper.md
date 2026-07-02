---
action_items:
- id: b52679c815ec
  severity: writing
  text: Figure 1 (teaser.pdf) and Figure 2 (intro.pdf) lack explicit axis labels and
    units where quantitative data is presented. Specifically, Figure 2 compares performance
    metrics (Cur., GME, etc.) and FPS but does not define the units or scales on the
    axes, making it difficult to interpret the magnitude of differences at print resolution.
- id: 658649c7d5a5
  severity: writing
  text: The color palette in Table 1 (main_results) and Figure 2 (intro.pdf) relies
    heavily on grayscale and standard blue/red. For print accessibility, ensure that
    the distinction between 'best' (bold) and 'second best' (underlined) is not solely
    dependent on color or font weight, as these may be lost in black-and-white printing.
    Consider adding distinct patterns or markers for data points in Figure 2.
- id: 5ec891234202
  severity: writing
  text: Figure 3 (analysis.pdf) contains attention visualization heatmaps. The colorbar
    for the attention weights is missing or illegible in the provided source context.
    Ensure the colorbar includes a clear label (e.g., 'Attention Weight'), a numerical
    scale, and a distinct colormap that is perceptually uniform and accessible to
    colorblind readers.
- id: c148dd028ace
  severity: writing
  text: Figure 4 (qualitative.pdf) and subsequent qualitative figures (app.pdf, ablation.pdf)
    are referenced as 'omitting prompts' in captions. While acceptable for space,
    the figure captions should explicitly state the resolution of the displayed frames
    (e.g., 720p) and the specific garment switching timestamps if applicable, to ensure
    the visual evidence is self-contained and reproducible without reading the full
    text.
artifact_hash: 8ac732f80d31fee19845b13e35eb49deeae5414cb6cb993b15f1b25017de2aa1
artifact_path: projects/PROJ-598-https-arxiv-org-abs-2605-15824/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T21:13:47.328760Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

The manuscript presents a visually rich set of figures, but several critical issues regarding clarity, legibility, and self-containment require attention before publication.

**Clarity and Axis Labels:**
In `sections/1-intro.tex`, Figure 2 (`figures/intro.pdf`) is a bar chart comparing performance metrics (Cur., GME, Amp., Smoo., VQ) and inference speed (FPS). The caption mentions "Average performance," but the figure itself lacks explicit axis labels indicating the metric names and their corresponding units or scales. For instance, the FPS axis needs a clear label "Frames Per Second (FPS)" and the other metrics need their specific score ranges (e.g., 0-1 or 0-5) indicated. Without these, the quantitative comparison is ambiguous. Similarly, in `sections/4-exp.tex`, Table 1 (`tab:main_results`) uses bold and underline for best/second-best results, but the column headers for metrics like "Cur." and "GME" are abbreviations. While defined in the text, the table caption or headers should ideally expand these or ensure the legend is robust enough for standalone reading.

**Legibility and Color Choices:**
The figures rely on standard color schemes (e.g., `taobaocolor` and `xmucolor` defined in `main.tex`). In `figures/analysis.pdf` (Figure 3), the attention visualization (right panel) uses a heatmap. The current source does not show a visible colorbar or legend explaining the intensity scale of the attention weights. This is a critical omission for a scientific figure; readers cannot interpret the "more concentrated" claim without a scale. Additionally, ensure that the distinction between the "Garment KV Refresh" and "Historical KV Withdraw" in the left panel of Figure 3 is distinguishable in grayscale, as the current description suggests a binary visual difference that might be lost in print.

**Self-Containment and Alt Text:**
Figures 4 (`qualitative.pdf`), 5 (`app.pdf`), and 6 (`ablation.pdf`) are central to the paper's claims of interactive customization and long-video extrapolation. The captions repeatedly state, "We omit the input prompts for brevity; see Appendix." While space-constrained, a figure in a paper should ideally be interpretable without cross-referencing the appendix for basic context. The captions should at least specify the resolution (e.g., 720p) and the specific frame intervals where garment switching occurs in the interactive examples. Furthermore, the LaTeX source lacks `alt` text or `description` fields for these figures, which is a requirement for accessibility compliance in modern publishing standards.

**Conclusion:**
The figures effectively demonstrate the method's capabilities but fail to meet the standard of being self-explanatory. The lack of axis labels in quantitative plots and missing legends in heatmaps significantly hinders the reader's ability to validate the claims visually. Minor revisions to add these labels, legends, and accessibility metadata are required.
