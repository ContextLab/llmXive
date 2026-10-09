# Revision Specification: Paper Science Revision — PROJ-609-https-arxiv-org-abs-2605-14236 round 1

**Generated**: 2026-06-13T11:34:05.384688+00:00
**Kind**: paper_science
**Project**: PROJ-609-https-arxiv-org-abs-2605-14236
**Round**: 1

## Input

Address the following reviewer-raised action items:

- **[e78b16e3112e] (severity: writing)** Add explicit data provenance statements for all datasets (TREC DL, BEIR) including download dates, preprocessing steps, and retrieval configuration
- **[1585fd85837e] (severity: writing)** Ensure all figure captions include complete methodological details for reproducibility (GPU type, inference batch size, random seed count)
- **[a07f67ffdd5b] (severity: writing)** Add glossary or expand first-use definitions for field-specific acronyms (PRP, NDCG, PAC, SST, BM25) to improve accessibility
- **[2e5405f1cdfe] (severity: writing)** Include citation verification status for all bibliography entries in supplementary materials as required by acceptance criteria
- **[33c162157101] (severity: science)** Clarify the claim in Section 3 (Line 106-107) that the Bidirectional oracle enforces pair-consistency (p_ij = 1-p_ji). The definition in Line 117 allows V_ij=0 and V_ji=0 on conflicting LLM outputs, which violates strict reciprocity. Specify if ties are resolved or if the assumption holds only in expectation.
- **[72300e0551d1] (severity: science)** Code repository (https://github.com/jerecoder/IReranker) remains inaccessible for review. Provide artifact hash or include minimal code snippets in appendix to verify reproducibility claims.
- **[bed7e2c0c4de] (severity: science)** Paper references implementation details (Mohajer algorithm, PAC+Bubble) but provides no pseudocode or algorithm listings. Add Algorithm 1-2 with complexity analysis for reproducibility.
- **[d891fa08e8fd] (severity: science)** No dependency list or environment specification (Python version, LLM API details, hardware specs) provided for experimental replication.
- **[5792033c013e] (severity: writing)** Pin the code repository version (e.g., commit hash or tag) in the manuscript to prevent link rot and ensure reproducibility.
- **[4fb44347304b] (severity: writing)** Explicitly state the exact versions of datasets used (e.g., BEIR v1.0.0, TREC DL2019/2020) to ensure data consistency.
- **[ac1420975237] (severity: writing)** Declare a software license for the code repository and any derived data artifacts to ensure legal clarity.
- **[0a8862916c7d] (severity: writing)** Add alt text for all figures using the graphicx alttext option or figure environment to ensure accessibility compliance for screen readers.
- **[3cc3966b1996] (severity: writing)** Figure 1 caption (line 290) should explicitly state x-axis units (seconds) and y-axis units (NDCG@10 %) for standalone readability without referring to text.
- **[f0bc9d0a3b70] (severity: writing)** Define NDCG@10 at first use in Abstract and Introduction. Currently appears as 'NDCG@10' without expansion.
- **[d3d03eaf4912] (severity: writing)** Define BEIR (Benchmarking Information Retrieval) when first mentioned in Introduction.
- **[7e61a93ac78d] (severity: writing)** Expand 'CI' to 'Confidence Interval' in Table 1 caption.
- **[d2704c93ba64] (severity: writing)** Define BM25 (Okapi BM25) in Section 5 or Introduction.
- **[49283a0a0e81] (severity: writing)** Replace 'call-constrained regime' with 'call-limited setting' in Abstract for clarity.
- **[f915c170ae76] (severity: science)** Clarify the scope of the randomized-direction oracle's unbiasedness. The proof (Appendix A) assumes strict pair-consistency, which may be violated by real LLM APIs (hidden state, non-stationarity). Either provide empirical validation of the unbiasedness claim or temper the statement to reflect this assumption.
- **[57ac686dd172] (severity: writing)** Revise the 'drop-in replacement' claim (Abstract & Conclusion). Active rankers require a warm-up phase (≈K² calls) and hyper-parameters (e.g., the PAC pool multiplier m). Explicitly discuss these prerequisites and their impact on deployment complexity.
- **[31c81d9070a4] (severity: science)** Limit the prescriptive recipe ('use Mohajer with randomized-direction when budget exceeds the warm-up threshold') to the specific models and datasets evaluated (Flan-T5-L/XL, Qwen-3-4B). Acknowledge that performance may differ for other LLM families or larger candidate pools.
- **[cf816086396f] (severity: writing)** Add a discussion of how the reported latency estimates (Section 6) might change with realistic parallel batching, and qualify any conclusions about 'time-to-quality' that are based on sequential upper-bounds.
- **[fdebf30cb2be] (severity: science)** Table 2 (BEIR) still compares methods at different converged budgets (e.g., BubbleSort@941 calls vs. Mohajer@345 calls). The requested fixed-budget comparison on BEIR was not added. Please clarify whether this is a fixed-budget comparison or an efficiency trade-off, and add fixed-budget BEIR results to strengthen the efficiency claim.
- **[a4841a98d0f6] (severity: science)** The Limitations section does not explicitly discuss the TREC DL dataset size (~50 queries/year) and its impact on statistical power for generalization. Bootstrapping is used, but the small query count limits robustness of significance tests (p < 0.05). Please add this discussion to the limitations section.
- **[ec4742e6e56a] (severity: science)** The randomized-direction oracle proof (Appendix sec:unbiased-proof) shows mathematical reciprocity but does not explicitly state the assumption that position bias is symmetric across all datasets. The flip-rate table provides empirical support but the assumption should be stated in the main text for rigor.
- **[cafcbcfc7240] (severity: science)** Bidirectional-oracle results still lack uncertainty estimates (Table 1). The caption states CIs are omitted because bidirectional is 'deterministic given outcomes,' but query-level resampling uncertainty remains unquantified. Add bootstrap CIs from query resampling or seed variation.
- **[c2ad4450894f] (severity: science)** Multiple-testing correction (Bonferroni/BH) is still absent when reporting significance across 9 budget columns × multiple ranker comparisons (Appendix Tables A.10-A.11). This inflates Type I error. Apply and report corrected p-values or adjusted significance indicators.
- **[0f962fc81111] (severity: science)** Dependence structure among LLM calls is mentioned in Limitations but not quantified. The bootstrap validity assumption (independent oracle outputs) may be violated by API caching/hidden state. Add empirical analysis (e.g., autocorrelation of outcomes) or sensitivity analysis quantifying impact on CI coverage.
- **[c2f1c0c77019] (severity: science)** Effect-size measures (mean ΔNDCG@10) are shown in Tables A.10-A.11 but without confidence intervals around these differences. Add 95% CIs for effect sizes to distinguish statistical from practical significance, as originally requested.
- **[bcd18ebc9e2c] (severity: writing)** Add \bibliographystyle{acl_natbib} before \bibliography{custom} at line 314 to ensure correct reference formatting.
- **[eef56cc49294] (severity: writing)** Change \begin{table*}[!hbp] to \begin{table*}[t] or [p] at lines 510 and 530, as [h] is invalid for table* in two-column layouts.
- **[871350d3bd52] (severity: writing)** Review \resizebox usage at line 200; prefer explicit font sizing (\scriptsize) within tabular to avoid text compression issues.
- **[0e73b0fbaf17] (severity: writing)** Add 'that' after 'show' in Abstract and Introduction (lines 48, 72) for grammatical precision.
- **[cec870057592] (severity: writing)** Remove the LaTeX comment '% Paste this in the Appendix...' from the Appendix source (line 1050) to ensure source cleanliness.
- **[4bf1194196b1] (severity: writing)** Rephrase 'flip the judge's choice between documents' in Introduction (line 76) to 'flip the preferred document' for clarity.


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 35 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
