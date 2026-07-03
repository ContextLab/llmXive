---
action_items:
- id: 1942ff28f813
  severity: science
  text: Report statistical significance (e.g., p-values, confidence intervals, or
    standard deviations over multiple seeds) for the performance gains in Table 2
    and Table 3. Single-run point estimates are insufficient to claim 'state-of-the-art'
    or 'significant' improvements over baselines like VideoAuto-R1.
- id: 6ccc96e19e66
  severity: science
  text: Clarify the statistical methodology for the benchmark difficulty claim in
    Section 1. The assertion that 'single-frame probing fails for all three frontier
    models' requires a formal hypothesis test or a clear definition of the failure
    threshold (e.g., accuracy < 30%) and the sample size used to derive this conclusion.
- id: 14e9d088999a
  severity: science
  text: In Table 1 (Ablation Studies), the use of single-point accuracy scores without
    error bars or variance metrics makes it impossible to assess the stability of
    the 'Skill-Oriented Data Composition' findings. Please provide results averaged
    over at least 3 random seeds with standard deviations.
artifact_hash: 442b60f42997ea4620ca51b6cec07f843dd48ca52b119472ba764f9d3b1bfbac
artifact_path: projects/PROJ-667-https-arxiv-org-abs-2606-05259/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T18:03:25.116073Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript presents a large-scale dataset and benchmark for knowledge-intensive video understanding, but the statistical rigor of the reported results is insufficient to support the strong claims of state-of-the-art performance.

**Lack of Variance and Significance Testing:**
The primary results in Table 2 (Benchmark results) and Table 3 (Ablation Studies) report single-point accuracy percentages (e.g., "46.6" vs "44.3"). In deep learning research, particularly with reinforcement learning (RL) and fine-tuning, performance can vary significantly based on random seeds, hyperparameter initialization, and data shuffling. Without reporting standard deviations (e.g., 46.6 ± 0.5) or conducting statistical significance tests (e.g., paired t-tests or bootstrap confidence intervals), it is statistically unsound to claim that VideoKR is "state-of-the-art" or that specific ablation components yield "significant" improvements. The observed margins (e.g., +1.4% or +0.5%) are often within the noise floor of a single run. The authors must re-run experiments with multiple seeds (n ≥ 3) and report mean ± std dev to validate these claims.

**Benchmark Difficulty Validation:**
In the Introduction, the authors claim the proposed benchmark (\eval) is filtered such that "single-frame probing fails for all three frontier models." This is a strong statistical claim about the distribution of difficulty. The manuscript does not provide the statistical evidence for this filtering process. How many samples were tested? What was the exact accuracy distribution of the three models (Claude-4.5, Qwen3, GPT-5) on the unfiltered set versus the filtered set? A formal hypothesis test or a clear reporting of the accuracy distribution (e.g., "mean accuracy < 35% with p < 0.01") is required to substantiate that the benchmark genuinely requires video reasoning rather than just being a hard subset of a general benchmark.

**Ablation Stability:**
Table 3 presents ablation studies on data composition and supervision format. The differences between "VR + KV" and "VR + KV + KVR" are marginal (e.g., 41.3 vs 42.4 on the Knowledge-Intensive average). Without variance estimates, it is unclear if these gains are reproducible or artifacts of a specific random seed. The conclusion that the full pipeline is necessary relies on these small, unverified deltas.

**Reproducibility of Analysis:**
While the code is hosted externally (as noted in the guidelines), the statistical analysis scripts (e.g., for calculating significance or aggregating seeds) are not described. The paper should explicitly state the number of seeds used for the main results and the statistical tests employed to compare models.

In summary, the paper requires a re-analysis of the experimental results to include measures of variance and statistical significance before the claims of superiority can be accepted.
