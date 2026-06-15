---
action_items:
- id: 50f003dabd98
  severity: science
  text: Report standard deviations or confidence intervals for all main results (Tables
    1-2). Current point estimates alone cannot establish statistical significance
    of the 21.4% improvement on ALFWorld.
- id: d3531e7eb331
  severity: writing
  text: Clarify whether evaluation results are averaged over multiple random seeds.
    LLM performance variance across seeds is substantial and must be quantified for
    reproducibility.
- id: 8641bcdfd139
  severity: science
  text: Apply multiple comparisons correction when selecting optimal alpha across
    9 values and 6 tasks. Current selection risks overfitting to the test set without
    correction.
- id: 33617e100e76
  severity: science
  text: Perform significance testing (e.g., bootstrap or paired t-tests) for key method
    comparisons. Claims of 'best performance' require p-values to support statistical
    validity.
artifact_hash: a8058c08d3783326623ffd4fe82cc98eaea95cd3e37911390d531e390197b756
artifact_path: projects/PROJ-685-latentskill-from-in-context-textual-skil/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-15T04:49:36.877917Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The paper presents compelling empirical results but lacks rigorous statistical analysis to support its claims. This review focuses exclusively on statistical reporting adequacy.

**Main Results (Tables 1-2):** All performance metrics (success rate, exact match) are reported as point estimates without standard deviations, confidence intervals, or significance tests. The claimed 21.4% improvement on ALFWorld seen split cannot be assessed for statistical significance. With 140 episodes per split, variance estimates are essential to determine if gains exceed random fluctuation.

**Injection Coefficient Analysis (Section 4.2, Appendix):** The alpha sweep evaluates 9 values across 6 tasks. Selecting the "optimal" alpha without multiple comparisons correction risks overfitting. The inverted-U curve claim lacks curve-fitting statistics or confidence bands in Figure 4.

**Skill Composition (Table 3):** Results are based on only 31 Look task episodes (13 seen, 18 unseen). Small sample sizes require careful uncertainty quantification. No confidence intervals are provided for the 84.6% vs. 61.5% comparison.

**Low-Rank Analysis (Appendix):** Claims of 380x stable rank difference between skill LoRAs and random initialization cite a single random baseline value (837.87) without variance. Multiple random seeds should be used to establish the distribution of random LoRA stable ranks.

**Sensitivity Analysis (Appendix):** Four perturbation types are compared against baselines without statistical tests. The 3.6-point average degradation under perturbations lacks significance testing.

**Recommendations:** (1) Add confidence intervals to all tables; (2) Report evaluation over multiple seeds (e.g., 5-10 runs); (3) Apply Bonferroni or similar correction for alpha selection; (4) Include p-values for key comparisons; (5) Provide variance for the random LoRA baseline in low-rank analysis. These changes are necessary for scientific validity.
