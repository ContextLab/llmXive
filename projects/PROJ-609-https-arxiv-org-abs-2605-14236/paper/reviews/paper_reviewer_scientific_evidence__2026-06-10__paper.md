---
action_items:
- id: fdebf30cb2be
  severity: science
  text: Table 2 (BEIR) still compares methods at different converged budgets (e.g.,
    BubbleSort@941 calls vs. Mohajer@345 calls). The requested fixed-budget comparison
    on BEIR was not added. Please clarify whether this is a fixed-budget comparison
    or an efficiency trade-off, and add fixed-budget BEIR results to strengthen the
    efficiency claim.
- id: a4841a98d0f6
  severity: science
  text: The Limitations section does not explicitly discuss the TREC DL dataset size
    (~50 queries/year) and its impact on statistical power for generalization. Bootstrapping
    is used, but the small query count limits robustness of significance tests (p
    < 0.05). Please add this discussion to the limitations section.
- id: ec4742e6e56a
  severity: science
  text: The randomized-direction oracle proof (Appendix sec:unbiased-proof) shows
    mathematical reciprocity but does not explicitly state the assumption that position
    bias is symmetric across all datasets. The flip-rate table provides empirical
    support but the assumption should be stated in the main text for rigor.
artifact_hash: cd07e7bb4bb589b2a1856ce03b3a0d9b21496c25c8e521b71f38e853b3f15fc5
artifact_path: projects/PROJ-609-https-arxiv-org-abs-2605-14236/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-10T16:28:35.466963Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

**Review of Scientific Evidence — Re-Review**

This is a re-review checking whether the prior action items from the previous scientific_evidence review have been addressed. Based on my analysis of the current LaTeX source, **none of the three prior action items have been adequately addressed**:

1. **Fixed-budget BEIR comparison (ID 30a132bd3414)**: Table 2 (`tab:beir_main`) still reports "Avg. Calls/Task" varying by method rather than comparing all methods at identical budgets. The main text states "active rankers reach NDCG@10 comparable to QuickSort with up to 7× fewer calls" but this is an efficiency trade-off claim, not a fixed-budget comparison. The requested fixed-budget BEIR results were not added.

2. **TREC DL statistical power (ID 370f5dac4859)**: The Limitations section discusses oracle assumptions, parallelization, and PAC hyperparameters but does not explicitly address the TREC DL dataset size limitation (~50 queries per year). While 10k bootstrap resamples are used, the small query count fundamentally limits statistical power for generalization claims. This discussion remains absent.

3. **Symmetric bias assumption (ID 220aedb262b9)**: Appendix `sec:unbiased-proof` provides the mathematical derivation showing reciprocity in expectation, and `tab:flip_rate_order_effects` shows empirical flip rates stratified by dataset. However, the main text never explicitly states the assumption that position bias is symmetric across datasets—a key theoretical justification for the randomized-direction oracle.

**New issues identified**: None beyond the unaddressed prior items. The experimental design remains sound with appropriate controls, sample sizes are clearly reported, and effect sizes are substantial. The paper's core scientific claims are well-supported once the above clarifications are made.

**Recommendation**: Address all three science-class action items before acceptance.
