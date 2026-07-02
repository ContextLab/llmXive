---
action_items:
- id: 165fed85d809
  severity: science
  text: Report standard deviations or confidence intervals for all quantitative results
    in Tables 2, 4, 5, and 6. The current tables present single-point averages (e.g.,
    GEditBench Avg) without indicating variance across seeds or runs, making it impossible
    to assess statistical significance of the reported improvements (e.g., the 8.1%
    gain over DiffusionOPD).
- id: 7e9522198860
  severity: science
  text: Clarify the number of random seeds used for all experiments. The text mentions
    'reproduced baselines' and 'diagnostic studies' but does not specify if the reported
    metrics are means over multiple independent runs or single runs. Without this,
    the robustness of the 'single-query' vs 'dense-query' conclusions cannot be statistically
    verified.
- id: fa1ccf2fd13c
  severity: science
  text: In Section 4.2 (Multi-Teacher Extension), the claim that 'same-step accumulation...
    loses 4.6% on average' lacks a statistical test. Please provide p-values or effect
    sizes to confirm that the observed degradation is statistically significant and
    not due to random variance in the evaluation metrics.
artifact_hash: 345c406695aa2dde1374386d01dde68941ce2b695d941d4807a3dc21f8ee698f
artifact_path: projects/PROJ-797-danceopd-on-policy-generative-field-dist/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T15:42:19.671236Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical reporting in the experimental section requires significant strengthening to support the paper's quantitative claims. While the experimental design (ablation of routing, query density, and objectives) is logically sound, the presentation of results lacks the necessary statistical rigor to validate the reported improvements.

**1. Lack of Variance Reporting:**
Throughout Section 4 and Tables 2, 4, 5, and 6, results are presented as single-point averages (e.g., "GEditBench average over the best reproduced OPD baseline by 8.1%"). There is no mention of standard deviation, standard error, or confidence intervals. In generative modeling, metrics like GEditBench and GenEval can exhibit variance depending on the random seed used for the evaluation set or the generation process itself. Without error bars or variance metrics, it is impossible to determine if the reported gains (e.g., the 16.1% improvement in local/global edit composition) are statistically significant or within the noise floor of the evaluation protocol.

**2. Missing Replication Details:**
The manuscript does not explicitly state the number of random seeds used for training or evaluation. For instance, in Section 4.3 (Ablation Study), the comparison between "Low-t" and "Median-t" queries shows a 23.7% difference. Without knowing if these results are averaged over multiple seeds (e.g., 3, 5, or 10) or represent a single run, the reliability of the "semantic-side single query" conclusion is compromised. The authors should explicitly state the number of seeds and report the mean ± standard deviation for all key metrics.

**3. Statistical Significance of Claims:**
In Section 4.2, the paper claims that "same-step accumulation... loses 4.6% on average" and that "dense-query... drops by 22.8%." These are strong claims about the failure modes of specific design choices. To support these, the authors should perform statistical significance testing (e.g., paired t-tests or Wilcoxon signed-rank tests) comparing the proposed method against the ablated variants. The current text relies solely on the magnitude of the difference, which is insufficient for a rigorous statistical analysis.

**4. Evaluation Protocol Consistency:**
While the evaluation metrics (GEditBench, GenEval) are standard, the statistical stability of these benchmarks is not discussed. If the evaluation set is small or the metric is sensitive to specific prompt variations, the reported "averages" might be unstable. The authors should clarify if the evaluation sets were fixed across all runs or if they were resampled, and how this impacts the variance of the reported scores.

In summary, the paper needs to include variance metrics (std dev/CI) for all tables, specify the number of random seeds used, and provide statistical tests for the key comparative claims to ensure the conclusions are robust.
