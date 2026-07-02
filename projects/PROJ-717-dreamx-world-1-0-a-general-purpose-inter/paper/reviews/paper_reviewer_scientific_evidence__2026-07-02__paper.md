---
action_items:
- id: 7b04ef64ff8b
  severity: science
  text: The evaluation section (Section 5) lacks statistical rigor. Tables 1, 2, and
    3 report single-point scores without standard deviations, confidence intervals,
    or p-values. Given the claim of outperforming baselines, the authors must report
    variance across multiple seeds or test splits to rule out random fluctuation.
- id: a99707dc3b52
  severity: science
  text: The 'Artifact Detection Metric' relies on a single VLM (Gemini-3.1-Pro) without
    reporting inter-rater reliability or calibration against human judgment. The binary
    pass/fail judgment is subjective; the authors should provide a validation study
    showing the VLM's agreement with human annotators on a held-out set.
- id: da18542da5a4
  severity: science
  text: The memory consistency evaluation (Table 3) reports 'gain-based' scores but
    does not specify the sample size (number of revisit pairs) or the statistical
    test used to determine if the observed gains are significant. Without this, the
    claim of 'stronger memory' is not statistically supported.
artifact_hash: dd358f57d42e68a3445f4b34d5b2202a60d20e2d68878dcf007801dde467660f
artifact_path: projects/PROJ-717-dreamx-world-1-0-a-general-purpose-inter/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T17:34:14.784330Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a comprehensive system for interactive world modeling, but the scientific evidence supporting the quantitative claims requires strengthening to meet publication standards.

**Statistical Rigor and Variance:**
The primary limitation in the evidence provided is the absence of statistical variance metrics. In Tables 1 (Basic Evaluation), 2 (Long-Horizon), and 3 (Memory Consistency), the authors report single scalar values for all models (e.g., DreamX-World 1.0: 84.76 vs. HY-WorldPlay 1.5: 80.79). There is no indication of whether these results are averages over multiple random seeds, different test splits, or a single run. In generative modeling, performance can vary significantly based on initialization and stochastic sampling. Without standard deviations or confidence intervals, it is impossible to determine if the reported improvements are statistically significant or within the noise floor of the evaluation pipeline. The authors must re-run evaluations with multiple seeds (e.g., n=5) and report mean ± std.

**Evaluation Metric Validity:**
The "Artifact Detection Metric" (Section 5.1) relies entirely on a single VLM (Gemini-3.1-Pro) to judge binary pass/fail outcomes for defects like "duplicated limbs" or "geometric pass-through." The paper does not provide evidence that this specific VLM aligns with human perception for these specific artifacts. A robust evaluation would include a human-in-the-loop validation study (e.g., calculating Cohen's Kappa between the VLM and human annotators on a subset of 100-200 samples) to establish the metric's validity. Relying on a black-box VLM without calibration risks measuring the VLM's biases rather than actual model artifacts.

**Memory Consistency Significance:**
In Section 5.3, the authors introduce a "gain-based" scoring system for memory consistency. While the methodology of comparing revisit pairs to non-revisit baselines is sound, the results in Table 3 lack context regarding sample size. How many revisit pairs were detected across the test set? A gain of 0.232 in DINO-Sim might be highly significant with 10,000 pairs but negligible with 50. Furthermore, no statistical tests (e.g., t-tests or Mann-Whitney U tests) are reported to confirm that the gains are distinguishable from zero or from the baselines.

**Reproducibility of Baselines:**
The comparison against HY-WorldPlay 1.5 and LingBot-World assumes these baselines were evaluated under identical conditions (resolution, frame rate, prompt distribution). The paper mentions augmenting the trajectory set for the camera control metric but does not explicitly state whether the baselines were re-evaluated on this *augmented* set or if the authors used the original benchmark scores. If the baselines were not re-evaluated on the exact same augmented test set, the comparison is invalid. The authors must clarify the evaluation protocol for all models to ensure a fair "apples-to-apples" comparison.
