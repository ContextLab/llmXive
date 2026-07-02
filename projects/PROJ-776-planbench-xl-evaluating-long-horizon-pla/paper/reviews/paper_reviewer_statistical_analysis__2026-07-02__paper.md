---
action_items:
- id: 8ce176706c5e
  severity: science
  text: Report confidence intervals or standard errors for the Pearson correlation
    coefficients (r=0.902, 0.800, 0.781, -0.443) in Section 4.2. With N=10 models,
    these point estimates lack precision metrics, making it difficult to assess the
    statistical significance of the claimed 'strong' relationships.
- id: 0b6dd70954d2
  severity: writing
  text: Clarify the statistical unit of analysis for the error category percentages
    (e.g., 72.4% Irrecoverable Drift). Are these proportions calculated over the total
    number of failed trajectories or the total number of tool calls? The denominator
    must be explicit to interpret the magnitude of the failure modes correctly.
- id: 0f0602912a32
  severity: science
  text: The claim that accuracy drops 'sharply' under blocking (Section 5) relies
    on visual inspection of Figure 5. Provide a formal statistical test (e.g., paired
    t-test or Wilcoxon signed-rank) comparing the no-block vs. block accuracies for
    each model to substantiate the significance of the performance degradation beyond
    the reported confidence intervals.
artifact_hash: 0fb9253adef42dcbc903c972875abcf8435cbde0a29a43054fe5430b0edd419c
artifact_path: projects/PROJ-776-planbench-xl-evaluating-long-horizon-pla/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T13:35:08.406936Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis in this paper is generally robust in its use of bootstrapping for confidence intervals (Table 1, 10,000 iterations), which appropriately addresses the uncertainty in the primary accuracy metrics given the sample size of N=327 tasks. However, several secondary statistical claims require further rigor to support the paper's conclusions.

First, in Section 4.2, the authors report Pearson correlation coefficients between model performance and various behavioral metrics (e.g., $r=0.902$ between Mean EDT and Accuracy). These correlations are computed over only $N=10$ data points (the ten evaluated models). While the coefficients are high, the paper does not report confidence intervals, p-values, or standard errors for these correlations. With such a small sample size, the point estimates are highly volatile, and the claim that these relationships are "strong" lacks statistical precision. The authors should either provide the confidence intervals for these correlations or temper the language to reflect the exploratory nature of these findings.

Second, the error analysis in Section 6.2 presents detailed percentages for failure categories (e.g., "Irrecoverable Drift accounts for 72.4% of reported failure categories"). The statistical unit of analysis is ambiguous. It is unclear if these percentages are calculated over the total number of *failed trajectories* or the total number of *tool calls* within those trajectories. If the latter, the independence assumption of the data points is violated, potentially inflating the apparent prevalence of certain error types. The denominator for these proportions must be explicitly stated to ensure correct interpretation.

Finally, while the paper uses confidence intervals to show the spread of accuracy scores, it relies on visual inspection to claim that performance drops "sharply" under blocking conditions (Section 5, Figure 5). To strengthen the claim that blocking causes a statistically significant degradation in performance, the authors should perform a formal hypothesis test (e.g., a paired t-test or Wilcoxon signed-rank test) comparing the no-block and block accuracies for each model. The current presentation of confidence intervals for the means does not directly test the difference between the two conditions.
