# Automated-review action items — Intern-Atlas: A Methodological Evolution Graph as Research Infrastructure for AI Scientists

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The citation for 'AI Idea Bench' (qiu2025ai) claims it models novelty as 'historical difference and contemporary influence penalized by conformity.' The provided bib entry (arXiv:2504.14191) is a preprint from 2025. Verify if the specific formulaic components described in the text (e.g., 'conformity penalty') are explicitly defined in the cited source or if this is an extrapolation by the authors.
- **[writing]** The paper cites 'latimer2025hindsight' to support the claim that 'LLM-judged novelty correlates negatively with scientific impact.' The bib entry describes a paper on 'agent memory' (arXiv:2512.12818). Verify if this specific correlation finding is actually present in the cited work, as the title suggests a different focus (memory/retention) rather than novelty-impact correlation.
- **[writing]** The text states 'AI Scientist v2... utilizes agentic tree search to generate workshop-accepted papers' citing 'yamada2025ai'. The bib entry is a 2025 preprint. Confirm that the specific claim of 'workshop-accepted papers' is a result reported in that paper, distinguishing it from the v1 capabilities or other baselines, to avoid overstating the cited evidence.
- **[science]** The paper claims 'Intern-Atlas... produces quality signals that monotonically stratify across publication tiers' (Conclusion). While Table 1 shows mean scores decreasing, the text does not explicitly cite a statistical test (e.g., ANOVA or trend test) confirming the *monotonicity* is statistically significant across all four strata, rather than just a general trend. Ensure the claim of 'monotonic alignment' is supported by the specific statistical evidence in the paper or the cited figures.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 2: The caption text is truncated at the end ('Lineage SGT-MCTS reconstruction wi'), cutting off the description of the bottom panels.
- **[writing]** Figure 2: The caption contains a LaTeX formatting artifact '$G=(V,E,,)$' with double commas, likely indicating a missing edge type variable.
- **[science]** Figure 2: The bottom-left panel displays a 'temporal coherence' line graph with a y-axis labeled 'TC(Δτ)' and x-axis 'Δτ(years)', but the caption does not define what 'temporal coherence' measures or how it is calculated.
- **[writing]** Figure 3: The legend in the top-right corner is illegible due to low resolution; the text describing edge types (extends, improves, adapts, replaces) is unreadable.
- **[writing]** Figure 3: The colorbar legend at the bottom right is blurry, making the specific year labels (2016, 2018, etc.) difficult to read.
- **[science]** Figure 4: The caption 'Graph quality scores' is too vague to support the specific claims of the chart; it should explicitly name the metrics (NMR, ERR, PSC) and the evaluation context (e.g., 'Method extraction accuracy').
- **[writing]** Figure 4: The y-axis labels (NMR, ERR, PSC) are undefined acronyms; the caption must define these terms (e.g., 'NMR: Normalized Method Recall') to ensure the figure is self-contained.
- **[science]** Figure 5: The heatmap displays correlation values (e.g., 0.81, 0.64) but lacks axis labels or a legend defining the row/column categories (e.g., 'Novelty', 'Feasibility', 'Expert', 'Pure LLM'), making the specific metrics and models being compared impossible to identify.
- **[writing]** Figure 5: The caption 'Human-alignment correlations' is insufficient; it fails to specify the statistical method (e.g., Spearman vs. Pearson) or the specific human evaluation criteria used, which are critical for interpreting the data.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Define 'SGT-MCTS' at first use in the Introduction (Section 1). The acronym appears before its full expansion 'Self-Guided Temporal Monte Carlo Tree Search' is provided, which excludes non-specialist readers.
- **[writing]** Replace the term 'parametric memory' in Section 1 with a plainer description (e.g., 'internal knowledge base' or 'trained weights') to improve accessibility for readers outside the specific LLM architecture subfield.
- **[writing]** Define 'BM25' at its first occurrence in Section 3.2. While common in IR, it is an acronym that should be spelled out (e.g., 'BM25 (Okapi BM25)') for a general scientific audience.
- **[writing]** Replace the phrase 'parametric familiarity' in Section 2.2 with a clearer term like 'reliance on training data patterns' to avoid unnecessary jargon.
- **[writing]** Define 'RAG' (Retrieval-Augmented Generation) at its first use in Section 4.3. The acronym is used without expansion, assuming prior knowledge from the reader.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** Clarify the normalization of Edge Recall (ER) in Table 1. If the graph's Edge Reachable Ratio is 89.7%, ER cannot exceed this cap. A 55.8-point gain implies a baseline near 23%, but the text claims the baseline recovers 'later segments'. Specify if ER is normalized against total reference edges or only reachable ones to resolve the apparent contradiction.
- **[science]** The Idea Generator's 'Novelty' score relies on the Evaluator, which includes a text-based 'duplicate-risk penalty' (App C.2). If the Generator improves 'Novelty' scores, clarify if this is due to topological disconnection or avoidance of text similarity. If the text penalty was active, the metric may not reflect the claimed graph-based novelty, creating a logical gap in the evaluation.
- **[science]** The Introduction claims LLMs cannot reconstruct method evolution from unstructured text, yet the Method section uses LLMs to extract edges and bottlenecks from that same text. Distinguish between 'global topology reconstruction' (claimed failure) and 'local edge extraction' (claimed success) to resolve the contradiction that LLMs are both incapable and capable of processing the text.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim that AI agents 'cannot reliably reconstruct method evolution topologies' (Intro) is an absolute negative unsupported by the provided evidence. The paper demonstrates that Intern-Atlas performs better than baselines on a specific benchmark, but does not prove that *no* agent can reconstruct these topologies from unstructured text. Qualify this to 'struggle to' or 'perform significantly worse than' based on the specific experimental results.
- **[writing]** The conclusion states that Intern-Atlas 'generates ideas preferred over... baselines under label-blind human judgment' (88% win rate). This overstates the generalizability of the result. The evaluation was limited to 100 queries and 10 experts. The claim should be tempered to reflect the specific scope of the study (e.g., 'in our limited evaluation setting') rather than implying a universal superiority.
- **[writing]** The paper asserts that the 'zero-trainable-parameter' design is a 'deliberate commitment... trading potential accuracy gains' (Appendix). While honest, the main text presents the graph-grounded scores as definitive improvements over LLM judges without explicitly quantifying the 'potential accuracy gains' lost by avoiding training. Clarify if this trade-off was empirically measured or is a theoretical assumption.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The 'Strata Dataset' (Sec 4.2) includes 'Rejected submissions' from ICLR 2026. The authors must explicitly confirm that these rejected papers were obtained via public channels (e.g., OpenReview) and that no private reviewer comments or confidential author identities were used in the evaluation pipeline to ensure compliance with conference data policies.
- **[writing]** The 'Human-Rated Subset' (App D.3) involves 10 AI PhD researchers scoring 100 ideas. The manuscript lacks a statement confirming that informed consent was obtained from these experts, that the study protocol was reviewed by an IRB (or equivalent ethics board), and that the data collection adhered to privacy standards regarding the experts' identities and scores.
- **[writing]** The 'Idea Generation' operator (Sec 3.3) proposes new research ideas based on 'structural gaps.' The authors must add a 'Broader Impact' or 'Limitations' subsection explicitly addressing the risk of these agents generating harmful, unethical, or dual-use research proposals (e.g., biosecurity risks, adversarial attacks) and describe any safety filters or human-in-the-loop safeguards implemented to prevent such outputs.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The evaluation of the SGT-MCTS algorithm (Table 1) relies on Node Recall (84.8%) and Edge Recall (79.0%) against a benchmark of 30 survey papers. The sample size (133 chains) is small for a graph of this scale. Please report confidence intervals or perform a statistical significance test (e.g., bootstrap) to confirm the 39.9-point gain over Beam@10 is not due to variance in the specific survey selection.
- **[science]** The 'Strata Dataset' for idea evaluation (Sec 4.2) uses publication venue (Top-tier vs. Rejected) as a proxy for idea quality. This introduces a circularity risk: the graph is trained on these papers, and the evaluation assumes the venue label is the ground truth. The authors must address whether the graph is merely memorizing venue-specific citation patterns rather than learning true methodological evolution, and provide an ablation or control to rule out this confound.
- **[science]** The human evaluation for idea generation (Sec 4.3) reports an 88% win rate for Intern-Atlas. The methodology states experts were 'permitted to consult external academic search tools.' If experts could verify the novelty of the generated ideas using the same graph or external sources, the 'blind' nature of the evaluation is compromised. Clarify if the experts had access to the Intern-Atlas graph during the pairwise comparison, as this would invalidate the claim of independent validation.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Section 4.2 (Human Evaluation): The paper reports Spearman correlations (0.81 vs 0.58) but omits confidence intervals or significance tests (e.g., Fisher's r-to-z transformation) to determine if the difference between Intern-Atlas and the LLM baseline is statistically significant. Add 95% CIs and p-values for the correlation differences.
- **[science]** Section 4.3 (Idea Generation): Table 3 reports mean scores and win rates (e.g., 88.0%) without reporting standard deviations, standard errors, or results of statistical tests (e.g., paired t-tests or Wilcoxon signed-rank tests) to validate that the observed improvements over baselines are not due to random variation.
- **[science]** Section 4.1 (Lineage Reconstruction): Table 1 presents point estimates for NR, ER, and CAS. Given the stochastic nature of MCTS and the baselines, the authors must report the variance (e.g., standard deviation over multiple runs) and statistical significance of the improvements to ensure the results are robust.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 1 (Introduction), the sentence 'Their parametric memory is a lossy compression that underrepresents low-frequency or long-tail methodological knowledge.Their autoregressive inference...' is missing a space between the period and the next sentence. Please correct this typo to ensure readability.
- **[writing]** In Section 2.1 (Related Work), the phrase 'Intern-Atlas bridges this critical infrastructure gap' appears twice in close proximity (once in the paragraph starting 'Modern large-scale platforms...' and again in the paragraph starting '{Intern-Atlas} bridges...'). The second instance is redundant and disrupts the flow; consider rephrasing or removing the repetition.
- **[writing]** In Section 3.2 (Methodological Graph Construction), the text states 'The graph has three node sets: papers V_P... methods V_M... and stubs V_S...'. The subsequent sentence 'The output of Step 1 is a citation graph in which every reference is mapped to a node in V_M U V_S' omits V_P, which is confusing as the graph includes paper nodes. Clarify whether the output includes paper nodes or if the mapping is strictly to method/stub nodes.
- **[writing]** In Section 4.1 (Evaluating Graph Construction...), the phrase 'survey-derived method-evolution graphs with 2,268 nodes, 1,462 edges, and 133 evolution chains' is followed by 'Each graph consists of method nodes and evolution relations from the corresponding survey'. The repetition of 'graph' and 'survey' in consecutive sentences is slightly clunky. Consider smoothing the transition for better flow.
