---
action_items:
- id: 1116c0963575
  severity: writing
  text: "Tables 1 and 2 report mean success rates to two decimals without SD or CI.\
    \ Report mean \xB1 SD for all 30 policies in the leaderboards to allow assessment\
    \ of ranking significance."
- id: f55a301d514a
  severity: writing
  text: Section 5.1 Finding 2 claims a '92.9% relative drop' without a statistical
    test or standard error. Add a paired test or SE for the difference to support
    the 'collapse' claim.
- id: 25f4df2ec6ad
  severity: science
  text: Table 3 compares throughput on different hardware/process settings. Re-calculate
    speedup against a baseline run on identical 8xRTX 4090 hardware or explicitly
    state the mismatch.
artifact_hash: ea08a1f2032c23dcddfe48c893242879f7f30600dd1ba71197caa7f1b2ba7f13
artifact_path: projects/PROJ-1024-robodojo-a-unified-sim-and-real-benchmar/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-10T03:34:06.452327Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical reporting in the RoboDojo paper is generally transparent regarding the number of seeds and episodes, but it lacks necessary uncertainty quantification for its primary quantitative claims.

**Missing Uncertainty in Leaderboards:**
The core contribution of the paper is the benchmark leaderboard (Tables 1 and 2), which ranks 30 policies. These tables report point estimates (e.g., "8.80% success rate") to two decimal places. In stochastic environments like robot manipulation, a difference of 0.01% is meaningless without a measure of variance. While the authors report standard deviations for a *subset* of policies in Section 5.3 (Stability) and in the appendix tables for specific policies (e.g., `part:pi_05`), the main summary tables do not include standard deviations (SD) or confidence intervals (CI) for the aggregate scores. This prevents readers from determining if the ranking differences (e.g., between 8.80% and 8.04%) are statistically significant or within the noise of the evaluation. The field norm for such benchmarks is to report "Mean ± SD" over the reported seeds.

**Unverified Significance Claims:**
In Section 5.1, Finding 2, the authors state that scene randomization causes a "broad performance collapse," citing a "92.9% relative drop" for one policy. This is a comparative claim derived from a single aggregate number (Standard Score vs. Random Score). Without a reported p-value, standard error of the difference, or a confidence interval for the drop, the claim of a "collapse" is descriptive rather than inferential. Given the large number of episodes (2,100 total), the variance might be low, but the paper must explicitly state the statistical test used (e.g., paired t-test across tasks) to validate that the drop is not a random fluctuation.

**Improper Baseline for Efficiency Claims:**
Table 3 compares the evaluation throughput of RoboDojo against RoboTwin 2.0. The caption notes that RoboDojo runs on "8xRTX 4090" while RoboTwin 2.0 runs on "two simulation processes per GPU" (hardware unspecified, likely different). Comparing raw throughput (interactions/s) across different hardware configurations and process parallelization strategies is a methodological error. The "1.94x speedup" is only valid if the baselines are normalized to the same hardware and process count. As written, the comparison conflates algorithmic efficiency with hardware capability, rendering the quantitative claim of "substantial improvement" unsupported.
