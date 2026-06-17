---
action_items:
- id: 6b5589bae70a
  severity: writing
  text: "Figure\u202F1(a) shows token entropy distribution but lacks a y\u2011axis\
    \ label (e.g., \u201CEntropy\u201D) and units; add clear axis labels and a legend\
    \ explaining any color coding."
- id: 76cb0f5908e2
  severity: writing
  text: "In Figure\u202F1(b) the x\u2011axis bins are described only in the caption;\
    \ include tick labels or a brief inset indicating the entropy/BS range for each\
    \ bin."
- id: 6f7ee3af648f
  severity: writing
  text: "Figure\u202F2\u2019s schematic uses several colored boxes (e.g., morandiblue,\
    \ morandired) without a legend; provide a legend that maps colors to the algorithmic\
    \ components (initial rollout, branching, advantage estimation)."
- id: affaa6e901c6
  severity: writing
  text: "Figures\u202F3,\u202F4,\u202F5,\u202F6 contain dense plots with small font\
    \ sizes that become illegible when printed at column width; increase font size\
    \ for axis tick labels and legends."
- id: 88fa338669d7
  severity: writing
  text: "All figures lack descriptive alt\u2011text for accessibility; add concise\
    \ alt\u2011text metadata (e.g., via \\caption[Alt\u2011text]{...}) describing\
    \ the visual content."
- id: def0fd6848a6
  severity: writing
  text: "Figure\u202F5 (branch distribution) uses DBSCAN clusters visualized with\
    \ colors that are hard to differentiate for color\u2011blind readers; use a color\u2011\
    blind\u2011friendly palette or add pattern overlays."
- id: 1d8751081481
  severity: writing
  text: "Figure\u202F6\u2019s word cloud mixes high\u2011entropy and BS\u2011selected\
    \ tokens but does not indicate token frequency or weighting; include a scale or\
    \ legend to convey the relative importance of displayed words."
- id: 050c465d2a73
  severity: writing
  text: "Across several figures (e.g., Fig\u202F1(c), Fig\u202F4) the legend symbols\
    \ (solid, dashed lines) are not explained in the caption; explicitly describe\
    \ each line style in the caption."
artifact_hash: 3a43673385ee45c44ff0ac04e7e12a654dbb1cefe913b5676a26e486f2c9fad4
artifact_path: projects/PROJ-707-appo-agentic-procedural-policy-optimizat/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-17T21:20:02.776848Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

The manuscript includes eight primary figures that are central to the authors’ claims about the APPO algorithm. Below is a focused assessment of each figure’s visual quality, labeling, and overall contribution.

**Figure 1 (a–c)**  
- *Clarity*: The three sub‑panels are packed into a single row, making the individual plots appear cramped. The entropy curve in (a) and the accuracy‑vs‑entropy bins in (b) are readable on screen but would lose detail at print scale.  
- *Axis Labels & Units*: The y‑axis in (a) is unlabeled; the caption mentions “token entropy” but the unit (bits) is not shown. In (b) the x‑axis is described only in the caption (“bins of the entropy and the APPO's Branching Score”), yet the plot itself shows no tick marks or numerical ranges. (c) displays pass@k curves but the y‑axis lacks a label (“Pass@k (%)”).  
- *Color Choices*: The use of a single color for all lines in (c) hampers distinguishing the methods; a contrasting palette or distinct line styles would improve readability.  
- *Legibility*: Legends are missing; readers must infer which curve corresponds to “oracle”, “entropy”, or “APPO” from the caption alone.  
- *Alt‑text*: No alternative description is provided, limiting accessibility.

**Figure 2 (Overview of APPO)**  
- *Design*: The schematic effectively conveys the pipeline (initial rollout → branching → advantage estimation). However, the colored blocks (morandiblue, morandired) are not explained anywhere in the figure.  
- *Labels*: Boxes contain text but lack explicit arrows or numbered steps that could be referenced in the main text. Adding a brief legend mapping colors to “initial rollouts”, “selected branches”, and “advantage computation” would clarify the flow.  
- *Resolution*: The diagram is vector‑based and scales well, but the font size of internal labels is small for a two‑column layout.

**Figure 3 (Pass@K analysis)**  
- *Axes*: Both axes are labeled, but the legend describing ARPO vs. APPO is placed inside the plot area, overlapping data points for some datasets. Relocating the legend to an outer corner would preserve data visibility.  
- *Color*: The two methods use similar hues; a more distinct palette (e.g., blue vs. orange) would make the comparison easier, especially for readers with color‑vision deficiencies.

**Figure 4 (Training dynamics)**  
- *Readability*: The curves for APPO and ARPO are thin and of similar color intensity, making it hard to differentiate them when printed in grayscale. Using thicker lines and contrasting dash patterns would help.  
- *Axis Units*: The x‑axis (training steps) lacks a unit (e.g., “episodes” or “updates”), and the y‑axis (“Reward”) does not specify the scale (raw reward, normalized?). Adding these details would contextualize the observed improvement.

**Figure 5 (Branch distribution clustering)**  
- *Color‑blind safety*: The DBSCAN clusters are colored with a rainbow palette, which is problematic for color‑blind readers. Switching to a palette such as Tableau‑10 or adding texture patterns would improve accessibility.  
- *Legend*: There is no legend indicating which color corresponds to which cluster; a small inset with cluster identifiers is needed.

**Figure 6 (Word cloud of high‑entropy vs. BS tokens)**  
- *Interpretation*: Word clouds are inherently qualitative. The figure does not convey token frequency or the quantitative difference between the two sets. Adding a bar chart or a table of the top‑10 tokens with their selection scores would make the claim about “BS filtering out rare nouns” more concrete.  
- *Caption*: The caption mentions “high‑entropy” and “BS” tokens but does not explain the visual encoding (size = frequency?). Explicitly stating this in the caption would avoid ambiguity.

**Figures 7–10 (Case studies)**  
- *Formatting*: These multi‑panel boxes combine code snippets, tool queries, and reasoning text. While informative, the font size is very small, and line breaks cause horizontal scrolling in some PDF viewers. Using a monospaced font at a slightly larger point size (e.g., 9 pt) would enhance readability.  
- *Labels*: Each case is titled (e.g., “Wrong Rollout”, “APPO Branching”), which is helpful, but the distinction between the “branching” and “final answer” sections could be highlighted with a visual separator (e.g., a thin line) to guide the reader through the logical flow.  
- *Alt‑text*: No descriptive alt‑text is supplied; adding brief summaries (e.g., “Case‑1 shows APPO correcting a mis‑calculated GCD after branching”) would improve accessibility.

**Overall Assessment**  
The figures collectively support the paper’s central claims that APPO’s fine‑grained branching yields better credit assignment and performance. However, several recurring issues diminish their effectiveness:

1. **Missing or ambiguous axis labels and units** (Figures 1, 4).  
2. **Insufficient legends and color explanations** (Figures 1, 2, 5, 6).  
3. **Low font sizes and line thicknesses** that hinder print readability (Figures 3‑5, 7‑10).  
4. **Lack of accessibility features** such as alt‑text and color‑blind‑friendly palettes.  

Addressing these points will make the visual evidence clearer, more reproducible, and accessible to a broader audience, thereby strengthening the paper’s overall impact.
