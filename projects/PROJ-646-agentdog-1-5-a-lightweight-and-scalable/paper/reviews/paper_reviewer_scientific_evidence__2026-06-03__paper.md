---
action_items:
- id: 97eb2d92c82f
  severity: science
  text: Report standard deviations or confidence intervals for all metrics in Tables
    1-4 to establish statistical significance.
- id: a4c04de6c991
  severity: science
  text: Provide an ablation study on training data size (e.g., 1k vs 10k) to justify
    the claim that 1k samples are sufficient for SOTA performance.
- id: 03ceae9178f2
  severity: fatal
  text: Verify baseline models (GPT-5.4, Gemini-3) are publicly available or provide
    independent evaluation logs, as 2026-dated baselines hinder reproducibility.
artifact_hash: 0da3b72044460a5165e111e630e8cbd536a6b5b6d368e4237e9f5b706de0008d
artifact_path: projects/PROJ-646-agentdog-1-5-a-lightweight-and-scalable/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-03T10:55:31.126560Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents compelling claims regarding the efficacy of AgentDoG 1.5, particularly the assertion that ~1k training samples suffice to match frontier models. However, from a scientific evidence perspective, the robustness of these claims is currently insufficient for acceptance.

First, the statistical reporting is incomplete. Tables 1, 2, 3, and 4 present point estimates (Accuracy, F1, etc.) without standard deviations, confidence intervals, or p-values. Without multiple runs across different random seeds, it is impossible to determine if the reported improvements (e.g., +20.6 points in fine-grained diagnosis, Section 4.2.2) are statistically significant or due to random variance. This lack of variance reporting is a critical omission for any machine learning benchmark paper.

Second, the sample size justification is weak. Section 4.2.2 claims that influence-function-based purification reduces the dataset to "roughly 1k samples" while maintaining performance. There is no ablation study presented in the main text comparing performance across varying dataset sizes (e.g., 1k, 10k, 100k). Without this curve, the claim that 1k is "sufficient" is unsubstantiated and risks overfitting to the specific test distribution.

Third, the baseline verification is problematic. The paper compares results against GPT-5.4 and Gemini-3.1-Pro (cited as 2025/2026 models in the bibliography, e.g., `openai_gpt54_2026`, `gemini3`). Since these models are not publicly verifiable at this time, the central claim of "comparable performance with leading closed-source models" cannot be independently validated by the community. This undermines the reproducibility of the core contribution.

Finally, the evaluation protocol in Section 5 mentions "Temperature set to 0," which is standard, but does not explicitly state if the baselines were evaluated under the same temperature settings or prompt constraints. Any discrepancy here could artificially inflate the proposed method's relative performance. To strengthen the scientific evidence, the authors must provide statistical variance, data size ablations, and verifiable baseline comparisons.
