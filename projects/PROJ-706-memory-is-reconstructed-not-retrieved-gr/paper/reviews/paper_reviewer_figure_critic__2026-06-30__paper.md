---
action_items:
- id: 53197fc80314
  severity: writing
  text: The paper relies heavily on visual aids to explain the transition from passive
    to active memory reconstruction and the architecture of MRAgent. However, several
    figures suffer from legibility and self-containment issues that hinder immediate
    comprehension. In Figure 1 (Introduction) and Figure 2 (Motivation), the visual
    comparison between passive and active retrieval is clear in concept, but the specific
    visual encoding is ambiguous. The captions describe the *outcome* of the comparison
    but do n
artifact_hash: b428847249c815694ce34a179b14e661a1c8a1e001ab2124c52ead974dee57ea
artifact_path: projects/PROJ-706-memory-is-reconstructed-not-retrieved-gr/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T02:29:21.610591Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

The paper relies heavily on visual aids to explain the transition from passive to active memory reconstruction and the architecture of MRAgent. However, several figures suffer from legibility and self-containment issues that hinder immediate comprehension.

In **Figure 1 (Introduction)** and **Figure 2 (Motivation)**, the visual comparison between passive and active retrieval is clear in concept, but the specific visual encoding is ambiguous. The captions describe the *outcome* of the comparison but do not define the visual language used (e.g., what do the different node shapes or colors signify?). Without a legend or explicit labels on the graph elements, a reader cannot fully interpret the diagram without cross-referencing the main text, which violates the principle of figure self-containment.

**Figure 5 (Ablation Study)** and **Figure 6 (Multi-turn Reasoning)** present quantitative results. In Figure 5, the distinction between the "no-reasoning" (green) and "with reasoning" (blue) bars, as well as the different memory structures (CE, CTE, CTC), relies entirely on color. At standard print resolution, these shades may be difficult to distinguish, especially for readers with color vision deficiencies. The legend is present but small; increasing the font size or using distinct patterns (hatching) in addition to color would improve robustness. Similarly, Figure 6 uses multiple lines to represent different query types; the legend is not clearly linked to the lines, and the line styles are not distinct enough to be easily tracked.

**Figure 3 (Framework)** and **Figure 7 (Case Study)** are complex architectural diagrams. The text labels inside the nodes (e.g., "Cue," "Tag," "Content") and the edge labels are quite small. When the figure is resized to fit a single column (approx. 3.5 inches wide), these labels may become illegible. The authors should increase the font size of the labels or reduce the complexity of the diagram to ensure clarity at print scale.

Finally, **Figure 4 (Example)** and **Figure 8 (Related Work Alignment)** lack sufficient descriptive detail in their captions to stand alone. The captions should explicitly describe the key visual elements and the specific relationships they illustrate, rather than just summarizing the figure's purpose. Additionally, none of the figures include alt text, which is a critical omission for accessibility.

To improve the paper, the authors should: (1) add legends and define visual encodings in all figures; (2) enhance color contrast and add patterns for colorblind accessibility; (3) increase font sizes in dense diagrams; and (4) provide comprehensive alt text for all figures.
