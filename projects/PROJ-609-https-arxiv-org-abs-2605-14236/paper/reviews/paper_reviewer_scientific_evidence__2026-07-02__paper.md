---
action_items:
- id: acc68aa694b5
  severity: science
  text: The abstract references an empirical sensitivity analysis on autocorrelation
    (rho=0.3) with results in Appendix~\ref{app:autocorr}, but this section is missing
    from the provided LaTeX source. This critical evidence for the robustness of the
    bootstrap validity assumption is absent.
- id: 95f6e716b558
  severity: science
  text: The paper reports 95% bootstrap CIs for the randomized oracle but omits them
    for the bidirectional oracle, claiming it is 'deterministic.' However, results
    vary across 8 seeds. Authors must clarify if bidirectional variance is zero or
    if CIs were omitted despite seed-level variance, affecting statistical rigor.
- id: 6dee6650df89
  severity: science
  text: The claim that HeapSort surpasses Mohajer at B=300 in the randomized regime
    relies on a small effect size (0.5 NDCG). The text must explicitly reference the
    p-values for this specific crossover point to confirm the 'catch up' is statistically
    robust and not noise, given the tight CIs in Table 1.
artifact_hash: 8b4e5d074a64eaa78e7927259e08b3cc001daf353c2dc417958eda25d90e918a
artifact_path: projects/PROJ-609-https-arxiv-org-abs-2605-14236/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T14:12:33.907446Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling reframing of PRP reranking as active learning, supported by extensive empirical results on TREC DL and BEIR datasets. The use of paired bootstrap tests (10k resamples) to establish significance for the gains of Mohajer over sorting baselines (Appendix Tables A.10–A.11) is a strong methodological choice that mitigates p-hacking risks. The effect sizes reported (e.g., +9.7 NDCG@10 at B=300) are substantial and practically significant for cost-constrained RAG pipelines.

However, the scientific evidence is currently incomplete in two critical areas. First, the abstract explicitly references an empirical sensitivity analysis regarding LLM non-stationarity and autocorrelation (rho=0.3) with results in "Appendix~\ref{app:autocorr}". This section is entirely absent from the provided LaTeX source. Without this data, the claim that the bootstrap validity is robust to moderate dependence structures is unsupported, leaving a major theoretical assumption unverified.

Second, the statistical reporting for the bidirectional oracle is ambiguous. The authors state that CIs are omitted because the oracle is "deterministic given outcomes," yet the table caption notes results are averaged over "8 oracle seeds." If the variance across seeds is non-zero (which is expected given the stochastic nature of LLMs), omitting CIs for the bidirectional condition while reporting them for the randomized condition creates an asymmetry in evidence presentation. It is unclear if the bidirectional results are truly deterministic or if the variance was simply ignored. To ensure the robustness of the comparison between the two oracles, the authors must either report the variance/CIs for the bidirectional condition or explicitly justify why seed-level variance is negligible for that specific oracle design.

Finally, the claim that HeapSort surpasses Mohajer at higher budgets (B=300+) in the randomized regime relies on small effect sizes (e.g., 68.50 vs 68.00). While the bootstrap tables indicate significance, the text should explicitly reference the p-values for these specific crossover points to confirm that the "catch up" is statistically robust and not a result of noise, given the tight confidence intervals shown in Table 1.
