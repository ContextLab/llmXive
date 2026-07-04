---
action_items:
- id: f8ee65e703ff
  severity: science
  text: "Table 1 (main) and Table~\ref{tab:pt_breakdown} report single-point accuracy\
    \ percentages (e.g., 73.5%, 61.1%) for the proposed BAGEL models without any measure\
    \ of variance (SD, SE, or CI) or number of seeds. In deep learning, single-run\
    \ reporting is insufficient to distinguish signal from stochastic noise. Report\
    \ mean \xB1 SD over at least 3 independent training seeds for all primary results,\
    \ or explicitly state that results are from a single run and treat them as preliminary."
- id: 0c4b513e12b1
  severity: science
  text: "The paper claims 'significant' improvements (e.g., Bagel label-only vs. base\
    \ in Table~\ref{tab:pt_breakdown}) based on point estimates alone. No hypothesis\
    \ tests (e.g., paired t-tests or bootstrap tests) are reported to validate these\
    \ differences. Given the multiple comparisons across 5 splits and 3 model variants,\
    \ apply a statistical test with appropriate multiple-comparison correction (e.g.,\
    \ Holm-Bonferroni) or rephrase claims to 'observed improvement' without invoking\
    \ statistical significance."
- id: ab1e80fa99ad
  severity: writing
  text: "Table~\ref{tab:qwen_discrete} and Table~\ref{tab:qwen_modality} report accuracy\
    \ differences (e.g., 55.0% vs 59.6%) for Qwen2.5-VL experiments without reporting\
    \ the number of seeds or variance. Since these are ablation studies on model architecture\
    \ (codebook size, grayscale), the lack of uncertainty reporting makes it impossible\
    \ to determine if the observed gains are robust or due to random initialization\
    \ variance. Report variance across seeds for these specific ablation results."
artifact_hash: c5de9734fccbfd100241f7fc8603c599264726354d7ecbedd4d657c0e121782f
artifact_path: projects/PROJ-681-imaginative-perception-tokens-enhance-sp/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-04T01:41:57.321171Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical treatment of the results in this paper is currently insufficient to support the quantitative claims made. While the experimental design (data curation, benchmarks) is detailed, the analysis of the resulting performance metrics lacks necessary rigor regarding uncertainty and inferential testing.

**1. Missing Uncertainty Reporting (Primary Concern):**
Throughout the results sections, specifically in Table 1 (main paper) and Table~\ref{tab:pt_breakdown} (supplementary), the authors report single-point accuracy percentages (e.g., "73.5%", "61.1%") for their proposed BAGEL models. There is no accompanying standard deviation (SD), standard error (SE), or confidence interval (CI), nor is there a mention of the number of random seeds used to generate these numbers. In the context of training deep learning models, performance can vary significantly based on random initialization, data shuffling, and optimization noise. Reporting a single number implies a level of precision and stability that is not statistically justified. Without variance estimates, a reader cannot determine if the reported "improvement" over baselines is a robust effect or a lucky run. This is a critical gap for any claim of "enhanced" performance.

**2. Unsubstantiated Claims of Significance:**
The paper frequently uses language implying statistical superiority (e.g., "outperforms," "improves") based solely on the magnitude of the point estimate difference. For instance, in Table~\ref{tab:pt_breakdown}, the "Bagel (label-only)" model shows a 37.2 percentage point jump over "Bagel (base)" on the EgoDir split. While this is a large difference, the paper does not perform or report a hypothesis test (such as a paired t-test or a bootstrap test) to confirm that this difference is statistically significant. Furthermore, with multiple splits (EgoDir, Path, PathArr, Real, Real+Arr) and multiple model variants being compared, the risk of Type I errors (false positives) is high. The authors should either run appropriate statistical tests with multiple-comparison corrections (e.g., Holm-Bonferroni) or soften their language to describe "observed improvements" rather than definitive "significant" gains.

**3. Inconsistent Reporting in Ablation Studies:**
In the supplementary experiments with Qwen2.5-VL (Tables~\ref{tab:qwen_discrete} and~\ref{tab:qwen_modality}), the authors report accuracy changes (e.g., 55.0% to 59.6% with grayscale) but again fail to report the number of seeds or variance. Since these are controlled ablation studies where the only variable is the token representation, the lack of variance reporting is particularly problematic. It prevents the community from assessing the reliability of the finding that "grayscale improves PT."

**Recommendation:**
The authors must re-run their primary experiments (BAGEL models) with at least 3 independent random seeds and report the mean ± standard deviation for all accuracy metrics. Additionally, they should perform statistical significance testing on the key comparisons and report the p-values (with correction for multiple comparisons) or explicitly state that no formal significance testing was performed and that the results are descriptive. Without these additions, the quantitative claims of the paper remain statistically unsupported.
