---
action_items:
- id: eb00addc5ca6
  severity: science
  text: Table 1 and Table 2 report point estimates (e.g., 84.21, 90.19) without measures
    of statistical uncertainty (standard deviation, standard error, or confidence
    intervals). Given the use of LLM backbones which can exhibit stochastic variance,
    the authors must report results over multiple seeds or provide confidence intervals
    to substantiate the claimed improvements.
- id: 557269b45ac5
  severity: science
  text: The paper claims significant improvements (e.g., 23.3% gain) but does not
    report the results of statistical significance tests (e.g., paired t-tests, Wilcoxon
    signed-rank) comparing MRAgent against the strongest baselines. Without p-values
    or effect sizes, it is unclear if the observed gains are statistically distinguishable
    from random variance.
- id: 409a6e148bda
  severity: science
  text: The ablation study (Figure 3) and budget sensitivity analysis (Figure 4) present
    performance trends but lack error bars or statistical validation. The authors
    should clarify if these curves represent single runs or averages, and whether
    the observed monotonic improvements are statistically significant.
artifact_hash: b428847249c815694ce34a179b14e661a1c8a1e001ab2124c52ead974dee57ea
artifact_path: projects/PROJ-706-memory-is-reconstructed-not-retrieved-gr/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T20:13:34.609847Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript presents a novel framework for active memory reconstruction, supported by extensive empirical results on LoCoMo and LongMemEval. However, from a statistical analysis perspective, the evaluation lacks necessary rigor to fully support the magnitude of the claims made.

First, the primary results tables (Table 1 on LoCoMo and Table 2 on LongMemEval) report only point estimates for metrics like F1 and the LLM-Judge score (J). There is no mention of the number of random seeds used for the experiments, nor are standard deviations, standard errors, or confidence intervals provided. In LLM-based research, performance can vary significantly due to stochasticity in the generation process and the non-deterministic nature of the baselines. Without reporting variance (e.g., mean ± std), it is impossible to assess the reliability of the reported gains, such as the 23.3% improvement on Gemini.

Second, the paper asserts that MRAgent outperforms strong baselines but does not provide results from statistical significance tests. To claim that the improvements are robust, the authors should perform paired statistical tests (such as a paired t-test or Wilcoxon signed-rank test) across the test set or across multiple seeds. The absence of p-values or effect sizes leaves the central claim of "significant improvement" unsupported by formal statistical evidence.

Finally, the ablation study (Section 5.3, Figure 3) and the budget sensitivity analysis (Section 5.4, Figure 4) illustrate trends but do not include error bars or statistical validation. The claim that "depth cannot be replaced by breadth" is visually supported but statistically unverified. The authors should clarify if the curves in these figures represent single runs or averages, and whether the differences between configurations are statistically significant.

To address these issues, the authors should re-run experiments with multiple seeds (e.g., 3-5), report mean and standard deviation for all metrics, and include p-values for comparisons against the best baselines.
