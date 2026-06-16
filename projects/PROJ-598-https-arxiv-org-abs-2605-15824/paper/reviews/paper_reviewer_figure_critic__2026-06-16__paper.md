---
action_items:
- id: c7e4ad168d08
  severity: writing
  text: "Figure \\ref{fig:intro} (average performance chart) lacks axis labels and\
    \ units; add a clear X\u2011axis label (e.g., \u201CMethod\u201D) and Y\u2011\
    axis label (e.g., \u201CScore / FPS\u201D) with numeric ranges."
- id: f4b6a11eaf92
  severity: writing
  text: "Figures \\ref{fig:overall_pipeline}, \\ref{fig:analysis}, and \\ref{fig:qualitative_comparison}\
    \ use color palettes that are not color\u2011blind friendly (red/green contrasts).\
    \ Replace with a palette that is distinguishable for deuteranopia/protanopia."
- id: 144966c0e8ea
  severity: writing
  text: "Several PDF figures (e.g., \\ref{fig:teaser}, \\ref{fig:overall_pipeline},\
    \ \\ref{fig:analysis}) are rendered at 0.98\u202F\xD7\u202Ftextwidth but may be\
    \ too small for print; increase their width to at least 0.9\u202F\\linewidth or\
    \ provide higher\u2011resolution raster versions."
- id: 77c4223c7b08
  severity: writing
  text: "Alt\u2011text descriptions are missing for all figures; add concise alt\u2011\
    text in the caption or a separate \\caption[]{...} command to improve accessibility."
- id: 32b139312989
  severity: science
  text: Figure \ref{fig:user_preference} (human evaluation bar plot) does not indicate
    error bars or statistical significance; include standard deviation or confidence
    intervals to support the claim of superiority.
- id: 5749293581b7
  severity: writing
  text: The analysis figure (\ref{fig:analysis}) shows attention visualisation but
    the color scale is not explained; add a legend indicating what the color intensity
    represents.
- id: a1a20908d09f
  severity: writing
  text: "In the ablation figure(s) (e.g., \\ref{fig:ablation2}), the sub\u2011figures\
    \ are not labelled (a), (b), etc., making it hard to reference them in the text;\
    \ add panel labels."
artifact_hash: 8ac732f80d31fee19845b13e35eb49deeae5414cb6cb993b15f1b25017de2aa1
artifact_path: projects/PROJ-598-https-arxiv-org-abs-2605-15824/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-16T04:46:24.580277Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

The manuscript relies heavily on visual evidence to support its claims of real‑time, interactive garment‑level video customization. While the figures are generally well‑chosen, several recurring issues impede clarity, accessibility, and scientific rigor.

**Labeling and Units**  
Figure \ref{fig:intro} presents a performance chart but omits axis labels and units, leaving readers uncertain whether the Y‑axis depicts raw scores, percentages, or FPS. Adding explicit X‑ and Y‑axis labels with appropriate tick marks is essential. Similarly, the human‑evaluation bar plot in Figure \ref{fig:user_preference} lacks error bars or confidence intervals, making the claim of superiority unsupported statistically.

**Color‑Blind Friendly Palettes**  
Figures \ref{fig:overall_pipeline}, \ref{fig:analysis}, and \ref{fig:qualitative_comparison} employ red/green contrasts that are problematic for common forms of color blindness. Switching to a palette such as blue‑orange or adding texture/pattern cues will improve interpretability for a broader audience.

**Resolution and Print‑Scale Legibility**  
The teaser (\ref{fig:teaser}) and several pipeline diagrams are inserted at near‑full width but originate from low‑resolution PDFs (~350 KB). When printed, fine details (e.g., arrows in the KV‑cache diagram) become illegible. Providing higher‑resolution PDFs (≥300 dpi) or increasing the displayed width to at least 0.9 \linewidth will ensure readability.

**Legends, Annotations, and Panel Labels**  
The attention heatmap in Figure \ref{fig:analysis} lacks a legend explaining the color intensity, and the ablation figure(s) (\ref{fig:ablation2}) do not include panel identifiers (a), (b), etc., making cross‑references ambiguous. Adding concise legends and panel labels will make the figures self‑contained.

**Accessibility**  
No alt‑text is supplied for any figure, which hampers accessibility for screen‑reader users. Concise alt‑text should be added either within the caption or via a dedicated \verb|\caption[]{...}| command.

Addressing these points will substantially enhance the manuscript’s visual communication, making the experimental evidence clearer and more trustworthy.
