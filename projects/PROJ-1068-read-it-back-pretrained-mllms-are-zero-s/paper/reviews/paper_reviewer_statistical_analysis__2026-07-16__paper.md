---
action_items:
- id: 50e3ffebffec
  severity: science
  text: "Tables 1-4 report single-point benchmark scores without uncertainty metrics\
    \ (SD/SE/CI) or seed counts. RL results vary stochastically; report mean \xB1\
    \ SD over \u22653 seeds for all main results to distinguish stable gains from\
    \ noise."
- id: 695bd7c6bf96
  severity: science
  text: Section 4.3 and Table 2 compare ~20+ configurations but claim 'significant'
    improvements without p-values or multiple-comparison corrections (e.g., Bonferroni).
    Apply FDR correction or rephrase claims to 'observed improvements' to avoid false
    positives.
- id: 28dffb1dcf8b
  severity: writing
  text: Figure 2 caption notes error bars over four pairs, but main tables lack uncertainty.
    Ensure consistent uncertainty reporting (e.g., SD over seeds) across all quantitative
    claims, not just in specific figures.
artifact_hash: 7fff84212e932b4d992732fd5a0527c97171ad9bb6da5fea5186ea23bf6fee03
artifact_path: projects/PROJ-1068-read-it-back-pretrained-mllms-are-zero-s/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-16T04:01:25.480020Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical treatment of the results in this paper is currently insufficient to support the strong claims of "significant" and "consistent" improvements. While the methodology for computing the reward (image-conditioned log-likelihood) is clearly defined, the inferential statistics applied to the benchmark results are missing.

First, the paper reports single-point estimates for all benchmark scores (e.g., GenEval, TIIF-Bench) in Tables 1 through 4 without any measure of uncertainty (standard deviation, standard error, or confidence intervals) or the number of random seeds used for training. In reinforcement learning, particularly with diffusion models, performance can fluctuate significantly due to stochasticity in the sampling process, initialization, and optimization trajectory. Reporting a single number (e.g., "89.5") implies a level of precision and stability that is not justified without replication. The authors must report results as mean ± standard deviation over at least 3 independent training runs (seeds) to demonstrate that the observed gains are robust and not artifacts of a specific random seed.

Second, the paper makes frequent use of the term "significantly" (Abstract, Section 4.2) to describe the performance gaps between the proposed method and baselines. However, no hypothesis tests (e.g., t-tests, Wilcoxon signed-rank tests) are performed, no p-values are reported, and no corrections for multiple comparisons are applied. The study involves comparing the proposed method against multiple baselines (AlphaGRPO, various MLLM backbones, different RL algorithms) across five different benchmarks. This constitutes a large number of pairwise comparisons (likely >20). Without a correction for multiplicity (such as Bonferroni or Benjamini-Hochberg), the probability of observing at least one "significant" result by chance alone is high. The current reporting style treats the observed differences as definitive truths rather than estimates subject to sampling variance.

Finally, while Figure 2 mentions error bars calculated over "four pairs" for a specific token-level analysis, this level of uncertainty reporting is not extended to the main benchmark results. The discrepancy between the detailed error analysis in the figure and the point estimates in the tables creates an inconsistency in statistical rigor. To be scientifically sound, the uncertainty reporting must be consistent across all quantitative claims, and the claim of "statistical significance" must be backed by actual statistical testing or removed in favor of reporting observed effect sizes with confidence intervals.
