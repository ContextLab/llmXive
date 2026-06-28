---
action_items:
- id: 59c2dd4e4a69
  severity: science
  text: Correct the statistical significance paragraph in Supplementary Materials;
    reported FID values (12.3) do not match OOD table (17.81) or main tables.
- id: 00cc1c54bae9
  severity: science
  text: Report confidence intervals or standard deviations for all main benchmark
    results (FID/LPIPS) across multiple seeds.
- id: d0564cab6ebd
  severity: science
  text: Include statistical significance tests (e.g., t-test, bootstrap) for User
    Study preference percentages.
- id: 3e9a7152b07e
  severity: writing
  text: Replace placeholder code link with actual repository URL for reproducibility.
artifact_hash: 5caa43767211f2848d0daf8334de16dd1c8a2e43a12207ac3a5c7a50cfbe8f32
artifact_path: projects/PROJ-751-moebius-0-2b-lightweight-image-inpaintin/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-28T12:42:04.360822Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: full_revision
---

The statistical analysis presented in the manuscript contains critical inconsistencies and omissions that undermine the validity of the performance claims. In the Supplementary Materials (Section 'Evaluation of Out-of-Distribution (OOD) Performance'), the authors claim statistical significance ($p<0.01$) with FID values of $12.3 \pm 0.4$. However, these values do not correspond to any data in the provided tables. Table `abla_ood` reports an OOD Natural FID of 17.81 for Moebius, and Table `total_natural` reports 9.48 for Places2 Test. This discrepancy suggests either a reporting error or a lack of alignment between the statistical analysis and the reported results.

Furthermore, the main results tables (e.g., `total_natural`, `total_portrait`) present single-point estimates without error bars or standard deviations. Given the stochasticity of deep learning training, reporting results from a single run (or unreported number of runs) is insufficient to claim superiority. The User Study (Section 4.3) claims Moebius 'significantly surpasses' industrial models based on preference percentages (31.76% vs 23.70%), but no statistical test (e.g., binomial test) or confidence intervals are provided to support this assertion.

Additionally, the paper compares Moebius against numerous baselines across multiple datasets without addressing the multiple comparisons problem. Without correction (e.g., Bonferroni), the risk of Type I errors increases. Finally, the Code Availability section contains a placeholder URL (`[username]`), preventing independent verification of the analysis. To ensure reproducibility and statistical rigor, the authors must align the statistical claims with the actual data, report variance across multiple seeds for all benchmarks, and perform formal significance testing for the user study.
