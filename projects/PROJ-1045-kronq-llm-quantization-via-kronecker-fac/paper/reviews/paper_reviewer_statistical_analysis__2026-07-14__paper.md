---
action_items:
- id: cd1c95090d62
  severity: writing
  text: "Table 1 and Table 2 report single-point perplexity and accuracy values (e.g.,\
    \ '5.56', '79.2') without any measure of uncertainty (standard deviation, standard\
    \ error, or range). Given that quantization results can vary with calibration\
    \ seeds or numerical noise, report mean \xB1 SD over at least 3 independent runs\
    \ for all reported metrics to establish stability."
- id: da24eab046b3
  severity: writing
  text: The abstract and Section 4.1 claim GPTQ/GPTAQ 'diverge' or produce 'degenerate'
    results (e.g., PPL > 2000) while KronQ achieves low PPL. While the magnitude difference
    is clear, the paper lacks a formal statistical test or confidence intervals to
    confirm that the observed gains (e.g., 7.93 vs >2000) are not artifacts of a single
    lucky/unlucky calibration seed. Report variance across seeds or explicitly state
    that results are deterministic under the fixed seed used.
artifact_hash: 6bdf7827fba12b0d8bdf1afc2ca37e869d5688f3fbc4e54d47c586b30e10b890
artifact_path: projects/PROJ-1045-kronq-llm-quantization-via-kronecker-fac/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-14T04:00:50.554265Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The paper presents a novel quantization method (KronQ) and reports extensive empirical results across multiple models and bit-widths. However, the statistical reporting of these results is insufficient for rigorous evaluation.

**Missing Uncertainty Reporting:**
Throughout the results sections (Sections 4.1, 4.2, and Appendices), all quantitative metrics (WikiText-2 perplexity, zero-shot accuracy) are reported as single point estimates (e.g., "5.56", "79.2%"). There is no mention of the number of random seeds used for calibration, nor are standard deviations (SD), standard errors (SE), or confidence intervals (CI) provided. In deep learning quantization, results can exhibit variance due to the stochastic nature of the calibration dataset sampling or numerical instabilities in the optimization process. Without reporting variance (e.g., "5.56 ± 0.02"), it is impossible to determine if the reported improvements over baselines are statistically significant or merely due to random fluctuation. The field standard for such comparisons is to report mean ± SD over at least 3 independent runs.

**Lack of Statistical Significance Testing:**
The paper makes strong comparative claims, such as KronQ achieving "strictly better" perplexity or baselines "diverging" (PPL > 2000). While the magnitude of the difference in the "divergence" cases is large enough to be practically significant, the smaller but consistent gains in other settings (e.g., 5.56 vs 5.69) are presented without any statistical test (e.g., paired t-test) or confidence intervals to support the claim of superiority. The absence of uncertainty metrics prevents the reader from assessing the reliability of these marginal improvements.

**Recommendation:**
The authors should re-run their experiments with multiple random seeds (e.g., 3-5) for the calibration set and report the mean and standard deviation for all perplexity and accuracy metrics in the main tables. If the results are deterministic given the fixed seed, this should be explicitly stated, and the potential for seed-dependent variance should be acknowledged as a limitation. Adding error bars or a "± SD" column to the tables is a minimal change that would significantly strengthen the statistical validity of the claims.
