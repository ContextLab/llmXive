---
action_items:
- id: 30d799ce7218
  severity: science
  text: Report standard deviation or confidence intervals for all reported F1 and
    BPS metrics to quantify variability.
- id: fb8acede9d0b
  severity: science
  text: Specify the number of random seeds used for training and evaluation in the
    main results and ablation studies.
- id: fc7e92a0ee22
  severity: writing
  text: Clarify the statistical significance tests supporting claims of 'significantly
    higher' throughput and accuracy.
artifact_hash: fd5c6b9375343e0bf1127bc6f967de79045e8b07b55446fb41fe382f0df7e34c
artifact_path: projects/PROJ-636-locateanything-fast-and-high-quality-vis/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-03T13:46:27.765567Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

## Statistical Analysis Review

This review focuses exclusively on the statistical rigor of the experimental design, reporting, and claims. While the proposed Parallel Box Decoding (PBD) shows promising performance trends, the statistical evidence provided is insufficient to fully support the strength of the claims made.

**1. Lack of Variance Estimates**
Throughout the paper, performance metrics (F1, AP, BPS) are reported as single point estimates without measures of variability (e.g., standard deviation, standard error, or confidence intervals). For instance, in **Table `lvis_coco_f1_merged`** (lines 100-120 of `tables/common_object_detection.tex`), LocateAnything-3B reports a mean F1 of 50.7 on LVIS compared to Rex-Omni's 46.9. Without variance estimates, it is impossible to determine if this 3.8% improvement is statistically significant or within the noise floor of the evaluation process. Similarly, **Figure `chart`** (right panel) displays throughput bars and lines without error bars, obscuring the stability of the speed gains across different image complexities.

**2. Ambiguity in "Significant" Claims**
The Abstract (lines 15-18 of `sec/0_abstract.tex`) states the model achieves "significantly higher decoding throughput while improving high-IoU localization quality." In statistical terminology, "significantly" implies a hypothesis test with a p-value (typically < 0.05). No hypothesis tests (e.g., t-tests, ANOVA) are described in **Section 4.1 Evaluation Setup** or the Ablation Study (**Section 4.3**). If the term is used colloquially to mean "substantially," the wording should be adjusted to avoid misleading statistical interpretation.

**3. Insufficient Experimental Repetition Details**
**Section 4.3 Ablation Study** (lines 150-180 of `sec/4_0_experiments.tex`) presents results in **Table `ablation`**. It is unclear whether these results are based on a single training run or averaged over multiple random seeds. Standard practice for SOTA comparisons requires at least 3-5 seeds to account for stochasticity in initialization and data shuffling. Without this information, the robustness of the ablation conclusions (e.g., PBD (Slow) achieving 52.1 F1 vs Quantized 50.1 F1) cannot be verified.

**4. Throughput Measurement Protocol**
Throughput is measured as Boxes Per Second (BPS) on a single H100 GPU (**Section 4.1**). While **Figure `chart`** analyzes throughput vs. number of boxes, it does not report the variance of the throughput measurements across different images or time intervals. Throughput can vary significantly based on input resolution and object density; reporting mean and variance would strengthen the claim of "robust" speed gains.

**Recommendations:**
-   Re-run key experiments (Main Results and Ablations) with at least 3 random seeds and report mean ± std dev.
-   Add error bars to **Figure `chart`** and consider adding them to tables where space permits.
-   Replace "significantly" with "substantially" unless formal statistical tests are performed and reported.
-   Explicitly state the number of seeds used in **Section 4.1**.

These additions are critical to establishing the scientific validity of the performance improvements claimed.
