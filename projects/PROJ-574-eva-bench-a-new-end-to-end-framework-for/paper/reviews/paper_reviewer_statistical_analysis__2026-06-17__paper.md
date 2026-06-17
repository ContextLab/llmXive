---
action_items:
- id: 335b7282933b
  severity: science
  text: "Clarify the multiple\u2011comparison correction strategy. While Holm\u2011\
    Bonferroni is applied to perturbation significance (Fig.\u202F5\u20119), other\
    \ families of tests (e.g., pairwise architecture comparisons in Fig.\u202F4 and\
    \ Table\u202F1) lack correction, inflating Type\u202FI error risk."
- id: 56d152c75488
  severity: science
  text: "Provide effect\u2011size estimates (e.g., Cohen\u2019s\u202Fd or odds ratios)\
    \ alongside p\u2011values for the reported significant differences (e.g., the\
    \ 10\u2011point drop in task completion under accent, Fig.\u202F5). This will\
    \ aid interpretation of practical significance."
- id: efe4a7f4cd8d
  severity: writing
  text: "Justify the choice of the pass\u2011at\u2011k thresholds (\u03C4\u202F=\u202F\
    0.8 for turn\u2011taking, \u03C4\u202F=\u202F0.5 for other EVA\u2011X sub\u2011\
    metrics). Include a sensitivity analysis showing how varying \u03C4 influences\
    \ system rankings (beyond Fig.\u202F13)."
- id: 75f2737d1f06
  severity: science
  text: "Report the raw bootstrap samples or seeds used for confidence\u2011interval\
    \ estimation (Section\u202F4.2) to enable exact reproducibility of the CIs shown\
    \ in Table\u202F1 and Fig.\u202F4."
- id: 54b9e714f487
  severity: science
  text: "Expand the variance decomposition (Section\u202F4.2) to include confidence\
    \ intervals for the variance components and clarify the model (e.g., REML) assumptions;\
    \ this will strengthen claims about trial vs. judge stochasticity."
artifact_hash: 9779db764c5e6d634d1311a56a0ec38a708da09d28018889a272cb266ef418fe
artifact_path: projects/PROJ-574-eva-bench-a-new-end-to-end-framework-for/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-17T08:00:53.824581Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript presents a thorough statistical evaluation of EVA‑Bench, but several methodological aspects need strengthening.  

1. **Bootstrap confidence intervals** – The authors report 95 % bootstrap CI half‑widths for all EVA‑A and EVA‑X metrics (Table 1, Fig. 4). However, the bootstrap procedure (number of resamples, random seed) is not specified, limiting reproducibility. Providing these details and the raw resampled estimates would allow independent verification.  

2. **Multiple‑comparison control** – Holm‑Bonferroni corrections are applied to perturbation significance (Fig. 5‑9), yet other extensive pairwise tests (e.g., architecture‑type means in Fig. 4, the 41 omitted rows in Table 1) are presented without adjustment. Given the large number of systems (12) and metrics (6), the family‑wise error rate may be substantially inflated. A unified correction strategy or false‑discovery‑rate control should be described.  

3. **Effect‑size reporting** – Statistical significance is reported for many differences (e.g., “accent reduces cascade task completion by 10 pts”; Fig. 5), but no effect‑size metrics are provided. Including Cohen’s d, odds ratios, or confidence intervals for the mean differences would clarify whether observed changes are practically meaningful.  

4. **Threshold justification** – Pass‑at‑k thresholds (τₜₜ = 0.8 for turn‑taking, τ = 0.5 for other sub‑metrics) are motivated in Section 5.3, yet the sensitivity analysis (Fig. 13) only explores a narrow range. A more extensive analysis showing how system rankings vary across τ ∈ [0.5,0.9] would support the robustness of the chosen cut‑offs.  

5. **Variance decomposition** – The variance‑component analysis (Section 4.2, Table “ICC”) reports percentages for scenario, trial, and judge sources but omits confidence intervals for these estimates. Since the conclusions hinge on trial stochasticity dominating judge stochasticity, reporting the uncertainty around these components (e.g., via parametric bootstrapping) would strengthen the claim.  

6. **Reproducibility of statistical pipelines** – The paper mentions custom scripts for bootstrapping, ANOVA, and permutation tests, but the code is not linked in the released repository. Providing the exact analysis scripts and the random seeds used would enable full replication of the statistical results.  

Overall, the statistical framework is solid and appropriately leverages bootstrap methods and mixed‑effects modeling, but addressing the points above will improve the rigor and transparency of the empirical claims.
