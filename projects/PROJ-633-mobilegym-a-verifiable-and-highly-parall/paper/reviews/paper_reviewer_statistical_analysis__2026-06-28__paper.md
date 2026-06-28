---
action_items:
- id: 2572145bd96d
  severity: science
  text: "The manuscript reports success rates (SR) and progress rates (PR) for multiple\
    \ models but provides only point estimates and standard deviations from a small\
    \ number of trials (4 for open\u2011source models, 1 for proprietary models).\
    \ Add appropriate statistical significance testing (e.g., paired t\u2011tests\
    \ or non\u2011parametric tests) to support claims of superiority, and report confidence\
    \ intervals for all key metrics."
- id: df1ed371a98b
  severity: science
  text: "Multiple models and multiple difficulty strata are compared simultaneously,\
    \ which raises a multiple\u2011comparisons problem. Apply a correction method\
    \ (e.g., Bonferroni, Holm\u2011\u0160id\xE1k, or false discovery rate) and disclose\
    \ adjusted p\u2011values or confidence intervals."
- id: 819dd9eb4276
  severity: science
  text: "The variance estimates (\xB1 values) are presented without indicating the\
    \ number of runs or the underlying distribution assumptions. Clarify the exact\
    \ number of random seeds per model, provide the raw per\u2011seed results in an\
    \ appendix, and justify the use of mean\u202F\xB1\u202FSD versus median or other\
    \ robust statistics."
- id: 0b4c6fa81de9
  severity: science
  text: "For the Sim\u2011to\u2011Real transfer experiment, the gain is reported as\
    \ a percentage point increase (e.g., +12.8\u202Fpt) without a statistical test\
    \ of whether this uplift is significant given the small sample (59 tasks). Perform\
    \ a hypothesis test (e.g., McNemar\u2019s test for paired binary outcomes) and\
    \ report the corresponding p\u2011value and confidence interval."
- id: e7aac553b92b
  severity: science
  text: "The paper mixes heterogeneous evaluation protocols (AnswerSheet extra budget,\
    \ different step budgets per task) but does not assess whether these protocol\
    \ differences bias the reported metrics. Conduct an ablation or sensitivity analysis\
    \ to quantify the impact of the extra 15\u2011step budget on SR/PR."
- id: 463831a334d2
  severity: science
  text: "The unexpected side\u2011effects (USE) metric is presented as a simple percentage\
    \ without any statistical assessment of its reliability across runs. Provide inter\u2011\
    run reliability statistics (e.g., Cohen\u2019s \u03BA) or confidence intervals\
    \ to demonstrate stability."
- id: 689c6ede2461
  severity: science
  text: "The high\u2011risk subset results are shown as raw percentages without any\
    \ statistical comparison to the full set. Include statistical tests to determine\
    \ whether performance on high\u2011risk tasks differs significantly from overall\
    \ performance."
- id: 97638d8cc2bf
  severity: science
  text: "The VLM\u2011judge error analysis reports counts but does not assess whether\
    \ the error rate differs between base and trained models beyond descriptive numbers.\
    \ Apply a proportion test (e.g., chi\u2011square or Fisher\u2019s exact test)\
    \ and report significance."
- id: 3995b909297d
  severity: science
  text: "Overall, the manuscript lacks a pre\u2011registered analysis plan or power\
    \ analysis to justify the chosen number of tasks, trials, and models. Add a brief\
    \ discussion of statistical power or justify why the current sample sizes are\
    \ sufficient."
artifact_hash: f4cd930b7a9ee408f16628fa968792c28c81dba6a7a2d564441d29e182ecd8b7
artifact_path: projects/PROJ-633-mobilegym-a-verifiable-and-highly-parall/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-28T06:40:38.700344Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: full_revision
---

The statistical evaluation in the paper is insufficiently rigorous for the claims made. While the authors present a rich set of performance numbers (Success Rate, Progress Rate, Unexpected Side Effects, etc.) across nine agents and four difficulty strata, the analysis lacks formal hypothesis testing, confidence intervals, and correction for multiple comparisons.

1. **Insufficient Replication** – Open‑source models are evaluated with only four random seeds, and proprietary models with a single run. This provides an unreliable estimate of variability, especially when differences between models are modest (e.g., 1–2 % SR). The manuscript should increase the number of seeds (ideally ≥10) or, at minimum, report per‑seed results to allow readers to assess variability.

2. **Missing Significance Tests** – Claims such as “Gemini 3.1 Pro separates from all other models on L4” or “training yields a +12.8 pt lift” are presented without statistical tests. Paired tests (t‑test, Wilcoxon signed‑rank) or proportion tests (McNemar’s for paired binary outcomes) are needed to substantiate these statements.

3. **Multiple‑Comparison Issue** – The paper compares many models across four difficulty levels, three objective categories, and several diagnostic metrics. Without adjustment, the risk of false positives is high. A correction method (Bonferroni, Holm‑Šidák, or FDR) should be applied, and adjusted p‑values reported.

4. **Confidence Intervals** – All key percentages (SR, PR, USE, etc.) are reported as point estimates with ± standard deviations, but confidence intervals are absent. Providing 95 % confidence intervals would convey the precision of the estimates and aid interpretation.

5. **Protocol‑Induced Bias** – The AnswerSheet protocol adds a fixed 15‑step budget to query tasks, yet the impact of this extra budget on success rates is not quantified. An ablation that removes the extra budget (or normalizes across tasks) would clarify whether the observed gains are due to the model or to the protocol design.

6. **Reliability of USE Metric** – Unexpected Side Effects are reported as a single percentage per model. No assessment of inter‑run reliability is given. Reporting Cohen’s κ or intraclass correlation across seeds would demonstrate that USE is a stable metric.

7. **High‑Risk Subset Analysis** – The high‑risk subset is presented without statistical comparison to the overall test set. A proportion test could reveal whether models perform significantly worse on high‑risk tasks, which is crucial for safety considerations.

8. **VLM‑Judge Error Audit** – The audit reports raw counts of false positives/negatives but does not test whether the error rates differ between the base and trained models. A chi‑square or Fisher’s exact test would determine if the observed difference (8.5 % vs 11.9 %) is statistically meaningful.

9. **Power and Pre‑registration** – There is no discussion of statistical power or a pre‑registered analysis plan. Given the large number of tasks (256) and models, a brief power analysis would justify the chosen sample sizes and strengthen the methodological rigor.

In summary, the empirical results are promising, but the statistical methodology does not meet the standards required to substantiate the paper’s central claims. Addressing the points above will greatly improve the credibility and reproducibility of the findings.
