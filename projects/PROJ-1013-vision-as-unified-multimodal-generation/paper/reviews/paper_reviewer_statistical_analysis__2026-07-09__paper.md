---
action_items:
- id: c2055b27abf7
  severity: science
  text: "Tables 1-4 report single point estimates (e.g., '56.6' mAP) for SenseNova-Vision\
    \ and baselines without any measure of uncertainty (SD, SE, or CI). In deep learning,\
    \ results vary across random seeds. Report mean \xB1 SD over at least 3 independent\
    \ training runs for the proposed method and key baselines to distinguish stable\
    \ improvements from run-to-run noise."
- id: 936bd091149b
  severity: writing
  text: Section 5.1 claims SenseNova-Vision is 'strong' or 'competitive' based on
    point estimates. Without reported variance or formal hypothesis tests (e.g., paired
    t-tests or bootstrap tests across seeds), these claims of superiority are statistically
    unsupported. Add uncertainty metrics or explicitly state that comparisons are
    based on single-run point estimates.
- id: c551fd3084f1
  severity: science
  text: Table 2 and Table 4 compare the proposed method against multiple baselines
    across several datasets (e.g., 5 depth benchmarks, 3 normal benchmarks). No correction
    for multiple comparisons (e.g., Bonferroni, Holm, or FDR) is applied to the 'significant'
    claims implied by the bolding of best results. Apply a correction or rephrase
    claims to avoid implying statistical significance where none was tested.
artifact_hash: 0af0fa627d69c39f9437c6e8b879903d02afc89b298d92518865da3572e8baac
artifact_path: projects/PROJ-1013-vision-as-unified-multimodal-generation/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-09T02:59:39.297007Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical reporting in the experimental section (Section 5) is insufficient for rigorous quantitative claims. While the paper presents extensive benchmark results across four task families, it consistently reports single point estimates (e.g., "56.6" mAP in Table 1, "4.0" abs rel in Table 2) without any accompanying measure of uncertainty such as standard deviation (SD), standard error (SE), or confidence intervals (CI).

In the context of deep learning, where training involves stochastic optimization and random data sampling, performance metrics naturally vary across different random seeds. Reporting a single number from one run (or an unreported average) makes it impossible to determine if the observed differences between SenseNova-Vision and baselines are statistically significant or merely artifacts of random initialization. For instance, in Table 1, SenseNova-Vision achieves 56.6 mAP on COCO-Common, while Grounding DINO-Swin-T achieves 56.6 as well (tied) and LocateAnything achieves 54.7. Without variance, we cannot assess the stability of these rankings.

Furthermore, the paper frequently uses language implying statistical superiority (e.g., "SenseNova-Vision achieves strong overall performance," "outperforming recent generation-based baselines") without providing the statistical machinery to support these assertions. The bolding of best results in tables is a common convention but does not constitute a statistical test. When comparing against multiple baselines across multiple datasets (e.g., 5 depth datasets in Table 2), the risk of false positives increases, yet no multiple-comparison correction (such as Bonferroni or Benjamini-Hochberg) is mentioned or applied.

To rectify this, the authors should re-run the experiments for the proposed method and key baselines with at least 3 independent random seeds. The results should be reported as mean ± SD. If the variance is small enough to support the claims, formal hypothesis tests (e.g., paired t-tests) should be conducted to validate the "outperforming" claims. If re-running is not feasible, the text must be softened to reflect that these are single-run observations, and the implication of statistical significance must be removed.
