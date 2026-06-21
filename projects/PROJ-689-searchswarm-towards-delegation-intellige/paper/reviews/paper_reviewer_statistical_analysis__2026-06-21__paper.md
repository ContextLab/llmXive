---
action_items:
- id: 24ff9eca610f
  severity: science
  text: The manuscript reports point estimates (e.g., 68.1 on BrowseComp) without
    any measure of variability (standard deviation, confidence interval, or error
    bars). This makes it impossible to assess whether observed differences between
    SearchSwarm and baselines are statistically significant.
- id: a4d719e63818
  severity: science
  text: "No statistical hypothesis tests (e.g., paired t\u2011test, Wilcoxon signed\u2011\
    rank) are performed to support claims of superiority over other models, despite\
    \ multiple benchmark comparisons. The risk of Type\u202FI error due to multiple\
    \ comparisons is not addressed."
- id: 82708f07009f
  severity: science
  text: "The experimental setup lacks details on random seed handling, number of training\
    \ runs, and whether results are averaged over multiple fine\u2011tuning runs.\
    \ Reproducibility of the reported scores cannot be verified."
- id: baf181e69bb9
  severity: science
  text: "The paper does not disclose the size of the evaluation sets (e.g., number\
    \ of questions per benchmark) for each metric, nor does it provide per\u2011question\
    \ score distributions. This omission hampers assessment of statistical power."
- id: aa3ae2333638
  severity: science
  text: "Hyper\u2011parameter choices (learning rate schedule, batch size, temperature,\
    \ top\u2011p) are listed, but there is no justification or sensitivity analysis\
    \ to show robustness of the results to these settings."
- id: 109038f7294b
  severity: science
  text: "When reporting ablation results (e.g., +10.0 gain from full harness), the\
    \ authors present a single aggregate number without indicating variance or statistical\
    \ testing, making the claim of a \u2018gain\u2019 ambiguous."
- id: 236f72ea5cc8
  severity: science
  text: "The paper uses a single judge model (DeepSeek\u2011V4\u2011Flash) for all\
    \ benchmark evaluations without discussing inter\u2011judge agreement or potential\
    \ bias, and does not provide inter\u2011rater reliability metrics."
artifact_hash: 23164a835e9fc14f10b36f04bd2aeba4213e5a3b759192c46a449dbfe25b61f3
artifact_path: projects/PROJ-689-searchswarm-towards-delegation-intellige/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-21T09:49:33.942527Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: full_revision
---

The statistical evaluation in the manuscript is insufficient for the claims made. All benchmark results are presented as single point scores (e.g., 68.1 on BrowseComp, 73.3 on BrowseComp‑ZH) with no accompanying variance estimates, confidence intervals, or significance testing. Given the large number of baselines (both closed‑source and open‑source) across four primary benchmarks and additional open‑ended tasks, the probability of observing apparent improvements by chance is non‑trivial. The authors should report either standard deviations over multiple runs or bootstrap confidence intervals for each metric, and conduct appropriate hypothesis tests (e.g., paired tests) to substantiate claims of superiority. Moreover, multiple‑comparison correction (e.g., Bonferroni or Holm) should be applied when drawing conclusions from many pairwise comparisons.

Reproducibility is also unclear. The paper mentions a learning‑rate schedule and other hyper‑parameters but does not specify random seeds, the number of fine‑tuning repetitions, or whether results are averaged. Providing these details, along with a sensitivity analysis of key hyper‑parameters (learning rate, batch size, temperature, top‑p), would strengthen confidence in the robustness of the findings.

The evaluation relies on a single judge model (DeepSeek‑V4‑Flash) without any discussion of inter‑judge reliability or potential systematic bias. Including inter‑rater agreement metrics or using multiple judges would mitigate this concern.

Finally, the ablation study reports a “+10.0 gain” from the full harness but again lacks variance or statistical testing, leaving the magnitude of the effect ambiguous. Adding error bars or statistical significance testing for ablation results is essential.

Addressing these statistical and reproducibility issues is necessary before the paper can be accepted.
