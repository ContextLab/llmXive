# Automated-review action items — Masking Stale Observations Helps Search Agents -- Until It Doesn't: A Regime Map and Its Mechanism

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Table 1 (Right) lists GPT-OSS-120B GAIA accuracy as 68.0/72.8 with delta -4.8. The text claims a -4.8 pt harm. Ensure the table header explicitly labels the columns as 'Acc (CM) / Acc (No-CM)' to prevent ambiguity about which value corresponds to the masked condition.
- **[writing]** The abstract claims a 'sharp collapse (≤0 pts)' for saturated models. Table 1 shows GPT-OSS-120B on BrowseComp-Plus with a +0.1 gain. This contradicts the '≤0' bound. Please adjust the claim to '≈0' or 'negligible' to accurately reflect the data.
- **[writing]** Section 5.2 cites specific attention percentages (53.7% reasoning, 25.6% observation) not found in the text body or tables. Explicitly reference Figure 4 or add a table row to support these precise numerical claims in the text.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[fatal]** Figure 1: The rendered image is a scatter plot of model performance regimes, but the caption describes a completely different figure (a 'Trace-SNR regression probe' with green/red dots and SNR axes). The caption text appears to belong to Figure 5, while the image content matches the paper's title regarding a 'Regime Map'.
- **[science]** Figure 1: The plot contains no legend defining the specific icons (e.g., purple hexagon, black knot, green eye) or the color-coding of the text labels (blue vs. red), making it impossible to distinguish between different model families or retriever types.
- **[writing]** Figure 1: The caption references a 'Right' panel and 'green and red dots' which are not present in the rendered image, indicating a severe mismatch between the provided figure and its description.
- **[fatal]** Figure 2: The caption text is truncated mid-sentence ('...account for over 8') and ends with a stray filename '[cm-fig1.png]', indicating a rendering or copy-paste error that obscures the result.
- **[science]** Figure 2: The caption describes a 'Right' panel showing context composition statistics, but the rendered image contains no such chart or graph; only the 'Left' schematic is visible.
- **[writing]** Figure 2: The legend on the left defines $o_i$ as a yellow box, but the schematic uses a white box with a tilde ($\tilde{o}_0$) for the initial observation, creating a visual inconsistency with the defined legend.
- **[science]** Figure 3: The caption describes three panels (Left, Middle, Right), but the rendered image only contains two panels (a heatmap and a line/bar chart). The 'Right' panel showing 'Relative positions of open targets' is missing.
- **[science]** Figure 3: The caption claims the heatmap separates reasoning (blue) and observation (orange) tokens, but the heatmap's colorbar is a single diverging scale (blue to orange) without a clear zero-point or legend indicating how the two token types are spatially separated or color-mapped.
- **[writing]** Figure 3: The right-hand plot has two y-axes ('Mean attention weight' and 'Cumulative attention share') but no legend or axis label explicitly links the line plots to the left axis and the bar plots to the right axis, creating ambiguity.
- **[science]** Figure 4: The caption claims the figure contains a 'Left' (heatmap) and 'Middle' (distribution) panel, but the rendered image shows two side-by-side plots (a heatmap and a line/bar chart) with no 'Middle' panel.
- **[writing]** Figure 4: The right y-axis label 'Cumulative attention share (%)' is rotated 90 degrees and illegible.
- **[writing]** Figure 4: The legend defines 'reasoning' and 'observation' but does not map these categories to the specific line markers (circle, square, triangle) used for the three models (4B, 9B, 3.6-35B) shown in the plot.
- **[fatal]** Figure 5: The rendered image displays a single line plot of Signal-to-noise ratio vs. Normalized No-CM prefix length, but the caption describes four distinct subplots (scatter plots and signal traces) arranged 'From left to right'. The visual content does not match the caption description.
- **[science]** Figure 5: The legend lists 'Qwen3.5-4B + BM25' (grey), but the caption does not define this configuration or explain its role in the 'Trace-SNR regression probe', making the inclusion of this data series unexplained.
- **[fatal]** Figure 6: The caption claims to show 'additional turns induced by CM' (turns), but the rendered image contains only a single plot of 'Δ rolling input tokens' with no data or axis for turns.
- **[science]** Figure 6: The caption states the figure contains data for 'Qwen3.5-35B+AgentIR' and 'GPT-OSS-120B+AgentIR', but the plot only displays four categories ('correct->correct', 'wrong->correct', etc.) without distinguishing between the two models.
- **[writing]** Figure 6: The y-axis label 'Δ rolling input tokens (CM - no CM)' is partially obscured by the top tick label '1e7', making the scientific notation hard to read.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on domain-specific shorthand and undefined acronyms that hinder accessibility for non-specialist readers. First, the acronym CM (Context Management) is introduced in the Abstract without its full expansion, and while it appears in the Introduction, the transition to the abbreviation is abrupt. Similarly, SNR (Signal-to-Noise Ratio) is used as a central metric in the Abstract without definition. The term No-CM is used repeatedly in the Results section (e.g., Table 1)

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** The claim that masking harms saturated models by removing 'crucial signals' contradicts the attention evidence showing models ignore the middle. The paper must explain why saturated models suddenly rely on ignored middle evidence while mid-capacity models do not.
- **[science]** The 'Model Saturated' regime is defined by No-CM accuracy >70%, yet GPT-OSS-120B shows +8.0 gain on xBench (78% No-CM) but -4.8 on GAIA (72.8% No-CM). The paper fails to logically derive why the same capacity threshold yields opposite results based solely on 'noise' without a quantitative interaction term.
- **[science]** The regression probe claims SNR is the bottleneck because saturated models have high AUC but low gain. This logic is incomplete: it does not prove masking lowers SNR for these cases or that the model fails due to SNR rather than simply having sufficient capacity to ignore noise without help.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim that masking 'collapses (≤0 pts) when the model is saturated' (Abstract) is contradicted by DS-V4-Flash-Max (+3.8 pts) and GPT-OSS-120B (+0.1 pts) in Table 1. The term 'collapse' is inaccurate for positive gains. Refine language to 'diminishes' or 'plateaus' for near-zero gains, and reserve 'collapse' only for negative outcomes, or clarify that 'saturation' is not a universal state.
- **[science]** The conclusion that 'future engineering should pivot toward high-fidelity retrieval' over-extrapolates from a correlational SNR probe. The probe shows SNR predicts rescue separability but does not prove better retrieval alone solves saturation without masking. Temper the claim to suggest retrieval as a complementary strategy rather than the primary solution to masking failures.
- **[science]** The abstract states masking fails when it removes evidence the model would use, yet DS-V4 (84.3% No-CM) still gains +3.8 pts. This implies the model is not 'saturated' in the way described. Distinguish between 'true saturation' (masking hurts) and 'high performance' (masking still helps) to avoid overgeneralizing the failure mechanism across all high-capacity models.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The 'Ethical Considerations' section (Section 6) is overly brief and generic. It must be expanded to explicitly address the risk of masking critical safety warnings or legal disclaimers found in retrieved documents, which could lead to agents providing harmful advice in high-stakes domains (e.g., medical or legal search).
- **[writing]** The 'Human Audit Evaluation' (Appendix, Section 2) claims 99.9% agreement with an LLM judge but does not disclose the specific safety guidelines or red-teaming criteria used to verify the correctness of the 15% sampled trajectories. Clarify if safety violations were part of the audit scope.
- **[writing]** The paper discusses 'low-quality content generation' as a risk but fails to address the potential for the proposed masking technique to be used as a dual-use tool to evade safety filters by systematically hiding context that triggers refusal mechanisms in other models.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The claim that masking removes 'crucial signals' in saturated regimes lacks direct causal proof. Provide a case study or analysis showing that the specific masked tokens contained the gold evidence required for the correct answer, rather than just inferring this from performance drops.
- **[science]** The regression probe uses a 'citation proxy' for live-web benchmarks where gold documents are unavailable. This risks circularity as the proxy depends on the model's own output. Clarify the limitations of this proxy or provide a sensitivity analysis against ground-truth relevance if possible.
- **[science]** The performance drop in the saturated regime correlates with a surge in tool calls. Disentangle whether the collapse is due to 'information loss' (masked content was needed) or 'retrieval cost' (agent failed to re-find masked info). Current analysis conflates these mechanisms.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Report confidence intervals or standard errors for the accuracy gains (ΔAcc.) in Table 1. With N=830 (BrowseComp-Plus), a 1.1% drop (Tongyi-DeepResearch) may not be statistically significant without variance estimates.
- **[science]** Clarify the statistical test used to validate the 'U-shaped' attention patterns in Section 5.2.1. Specify the null hypothesis and p-values for the claim that middle-turn attention is significantly lower than periphery attention.
- **[science]** The regression probe (Section 5.2.2) reports AUC scores (e.g., 0.74) but lacks significance testing against a random baseline or confidence intervals for the AUC estimates. Add these to support the claim of 'separability'.
- **[science]** The human audit agreement rate is stated as >99.9% (Appendix E001) based on a 15% sample. Report the exact sample size (N) and the 95% confidence interval for this agreement rate to assess the reliability of the LLM-as-Judge metric.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 5.1 (Trade-Off), the phrase 'broken queries (correct -> wrong)' is ambiguous. Clarify that this refers to queries that were correct without masking but became incorrect with masking.
- **[writing]** Section 5.2.1 states 'Reasoning absorbs 53.7% of attention budget vs 25.6% for observations'. Ensure the sum of these percentages is explained or that other attention targets (e.g., system prompt, tool calls) are accounted for to avoid confusion.
- **[writing]** The caption for Figure 1 (teaser) uses 'Whereas' to start a sentence ('Whereas, the retriever bottleneck...'). This is grammatically awkward; rephrase to 'In contrast, the retriever bottleneck...' or similar.
- **[writing]** In Table 1, the column header '$\Delta$ calls/q$^\downarrow$' uses a down arrow to indicate lower is better, but the values are positive increases. Clarify if the arrow refers to the desirability of the metric or the direction of change, as the current notation is slightly confusing.
