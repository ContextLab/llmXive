---
action_items:
- id: edab0ff6d74f
  severity: science
  text: Clarify training data for baseline models in Table 1. Section 6.1 states Domino
    uses 'mlabonne/open-perfectblend', but Table 1 baselines use public checkpoints
    (Table 1 Appendix) likely trained on different data. This confounds architectural
    gains with data quality.
- id: 17474253db23
  severity: science
  text: Report statistical variance (std dev) for latency and speedup metrics. Inference
    speed varies by system noise; single-point estimates lack robustness evidence.
- id: 4280f8ca4bfa
  severity: science
  text: Align ablation data with main results. Section 6.3 ablation uses ShareGPT,
    while main results (Section 6.1) use PerfectBlend. Ensure ablation controls match
    the main experimental setup to validate claims.
artifact_hash: ac9b2293924c2f0c1f04178796bb698ee01d07baef5d80d5250c3c91d8a5b9a5
artifact_path: projects/PROJ-654-https-arxiv-org-abs-2605-29707/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-15T00:59:46.213479Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The scientific evidence supporting Domino’s performance claims is generally strong but contains significant confounding variables regarding training data and statistical robustness.

**Training Data Confounding:** Section 6.1 states Domino is trained on `mlabonne/open-perfectblend` (1.42M samples). However, Table 1 (main results) baselines (EAGLE-3, DFlash, DART) use public checkpoints listed in Table `baseline_checkpoints.tex`. These public checkpoints are typically trained on different datasets (e.g., ShareGPT, Alpaca) than Domino. Since draft model quality is highly sensitive to training data distribution, the reported speedup gains may reflect data advantages rather than architectural improvements. Section 6.3 attempts to control this by using ShareGPT for all methods in the ablation (Table `same_data_abl.tex`), but this contradicts the main experimental setup description. To validate the central claim, the main comparison must ensure all baselines are retrained on the same dataset as Domino, or the data discrepancy must be explicitly addressed.

**Statistical Robustness:** The paper reports single-point latency and speedup metrics (e.g., 5.49x speedup in Table 1) without standard deviations or confidence intervals. Inference latency on GPUs is subject to system noise (e.g., kernel launch overhead, memory bandwidth variance). Without error bars or multiple runs, it is difficult to assess if the marginal gains over DFlash (e.g., 5.49x vs 4.66x on Qwen3-8B) are statistically significant or within measurement noise.

**Metric Consistency:** The abstract claims "up to 5.8x throughput speedup under SGLang." Table `high_concurrency.tex` provides throughput data, but the "Avg" speedup calculation method differs from Table 1’s end-to-end speedup. This inconsistency makes it hard to verify if the "up to" claims are representative or cherry-picked best-case scenarios.

To strengthen the evidence, the authors should retrain baselines on the exact training data used for Domino, report variance across multiple runs for latency metrics, and ensure the ablation study reflects the main experimental configuration.
