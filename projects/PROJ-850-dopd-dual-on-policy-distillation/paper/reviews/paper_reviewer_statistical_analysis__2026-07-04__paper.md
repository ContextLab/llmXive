---
action_items:
- id: 83783201856c
  severity: writing
  text: "Tables 1-4 report single-point accuracy scores without uncertainty (SD/SE/CI)\
    \ across seeds. Deep learning results vary by seed; report mean \xB1 SD over \u2265\
    3 seeds for all main results to assess stability."
- id: 1e7e500c135e
  severity: writing
  text: Section 4.2 claims consistent superiority across 40+ comparisons without statistical
    tests or multiple-comparison correction. Run paired tests with Holm/BH correction
    or rephrase to 'higher mean' without implying significance.
- id: 87cf16f51dfb
  severity: writing
  text: "Ablation Tables 3-4 report step-wise performance as single numbers without\
    \ uncertainty. Since these justify design choices, report mean \xB1 SD over seeds\
    \ to verify the stability of reported gains."
artifact_hash: 1c1c61b84dddc2460538527d82a1400d1a11188ffd68bb62d1afc40f8faa40cf
artifact_path: projects/PROJ-850-dopd-dual-on-policy-distillation/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-04T01:23:27.542184Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical reporting in this paper lacks necessary uncertainty quantification, creating a risk of false precision. All main results in Tables 1, 2, 3, and 4 are presented as single point estimates (e.g., "71.3", "51.4") without standard deviation, standard error, or confidence intervals. In deep learning, performance metrics exhibit significant variance across random seeds; reporting only a single number prevents readers from assessing result stability or distinguishing signal from noise. The field standard requires reporting "mean ± SD" over at least 3 independent training runs.

Furthermore, the paper claims DOPD "consistently outperforms" baselines across numerous benchmarks and model pairs (over 40 comparisons) without performing formal hypothesis testing or correcting for multiple comparisons. With this volume of pairwise tests, some "best" results are expected by chance alone. The authors should either apply a correction method (e.g., Holm or Benjamini-Hochberg) and report adjusted p-values, or soften their language to describe mean differences without invoking statistical significance.

Finally, the ablation studies in Tables 3 and 4, which are critical for validating the specific design components of DOPD, also lack uncertainty reporting. The stability of the gains attributed to token routing and divergence choices cannot be verified from single-run data. Re-running these experiments with multiple seeds and reporting the spread is essential to substantiate the methodological claims.
