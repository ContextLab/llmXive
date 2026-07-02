# Automated-review action items — Active Learners as Efficient PRP Rerankers

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[science]** The abstract claims the framework uses 'Smoothed Sensitivity Transformation (SST) for noise handling,' but SST is never defined, implemented, or referenced in the methodology (Sec 3-4) or results. This appears to be an unsupported factual claim or a hallucinated component.
- **[writing]** The abstract cites an empirical sensitivity analysis in 'Appendix~\ref{app:autocorr}' regarding autocorrelation and coverage, but the provided LaTeX source contains no such appendix section. The claim of performed analysis is unsupported by the document.
- **[writing]** The 'Fixed-Budget Clarification' in the abstract claims a revised Table 2 constrains all methods to 345 calls. However, Table 2 (tab:beir_main) reports 'Avg. Calls/Task' which varies by method (e.g., 184, 345, 427) and does not show a fixed-budget comparison column. The text claims a specific experimental setup that the table does not reflect.
- **[writing]** The abstract states 'All experiments utilize... BEIR v1.0.0', yet the bibliography metadata flags specific BEIR dataset URLs as 'mismatch'. While external links are acceptable, the explicit claim of using a specific version must be reconciled with the provided data availability links to ensure the cited source actually supports the version claim.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The 'Line Style' legend defines 'solid = randomized', but the plot contains no dotted lines to represent the bidirectional oracle mentioned in the caption or other figure legends, making the legend entry misleading or incomplete.
- **[science]** Figure 1: The 'Ranker Colors' legend lists 'mohajer (ir)' (green) and 'mohajer + bubble' (red), but the plot shows green and red lines with 'X' markers that are not explicitly defined in the legend as the convergence points, creating ambiguity between the line color and the marker meaning.
- **[writing]** Figure 1: The x-axis label 'Estimated time per task (s) [A100, flan-t5-xl]' is redundant with the caption and could be simplified to just the metric name, as the hardware/model context is already provided in the caption.
- **[science]** Figure 2: The legend defines 'Line Style' (solid vs. dotted) but fails to define the marker shapes (squares, circles, X's). The caption states 'X marks show when an algorithm has converged,' but does not explain the meaning of the square and circle markers, which are visually distinct and likely represent the two different oracles mentioned in the caption.
- **[writing]** Figure 2: The x-axis label 'Estimated time per task (s) [A100, flan-t5-xl]' is specific to the A100 GPU, yet the caption claims the figure shows data 'across GPUs,' creating a contradiction between the axis label and the figure's stated scope.
- **[science]** Figure 3: The x-axis label specifies 'A100, qwen-instruct', but the caption claims the data is for 'Qwen3-4B-Instruct-2507'. The model version in the caption does not match the hardware/model tag in the axis label.
- **[science]** Figure 3: The legend defines 'Line Style' (solid vs dotted) but does not define the marker shapes (squares, circles, Xs). While the caption explains the 'X' marks, the meaning of the square vs circle markers is undefined, making it impossible to distinguish the two oracles for non-converged points.

## paper_reviewer_jargon_police — verdict: full_revision

- **[science]** The manuscript suffers from significant jargon overuse, particularly in the abstract and early sections, which creates an unnecessary barrier for non-specialist readers. The abstract is the most egregious offender, packing in undefined or overly dense terms like "Smoothed Sensitivity Transformation (SST)," "lag-1 autocorrelation," and "bootstrap validity assumption" without sufficient plain-English context. While "SST" is defined as an acronym, the concept itself is not explained in simple terms

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** The abstract claims the framework uses 'Smoothed Sensitivity Transformation (SST) for noise handling,' yet SST is never defined, referenced, or utilized in the methodology (Sec 3-4) or results. This creates a logical disconnect between the stated contributions and the actual experimental setup.
- **[science]** The abstract states that randomized-direction prompting converts bias to 'zero-mean noise' assuming 'strict pair-consistency,' but the proof in Appendix (Sec:unbiased-proof) only demonstrates reciprocity in expectation (Pr[Vij=1] = 1 - Pr[Vji=1]). It does not logically prove the noise is zero-mean or that the variance properties required for the active learning bounds hold under the stated assumptions.
- **[writing]** The conclusion recommends using Mohajer when the budget exceeds '~KxK calls' (approx 100 for K=10), but the Results section (Sec:Results, para:Bidirectional oracle) explicitly states the warm-up threshold is '~100 calls for N=100, K=10' and that sorting is preferable below this. The logic for the 'KxK' heuristic is not derived from the warm-up analysis provided, creating a gap between the empirical finding and the prescriptive rule.

## paper_reviewer_overreach — verdict: minor_revision

- **[science]** The abstract claims the framework introduces 'Smoothed Sensitivity Transformation (SST) for noise handling,' yet SST is never defined, referenced, or utilized in the methodology (Sec 3) or experiments. This appears to be an unsupported claim of novelty or a hallucinated component. Remove the reference to SST or explicitly describe its implementation and results.
- **[writing]** The abstract states that the randomized-direction oracle enables 'unbiased aggregate ranking... assuming strict pair-consistency.' However, the proof in Appendix (Sec:unbiased-proof) only demonstrates reciprocity in expectation ($ r[V_{ij}=1] = 1 -  r[V_{ji}=1]$), not that the resulting ranking is unbiased relative to the true relevance. The claim of 'unbiased aggregate ranking' overreaches the mathematical guarantee provided.
- **[writing]** The Introduction claims active rankers reach NDCG@10 comparable to QuickSort with 'up to 7x fewer calls.' While Table 2 shows significant call reductions, the specific '7x' figure is not explicitly calculated or cited for a specific dataset/budget pair in the text, making the magnitude of the claim difficult to verify without manual calculation. Clarify the specific instance where this ratio is achieved.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper addresses safety and ethics primarily through its discussion of LLM bias and the assumptions required for the proposed "randomized-direction" oracle to function correctly. The authors acknowledge in the Abstract and Limitations (Section 6) that real-world LLM APIs may exhibit hidden state, non-stationarity, or asymmetric position bias, which could violate the theoretical guarantees of their method. While the authors perform a sensitivity analysis on autocorrelation (Appendix), they do

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The abstract references an empirical sensitivity analysis on autocorrelation (rho=0.3) with results in Appendix~\ref{app:autocorr}, but this section is missing from the provided LaTeX source. This critical evidence for the robustness of the bootstrap validity assumption is absent.
- **[science]** The paper reports 95% bootstrap CIs for the randomized oracle but omits them for the bidirectional oracle, claiming it is 'deterministic.' However, results vary across 8 seeds. Authors must clarify if bidirectional variance is zero or if CIs were omitted despite seed-level variance, affecting statistical rigor.
- **[science]** The claim that HeapSort surpasses Mohajer at B=300 in the randomized regime relies on a small effect size (0.5 NDCG). The text must explicitly reference the p-values for this specific crossover point to confirm the 'catch up' is statistically robust and not noise, given the tight CIs in Table 1.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The abstract claims a sensitivity analysis on autocorrelation (rho=0.3) with results in Appendix~\ref{app:autocorr}, but the provided LaTeX source contains no such appendix section. This prevents verification of the bootstrap validity claims under dependence.
- **[science]** Table 1 reports 95% bootstrap CI half-widths for the randomized oracle but omits CIs for the bidirectional oracle, stating it is 'deterministic given outcomes.' However, the experiment uses 8 oracle seeds; the variance across these seeds should be reported to distinguish algorithmic stability from oracle stochasticity.
- **[writing]** The 'Multiple-Testing Correction' section states Benjamini-Hochberg was applied to Appendix Tables A.10–A.11, but the provided source only contains Tables A.1–A.4 and significance tables A.5–A.6. The specific tables referenced for FDR control are missing or misnumbered.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The abstract contains a grammatical error: 'We also employ that Normalized Discounted Cumulative Gain...' should be 'We also employ Normalized Discounted Cumulative Gain...' or 'We use...'. The word 'that' is extraneous and disrupts the sentence flow.
- **[writing]** The abstract includes a bolded section labeled 'Fixed-Budget Clarification' which reads like a direct response to a reviewer rather than part of the manuscript narrative. This meta-commentary should be removed or rewritten to integrate the clarification seamlessly into the text (e.g., 'To address efficiency concerns, we added a fixed-budget evaluation...').
- **[writing]** The 'Supplementary Materials' section at the beginning of the paper contains meta-text ('Citation Verification Status', 'Multiple-Testing Correction') that describes the review process rather than the paper's content. This section should be removed or converted into standard footnotes or a 'Revisions' note if required by the venue, as it breaks the fourth wall of the academic narrative.
- **[writing]** In the Introduction, the sentence 'Major cloud providers now offer reranking as managed services...' is preceded by a citation block that appears disconnected from the preceding paragraph about data provenance. The transition between the data provenance paragraph and the cloud provider sentence is abrupt and lacks a logical connector.
