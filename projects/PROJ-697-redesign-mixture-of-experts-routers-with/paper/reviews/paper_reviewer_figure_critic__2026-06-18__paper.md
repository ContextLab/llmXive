---
action_items:
- id: a773eb7a5b79
  severity: writing
  text: "Add explicit axis labels (including units where applicable) to all loss and\
    \ performance plots (e.g., Fig.\u202F1, Fig.\u202F2, Fig.\u202F3, Fig.\u202F4,\
    \ Fig.\u202F5)."
- id: dfaba5d4f03f
  severity: writing
  text: "Replace the default color scheme in the plots with a color\u2011blind\u2011\
    friendly palette (e.g., use colorblind\u2011safe blues/oranges or patterns) and\
    \ ensure that line styles are distinguishable when printed in grayscale."
- id: c80e9566197b
  severity: writing
  text: "Provide concise alt\u2011text descriptions for each figure (including sub\u2011\
    figures a/b) in the LaTeX source using the \\caption[...]{...} optional argument\
    \ or the \\includegraphics[alt=...]{...} package option."
- id: bb259d2a792b
  severity: writing
  text: "Increase the font size of tick labels and legends in the PDF figures to guarantee\
    \ legibility at typical conference print scales (e.g., \u22659\u202Fpt)."
- id: 4ac8b3e0f518
  severity: writing
  text: "For the code\u2011listing figure (Fig.\u202F1), avoid colored background\
    \ highlights (blue/pink) that may not reproduce well in print; use a neutral gray\
    \ or no background, and ensure the listing remains readable in monochrome."
- id: ee11c8225ac3
  severity: writing
  text: "Clarify in the captions which curve corresponds to which optimizer or model\
    \ variant (e.g., in Fig.\u202F2 and Fig.\u202F3) either by adding a legend within\
    \ the figure or by explicitly naming the curves in the caption."
- id: e44a68be869e
  severity: writing
  text: Ensure that all figures are referenced in the text before they appear and
    that the figure numbers match the order of appearance.
artifact_hash: 34fabb025335fc2fcf0855d53316dbb275a62eee03c0f1ad1b72c49ea11b1392
artifact_path: projects/PROJ-697-redesign-mixture-of-experts-routers-with/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-18T04:40:02.205025Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

The manuscript contains several figures that are central to the empirical claims, but their current presentation hampers clear interpretation.  

**Figure 1 (code pseudo‑code)** – This is rendered as a listing with blue and pink background highlights. While the highlighting helps readability on screen, it will not survive typical grayscale printing and may be confusing for readers with color‑vision deficiencies. Use a neutral background or pattern‑based emphasis, and ensure the font size remains legible when printed.  

**Figure 2 (loss_1b_MuonH.pdf)** – The caption mentions a reduction in pre‑training loss but does not specify what the axes represent. It is unclear whether the x‑axis displays training steps, tokens processed, or epochs, and the y‑axis should be labelled with the loss metric (e.g., “Cross‑entropy loss”). Adding axis labels, units, and a legend identifying the curves (baseline vs. + MPI) would make the improvement immediately apparent.  

**Figure 3 (loss_task.pdf)** – This composite figure shows both convergence and downstream performance, yet the caption only generically describes “Convergence and Downstream Performance Comparison.” The sub‑figures (a) and (b) are not individually labeled in the caption, and the axes lack units. Explicitly label the x‑axis (e.g., “Tokens (Billion)”) and y‑axes (“Training loss” and “Average accuracy %”), and include a legend for the model variants.  

**Figure 4 (loss_3b_bal_loss.pdf)** – The plot of load‑balancing loss suffers from the same missing axis labels and legend issues. The y‑axis should indicate the specific loss term (e.g., “Balancing loss”) and the x‑axis the training progress.  

**Figure 5 (ablation-3b.pdf)** – The ablation study plot does not identify which curve corresponds to which ablation condition. Adding a clear legend and axis labels (e.g., “Training steps” vs. “Loss”) is essential.  

Across all plots, the current color choices (solid lines of similar hue) may be difficult to distinguish for color‑blind readers. Switching to a palette that is verified for color‑blind safety, or adding distinct line styles (dashed, dotted), will improve accessibility.  

The captions should also include brief alt‑text (via the optional argument of \\caption) that describes the visual content for screen‑reader users.  

Finally, the code‑listing figure’s background colors should be removed or replaced with a neutral tone to ensure the figure prints correctly and remains accessible.  

Addressing these issues will significantly enhance the clarity, accessibility, and reproducibility of the presented results without altering the scientific content.
