---
action_items:
- id: a6305e9e106c
  severity: writing
  text: "Figure\u202F1 (Overview) lacks a clear legend for the color coding used in\
    \ the bottom panel. Add a concise legend or annotate the regions directly to indicate\
    \ which colors correspond to high activation versus low causal response."
- id: 899bdc07494c
  severity: writing
  text: "Figures\u202F4 and\u202F5 (causal ranking and concept activation maps) present\
    \ flatmaps without axis ticks or a scale bar indicating cortical distance. Include\
    \ a scale bar or annotate approximate anatomical landmarks to aid interpretation."
- id: 3211cfc009df
  severity: writing
  text: "Figure\u202F6 (clusters) uses color gradients but does not provide a color\
    \ bar for the intensity values. Add a color bar to clarify the meaning of the\
    \ color scale."
- id: 28050683acce
  severity: writing
  text: "In Figure\u202F7 (Retrieval Statistics) the two histograms share the same\
    \ y\u2011axis label but the units differ (counts vs. number of images). Separate\
    \ the axes or add distinct labels to avoid confusion."
- id: 8a0aa9cecbf0
  severity: writing
  text: "Several supplementary figures (e.g., S1 activation comparison, S2 negative\
    \ fail) contain small text that becomes illegible when printed at 1\u202Fcolumn\
    \ width. Increase font size for axis labels and legends to ensure legibility at\
    \ print scale."
- id: 43a738665f5b
  severity: writing
  text: "Alt\u2011text descriptions are missing for all figures, which hampers accessibility.\
    \ Provide concise alt\u2011text for each figure describing the main visual content\
    \ and the key takeaway."
- id: 2fd99d150cec
  severity: writing
  text: "Figure\u202F3 (causal evaluation) shows example regions but does not label\
    \ which brain area each panel corresponds to (e.g., FFA, EBA). Adding region labels\
    \ will help readers connect the visualizations to known functional anatomy."
- id: a6166bc5fbdb
  severity: writing
  text: "Figure\u202F2 (Methods) includes a dense schematic with multiple arrows;\
    \ some arrows overlap, reducing clarity. Redraw the schematic with clearer spacing\
    \ or use numbered steps to improve readability."
- id: ceea1f7bdc9c
  severity: writing
  text: "The color palette in Figures\u202F4 and\u202F5 uses reds and blues that may\
    \ be problematic for color\u2011blind readers. Consider using a color\u2011blind\u2011\
    friendly palette or adding patterns/annotations to differentiate categories."
artifact_hash: 3e7821bc4196322444417ea380054aced908f7d581b2fd2f7cbee1140a5fd1b0
artifact_path: projects/PROJ-660-https-arxiv-org-abs-2605-23895/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-16T10:19:52.541847Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

The manuscript contains a substantial set of figures that are central to conveying the proposed BrainCause pipeline and its empirical results. Overall, the visualizations are well‑designed and effectively illustrate the contrast between activation‑based and causally validated localization. However, several issues limit their clarity and accessibility.

Figure 1 (Overview) presents a high‑level diagram of the approach but the bottom panel lacks a legend for the color coding of activation versus causal response, making it difficult for readers to interpret the visual difference. Figure 4 (causal ranking) and Figure 5 (concept activation maps) display cortical flatmaps without any scale bar or explicit anatomical markers; adding a distance scale or annotating landmarks (e.g., V1, FFA) would ground the maps. Figure 6 (clusters) uses a gradient to show voxel density but omits a color bar, leaving the intensity meaning ambiguous.

Figure 7 (Retrieval Statistics) combines two histograms side‑by‑side but reuses the same y‑axis label, which could mislead readers because the left histogram counts retrieved positives while the right counts per‑pair negatives. Separate axis labels or a clarifying caption would resolve this. In several supplementary figures (S1 activation comparison, S2 negative failure), the font size of axis labels and legends is too small for typical conference print sizes; increasing the font will improve legibility.

Accessibility concerns arise from the absence of alt‑text for every figure, which is required for screen‑reader users. Providing concise descriptions that capture the main visual elements and findings will make the paper more inclusive. Moreover, the color palette in the main causal versus correlation plots relies heavily on red‑blue contrasts, which are not optimal for readers with red‑green color‑blindness. Switching to a color‑blind‑safe palette or adding pattern overlays would enhance interpretability.

Finally, Figure 3 (causal evaluation of discovered regions) and Figure 2 (Methods schematic) could benefit from additional annotations: labeling the specific brain regions (e.g., FFA, EBA) in Figure 3, and improving arrow spacing or numbering steps in the schematic to avoid visual clutter.

Addressing these points—adding legends, scale bars, clearer labels, larger fonts, alt‑text, and color‑blind‑friendly palettes—will substantially improve the readability, reproducibility, and accessibility of the figures without altering the scientific content.
