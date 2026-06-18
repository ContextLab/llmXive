---
action_items:
- id: 06d38599b286
  severity: science
  text: "Provide statistical significance testing (e.g., chi\u2011square or Fisher\u2019\
    s exact test) when comparing ASR/accuracy across model families and reasoning\
    \ settings, and report corresponding p\u2011values or confidence intervals."
- id: d8086741df62
  severity: science
  text: "Apply a multiple\u2011comparisons correction (e.g., Bonferroni or Benjamini\u2011\
    Hochberg) to the many stratified analyses (content type \xD7 provenance \xD7 dataset)\
    \ to control the family\u2011wise error rate."
- id: 95c0ceeef940
  severity: science
  text: "Report confidence intervals (e.g., Wilson or Agresti\u2011Coull intervals)\
    \ for all proportion metrics (clean accuracy, Type\u202F1/2 accuracy, ASR, TASR)\
    \ rather than only point estimates."
- id: 05c7f4bb329d
  severity: writing
  text: "Clarify the independence assumptions underlying the paired clean\u2011injected\
    \ evaluation (e.g., whether the same item appears in multiple model evaluations)\
    \ and discuss potential clustering effects."
- id: c67726baf179
  severity: science
  text: "Include a power analysis or sample\u2011size justification for the clinician\
    \ review cohort (89 items) to demonstrate that the reported harm rates are statistically\
    \ reliable."
- id: fbfbcf0eef01
  severity: writing
  text: Document the exact random seeds and any stochastic decoding parameters used
    for each model run to ensure full reproducibility of the reported proportions.
artifact_hash: b321ce34848cd04bd8d899e341b97cc74f8e7595fd9393bb1f9638bbf57b0d10
artifact_path: projects/PROJ-704-measuring-epistemic-resilience-of-llms-u/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-18T21:47:50.551550Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical evaluation in the manuscript is generally sound in its basic design: each model is first assessed on the clean benchmark, then on the same items after injecting misleading context, and epistemic‑resilience loss is quantified via attack‑success rate (ASR) and targeted‑ASR (TASR). However, several aspects of the analysis could be strengthened to meet rigorous statistical standards.

1. **Absence of significance testing** – The paper reports many point estimates (e.g., overall ASR = 51.5 % in Fig. 2, model‑specific ASR values in Tables A‑1/A‑2) but does not test whether observed differences between models, reasoning levels, or delivery protocols are statistically significant. Simple proportion tests (χ² or Fisher’s exact) could be applied to the 2 × 2 contingency tables (clean‑correct vs. flipped) for each comparison, providing p‑values and confidence intervals that would substantiate claims such as “Gemini‑3.1‑pro high reasoning has higher ASR than GPT‑5.4 medium reasoning.”

2. **Multiple‑comparison concerns** – The authors conduct extensive stratified analyses across five content‑corruption types, three provenance framings, five source datasets, and three model families (see Tables A‑5 and A‑6). Without correction, the risk of false‑positive findings is inflated. Applying a family‑wise error control (Bonferroni) or a false‑discovery‑rate procedure (Benjamini‑Hochberg) to the set of reported subgroup differences would make the taxonomy conclusions (e.g., “authority‑framed claims are most damaging”) statistically robust.

3. **Confidence intervals for proportions** – While the clinician‑review section includes bootstrap CIs for the worst‑case harm rate, the core benchmark metrics (clean accuracy, Type 1/2 accuracy, ASR, TASR) are presented without any uncertainty quantification. Reporting Wilson or Agresti‑Coull intervals for each proportion would allow readers to assess the precision of the estimates, especially for smaller splits such as MedMisHLE (≈ 100 items) where sampling variability is non‑trivial.

4. **Independence and clustering** – The paired evaluation treats each item as an independent trial, yet the same question appears across multiple model configurations and both delivery protocols. This creates a hierarchical data structure (items nested within models) that can induce clustering. A mixed‑effects logistic regression (random intercepts for items) would more appropriately model the data and could be used to test fixed effects such as “reasoning level” or “provenance” while accounting for item‑level correlation.

5. **Sample‑size justification for clinician review** – The harm analysis is based on 89 reviewed tasks (64 dual‑rated). The manuscript reports percentages (e.g., 38.2 % worst‑case harm) but does not discuss whether this sample provides sufficient power to detect meaningful differences across content types or provenance. A brief power analysis (e.g., using binomial proportion tests) would strengthen the claim that the observed harm rates are reliable.

6. **Reproducibility details** – The paper mentions temperature = 0 and default system prompts, but does not disclose random seeds, token‑level stopping criteria, or any nondeterministic aspects of the API calls (e.g., server‑side sampling). Providing these details, together with the exact version identifiers of the commercial APIs at the time of evaluation, would enable exact replication of the reported ASR values.

7. **Effect size reporting** – Beyond statistical significance, reporting effect sizes (e.g., risk ratios or odds ratios for ASR between models) would give a clearer picture of practical impact. The mixed‑effects logistic regression mentioned in the clinician‑review section (Table B‑4) is a good start; extending this to the main benchmark results would be valuable.

In summary, the experimental design is appropriate for measuring epistemic resilience, but the statistical analysis would benefit from formal hypothesis testing, correction for multiple comparisons, uncertainty quantification, and clearer reporting of reproducibility parameters. Addressing these points will make the benchmark’s conclusions more defensible and the paper more methodologically rigorous.
