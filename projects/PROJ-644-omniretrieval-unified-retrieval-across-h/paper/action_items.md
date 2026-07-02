# Automated-review action items — OmniRetrieval: Unified Retrieval across Heterogeneous Knowledge Sources

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[fatal]** The paper cites 'GPT-5.4' and 'Gemini-3.1' as evaluation backbones. These models do not exist in public records or the provided bibliography (which lists GPT-5 and Gemini-2.5). This appears to be a hallucinated citation, rendering the experimental results unverifiable.
- **[fatal]** Citation keys like 'GPT-54' in the text do not match the semantic names 'GPT-5.4' used in prose. The bibliography entries point to future dates (2026) or mismatched versions, undermining the claim of using specific, real-world backbones for the reported metrics.
- **[writing]** The claim of '309 distinct knowledge bases' treats 7 BEIR datasets as single bases. While mathematically summing to 309, this phrasing is misleading as it implies 309 separate database instances rather than distinct corpora within a benchmark suite.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[fatal]** Figure 2: The figure has no caption (stated as '(no caption)'), making it impossible to verify if the displayed data matches the authors' intended claims or context.
- **[science]** Figure 2: The stacked bars do not sum to 100% (e.g., the 'GPT-5.4' bar sums to ~98.9% and 'Gemma-4' sums to ~99.5%), suggesting missing data categories or calculation errors.
- **[writing]** Figure 2: The legend is partially obscured by the figure title, making the '2+ Cand., Gold Included' entry difficult to read.
- **[writing]** Figure 3: The figure lacks a descriptive caption; the current placeholder '(no caption)' fails to explain the experimental setup, the meaning of the 'Balanced Reference' line, or the specific models being compared.
- **[writing]** Figure 3: The legend is positioned outside the plot area and is not enclosed in a box, which can make it visually disconnected from the data in some rendering contexts.
- **[writing]** Figure 4: The figure lacks a descriptive caption, providing no context for the 'Source Selection', 'Retrieval', and 'Judge' subplots or the specific experiment being visualized.
- **[writing]** Figure 4: The legend is located only in the rightmost subplot ('Judge'), making it ambiguous for the 'Source Selection' and 'Retrieval' subplots which use the same symbols but lack a direct legend.
- **[writing]** Figure 5: The caption is missing; the provided text '(no caption)' prevents verification of the specific experimental setup, dataset, or metric definitions required to interpret the 'Accuracy' and 'Candidate Sources' axes.
- **[writing]** Figure 5: The y-axis label 'Accuracy (%)' is ambiguous without a caption specifying the exact task (e.g., retrieval, generation, or classification) or the baseline against which the 'Oracle' is compared.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on specialized terminology that obscures meaning for non-expert readers. The most frequent offender is "structural affordances," which appears in the Abstract, Introduction, and Related Work without ever being defined. While the authors imply it refers to schemas or query capabilities, a general reader cannot parse this without guessing. Similarly, "native execution engines" (Section 2.1) and "atomic-unit retrieval" (Section 5) are jargon-heavy phrases that could be

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** Source Selection Gap: 100.00 - 65.71 = 34.29 (matches 34.27 approx).
- **[writing]** Retrieval Accuracy Gap: 61.85 (Oracle) - 44.34 (OmniRetrieval) = 17.51.
- **[writing]** LLM-as-a-Judge Gap: 74.55 (Oracle) - 65.88 (OmniRetrieval) = 8.67. Wait, the text says the gap narrows *from* selection *to* judge, listing three numbers. If the sequence is Selection -> Retrieval -> Judge, the gaps are 34.29 -> 17.51 -> 8.67. This is a monotonic narrowing. My previous calculation of the Retrieval gap was wrong in the thought trace (I used 100 as the oracle for retrieval, but the table lists 61.85). Let's re-verify the text's claim: "The gap to Oracle narrows from selection to j
- **[writing]** Selection Gap: 100 - 65.71 = 34.29.
- **[writing]** Retrieval Gap: 61.85 - 44.34 = 17.51.
- **[writing]** Judge Gap: 74.55 - 65.88 = 8.67. The numbers in the text (34.27, 17.51, 8.67) match the calculated gaps (34.29, 17.51, 8.67) within rounding error. The logic holds *mathematically*. However, the *interpretation* of this trend is logically flawed. The text claims this narrowing "indicates evidence selection recovers answers even if source selection misses." This is a non-sequitur. The narrowing of the gap is primarily driven by the fact that the Oracle metric changes definition across the three r
- **[writing]** The Oracle for "Source Selection" is 100% (perfect selection).
- **[writing]** The Oracle for "Retrieval Accuracy" is 61.85% (perfect selection + perfect query generation + perfect execution).
- **[writing]** The Oracle for "LLM-as-a-Judge" is 74.55% (perfect selection + perfect query + *semantic* equivalence). The gap narrows because the Oracle's performance drops significantly from Selection (100%) to Retrieval (61.85%), while OmniRetrieval's performance also drops but less drastically relative to the Oracle's drop? No, OmniRetrieval drops from 65.71 to 44.34 (21.37 pts), while Oracle drops from 100 to 61.85 (38.15 pts). The gap narrows because the Oracle is penalized more heavily for the difficult
- **[writing]** Misinterpretation of the "gap narrowing" trend as evidence of "recovery" when it is actually an artifact of the Oracle's ceiling dropping.
- **[writing]** Ambiguous description of the "constrained setup" for the unified baseline, which could mislead readers about the fairness of the comparison.
- **[writing]** A non-sequitur in the "Source Candidate Size" analysis regarding the "impactful lever". The paper should revise the "Main Results" analysis to correctly attribute the gap narrowing to the Oracle's ceiling drop, and clarify the "constrained setup" to emphasize that the unified method was given an advantage. The "Source Candidate Size" analysis should be rephrased to correctly identify the selector as the bottleneck.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The paper makes several claims that extend beyond the empirical evidence provided in the benchmark evaluation. First, the abstract and conclusion characterize OmniRetrieval as a "general-purpose interface" to heterogeneous sources. This terminology implies a level of universality and dynamic adaptability that the experimental setup does not support. The evaluation is strictly confined to 13 pre-defined datasets and 309 static knowledge bases. The paper does not present evidence of the system suc

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper addresses a technically sound approach to heterogeneous retrieval but presents notable safety and ethical gaps regarding data privacy and content moderation. The primary concern lies in the Ethical Considerations (Section 7) and Use of Existing Artifacts (Appendix B.5). The authors explicitly state they "do not perform additional filtering for personally identifying information or offensive content" and defer entirely to upstream dataset policies. While the benchmark datasets (e.g., Sp

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The evaluation relies on a single deterministic run (temperature 0.0) for all 5 backbone models across 13 datasets. Without multiple seeds or variance reporting, the observed gains (e.g., +4.66 pp in Retrieval Accuracy) cannot be distinguished from stochastic noise or specific prompt sensitivities. Re-run experiments with at least 3 seeds to report mean and standard deviation.
- **[science]** The 'LLM-as-a-Judge' metric (GPT-5.4-mini) is used as a primary evaluation signal but lacks calibration against human annotations. Given the potential for LLM judges to exhibit bias toward their own outputs or specific phrasing, the paper must include a validation study (e.g., correlation with human ratings on a subset) to establish the metric's reliability.
- **[science]** The 'Oracle' baseline is defined as perfect source selection, yet the gap between OmniRetrieval and Oracle remains significant (e.g., 65.71 vs 100.00 in Source Selection). The paper does not sufficiently analyze the specific failure modes of the source selection module (e.g., hallucinated KBs vs. missed relevant KBs) to explain why the gap persists despite the 'broad exploration' strategy.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The paper reports results from a single deterministic run (temperature 0.0) without any measure of variance (e.g., standard deviation, confidence intervals) or statistical significance testing. Given the small performance gaps between OmniRetrieval and KB Routing in some backbones (e.g., +3.86 pp on GPT-5.4 for Source Selection), the authors must provide evidence that these improvements are not due to random variation or specific dataset idiosyncrasies.
- **[science]** The evaluation relies heavily on an 'LLM-as-a-Judge' metric (GPT-5.4-mini) for semantic equivalence without reporting inter-rater reliability or calibration against human annotations. The statistical validity of using a single LLM instance as the ground truth for 'correctness' across 13 datasets is unverified and requires a sensitivity analysis or comparison with human-annotated subsets.
- **[science]** The macro-averaging of metrics across four heterogeneous paradigms (Search, SQL, SPARQL, Cypher) with vastly different baseline difficulties and sample sizes (e.g., 286 SQL DBs vs 15 Cypher graphs) may obscure significant performance disparities. The authors should clarify if the reported averages are weighted by dataset size or if a stratified analysis was performed to ensure the results are not dominated by the largest paradigm.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The abstract in the main body (e002) is significantly longer and more detailed than the abstract in the initial snippet (e000). Ensure the final manuscript uses the complete, polished version consistently and that the short snippet in e000 is not accidentally included in the final PDF.
- **[writing]** In Section 5 (Experimental Results), the phrase 'The gap to Oracle narrows from selection to judge (34.27 -> 17.51 -> 8.67 pts)' lacks explicit definition of the intermediate metric. Clarify that the middle value corresponds to 'Retrieval Accuracy' to ensure the progression is immediately clear to the reader.
- **[writing]** The caption for Table 1 (e002) states 'macro-averaged across four retrieval paradigms,' but the table columns represent different LLM backbones. The caption should clarify that the 'Average' column is the macro-average across paradigms, while the other columns represent specific backbone performance.
- **[writing]** In the Appendix, the prompt examples (e001) use a mix of formatting styles (e.g., `\textbf` vs. bold text in verbatim blocks). Standardize the visual presentation of system/user prompts across all figures for better readability.
