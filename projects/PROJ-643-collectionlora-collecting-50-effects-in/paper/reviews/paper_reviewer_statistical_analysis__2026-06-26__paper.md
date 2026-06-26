---
action_items:
- id: cd3adc3cf8c1
  severity: science
  text: Report confidence intervals or standard deviations for all quantitative metrics
    (CLIP, DreamSim, VSA, BCR) across multiple runs. Single point estimates without
    variance measures are insufficient for statistical claims.
- id: bb1a4bb83bff
  severity: science
  text: Add statistical significance testing (e.g., paired t-tests, bootstrap) when
    comparing methods. Current tables show differences (e.g., CLIP 0.727 vs 0.703)
    without indicating if they are statistically significant.
- id: 705597d3b65b
  severity: science
  text: Address multiple-comparisons problem. With 6+ metrics tested across multiple
    baselines, apply appropriate corrections (e.g., Bonferroni, FDR) or justify why
    they are not needed.
- id: 4d94f7d476dd
  severity: science
  text: Validate MLLM-based metrics (VSA, BCR). Report inter-rater agreement or calibration
    against human evaluation. The current reliance on Qwen-VL-Max-Latest without reliability
    metrics is a statistical weakness.
- id: cb8ade4128a3
  severity: science
  text: Include variance information for user study results (66.2% preference rate).
    Report confidence intervals and statistical tests (e.g., chi-square) for preference
    distributions.
artifact_hash: 2a1b4c65ebf4844ee4cfea5a1931c70997d4322d1755391c095bba4101b76763
artifact_path: projects/PROJ-643-collectionlora-collecting-50-effects-in/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-26T10:47:15.260269Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

**Statistical Analysis Review**

This review focuses exclusively on the statistical rigor of the experimental evaluation and analysis presented in the manuscript.

**Major Concerns:**

1. **Lack of Variance Reporting**: All quantitative results in Tables 1-4 (main.tex, sections/exp.tex) report single point estimates without standard deviations, confidence intervals, or error bars. For example, Table 1 shows CLIP: 0.727, VSA: 4.380, BCR: 0.087 with no indication of measurement uncertainty. This makes it impossible to assess whether observed differences between methods are meaningful or within expected variance.

2. **No Statistical Significance Testing**: When comparing CollectionLoRA against baselines (e.g., CLIP 0.727 vs FM+Lightning 0.703), the paper claims "state-of-the-art" performance without statistical tests. A paired t-test, bootstrap analysis, or at minimum multiple random seed runs with variance reporting is required to support these claims.

3. **Multiple Comparisons Problem**: The study evaluates 6+ metrics (CLIP, DreamSim, DINO, VSA, EditReward, BCR) across 4+ baselines. No correction for multiple hypothesis testing is applied. This inflates Type I error rates and may lead to false positive conclusions about method superiority.

4. **MLLM Metric Validation**: VSA and BCR rely on Qwen-VL-Max-Latest API evaluation (supp.tex, Appendix 7). There is no validation of the MLLM's reliability, inter-rater agreement with human evaluators, or calibration. The user study (10 evaluators, 50 samples) reports preference rates (66.2% for Consistency) without confidence intervals or statistical tests.

5. **Sample Size Justification**: No power analysis or justification is provided for the chosen sample sizes (50 effects, 20 pairs/effect, 5000 test instructions). This is particularly important given the few-shot nature of the task.

**Minor Concerns:**

- Training dynamics figures (Fig. 10) show single curves without variance bands across runs.
- Deployment cost measurements (Table 2) report single latency values without variance across queries.
- The ablation study (Table 3) does not indicate whether component differences are statistically significant.

**Recommendations:**

1. Run experiments with multiple random seeds (≥3) and report mean ± std for all metrics.
2. Add statistical significance tests for key comparisons.
3. Validate MLLM metrics against human evaluation with correlation analysis.
4. Report confidence intervals for user study preference rates.
5. Address multiple comparisons in the statistical analysis section.

These revisions are necessary to establish the statistical validity of the paper's claims.
