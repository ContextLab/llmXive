---
action_items:
- id: 27ef6139b4a3
  severity: science
  text: "Provide statistical significance testing (e.g., paired t\u2011tests or bootstrap\
    \ confidence intervals) for the reported improvements over baselines in Tables\u202F\
    1\u20114, and report corresponding p\u2011values or confidence intervals."
- id: 14aaa9595f13
  severity: science
  text: "Address the multiple\u2011comparisons problem arising from evaluating many\
    \ task categories (Pick, Look, Clean, etc.) by applying a correction method (e.g.,\
    \ Bonferroni or Holm) or clearly stating that each metric is considered independently."
- id: eb9faa496a4f
  severity: writing
  text: "Include a more detailed description of the random seed handling and the exact\
    \ number of runs for each experiment; the current statement of \u201Cthree runs\u201D\
    \ (Table\u202F9) should be accompanied by variance estimates and reproducibility\
    \ instructions."
- id: 6e14d05d4d17
  severity: science
  text: "Report effect sizes (e.g., Cohen\u2019s d) for key comparisons such as Role\u2011\
    Agent vs. GiGPO to quantify the practical magnitude of gains beyond raw percentages."
- id: ce710aee326d
  severity: science
  text: "Clarify the computation of the predictive reward correlation (point\u2011\
    biserial r\u202F=\u202F0.41) by providing the sample size, confidence interval,\
    \ and a hypothesis test to assess whether this relationship is statistically robust."
artifact_hash: 3eaf93f21c39f248e829c853cd8d9efc8318a737e9dbae23f33fdd68c6c59724
artifact_path: projects/PROJ-691-role-agent-bootstrapping-llm-agents-via/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-17T00:45:44.071605Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript presents a novel dual‑role framework (World‑In‑Agent and Agent‑In‑World) and reports extensive empirical results across ALFWorld, WebShop, and several QA benchmarks. While the experimental tables are thorough, the statistical analysis lacks rigor in several respects.

First, improvements over strong baselines (e.g., Role‑Agent’s 90.9 % vs. GiGPO’s 86.7 % on ALFWorld) are presented as raw percentages without any significance testing or confidence intervals. Given the modest absolute differences and the variability observed in Table 9 (±0.8 % for Role‑Agent), it is unclear whether these gains are statistically reliable. The paper should incorporate appropriate hypothesis tests (paired t‑tests, Wilcoxon signed‑rank, or bootstrap methods) and report p‑values or 95 % confidence intervals for each comparison.

Second, the evaluation spans many task sub‑categories (Pick, Look, Clean, etc.) and multiple datasets. Conducting multiple pairwise comparisons inflates the family‑wise error rate. The authors should either apply a correction (Bonferroni, Holm, or false discovery rate) or explicitly justify why each metric is treated independently. Without this, the risk of false‑positive claims increases.

Third, reproducibility details are insufficient. The manuscript mentions “three runs” for stability (Table 9) but does not specify the random seeds, exact number of episodes per run, or whether the same seeds were used across baselines. Providing seed values, the total number of rollouts, and a clear description of variance estimation would enable independent verification.

Fourth, effect sizes are absent. Reporting Cohen’s d or similar metrics for the primary comparisons would help readers assess practical significance, especially when percentage differences are small (e.g., 0.1 % on some tasks).

Finally, the correlation between predictive reward and outcome reward (r = 0.41, p < 0.01) is reported without sample size, confidence interval, or a test of the null hypothesis. Supplying these details would strengthen the claim that predictive reward is a meaningful auxiliary signal.

Overall, the experimental design is promising, but the statistical reporting must be strengthened to support the claimed advantages. Addressing the points above will improve the scientific robustness of the work.
