---
action_items:
- id: 1f81891257ad
  severity: science
  text: The publication trend analysis (Fig 1) reports 2025 contributing 45.7% of
    411 references. As 2025 is the current year, this figure is likely biased by the
    cutoff date of the bibliography rather than a true exponential surge. The authors
    must clarify the data collection window and whether this percentage reflects a
    genuine trend or a sampling artifact.
- id: 95064d2e5fb9
  severity: science
  text: The 'Stress Testing' section (Sec 6) presents qualitative failure modes (e.g.,
    Metro Map, Jigsaw) without quantitative aggregation. To support claims about 'spatial
    logic' failures, the authors should report success rates, confidence intervals,
    or statistical significance tests across a larger, defined set of prompts rather
    than relying on anecdotal case studies.
- id: 262f950f64cf
  severity: science
  text: "In the evaluation section (Sec 5), the paper cites Spearman agreement scores\
    \ (0.57\u20130.75) for VLM judges against humans but does not specify the sample\
    \ size (N) or the specific benchmark subsets used. Without N and p-values, the\
    \ statistical reliability of these correlation claims cannot be assessed."
artifact_hash: 95c6cfb0cd885d3a15ec9e77a9e8d06788a35e40acba2d1245cdfd2be8660dc4
artifact_path: projects/PROJ-572-https-arxiv-org-abs-2604-28185/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:36:08.040291Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript is a comprehensive survey that proposes a novel taxonomy for visual generation. However, from a statistical analysis perspective, the paper relies heavily on qualitative assertions and anecdotal evidence rather than rigorous quantitative validation.

First, the analysis of publication trends in Figure 1 (Section 1) claims an "exponential acceleration" with 2025 contributing 45.7% of the 411 references. This statistic is highly susceptible to sampling bias, as 2025 is the current year and the bibliography is necessarily truncated. Without a clear definition of the data collection window (e.g., "papers published up to [Date] in 2025") and a comparison against a baseline (e.g., 2024's full-year contribution), this percentage likely reflects a cutoff artifact rather than a genuine statistical trend. The authors must clarify the data provenance and statistical validity of this claim.

Second, the "Stress Testing" section (Section 6) is the core of the paper's argument regarding model limitations, yet it lacks statistical rigor. The authors present specific failure cases (e.g., the Metro Map challenge, the Jigsaw puzzle) as evidence of systemic failures in spatial logic. While illustrative, these are anecdotal. To support the claim that models "fail on spatial reconstruction" generally, the authors should report results from a systematic evaluation: the number of prompts tested, the success/failure rates, and ideally, confidence intervals or statistical significance tests comparing different model classes. Currently, the evidence is qualitative, which weakens the scientific weight of the conclusions drawn about "causal competence."

Third, in Section 5.2, the paper discusses the shift to "VLM-as-a-Judge" and cites Spearman correlation coefficients (0.57–0.75) between VLMs and human preferences. However, the text omits the sample size ($N$) and the specific benchmark subsets used to derive these correlations. Without $N$, it is impossible to determine the statistical power of these estimates or whether the correlations are significantly different from zero or from each other. The authors should provide the sample sizes and, where appropriate, p-values or confidence intervals for these correlation metrics to ensure the reproducibility and validity of the evaluation claims.

Finally, the paper mentions various performance metrics (e.g., accuracy scores for GenEval, text rendering accuracy) but often presents them as single point estimates without context regarding variance or experimental setup (e.g., number of seeds, randomization). While this is a survey, the synthesis of these metrics should acknowledge the statistical uncertainty inherent in the underlying studies.
