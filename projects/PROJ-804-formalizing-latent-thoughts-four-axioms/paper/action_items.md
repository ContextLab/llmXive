# Automated-review action items — Formalizing Latent Thoughts: Four Axioms of Thought Representation in LLMs

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[science]** Appendix e000 claims Soft Thinking (Gumbel) is 'indistinguishable from Random Vector' with Delta_cos in [0.02, 0.05]. However, Table tab:stability-headline shows STN AUROC ~0.85 vs RV ~0.50. Define Delta_cos or correct the claim to match reported DCS data.
- **[writing]** Appendix e000 states 95% CI is 'mu +/- 1.96 * sigma_B' but claims to use the 'percentile method'. These are contradictory. Clarify if the normal approximation or percentile method was actually used for the reported intervals.
- **[writing]** Section 'Results' claims 'No candidate exceeds IE on every axis'. While supported by tables, explicitly cite the specific table cells (e.g., tab:minimality-headline vs tab:causality-results) to clarify metric directionality (higher/lower is better) and avoid ambiguity.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The top-left panel ('Anchors') contains a legend with six entries, but the 'Exact Output Embedding' and 'Pooled Output Embedding' lines are visually indistinguishable (overlapping) in the plot, making it impossible to verify if they differ.
- **[writing]** Figure 1: The top-left panel ('Anchors') legend lists 'Last Input Token (final layer)' and 'Last Input Token (all layers)' as distinct entries, but the corresponding purple lines are nearly identical, raising questions about the visual distinction or the necessity of separate legend entries.
- **[science]** Figure 2: The legend defines 'W' as the averaging window size, but the x-axis labels (e.g., 'Soft Think. 1', 'Soft Think. 16') represent the number of thinking steps. The caption states the figure shows 'bars per averaging window', yet the plot groups bars by thinking step and colors them by window size, contradicting the caption's description of the grouping.
- **[writing]** Figure 2: The y-axis label uses LaTeX formatting ($\sigma^2_{between} / (\sigma^2_{between} + \sigma^2_{within})$) that renders as raw code rather than formatted math, making it difficult to read.
- **[science]** Figure 3: The caption states the plot includes '95% cluster-bootstrap CI bands', but the rendered figure displays only lines and markers with no visible error bands or shaded regions.
- **[science]** Figure 3: The legend lists 'Last Input Token (all layers)' (pink), but the plot shows this series starting abruptly at x=64 with no data points at lower lengths, despite the caption implying a comparison across varying L.
- **[writing]** Figure 4: The caption states 'Candidates follow the order of .' but the reference is missing; the x-axis labels (Exc, Pool, All, Fin, 1, 16, etc.) are not defined in the caption or the figure itself.
- **[writing]** Figure 4: The y-axis label 'r vs. input length' (top) and 'r vs. output length' (bottom) is grammatically incorrect and ambiguous; it should likely be 'Pearson r with input/output length'.
- **[writing]** Figure 4: The x-axis labels are crowded and difficult to read, particularly in the 'Soft Thinking' and 'Soft T. (Gumbel)' sections where numbers (1, 16, 32, 64, 128) are tightly packed.
- **[writing]** Figure 5: The caption states the plot shows 'Mean causality KL', but the y-axis is labeled only 'Mean KL', omitting the specific 'causality' descriptor for precision.
- **[writing]** Figure 5: The x-axis label 'Tail window (tokens)' is present only on the bottom row; the top row panels lack this label, creating visual inconsistency.
- **[science]** Figure 5: The caption promises '95% bootstrap CI bands', but the 'Baselines' panel (bottom right) displays only single lines without the corresponding shaded error bands.
- **[writing]** Figure 7: The caption states the bottom row shows distributions 'with the threshold tau = 0.9 overlaid', but the symbol 'tau' is missing from the text in the image (showing only '= 0.9') and the legend in the rightmost panel is missing the Greek letter 'tau'.
- **[writing]** Figure 7: The caption mentions 'one panel per source model' for the top row, but the panels are labeled with model names (Llama-3.1 8B, Llama-3.3 70B, DS-R1-Qwen 32B) rather than explicitly stating which 'source model' corresponds to which panel in the text description.
- **[writing]** Figure 8: The caption states the top row shows AUROC 'at $	au=0.9$', but the individual panel titles display varying thresholds (e.g., 'Hx > 0: 28.2%', 'Hx > 0: 1.0%'), creating a contradiction between the summary text and the visual data.
- **[writing]** Figure 8: The top row x-axis labels are rotated 90 degrees and extremely dense, making the method names (e.g., 'Thinking@32 + Gumbel@2') difficult to read without zooming.
- **[science]** Figure 8: The bottom row legend defines 'Soft Thinking' and 'Latent Thinking' but omits the 'Soft Thinking + Gumbel' family, which is clearly plotted in the Skywork-OR1 and GPT-OSS panels.
- **[writing]** Figure 9: The caption refers to 'semantic equivalence threshold $$' but the x-axis is labeled with the symbol 'τ' (tau); the caption should explicitly define τ as the threshold.
- **[writing]** Figure 9: The legend is located inside the rightmost panel (GPT-OSS 20B) and obscures the data lines; it should be moved outside the plot area or made semi-transparent.
- **[writing]** Figure 9: The y-axis label 'AUROC' is missing; while the caption mentions AUROC, the axis itself is unlabeled, making the plot standalone interpretation difficult.
- **[writing]** Figure 10: The caption contains LaTeX formatting artifacts ('Spearman $$') instead of the rendered symbol ($ho$) shown in the plot.
- **[writing]** Figure 10: The legend in the right panel lists 'Llama-3.1 8B' and 'Llama-3.3 70B', but the caption states the data is averaged across five LLMs; the legend does not account for the other three models.
- **[science]** Figure 11: The legend defines 'Soft Thinking (1→128 steps)' as a single entry, but the blue line in the plots is annotated with '1' at the start and '128' at the end. The caption states lines trace trajectories as step count grows, but the legend fails to explicitly indicate that the lines represent a range of steps rather than a single static comparison, which may confuse readers regarding the data density.
- **[writing]** Figure 11: The x-axis label 'within-task participation ratio PR' is only present on the bottom row of plots. The top row panels (Llama-3.1-8B-Instruct, Llama-3.3-70B-Instruct, DeepSeek-R1-Distill-Qwen-32B) lack x-axis labels, forcing the reader to infer the axis meaning from the bottom row.
- **[writing]** Figure 11: The y-axis label 'k-NN task purity' is only present on the bottom-left plot. The other four panels lack y-axis labels, which is poor practice for multi-panel figures even if the axis is shared.
- **[writing]** Figure 12: The orange diamond symbol is defined in the legend as 'mean', but the caption text only discusses the 'median' (box line) and does not mention the mean, creating a disconnect between the visual data and the textual description.
- **[writing]** Figure 12: The x-axis labels are rotated at a steep angle, which is unnecessary for the short model names and reduces readability compared to a horizontal layout.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on specialized shorthand and undefined acronyms that create a barrier for non-specialist readers. In Section 3 (Table 1) and the Appendix, the term DCS is used repeatedly without being spelled out as "Discriminator-based Causal Stability" or similar, forcing the reader to guess its meaning from context. Similarly, TR appears in Appendix A.2 ("TR-independent constant") without definition; it should be explicitly stated as "Thought Representation" upon first use. In A

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The logical consistency of the paper is compromised by a disconnect between the abstract axiomatic definitions and the specific empirical metrics used to evaluate them. First, the central conclusion that "No candidate satisfies all four axioms" (Introduction) does not strictly follow from the data. The paper defines "Stability" as the ability to encode entropy and "Separability" as linear discriminability. The results show that Output Embedding (OE) achieves high scores on both (DCS ~0.96, Separ

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim that the four axioms are 'complete' (Appendix:app:completeness) is an overreach. The proof asserts a 'functional isomorphism' based on idealized limits, yet the empirical results (Section 5) show no candidate satisfies all axioms simultaneously. The paper must clarify that 'completeness' applies only to the theoretical construct, not the current empirical reality of LLMs.
- **[writing]** The conclusion states the protocol 'exposes representational collapse on per-question identity not revealed by downstream accuracy.' This overstates the finding. The data (Appendix:appendix:downstream) shows near-zero correlation (rho=0.10) between discriminator accuracy and task pass@1, but this does not prove 'collapse' is the *cause* of the lack of correlation, nor that accuracy metrics are blind to it. The causal language should be softened to 'suggests a disconnect'.
- **[writing]** The abstract and introduction imply the axioms define a 'Functional Thought Representation' that LLMs *should* possess. However, the results show current methods (Soft Thinking, Latent Thinking) often degrade as steps increase. The paper overreaches by framing these methods as attempts to satisfy the axioms when the data suggests they may be fundamentally misaligned with the 'Stability' and 'Minimality' requirements as defined.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The 'Broader Impacts' section (Appendix Impact) dismissively states 'no negative societal effects identified' without addressing the dual-use risk of the proposed diagnostic protocol. If these axioms can identify 'representational collapse' or specific latent states, malicious actors could use this to engineer models that bypass safety filters by optimizing for 'stable' but deceptive representations. This requires a substantive discussion of potential misuse.
- **[writing]** The paper evaluates models on sensitive reasoning tasks (e.g., 'Causal Understanding', 'Social Reasoning', 'SARC Triples') using the BBEH benchmark. While the data is public, the manuscript lacks a statement confirming that the evaluation protocol adheres to the original benchmark's data usage licenses and that no private or personally identifiable information was inadvertently exposed during the beam-search generation and analysis.
- **[writing]** The 'Reproducibility' section links to an external GitHub repository. The safety review cannot verify if the released code contains scripts that could be used to extract or exploit the specific latent representations identified as 'collapsed' or 'unstable'. A statement confirming that the released code is limited to the diagnostic metrics and does not include tools for adversarial manipulation of these states is required.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The claim that 'No candidate satisfies all four axioms' relies on the Input Embedding (IE) baseline failing Stability (DCS). However, Table 4 shows IE DCS scores of 0.92-0.94 for most models, which are high. The text must explicitly clarify why these high scores are considered a failure of the Stability axiom or if the 'collapse' refers to a different metric not clearly distinguished in the summary.
- **[science]** The Causality metric (KL divergence) is reported as a single mean per cell in Table 2, but the text claims 'No candidate consistently exceeds Input Embedding.' Given the small effect sizes (e.g., 4.56 vs 4.71 in Llama 70B) and the lack of per-problem paired statistical tests (e.g., Wilcoxon signed-rank) in the main text, the robustness of this ranking is unclear.
- **[science]** The Separability results (Table 4) show 'Same-task' accuracy near random (50-54%) for most candidates. The paper attributes this to 'representational collapse.' However, without a control showing that a known good representation (e.g., the Output Embedding) achieves significantly higher same-task accuracy in the *same* experimental setup, the baseline for 'good' separability is ambiguous.
- **[science]** The bootstrap confidence intervals (B=10,000) are mentioned in the appendix, but the main tables (e.g., Table 2, 4) do not display these intervals or standard errors for the headline metrics. To verify the 'no consistent advantage' claim, the reader needs to see the error bars to assess if the differences between candidates are statistically significant or within noise.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** The statistical analysis framework is generally robust, utilizing a large number of bootstrap resamples ($B=10,000$) to estimate uncertainty, which is appropriate for the complex metrics involved (KL divergence, Information Bottleneck residuals). The explicit definition of the statistical unit as the "problem" and the use of cluster bootstrapping for the Causality metric (Section appendix:sub:bootstrap) are strong practices that account for the hierarchical nature of the data (beams within probl

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 2 (Methodology), the definition of Stability ('T must encode entropy of P(S|x)') is conceptually ambiguous and grammatically disconnected from the subsequent DCS metric description. Clarify the logical link between the axiom statement and the AUROC measurement.
- **[writing]** The Conclusion section contains a sentence fragment: 'Measurement cost exceeds single benchmarks.' This lacks a subject and verb, making the claim unclear. Rephrase to a complete sentence (e.g., 'The measurement cost exceeds that of single benchmarks.').
- **[writing]** In Appendix A.1, the phrase 'Beams excluded by the 51-token length gate are absent' is awkward and passive. Suggest rewriting for clarity, such as 'Beams excluded by the 51-token length gate are omitted from the analysis.'
