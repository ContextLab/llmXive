---
action_items:
- id: bbfe96945365
  severity: writing
  text: "Section 5 and Tables 1-4 report single point estimates (e.g., '34% vs 30%')\
    \ without uncertainty measures (SD/SE/CI) across seeds. Deep learning results\
    \ require variance reporting to distinguish signal from noise. Report mean \xB1\
    \ SD over \u22653 seeds or explicitly state results are from a single run."
- id: 3bbd201be286
  severity: writing
  text: The paper claims 'significantly improves' (e.g., Sec 5.2) without reporting
    p-values or hypothesis tests. Statistical significance requires a formal test
    (e.g., paired t-test) and alpha level. Either run the test and report p-values
    or rephrase claims to describe magnitude (e.g., 'improves by X points') without
    invoking significance.
- id: e651f0c94788
  severity: writing
  text: Ablation studies in Sec 5.3 compare multiple configurations without correcting
    for multiple comparisons. Highlighting the 'best' configuration among many tests
    inflates false-positive risk. Apply a correction (e.g., Bonferroni) or explicitly
    acknowledge the uncorrected nature of these comparisons.
artifact_hash: f098ae707662ea7ce696ff8b8606006fdddb80c25be82361ec114d13c9a397ed
artifact_path: projects/PROJ-1037-why-can-t-i-open-my-drawer-mitigating-ob/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-11T04:13:20.839694Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical reporting in this paper lacks the rigor required to substantiate claims of "significant" improvement or to distinguish signal from noise.

First, the paper reports single point estimates for accuracy, FSP, FCP, and Compositional Gap in Section 5 and Tables 1-4 without any measure of uncertainty (standard deviation, standard error, or confidence intervals). In deep learning, where stochasticity can lead to variance of 1-3% or more, a 4-point gap (e.g., 34% vs 30%) from a single run is not statistically distinguishable from random fluctuation. The authors must report results as mean ± standard deviation over at least 3-5 independent seeds to validate the stability of the proposed method.

Second, the term "significantly" is used repeatedly (e.g., "significantly improves unseen composition accuracy") without supporting statistical evidence. No hypothesis tests (e.g., paired t-test, Wilcoxon) or p-values are reported. Without a formal test and a stated alpha level, this terminology is misleading. The authors should either perform these tests and report the results or rephrase their claims to describe the magnitude of the improvement without invoking statistical significance.

Finally, the ablation studies in Section 5.3 involve multiple comparisons across different loss components and hyperparameters. The paper highlights a "best" configuration without addressing the multiple testing problem, which increases the risk of false positives. The authors should apply a correction (e.g., Bonferroni) or explicitly acknowledge this limitation when interpreting the results.
