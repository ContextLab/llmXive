---
action_items:
- id: b31f5be174d5
  severity: writing
  text: 'The statistical reporting in the Evaluation section requires clarification
    regarding sample sizes and uncertainty quantification to ensure the reported numbers
    accurately reflect the underlying data. In Table 1 (VLA deployment results), the
    success rates are presented with confidence intervals (e.g., HY-VLA: 100.0% [83.9,
    100.0]). The presence of a lower bound significantly below 100% for a point estimate
    of 100% strongly suggests a small number of trials (likely fewer than 10). However,
    the man'
artifact_hash: 09a01042a88fbdf5f5c789375b34beb2ecc7627cb133cf76d171a0ac8c9d372b
artifact_path: projects/PROJ-996-embodied-cpp-a-portable-inference-runtim/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-07T03:31:54.370913Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical reporting in the Evaluation section requires clarification regarding sample sizes and uncertainty quantification to ensure the reported numbers accurately reflect the underlying data.

In Table 1 (VLA deployment results), the success rates are presented with confidence intervals (e.g., HY-VLA: 100.0% [83.9, 100.0]). The presence of a lower bound significantly below 100% for a point estimate of 100% strongly suggests a small number of trials (likely fewer than 10). However, the manuscript does not explicitly state the number of trials (N) performed for each task, nor does it specify the statistical method used to calculate these intervals (e.g., Clopper-Pearson exact interval, Wilson score interval). Without N and the method, the reader cannot assess the reliability of the "100.0%" claim or the width of the interval. The text should explicitly state the number of episodes/trials and the CI calculation method.

In Table 2 (LingBot-VA microbenchmark), the authors state that "100 random input samples" were used to compare the Python and C++ implementations. However, the results for Mean Absolute Error (MAE) and Cosine Similarity are reported as single point estimates (e.g., MAE < 3.3e-2) without any measure of dispersion (standard deviation, standard error) or confidence intervals. Since the inputs are random samples, the error metrics are themselves random variables. Reporting only the aggregate or worst-case bound without the variance across the 100 samples obscures the stability of the quantization error. The authors should report the mean ± standard deviation (or 95% CI) of the MAE and Cosine Similarity across the 100 samples to provide a complete picture of the quantization impact.

These are reporting gaps rather than fundamental flaws in the experimental design, but they are necessary for the numbers to mean what the paper claims they mean.
