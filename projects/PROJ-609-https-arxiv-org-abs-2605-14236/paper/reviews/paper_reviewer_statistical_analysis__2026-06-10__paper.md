---
action_items:
- id: 975930f5a261
  severity: science
  text: "Report uncertainty estimates (e.g., bootstrap confidence intervals) for the\
    \ bidirectional\u2011oracle results, which are currently presented as deterministic\
    \ point estimates."
- id: 160b9279ea2b
  severity: science
  text: "Apply a multiple\u2011testing correction (e.g., Bonferroni or Benjamini\u2011\
    Hochberg) when assessing statistical significance across the many budget columns\
    \ and ranker comparisons."
- id: 73441eaeea4c
  severity: science
  text: "Discuss and, if possible, quantify the dependence structure among LLM calls\
    \ (especially under the randomized\u2011direction oracle) and its impact on the\
    \ validity of the bootstrap procedures."
- id: c47c3d91fe3b
  severity: science
  text: "Include effect\u2011size measures (e.g., mean \u0394NDCG@10 with confidence\
    \ intervals) alongside p\u2011values to give a clearer picture of practical significance."
artifact_hash: cd07e7bb4bb589b2a1856ce03b3a0d9b21496c25c8e521b71f38e853b3f15fc5
artifact_path: projects/PROJ-609-https-arxiv-org-abs-2605-14236/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-10T16:29:04.188408Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript presents an extensive experimental evaluation of active‑learning rankers (Mohajer, PAC) against traditional sorting‑based PRP rerankers. From a statistical‑analysis standpoint the authors make several commendable choices: they use paired bootstrap resampling over queries to test differences between methods (Section 6, Tables A.9–A.10) and they report 95 % bootstrap confidence‑interval half‑widths for the randomized‑direction oracle (Table 1). This demonstrates awareness of variability in LLM‑based comparisons.

However, the statistical treatment has gaps that limit confidence in the reported gains:

1. **Uncertainty for deterministic (bidirectional) results** – The bidirectional oracle yields a single deterministic outcome per query, yet the authors present only point estimates (e.g., Table 1, “Bidirectional” rows). Without confidence intervals or a variance estimate, it is impossible to gauge the stability of these numbers or to compare them fairly to the randomized‑direction results, which do include CIs.

2. **Multiple‑testing across budgets and rankers** – Significance tests are performed for each budget column separately (e.g., Table A.9). Given the large number of simultaneous comparisons (multiple rankers, two oracles, ten budgets), the risk of inflated Type I error is high. A correction method (Bonferroni, Holm, or FDR) should be applied and the adjusted p‑values reported.

3. **Assumption of independent LLM calls** – The bootstrap analysis assumes that each query’s set of pairwise calls is independent. In practice, LLM APIs may cache prompts or share hidden state, especially when the same model is queried repeatedly within a query. This could induce correlation across comparisons, violating the bootstrap’s independence assumption. The authors should at least discuss this limitation and, if possible, provide an empirical check (e.g., intra‑query correlation estimates).

4. **Effect‑size reporting** – The tables show ΔNDCG@10 differences, but the magnitude of these differences relative to the variability of NDCG is not quantified. Reporting mean differences with confidence intervals (or standardized effect sizes) would help readers assess practical significance, beyond binary “significant / not significant” statements.

5. **Bootstrap seed variability** – The authors run eight oracle seeds for the randomized oracle and report CI half‑widths, but they do not provide the distribution of results across seeds (e.g., mean ± SD). Presenting this would illustrate whether performance is robust to seed choice.

6. **Choice of NDCG metric** – NDCG@10 is reported as a percentage, but the denominator (ideal DCG) can vary substantially across queries. Normalizing across queries before averaging can introduce bias. Clarifying whether the authors compute per‑query NDCG and then average, or aggregate DCG across the dataset, would improve reproducibility.

Overall, while the experimental design is sound and the use of bootstrap methods is a strength, the statistical reporting lacks completeness and rigorous control for multiple comparisons. Addressing the points above would substantially strengthen the evidential basis of the paper’s claims.
