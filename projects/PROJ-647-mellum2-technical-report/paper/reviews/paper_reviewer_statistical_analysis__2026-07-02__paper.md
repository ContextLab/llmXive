---
action_items:
- id: b6f650412d85
  severity: science
  text: Report uncertainty metrics (standard deviation or confidence intervals) for
    all benchmark scores in Tables 1, 4, and 5. Single-point estimates without variance
    measures prevent assessment of statistical significance, especially for small
    margins (e.g., MMLU-Pro 59.3% vs 58.6%).
- id: 7ef74ff55a09
  severity: science
  text: Clarify the statistical methodology for RLVR evaluation. Specify the number
    of independent seeds, sampling temperature, and whether results are averaged over
    multiple runs or single deterministic passes. The lack of variance reporting in
    RL tables (e.g., LiveCodeBench 75.1% vs 69.9%) obscures result stability.
- id: 369c5613454d
  severity: science
  text: Define the statistical basis for the '21% higher throughput' claim in Section
    6. Provide the sample size (number of requests), confidence interval, or p-value
    supporting this difference against the Qwen2.5-7B baseline to rule out random
    fluctuation.
artifact_hash: cb4466a31e7b640ad51d8c2f8310c27b9827d874fc645a40e58bc959301ab98e
artifact_path: projects/PROJ-647-mellum2-technical-report/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T15:31:51.620732Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript presents a comprehensive technical report on the Mellum2 model, but the statistical rigor of the evaluation section requires significant strengthening to support the comparative claims.

**Lack of Variance Reporting:**
The primary statistical deficiency is the reporting of benchmark results as single-point percentages without any measure of uncertainty (standard deviation, standard error, or confidence intervals). This is evident in **Table 1 (Pre-training evaluation)**, **Table 4 (Post-training Instruct)**, and **Table 5 (Post-training Thinking)**. For instance, the claim that Mellum2 achieves 59.3% on MMLU-Pro compared to Qwen3.5-4B's 52.4% is presented as a definitive fact. However, without knowing the variance across multiple evaluation runs or seeds, it is impossible to determine if this 6.9 percentage point difference is statistically significant or within the noise margin of the benchmark. This is particularly critical for benchmarks like HumanEval (41.5% vs 45.1%) where the differences are smaller and the pass@k metric inherently has high variance.

**RL Evaluation Methodology:**
In **Section 5 (Post-Training)**, the Reinforcement Learning (RL) results are presented without methodological details regarding statistical stability. The tables show SFT vs. RL improvements (e.g., LiveCodeBench v6 jumping from 30.9% to 37.2% in Instruct mode). The text does not specify:
1. The number of independent training seeds used.
2. Whether the reported scores are averages over multiple inference runs with different sampling temperatures or seeds.
3. The confidence intervals for these improvements.
Given the stochastic nature of RL training and inference, a single run result is insufficient to claim a robust improvement. The "Thinking" variant's performance drop on LiveCodeBench (75.1% to 69.9%) after RL also lacks context on whether this is a statistically significant regression or a fluctuation.

**Throughput Claims:**
In **Section 6 (Efficiency and Deployment)**, the authors claim Mellum2 achieves "21% higher throughput" (20.2 req/s vs 16.7 req/s) compared to Qwen2.5-7B. This is a precise quantitative claim that requires statistical backing. The manuscript does not state the sample size (number of requests processed), the duration of the measurement, or the variance in throughput measurements. Without this, the claim could be influenced by transient system load or measurement noise.

**Recommendations:**
1. Re-run evaluations with multiple seeds (at least 3-5) for all key benchmarks and report mean ± standard deviation.
2. Add confidence intervals (e.g., 95% CI) to the benchmark tables or explicitly state the statistical significance (p-values) of the differences between Mellum2 and baselines.
3. Clarify the inference protocol (temperature, top-p, number of samples) used for generating the reported scores.
4. Provide statistical details (N, variance) for the throughput comparison in Section 6.

Until these statistical details are provided, the comparative claims regarding performance superiority or parity remain scientifically unsupported.
