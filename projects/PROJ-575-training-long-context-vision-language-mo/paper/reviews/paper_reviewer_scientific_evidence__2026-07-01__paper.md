---
action_items:
- id: c33000b4f9f0
  severity: science
  text: The scientific evidence presented in this paper is currently insufficient
    to support its central claims regarding the robustness of the proposed training
    recipe and the model's generalization capabilities. First, the evaluation methodology
    lacks statistical rigor. Key results, particularly the generalization to 256K
    and 512K contexts (Section 6, Table 2) and the ablation studies on data mixture
    (Section 5), are reported as single-point estimates. In long-context modeling,
    performance can vary si
artifact_hash: 27eba2e5ea40297ff1b355e2383ef9ee011ad854079e699d6346f41869d2df3c
artifact_path: projects/PROJ-575-training-long-context-vision-language-mo/paper/specs/001-paper/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T20:41:27.923725Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: full_revision
---

The scientific evidence presented in this paper is currently insufficient to support its central claims regarding the robustness of the proposed training recipe and the model's generalization capabilities.

First, the evaluation methodology lacks statistical rigor. Key results, particularly the generalization to 256K and 512K contexts (Section 6, Table 2) and the ablation studies on data mixture (Section 5), are reported as single-point estimates. In long-context modeling, performance can vary significantly based on random seed, data shuffling, and evaluation prompt sensitivity. Without reporting standard deviations from multiple runs (e.g., 3-5 seeds) or conducting statistical significance tests (e.g., t-tests), it is impossible to determine if the observed gains (e.g., +7.1% on MMLongBench) are real or artifacts of variance. The claim of "generalization beyond 128K" is particularly fragile without this evidence.

Second, the experimental design in the ablation studies contains potential confounders. In Section 5.1, the comparison between "pool-native" and "long-biased" distributions changes not just the length distribution but also the source document complexity (32-50 pages vs. 50-100 pages). The observed performance difference could be driven by the inherent difficulty or diversity of the longer documents rather than the length distribution itself. A more controlled experiment, holding document sources constant while varying only the sampling strategy, is required to isolate the effect of length distribution.

Third, the comparison between VQA and OCR tasks in Table 1 is methodologically flawed. The OCR baselines labeled "SFT" undergo an additional 5B-token supervised fine-tuning stage, whereas the VQA baselines do not. This introduces a confounding variable: the superior performance of VQA might be due to the absence of the SFT stage (which could introduce noise or catastrophic forgetting) rather than the intrinsic superiority of the VQA task. The paper fails to present a fair comparison where both task types are evaluated under identical training pipelines (e.g., VQA without SFT vs. OCR without SFT).

Finally, the claim that short-context capabilities are "preserved" (Section 5.3) is based on a marginal difference (66.47 vs 65.48) without statistical validation. Given the noise in LLM evaluation, this difference may not be significant. The authors must provide statistical evidence to support the assertion that the drop is negligible.

To proceed, the authors must re-run key experiments with multiple seeds, report confidence intervals, and redesign the ablation studies to eliminate confounding variables.
