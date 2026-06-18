---
action_items:
- id: 9a865aa34a39
  severity: science
  text: "The manuscript reports point estimates (e.g., +2.4\u202F% step accuracy)\
    \ without any measure of variability (standard deviation, confidence interval)\
    \ or statistical significance testing. Add appropriate statistical analyses (e.g.,\
    \ paired bootstrap, t\u2011tests) to demonstrate that observed gains are not due\
    \ to random variation."
- id: 72575b162e7c
  severity: science
  text: "Multiple models, agents, and benchmark subsets are evaluated, leading to\
    \ a large number of comparisons. Apply a multiple\u2011comparison correction (e.g.,\
    \ Bonferroni, Holm\u2011\u0160id\xE1k, or false discovery rate) and report adjusted\
    \ p\u2011values or confidence intervals."
- id: 1aac366a6b1e
  severity: writing
  text: 'Provide details on experimental reproducibility: number of random seeds,
    seed values, hardware configuration, and any stochastic components (e.g., temperature
    settings, sampling). Include this information in the appendix or a reproducibility
    checklist.'
- id: 69b5ec448e90
  severity: science
  text: "Report variance or distribution of performance metrics across runs (e.g.,\
    \ mean\u202F\xB1\u202FSD) for each model/agent combination. If only a single run\
    \ was performed, justify why and discuss the potential impact on result reliability."
- id: 36e57ecb611e
  severity: science
  text: "Clarify the statistical assumptions underlying any reported metrics (e.g.,\
    \ independence of chain steps, normality of accuracy distributions) and verify\
    \ that they hold, or choose non\u2011parametric alternatives."
artifact_hash: 6cdb16771eea5c1aa0e0ff5e854ffcdbbe5d0a407e5c9d421612d453db08e7c6
artifact_path: projects/PROJ-703-evoarena-tracking-memory-evolution-for-r/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-18T18:54:11.521568Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The paper introduces EvoArena and the EvoMem memory augmentation, presenting many percentage improvements across three benchmark subsets and two standard benchmarks. However, from a statistical standpoint the manuscript lacks essential quantitative rigor:

1. **Absence of variability estimates** – All results are reported as single point percentages (e.g., “+2.4 % step accuracy”) with no standard deviations, confidence intervals, or error bars. Given the modest magnitude of many gains, it is impossible to assess whether they are statistically meaningful.

2. **No significance testing** – The authors never conduct hypothesis tests (e.g., paired t‑tests, Wilcoxon signed‑rank) to determine if the EvoMem enhancements differ from baselines beyond chance. This omission undermines the credibility of claims such as “consistent improvements” across agents.

3. **Multiple‑comparison problem** – The experiments span eight models, four agents, three EvoArena subsets, and two external benchmarks, yielding dozens of pairwise comparisons. Without correction, the risk of false positives is high. The manuscript should adopt a family‑wise error control or false discovery rate approach and report adjusted significance levels.

4. **Reproducibility details are sparse** – While code repositories are cited, the paper does not disclose random seeds, number of evaluation runs, or hardware specifications. Since many LLM evaluations are stochastic (temperature settings, sampling), these details are crucial for replication.

5. **Model‑assumption checks are missing** – Accuracy percentages are treated as if they follow a normal distribution, yet the underlying data (binary success/failure per step) are Bernoulli. Appropriate binomial proportion confidence intervals or non‑parametric methods should be used, and the independence of chain steps should be justified.

6. **Efficiency analysis lacks statistical framing** – Figure 7 compares token usage versus accuracy, but no statistical analysis (e.g., regression with confidence bands) is provided to support the observed trends.

To strengthen the statistical foundation, the authors should (i) run each experiment multiple times (e.g., 5–10 seeds), (ii) report mean ± SD or 95 % confidence intervals, (iii) perform hypothesis testing with proper multiple‑comparison adjustments, and (iv) document all stochastic settings. These additions will make the reported gains robust and the paper’s conclusions defensible.
