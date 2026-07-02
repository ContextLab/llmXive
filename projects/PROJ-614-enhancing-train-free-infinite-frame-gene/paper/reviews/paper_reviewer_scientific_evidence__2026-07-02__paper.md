---
action_items:
- id: d6df0227251a
  severity: science
  text: The ablation studies (Tab. 1, Tab. 2) report single-point performance metrics
    without standard deviations or confidence intervals. Given the stochastic nature
    of diffusion sampling, statistical significance testing (e.g., paired t-tests)
    is required to confirm that the observed gains (e.g., +2.03% O.S.) are not due
    to random variance.
- id: dac435090eec
  severity: science
  text: The user study (Tab. 3) relies on a small sample size (48 prompts, 8 annotators)
    without reporting statistical power analysis or inter-annotator agreement (e.g.,
    Krippendorff's alpha). The claim of 'large-scale' validation is unsupported by
    these numbers; a more rigorous statistical treatment or larger sample is needed.
- id: 969dd80364e7
  severity: science
  text: The comparison with training-based methods (Tab. 4) lacks a clear definition
    of the evaluation subset. If the same prompts were used for both train-free and
    train-based methods, potential data leakage or prompt bias could inflate the train-free
    scores. The experimental protocol must explicitly state how the test set was constructed
    to ensure fair comparison.
artifact_hash: 2fc45fd89cfd8c3cc27102ad20713af6a66d4f721af1c258a0cd318f7ea682b3
artifact_path: projects/PROJ-614-enhancing-train-free-infinite-frame-gene/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T14:35:05.540384Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents MIGA, a train-free method for infinite-frame video generation, claiming significant improvements in consistency over FIFO-Diffusion. While the methodological contribution is clear, the scientific evidence supporting the quantitative claims requires strengthening regarding statistical rigor and experimental design.

First, the core results in Tables 1 and 2 (VBench and NarrLV) present point estimates for metrics like Subject Consistency (S.C.) and Overall Score (O.S.) but omit measures of variance (standard deviation) across the evaluation set. In generative modeling, where outputs are stochastic, a single run or an unreported average can be misleading. For instance, the reported gain of +2.03% in O.S. for the TTA mechanism (Sec. 4.2, Tab. 1) lacks context on whether this difference is statistically significant. The authors should report standard deviations over multiple seeds or prompts and include p-values from appropriate statistical tests (e.g., paired t-tests) to validate that the improvements are robust and not artifacts of random sampling.

Second, the human evaluation (Sec. 4.2, Tab. 3) is described as a "large-scale user study" but is based on only 48 prompts and 8 annotators. This sample size is relatively small for establishing strong human preference claims, especially given the high variance in subjective video quality assessment. The manuscript does not report inter-annotator agreement metrics (such as Cohen's kappa or Krippendorff's alpha), which are essential to verify the reliability of the annotations. Without this, the claim that MIGA "consistently outperforms" baselines across all dimensions is not fully supported by the provided evidence.

Finally, the comparison with training-based methods (Tab. 4) raises questions about the fairness of the evaluation protocol. The paper does not explicitly state whether the same set of prompts was used for both the train-free MIGA and the training-based baselines (e.g., Infinity-RoPE, CausVid). If the test sets differ, or if the prompts were selected to favor the specific strengths of MIGA, the comparison could be biased. The authors must clarify the prompt selection strategy and ensure that the evaluation conditions are identical across all compared methods to support the claim of "comparable performance."

In summary, while the proposed method appears effective, the current evidence lacks the statistical depth required to definitively support the magnitude of the claimed improvements. Addressing the variance reporting, statistical significance, and evaluation protocol transparency is necessary before the claims can be considered fully robust.
