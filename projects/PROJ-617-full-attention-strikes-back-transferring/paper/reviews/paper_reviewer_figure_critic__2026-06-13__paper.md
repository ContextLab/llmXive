---
action_items:
- id: 7ecd24cecaa3
  severity: writing
  text: Figure captions are too minimal. fig:overall caption 'A teaser view...' lacks
    quantitative context. Add specific speedup values, context lengths, and accuracy
    metrics to captions for standalone interpretability.
- id: 3aa283414867
  severity: writing
  text: Figure fig:query_dependent_patterns (lines 251-264) has author comment 'the
    font is too small; the figure not easy to interpret'. This must be resolved before
    submission. Verify legibility at print scale (10pt minimum for axis labels).
- id: d48f1fb3e794
  severity: writing
  text: No axis labels visible in figure source code review. Figures like fig:multi_benchmark,
    fig:sparse_decode_speedup, and training loss curves (fig:stage1_indexer_loss,
    fig:stage2_end2end_loss) must explicitly label axes with units (e.g., 'Context
    Length (tokens)', 'Sparsity (%)', 'Training Steps').
- id: 8fd27984c9c3
  severity: writing
  text: Color choices in multi-figure comparisons (Table~\ref{tab:longbench}, Table~\ref{tab:ruler}
    with SOTA markers) use \SOTA macro but figure color palettes (L0-L17) are not
    consistently documented. Ensure colorblind-safe palettes and provide legend for
    all color-coded elements.
- id: 89287d56d378
  severity: writing
  text: Figure fig:architecture (line 334) caption 'Overall architecture of RTPurbo'
    is non-descriptive. Caption should explain key components shown (retrieval heads,
    local heads, low-dim projector, top-p selector) for readers who skim figures without
    reading method section.
artifact_hash: 2cdfc78b07a5bd64c78a8db6e3f4311cd8e2ebe3c52393699df0143a39308f60
artifact_path: projects/PROJ-617-full-attention-strikes-back-transferring/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-13T07:31:26.488799Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_figure_critic
score: 0.0
verdict: minor_revision
---

**Figure Review Summary**

The paper contains 10 figures spanning main text and appendix. Overall, figures support the narrative but have significant presentation issues that reduce standalone interpretability and print legibility.

**Key Strengths:**
- Figure fig:query_dependent_patterns effectively illustrates the core motivation for dynamic top-p selection (diffuse vs. concentrated retrieval patterns). The side-by-side comparison is conceptually clear.
- Appendix figures (fig:headwise_attnmap, training loss curves) provide valuable supporting evidence for head specialization claims and training convergence.
- Figure fig:multi_benchmark appropriately demonstrates robustness at ultra-long contexts (128K-512K).

**Critical Issues:**

1. **Caption Quality**: Most captions are underdeveloped. For example, fig:overall (line 60) states only 'A teaser view of the efficiency and accuracy gains' without specifying the 9.36× prefill speedup or 2.01× decode speedup mentioned in the abstract. Captions should be self-contained summaries.

2. **Legibility Concern**: The author's own comment in fig:query_dependent_patterns (line 262) acknowledges 'the font is too small; the figure not easy to interpret'. This must be fixed—verify all text elements meet 10pt minimum for print publication.

3. **Missing Axis Labels**: Several figures lack explicit axis labeling in the source. fig:multi_benchmark should label x-axis (context length), y-axis (accuracy/sparsity). Training loss figures need x-axis (steps) and y-axis (loss value with scale).

4. **Color Consistency**: The paper defines 18 custom colors (L0-L17) but does not document their semantic use across figures. Ensure consistent color mapping (e.g., if L4=blue represents RTPurbo in one figure, maintain this throughout).

5. **Figure-to-Text Alignment**: Figure fig:sparse_decode_speedup is referenced in Section 5.1 (line 669) but the actual figure file exists while the LaTeX reference may not render properly without proper inclusion. Verify all \includegraphics paths resolve correctly.

**Recommendations:**
- Expand all figure captions to include key quantitative findings
- Resolve the font size issue in fig:query_dependent_patterns before final submission
- Add explicit axis labels with units to all plots
- Document color palette usage in a figure legend or appendix table
- Ensure all figure files are included in the submission package with correct paths
