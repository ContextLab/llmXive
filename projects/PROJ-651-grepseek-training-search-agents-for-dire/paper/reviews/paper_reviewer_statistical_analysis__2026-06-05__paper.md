---
action_items:
- id: d85b8152e000
  severity: science
  text: Report confidence intervals or standard deviations for all F1/EM scores across
    multiple independent runs. Current tables show point estimates only (e.g., Table
    1 F1 scores like 0.5223, 0.7673) without uncertainty measures.
- id: 0186ae9a4e50
  severity: science
  text: Clarify multiple-comparisons correction methodology. Bonferroni is mentioned
    for EM ablation (Table 2 caption) but not for main F1 results (Table 1). Testing
    across 7 datasets with 4+ methods inflates Type I error risk.
- id: eeb13e696586
  severity: writing
  text: Add error bands to training dynamics figure (Figure 4). Curves showing mean
    reward, response length, and search queries over 200 GRPO steps lack variance
    visualization.
- id: 9550b991affa
  severity: science
  text: Document random seeds, number of independent runs, and stratification strategy
    for the 10k-sample cold-start dataset generation. This affects reproducibility
    of SFT initialization results.
artifact_hash: 5d85c06c69d8e12a9cf2281b0d8f94964a15c102cc7625c442c21ea4362e7831
artifact_path: projects/PROJ-651-grepseek-training-search-agents-for-dire/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-05T19:00:43.713443Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

## Statistical Analysis Review

### Strengths
The paper employs appropriate statistical tests for its evaluation design. McNemar's test is correctly chosen for paired binary exact-match outcomes (Table 1 and 2 captions, Section 5.2). The evaluation corpus is substantial (51,713 queries across 7 benchmarks, Appendix Table 1), providing adequate statistical power for detecting meaningful differences.

### Critical Concerns

**1. Missing Uncertainty Quantification** (Section 5, Tables 1-2)
All reported F1 and EM scores are point estimates without variance measures. For example, the main method achieves 0.5223 F1 on NQ and 0.7673 on TriviaQA (Table 1), but readers cannot assess whether these improvements over baselines are stable or due to random variation. Standard practice requires either standard deviation across multiple independent runs (recommended: ≥3 runs with different seeds) or confidence intervals (e.g., 95% CI). The EM ablation table similarly lacks variance reporting.

**2. Multiple Comparisons Not Fully Addressed** (Section 5.2)
The paper conducts significance testing across 7 datasets with multiple baseline comparisons. While Bonferroni correction is mentioned for EM ablation (Table 2 caption), it is unclear whether the main F1 results (Table 1) apply similar correction. With 7 datasets × 3+ baseline comparisons = 21+ hypothesis tests, the nominal p < 0.05 threshold inflates Type I error. A clear statement of correction methodology for all significance claims is required.

**3. Training Dynamics Lack Variance Visualization** (Figure 4)
The training curves show mean reward, response length, and search queries over 200 GRPO steps but omit error bands. This obscures whether observed trends (e.g., command reduction from 3.06 to 2.56 in Table 3) are consistent across training instances or artifacts of single-run behavior.

**4. Reproducibility Gaps** (Appendix A, Tables)
The 10,000-sample cold-start dataset generation (Algorithm 1, Table hyperparameters) lacks documentation of random seed initialization, stratification strategy across train/evaluation splits, and whether SFT/RL training was repeated with different seeds. Without these details, the reported performance gains cannot be independently verified.

### Recommendations
1. Add standard deviation or 95% confidence intervals to all performance tables
2. Specify multiple-comparisons correction for all significance claims (FDR or Bonferroni)
3. Include error bands in training dynamics figure
4. Document random seeds and number of independent runs in appendix

These additions are essential for establishing the reliability of the reported improvements and meeting publication standards for statistical rigor.
