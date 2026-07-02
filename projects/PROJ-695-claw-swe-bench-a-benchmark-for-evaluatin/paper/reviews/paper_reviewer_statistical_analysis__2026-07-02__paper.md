---
action_items:
- id: 5c4bdd2e3b28
  severity: science
  text: Report confidence intervals or standard errors for Pass@1 metrics. The paper
    claims harness choice changes Pass@1 by 12.5pp and 27.4pp (Section 5.4), but without
    variance estimates (e.g., from bootstrapping or multiple seeds), the statistical
    significance of these differences cannot be assessed.
- id: 2f5499bad696
  severity: science
  text: Address the lack of multiple-seed replication. The authors acknowledge in
    the Discussion (Section 7) that single-run aggregates limit the stability of small
    differences. The statistical analysis section must explicitly state that p-values
    or significance tests are not applicable due to N=1 per configuration, or provide
    a plan for variance estimation.
- id: eaa6aeb0b4a8
  severity: science
  text: Clarify the statistical basis for the Lite-80 subset selection. Section 4.2
    describes an optimization loss (L1, ranking hinge) but does not provide a statistical
    power analysis or a formal test (e.g., equivalence testing) to justify that the
    0.4pp difference is statistically indistinguishable from zero rather than just
    numerically small.
artifact_hash: 4cbc990cab4c872e8fedf7a60e18736892d8e224cc636e696339b1c9414fd4ed
artifact_path: projects/PROJ-695-claw-swe-bench-a-benchmark-for-evaluatin/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T22:11:45.419724Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript presents a comprehensive benchmark for evaluating agent harnesses, but the statistical analysis of the results requires strengthening to support the quantitative claims made.

**1. Absence of Variance Estimates and Significance Testing**
The core findings rely on comparing Pass@1 rates across different models and harnesses. For instance, Section 5.4 states that "harness choice changes Pass@1 by 12.5 pp (GLM 5.1) and 27.4 pp (Qwen 3.6-flash)." These are point estimates derived from a single run per instance (N=350). Without reporting confidence intervals (CIs) or standard errors, it is impossible to determine if these differences are statistically significant or if they could arise from random variance in the task difficulty distribution. Given the binary nature of the outcome (resolved/not resolved), the standard error for a proportion $p$ is $\sqrt{p(1-p)/n}$. For $p \approx 0.7$ and $n=350$, the standard error is roughly 2.4%. A difference of 12.5pp is likely significant, but a difference of 3-4pp (as seen in the Lite validation) is not. The authors should calculate and report 95% CIs for all Pass@1 metrics in Tables 1, 2, and 3.

**2. Single-Run Limitations**
The Discussion (Section 7) correctly identifies that "single-run aggregates" are a limitation and that "differences of only a few percentage points should not be overinterpreted." However, the Results section presents these single-run aggregates as definitive facts without qualifying the uncertainty. The statistical analysis section (or the Results introduction) must explicitly state that the reported metrics are point estimates with unknown variance due to the lack of multiple seeds. If the authors cannot re-run experiments with multiple seeds, they must frame the results as "observed differences in this specific run" rather than generalizable performance gaps, or perform a bootstrap analysis on the instance-level outcomes to estimate the variance of the aggregate metric.

**3. Statistical Justification for Lite-80 Subset**
Section 4.2 describes the selection of the Lite-80 subset using an optimization objective (minimizing L1 difference, ranking hinge, etc.). While the resulting mean difference is small (0.4 pp), the paper lacks a formal statistical test to validate the claim that the subset is representative. A simple mean difference does not prove equivalence. The authors should perform an equivalence test (e.g., Two One-Sided Tests, TOST) or report the 95% CI of the difference between the full and lite sets to demonstrate that the difference falls within a pre-defined equivalence margin (e.g., $\pm 2\%$). Currently, the claim that Lite-80 "approximates full-350 behavior" is supported only by point estimates, not statistical evidence.

**4. Multiple Comparisons**
The paper reports results for 9 models and 5 harnesses across multiple metrics (Pass@1, Cost, Duration). While the primary focus is on Pass@1, the sheer number of comparisons increases the risk of Type I errors if any hypothesis testing were performed. Since the authors are currently reporting descriptive statistics, this is less critical, but if they proceed to claim "Model X is significantly better than Model Y," they must apply a correction for multiple comparisons (e.g., Bonferroni or Benjamini-Hochberg) to the p-values.

In summary, the experimental design is sound, but the statistical reporting is insufficient for a benchmark paper intended to establish new standards. The addition of confidence intervals and a more rigorous discussion of the single-run variance is required.
