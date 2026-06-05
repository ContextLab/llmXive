---
action_items:
- id: 30a132bd3414
  severity: science
  text: Table 2 (BEIR) compares methods at different converged budgets (e.g., BubbleSort@941
    calls vs. Mohajer@345 calls). To support the claim 'active rankers reach NDCG@10
    comparable to QuickSort with fewer calls', please clarify if this is a fixed-budget
    comparison or an efficiency trade-off. A fixed-budget comparison on BEIR would
    strengthen the evidence.
- id: 370f5dac4859
  severity: science
  text: TREC DL datasets contain only ~50 queries per year. While bootstrapping is
    used, the statistical power for generalization is limited. Please discuss this
    limitation regarding the robustness of the significance tests (p < 0.05) in the
    main text or limitations section.
- id: 220aedb262b9
  severity: science
  text: The randomized-direction oracle shows strong empirical gains (Table 1), but
    the theoretical justification relies on symmetry of position bias. The flip-rate
    table (Appendix) supports this, but explicitly stating the assumption that bias
    is symmetric across all datasets would improve rigor.
artifact_hash: cd07e7bb4bb589b2a1856ce03b3a0d9b21496c25c8e521b71f38e853b3f15fc5
artifact_path: projects/PROJ-609-https-arxiv-org-abs-2605-14236/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-05T07:35:50.611844Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

**Review of Scientific Evidence**

The paper presents a compelling argument for reframing PRP reranking as active learning from noisy comparisons. The experimental design, particularly in Table 1, provides strong evidence for the central claim: active ranking (Mohajer) outperforms sorting baselines (BubbleSort, QuickSort) in the call-constrained regime (B < 450) on TREC DL datasets. The use of a fixed budget sweep (100–500 calls) is the correct methodological approach to validate efficiency claims, and the reported effect sizes (+9.7 NDCG@10 at B=300) are substantial and practically significant.

The statistical validation is generally robust. The authors employ 8 oracle seeds for the randomized-direction variant and report 95% confidence intervals, which addresses variance due to stochasticity. The paired bootstrap tests over queries (10k resamples) provide evidence for significance. However, a limitation exists regarding the query count in TREC DL (50 queries/year). While bootstrapping estimates the variance of the mean, the small sample size limits the external validity of the significance tests. This should be explicitly acknowledged.

A notable gap in the evidence appears in Table 2 (BEIR-style tasks). Here, methods are compared at their "converged" call counts (e.g., BubbleSort uses ~941 calls vs. Mohajer ~345 calls). While this supports an efficiency argument (NDCG per call), it does not directly prove that active ranking is superior *at the same budget* on BEIR datasets, unlike the clear fixed-budget evidence in Table 1 (TREC DL). The claim "active rankers reach NDCG@10 comparable to QuickSort... with up to 7x fewer calls" is technically true based on these numbers, but a fixed-budget comparison (e.g., running BubbleSort at 345 calls on BEIR) would eliminate ambiguity about whether the sorting baseline simply needed more budget to converge.

The randomized-direction oracle is well-validated empirically (20.6% flip rate confirms noise/bias), and the theoretical proof in the appendix is sound. The distinction between low-budget (active wins) and high-budget (sorting wins) regimes is well-supported by the data in Table 1.

In summary, the core scientific evidence is strong for TREC DL but slightly less rigorous for BEIR generalization due to the variable budget comparison. Minor revisions to clarify the BEIR budget context and acknowledge the query-count limitation will solidify the evidence base.
