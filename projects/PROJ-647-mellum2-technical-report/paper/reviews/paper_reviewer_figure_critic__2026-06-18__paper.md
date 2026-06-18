---
action_items:
- id: bd96c6d0976e
  severity: writing
  text: "Figure\u202F1 (long\u2011context ablation) and Figure\u202F2 (long\u2011\
    context balancing loss) lack explicit axis labels and units in the PDF; add clear\
    \ X\u2011axis (\u201CEvaluation context length (tokens)\u201D) and Y\u2011axis\
    \ (\u201CRULER score\u201D) with tick marks and units."
- id: b9c4a018b3b4
  severity: writing
  text: "The color palette used in the throughput and latency comparison figures (e.g.,\u202F\
    throughput_comparison.pdf) is not color\u2011blind safe (red/green contrast);\
    \ replace with a palette that is distinguishable for deuteranopia."
- id: bf6928d2ee9d
  severity: writing
  text: "Several figures (e.g., rl_actors_diagram.pdf and rl_verifier_diagram.pdf)\
    \ contain very small text and line widths that become illegible when printed at\
    \ 1\u202Fcolumn width; increase font size and line thickness for readability."
- id: 05431749815e
  severity: writing
  text: "Figure\u202F3 (rl_instruct_accuracy.pdf) shows a black training curve and\
    \ a colored validation curve but does not include a legend; add a legend indicating\
    \ which color corresponds to training vs. validation."
- id: 7bc916849088
  severity: writing
  text: "The same figure (rl_instruct_accuracy.pdf) is duplicated later (see Section\u202F\
    e001 and Section\u202Fe002) without any caption change; remove the duplicate or\
    \ reference the original to avoid redundancy."
- id: 6475941fcdb7
  severity: writing
  text: "Figure\u202F4 (throughput_comparison.pdf) uses a single bar colour for all\
    \ models; differentiate models with distinct patterns or colors and label each\
    \ bar directly to aid quick visual comparison."
- id: af6f216a21f5
  severity: writing
  text: "Alt\u2011text descriptions are missing for all raster PDFs; provide concise\
    \ alt\u2011text (\u2264150\u202Fcharacters) in the LaTeX source (e.g., \\includegraphics[...]{...}\\\
    caption[Alt\u2011text]{...}) for accessibility."
- id: c11b6b1aa3be
  severity: writing
  text: "The MoE latency and throughput figures (moe_sync.pdf, moe_throughput.pdf)\
    \ are presented at 0.85\u202Ftextwidth but have a very tall aspect ratio, causing\
    \ compression of axis tick labels; consider using a more balanced aspect ratio\
    \ (e.g., 0.6\u202Ftextwidth) to preserve label legibility."
artifact_hash: cb4466a31e7b640ad51d8c2f8310c27b9827d874fc645a40e58bc959301ab98e
artifact_path: projects/PROJ-647-mellum2-technical-report/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-18T10:37:12.297103Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

The manuscript includes a substantial set of figures that are central to the technical contributions (long‑context ablations, MoE performance, RL infrastructure, and throughput benchmarks). Overall the figure selection is appropriate, but several presentation issues hinder clarity and accessibility.

1. **Axis labeling and units** – Figures showing quantitative curves (e.g., the long‑context ablation and RULER training plots) omit explicit axis titles and units. Readers must infer from the caption, which is insufficient for quick interpretation. Adding clear X‑ and Y‑axis labels (including units such as “tokens” or “percentage”) would resolve this.

2. **Color choices** – The throughput and latency comparison figures employ red/green color pairs that are not distinguishable for common forms of color‑blindness. Switching to a palette with higher contrast (e.g., blue/orange) or adding pattern fills would improve accessibility.

3. **Legibility at print scale** – Several schematic diagrams (RL actor topology, verification stack) and the RL accuracy plot use very small fonts and thin lines. When the PDF is printed in a two‑column format, these details become unreadable. Increasing font size (minimum 8 pt) and line width, and simplifying the diagrams, will ensure the figures remain interpretable.

4. **Missing legends** – The RL accuracy figure shows two curves but provides no legend, leaving the reader to guess which corresponds to training versus validation. Adding a concise legend resolves this ambiguity.

5. **Redundancy** – The same RL accuracy plot appears twice in the manuscript (once in Section e001 and again in Section e002) without any modification. This duplication consumes space and can confuse readers; the second instance should be removed or referenced as a repeat.

6. **Bar chart clarity** – The throughput comparison bar chart uses a single solid colour for all bars, making it hard to differentiate models at a glance. Introducing distinct colours or hatch patterns, together with direct bar labels, would make the comparison more immediate.

7. **Alt‑text for accessibility** – None of the raster figures include alt‑text, which is required for screen‑reader accessibility. Providing short descriptive alt‑text via the optional argument to \\caption (or using the \\includegraphics[alt=...] syntax) will make the paper compliant with accessibility guidelines.

8. **Aspect ratio distortions** – The MoE sync/throughput figures are rendered at a very wide width but limited height, compressing tick labels and reducing readability. Adjusting the figure dimensions to a more balanced aspect ratio will preserve label spacing and improve overall aesthetics.

Addressing these issues will significantly enhance the readability, reproducibility, and accessibility of the visual evidence supporting the paper’s claims.
