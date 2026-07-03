---
action_items:
- id: 5c2d0a1ec3b9
  severity: science
  text: "Table 1 and Section 4.2 report single-point accuracy/success rates without\
    \ variance (SD/SE/CI) or seed counts. RL results are stochastic; reporting single\
    \ runs implies false precision. Report mean \xB1 SD over \u22653 seeds for all\
    \ main results to assess stability."
- id: b7cc21d820cf
  severity: writing
  text: Section 4.2 claims OPID 'improves' or is 'better' based on point estimates
    alone, with no hypothesis test (t-test, Wilcoxon, bootstrap) or p-values reported.
    Without statistical validation, these are descriptive, not inferential. Run tests
    on seed data or rephrase to 'observed improvement'.
- id: 64c9e541fad0
  severity: writing
  text: Ablation Tables 3 and 4 compare OPID to variants using single-point averages.
    With multiple comparisons, false positives are possible. Report variance across
    seeds or acknowledge multiplicity to ensure observed drops (e.g., -10.2 points)
    are robust and not noise.
artifact_hash: ebe41e02149487ccd15d4c76bf5323b1b6f5d76f7c2ba35eb80cabef31288797
artifact_path: projects/PROJ-795-opid-on-policy-skill-distillation-for-ag/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T20:05:54.046847Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical treatment of results in this paper is insufficient to support the inferential claims made. While the experimental design appears sound, the **reporting of quantitative results** lacks necessary uncertainty measures.

**1. Missing Uncertainty Reporting:**
Throughout Section 4 and Tables 1, 3, and 4, performance metrics are reported as single point estimates (e.g., "92.7%"). There is no mention of the number of random seeds, nor are standard deviations (SD), standard errors (SE), or confidence intervals (CI) provided. In RL/LLM training, performance is highly sensitive to initialization. Reporting a single number creates false precision and makes it impossible to determine if differences (e.g., +9.3 points) are significant or due to random variance. The field standard is `mean ± SD` over at least 3-5 independent runs.

**2. Unsubstantiated Claims of Significance:**
The text uses language implying statistical significance (e.g., "consistently strengthens," "improves") based solely on point estimate differences. No hypothesis tests (paired t-test, Wilcoxon, bootstrap) are described or reported. Without p-values or CIs, these claims are descriptive observations, not statistical inferences. Authors must either perform tests on seed-level data and report results or soften language to reflect observed improvements without statistical validation.

**3. Multiple Comparisons in Ablations:**
Ablation studies (Tables 3 and 4) involve multiple pairwise comparisons. The lack of variance reporting makes it difficult to assess the reliability of observed drops. If authors claim a component is "essential" based on a performance drop, they must demonstrate robustness across seeds.

**Recommendation:**
Re-run experiments with multiple random seeds (min 3, preferably 5) and report mean and SD for all main results and ablations. Apply appropriate statistical tests to seed-level data to validate improvement claims. If re-running is not feasible, remove all language implying statistical significance and state results are from single runs or unverified means.
