---
action_items:
- id: 0b7cbf22b60c
  severity: science
  text: "The paper reports mean scores for persona\u2011alignment and quality metrics\
    \ but provides no confidence intervals or standard deviations, making it impossible\
    \ to assess the statistical reliability of the reported differences."
- id: b49ad7912c31
  severity: science
  text: "No statistical significance testing (e.g., paired t\u2011tests, Wilcoxon\
    \ signed\u2011rank tests) is reported for the comparisons between MemSlides and\
    \ baselines, despite multiple metrics and model families being evaluated; this\
    \ raises the risk of false positives due to multiple comparisons."
- id: 349d7e274670
  severity: science
  text: "The diagnostic matched\u2011pair tool\u2011memory evaluation aggregates results\
    \ across nine pairs, yet the paper does not correct for the multiple hypothesis\
    \ tests performed (e.g., Bonferroni or Holm correction), nor does it report effect\
    \ sizes."
- id: 6d7e3a89cb49
  severity: science
  text: Assumptions underlying the use of arithmetic and geometric means (e.g., normality,
    independence) are not justified, especially for metrics like Core Tool Time Ratio
    that are ratios of skewed timing data.
- id: adfdebb6b047
  severity: science
  text: "Reproducibility of the statistical analysis is limited: the code for computing\
    \ the paired\u2011robustness sign test, the exact formulas for the geometric mean\
    \ of time ratios, and the random seed settings are not released."
- id: 27ca2f6b2c64
  severity: writing
  text: "The paper mixes different scales (0\u201110 judges, 1\u20115 quality scores,\
    \ raw seconds) in a single table without normalizing or providing variance estimates,\
    \ which can mislead readers about the relative magnitude of improvements."
artifact_hash: d44b33b66588093736bc35436b4297f50da94321f7a3c7c12e6ba0ea57e820cd
artifact_path: projects/PROJ-768-memslides-a-hierarchical-memory-driven-a/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-23T10:19:41.081037Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript presents several quantitative evaluations (persona‑alignment judgments, DeepPresenter‑style quality scores, and tool‑memory process metrics) but the statistical treatment of these results is insufficient for a rigorous claim of improvement. First, all reported scores are presented as point estimates (means) without any measure of dispersion (standard deviation, standard error, or confidence interval). Given the small sample sizes for some evaluations (e.g., nine matched pairs for tool‑memory), the variability could be substantial; confidence intervals would allow readers to judge whether observed differences are statistically meaningful.

Second, the paper does not perform any hypothesis testing to support the claim that MemSlides outperforms baselines. For the persona‑alignment table, multiple models (GPT‑5, GLM‑5, Gemini 3.1 Pro) and four dimensions are compared simultaneously. Without paired statistical tests (e.g., paired t‑test or non‑parametric alternatives) and correction for multiple comparisons, the risk of Type I error is high. The same issue applies to the quality‑evaluation table, where six scores are compared across three systems.

Third, the tool‑memory analysis includes a sign test on win/loss counts, but the manuscript omits the exact p‑values for the “directional” metrics (Closed‑Loop Completion, First Correct Edit) and does not report effect sizes (e.g., odds ratios). Moreover, the sign test assumes independence of pairs, an assumption that may be violated if the same model or persona appears in multiple pairs.

Fourth, the use of arithmetic means for time‑based metrics and a geometric mean for the Core Tool Time Ratio presumes underlying distributions that are approximately symmetric and independent. Timing data are typically right‑skewed; a log‑transformation or non‑parametric summary would be more appropriate, and the paper should justify the chosen aggregation method.

Finally, reproducibility of the statistical analysis is limited. The manuscript mentions that “selected evaluation artifacts will be released when documentation and licensing checks are finalized,” but the scripts for computing the paired robustness checks, the exact formulas for the geometric mean ratios, and the random seeds for any stochastic components are not provided. Sharing these details (e.g., a Jupyter notebook) would enable independent verification and foster confidence in the reported gains.

In summary, the experimental results are promising, but the statistical analysis needs to be expanded: include variance estimates, perform appropriate significance testing with multiple‑comparison corrections, justify aggregation choices, and release the analysis code. Addressing these points will substantially strengthen the evidential basis of the paper.
