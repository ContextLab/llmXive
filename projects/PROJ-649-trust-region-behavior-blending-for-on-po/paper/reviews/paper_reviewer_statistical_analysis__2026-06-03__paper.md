---
action_items:
- id: 2d8787e007a4
  severity: science
  text: Clarify the number of random seeds used for training runs. Appendix A does
    not specify if results are averaged over seeds, which is critical for statistical
    validity.
- id: 72196be2a5b4
  severity: science
  text: Report variance (standard deviation) or confidence intervals for benchmark
    scores in Table 1. Point estimates alone do not support claims of statistical
    superiority.
- id: e6bd79f920e6
  severity: science
  text: Address checkpoint selection bias in Section 5.1. Selecting the best checkpoint
    per method inflates performance; compare at fixed steps or use a held-out validation
    set.
- id: 8518dc497df1
  severity: science
  text: Justify evaluation sample sizes (e.g., n=32 for GSM8K). Smaller sample sizes
    increase variance in pass@1 estimates; ensure sufficient power for comparisons.
artifact_hash: a0fcc4014c0149719a56a0fd8c9438fb07408db2050a8ea923c6bb42f703660e
artifact_path: projects/PROJ-649-trust-region-behavior-blending-for-on-po/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-03T22:06:51.706533Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical rigor of the experimental evaluation is currently insufficient to substantiate the claim that TRB attains the "strongest average" (Abstract, Section 5.2). While the mathematical derivation of the trust-region solver is sound (Appendix E), the empirical validation lacks necessary statistical controls.

First, the number of random seeds for training runs is not specified in Appendix A (Experimental Details). LLM training is stochastic; without averaging over multiple seeds (e.g., 3-5), observed differences (e.g., 33.2 vs 32.3 in Table 1) may be due to variance rather than method efficacy. Please clarify if results are single-seed or averaged, and report seed counts.

Second, Table 1 (Section 5.2) reports only point estimates for pass@1. There are no standard deviations, standard errors, or confidence intervals. Given the small margins between methods (e.g., TRB vs Vanilla OPD on 1.7B-8B), statistical significance testing (e.g., bootstrap or t-tests) is required to confirm improvements are not noise.

Third, the checkpoint selection protocol introduces bias. Section 5.1 states checkpoints are selected based on the "highest setup-specific mean score" on the evaluation suite. This optimizes for the test set, inflating reported performance. A fair comparison requires fixed-step evaluation or a held-out validation set for checkpoint selection, not the final benchmark suite.

Fourth, evaluation sample sizes vary significantly (32 for GSM8K vs 512 for AIME). The variance of pass@1 scales with $1/n$; smaller $n$ yields noisier estimates. Justify these choices or standardize them to ensure comparable precision across benchmarks.

Finally, multiple comparisons are made across two setups, six baselines, and ten benchmark columns without correction (e.g., Bonferroni). With so many comparisons, some apparent wins may be false positives. Reproducibility would also be improved by releasing evaluation scripts to verify the pass@1 computation.

In summary, the method is promising, but the statistical evidence needs strengthening to support the conclusions.
