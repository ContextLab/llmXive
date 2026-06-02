---
action_items:
- id: c694d97310e5
  severity: science
  text: "Report mean \xB1 standard deviation for all quantitative metrics in Tables\
    \ 1-4 to assess result stability across scene samples."
- id: 58aacf9b38ec
  severity: science
  text: Conduct formal hypothesis testing (e.g., paired t-tests) comparing TriSplat
    against baselines to validate claims of "consistent outperformance."
- id: 3ed67aa4ae20
  severity: science
  text: Include per-scene variance or confidence intervals for the zero-shot ScanNet
    evaluation (Table 3) to demonstrate generalization stability.
artifact_hash: 375d837bf9b63242d32116a8a2f6433796abb291136cadef4ae07e469b227763
artifact_path: projects/PROJ-627-trisplat-simulation-ready-feed-forward-3/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-02T07:46:31.899535Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical reporting in Section 4 lacks necessary rigor to support the claimed superiority of TriSplat. Tables 1-4 (DL3DV/RE10K/ScanNet) report mean metrics (PSNR, CD, F1, SSIM) without standard deviations, standard errors, or confidence intervals (e.g., `sections/04_experiments.tex`, lines 210-250). This prevents assessment of result stability across scene samples and undermines claims of robustness. Claims such as "consistently outperforming" (Introduction, line 45) and "clear margin" (Section 4.3, line 350) are unsupported without formal hypothesis testing (e.g., paired t-tests or Wilcoxon signed-rank tests).

Furthermore, the ablation studies in Appendix 8 (Tables 5-7) present single-point estimates for hyperparameter variations (e.g., CD 0.190 vs 0.189 in Table 5, line 620). Without variance estimates, it is impossible to determine if these differences are statistically significant or within noise margins. The zero-shot evaluation on ScanNet (Table 3, line 235) aggregates results over 100 scenes but reports no per-scene variance, making it difficult to assess generalization stability.

Additionally, multiple comparisons are conducted across six baselines and four surface metrics (CD, Prec, Rec, F1) without correction for false discovery rate. The mesh evaluation protocol (Appendix 6, line 750) should specify the random seed or resampling method used for metric computation to ensure reproducibility of the reported means. To meet statistical standards, the authors should report mean ± std dev for all quantitative tables and conduct significance tests comparing TriSplat against the strongest baseline (YoNoSplat) across all key metrics.
