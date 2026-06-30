---
action_items:
- id: 2b4b789ff41e
  severity: science
  text: The user study (Sec. 6) reports a Spearman's rank correlation (SRCC) of 0.90
    based on only 6 participants and 100 samples. This sample size is statistically
    insufficient to support a claim of 'high consistency' without reporting confidence
    intervals or a significance test (p-value). The variance in human ranking is likely
    high; a single outlier could drastically alter the SRCC.
- id: eca6f9f690bf
  severity: science
  text: The MLLM-Score metric relies on a single judge (Gemini-3.0-Pro) without reporting
    inter-rater reliability or variance. For the subject-side task, the mean score
    is 0.34 with a standard deviation not reported. Without confidence intervals or
    error bars on the quantitative results (Tables 1 & 2), the statistical significance
    of the differences between ShutterMuse and baselines (e.g., 0.34 vs 0.35) cannot
    be determined.
- id: a0b899919727
  severity: science
  text: The EMDP pipeline reliability analysis (Fig. 5) presents F1-scores and acceptance
    rates but lacks statistical error bounds. The claim that the verifier is 'reliable'
    based on a single point estimate (F1 > 87%) is weak without a confidence interval
    derived from the sampling process (100 examples/round).
- id: 26b0ba5022fd
  severity: science
  text: The ablation study (Table 3) shows small performance deltas (e.g., IoU 74.30
    vs 74.10). Without a statistical significance test (e.g., paired t-test or bootstrap
    confidence intervals) across the benchmark samples, it is unclear if these improvements
    are real or due to random variance in the test set.
artifact_hash: c05d947baccac31badb983e4672bc18e6d1ae08f6b2511780ab5cbcde805c567
artifact_path: projects/PROJ-789-shuttermuse-capture-time-photography-gui/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T22:07:54.473688Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: full_revision
---

The statistical rigor of the evaluation metrics and user study requires significant revision to support the paper's claims.

First, the **User Study** (Section 6) is statistically underpowered. The authors report a Spearman's rank correlation (SRCC) of 0.90 between MLLM rankings and human preferences based on only **six participants** and 100 samples. In statistical terms, a sample size of $N=6$ for the correlation calculation (if treating participants as the unit of analysis) or even $N=100$ (if treating samples as independent) is insufficient to claim "high consistency" without reporting **confidence intervals** or a **p-value**. Human aesthetic judgment is inherently noisy; without quantifying the variance or performing a significance test, the reported SRCC of 0.90 could be an artifact of the specific sample distribution or a small number of participants. The authors must report the 95% confidence interval for the SRCC and justify the sample size.

Second, the **quantitative results** in Tables 1 and 2 lack measures of uncertainty. The paper reports point estimates for metrics like IoU (74.30%), RSR (82.76%), and MLLM-Score (0.64) but provides no **standard deviations**, **confidence intervals**, or **error bars**. For instance, the difference in mean subject-side scores between ShutterMuse (0.34) and GPT-Image-2 (0.35) is negligible without a statistical test (e.g., a paired t-test or bootstrap resampling) to determine if the difference is statistically significant. Similarly, the ablation study (Table 3) shows marginal gains (e.g., IoU increasing from 74.10% to 74.30% when adding $R_{mask}$). Without statistical significance testing, it is impossible to distinguish genuine model improvements from random noise in the benchmark.

Third, the **MLLM-based evaluation** relies on a single judge (Gemini-3.0-Pro) without assessing **inter-rater reliability**. The "MLLM-Score" is treated as a ground truth proxy, yet LLM judges can be inconsistent. The authors should either report the variance across multiple judge runs (if stochastic) or use multiple distinct models to verify the stability of the scores. The current presentation implies a deterministic precision that is not supported by the methodology.

Finally, the **EMDP reliability analysis** (Figure 5) presents F1-scores and acceptance rates as single values. Given that these are estimated from a sample of 100 examples per round, the authors should report the **confidence intervals** for these estimates to demonstrate the stability of the self-distillation pipeline.

To proceed, the authors must re-run the statistical analyses to include confidence intervals, p-values for significance testing, and variance measures for all reported metrics.
