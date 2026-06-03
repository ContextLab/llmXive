---
action_items:
- id: ae922e5e73cb
  severity: writing
  text: Remove the claim of training a 754B model from the abstract as no results
    are presented for this scale in the Experiments section.
- id: 693bb2e39e2e
  severity: writing
  text: Clarify the discrepancy between the reported overall score of 75.6 in the
    text and the 3.72 Avg. in Table 1. Define the metric scale clearly (e.g., 0-100
    vs 1-5).
artifact_hash: 64f9753c508342ff47b0fefdddb7219cc59ae325dbfacf0e2b9d4340a33d4e53
artifact_path: projects/PROJ-629-macaron-a2ui-a-model-for-generative-ui-i/paper/metadata.json
backend: dartmouth
feedback: Abstract claims 754B model and 75.6 score, but experiments only cover 30B/235B
  and table shows 3.72 scale; requires clarification.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-03T06:17:01.534480Z'
reviewer_kind: llm
reviewer_name: paper_reviewer
score: 0.0
verdict: major_revision_science
---

# Free-form review body

## Strengths
- **Comprehensive Data Construction:** The paper presents a well-structured pipeline for converting heterogeneous dialogue corpora (MultiWOZ, SGD, ESConv, AnnoMI) into an A2UI-grounded dataset, including a clear validation and repair process.
- **Multi-Level Benchmark:** A2UI-Bench offers a detailed evaluation framework (L1 protocol, L2 task construction, L3 experience, plus visual V1-V3 metrics) that goes beyond simple accuracy to assess interaction quality and renderability.
- **Parameter-Efficient Training:** The two-stage pipeline (SFT + GRPO) effectively demonstrates that Generative UI capabilities can be internalized without heavy schema prompting at inference time.

## Concerns
- **Inconsistent Model Reporting:** The Abstract explicitly states that "30B, 235B and 754B models" were trained. However, the Experiments section (Section 6) only details results for 30B and 235B models (Qwen backbones and GLM-5.1). There is no mention of a 754B model's results or architecture in the body. This suggests either a typo in the Abstract or missing experimental data.
- **Score Reporting Discrepancy:** The text repeatedly claims an "overall score of 75.6" (Abstract, Introduction, Section 6). However, Table 1 (`full_prompt_results`) reports an "Avg." of `3.72` for the corresponding model (Macaron-A2UI-Venti). While these numbers might represent different scales (e.g., 0-100 vs. 1-5), the paper does not explicitly define the metric scale or conversion factor. This makes it impossible for a reader to verify the claim against the table.
- **Metric Definition:** Section 5 states that language-side evaluation is mapped to the range `[0,1]`, but the results in Section 6 are reported as `75.6` and `3.72`. This inconsistency in metric definitions needs to be resolved to ensure scientific rigor.

## Recommendation
The paper presents a strong contribution to Generative UI but requires significant revision to ensure the reported results match the claims. Specifically, the abstract must be aligned with the actual experiments (remove or justify the 754B claim), and the metric scales must be clearly defined to resolve the 75.6 vs. 3.72 discrepancy. These are scientific reporting issues that undermine the validity of the performance claims. Please revise the manuscript to clarify these points before resubmission.
