---
action_items:
- id: 78c76961f363
  severity: science
  text: "Report variability (e.g., standard deviation, confidence intervals) for all\
    \ quantitative metrics in Tables\u202F2,\u202F3,\u202F4, and\u202F5. This includes\
    \ SR, MPJPE, MPJVE, RootVelErr, and MPKPE across multiple random seeds or runs."
- id: 20dbd4969866
  severity: science
  text: "Conduct appropriate statistical significance tests (e.g., paired t\u2011\
    tests or non\u2011parametric tests) when comparing Humanoid\u2011GPT variants\
    \ to baselines (GMT, TWIST, Any2Track). Clearly state the null hypothesis, test\
    \ used, and p\u2011values."
- id: 055030aaf588
  severity: writing
  text: "Provide details on random seed handling, number of repetitions per experiment,\
    \ and any variance reduction techniques employed. This information should be added\
    \ to the implementation and reproducibility section (Sec\u202F6)."
- id: c75661edd7f9
  severity: science
  text: "When presenting scaling\u2011law curves (Fig.\u202F7 and Fig.\u202F8), fit\
    \ explicit regression models, report the fitted parameters with confidence intervals,\
    \ and discuss goodness\u2011of\u2011fit (e.g., R\xB2)."
- id: e372b66cd174
  severity: science
  text: "Address multiple\u2011comparison concerns: if many model\u2011size and data\u2011\
    size configurations are evaluated, apply a correction (e.g., Bonferroni or Holm)\
    \ or justify why it is unnecessary."
artifact_hash: 11a83a092083d485002512d3e56d130e02aef8501fdca7259786be2bc34086fd
artifact_path: projects/PROJ-658-humanoid-gpt-scaling-data-and-structure/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-23T12:59:36.517722Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript presents impressive engineering results, but the statistical treatment of the experimental data is insufficient for a rigorous scientific claim. All quantitative results (e.g., Table 2 “Comparison of backbone architectures and scaling effects”, Table 3 “Real‑world tracking accuracy”, and the scaling‑law plots in Figures 7 and 8) are reported as single point estimates without any measure of variability. There is no indication of how many random seeds were used, whether the reported numbers are averages, medians, or best‑case runs, nor any confidence intervals or error bars. This makes it impossible to assess the reliability of the observed improvements, especially when differences between methods are modest (e.g., SR = 90.43 % vs 88.27 % in Table 2).

Furthermore, the paper does not perform any statistical hypothesis testing when comparing Humanoid‑GPT to baselines such as GMT, TWIST, or Any2Track. Without p‑values or effect‑size estimates, readers cannot judge whether the reported gains are statistically significant or could be due to random variation. The scaling‑law analysis (Section 7) also lacks formal regression diagnostics; the curves are shown qualitatively, but the fitted exponents, confidence intervals, and goodness‑of‑fit metrics are omitted.

The authors should also address the multiple‑comparison problem inherent in evaluating many model sizes (S, B, L) and data scales (2 M, 20 M, 200 M, 2 B tokens). Either apply a correction method or provide a justification for why it is not needed.

Finally, reproducibility details concerning random seeds, the number of independent runs, and the statistical software used for analysis are missing from the implementation section (Sec 6). Including this information would greatly enhance the paper’s transparency.

In summary, while the engineering contributions are strong, the statistical analysis must be bolstered before the work can be accepted. Adding variability reporting, significance testing, and proper scaling‑law fitting will substantively improve the scientific rigor of the manuscript.
