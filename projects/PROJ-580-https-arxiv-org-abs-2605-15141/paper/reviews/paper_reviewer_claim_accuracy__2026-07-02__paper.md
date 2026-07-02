---
action_items:
- id: 98bd24fd0b6d
  severity: writing
  text: Abstract claims '0.1 in VBench Total, 0.3 in VBench Quality' over SOTA. Table
    1 shows these deltas apply only to the 2-step setting (84.14 vs 84.04; 84.89 vs
    84.59). The 4-step setting yields different deltas (Total 84.10 vs 84.04; Quality
    84.94 vs 84.59). Clarify that these specific gains refer to the 2-step setting
    to avoid ambiguity.
- id: 85929c029aac
  severity: writing
  text: Section 3.2 claims cost reduction from ~11,600 to ~2,900 GPU hours at '80K-video
    scale'. Table 1 lists these exact numbers but does not explicitly label the dataset
    size. Add '80K' to the table caption or row labels to fully support the scalability
    claim.
- id: ec2c017edbb5
  severity: writing
  text: Abstract claims '50% reduction in first-frame latency'. Table 1 shows 0.60s
    vs 0.27s, which is a 55% reduction. While 50% is a valid approximation, 'over
    50%' or '55%' is more precise given the specific data provided.
artifact_hash: bc6ea3b7abb50e6d2d0c61521fe88f76d18733e7f3e4d74c5eba9d5fe9acb8e6
artifact_path: projects/PROJ-580-https-arxiv-org-abs-2605-15141/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:54:40.949404Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The review focuses on the accuracy of factual claims and their alignment with the provided evidence (tables and text).

The manuscript makes several quantitative claims regarding performance improvements and efficiency gains. Most claims are supported by the data in Table 1 (`Tables/performance_comparison.tex` and `Tables/ablation.tex`), but some require minor clarification to ensure precision.

1.  **Performance Deltas (Abstract & Section 4):** The abstract states that Causal Forcing++ surpasses the SOTA 4-step chunk-wise Causal Forcing by "0.1 in VBench Total, 0.3 in VBench Quality". Table 1 confirms that the **2-step** Causal Forcing++ (Total: 84.14, Quality: 84.89) beats the 4-step Causal Forcing (Total: 84.04, Quality: 84.59) by exactly 0.10 and 0.30 respectively. However, the **4-step** Causal Forcing++ (Total: 84.10, Quality: 84.94) actually achieves a higher Quality score (84.94 vs 84.59, a 0.35 gain) and a slightly lower Total score (84.10 vs 84.04, a 0.06 gain). The text implies the 2-step setting is the primary benchmark for these specific deltas. While factually correct for the 2-step comparison, the phrasing could be slightly ambiguous as the 4-step setting yields even better Quality results. It is recommended to explicitly state "in the 2-step setting" when citing these specific deltas to avoid confusion with the 4-step results which show different margins.

2.  **Latency Reduction (Abstract & Section 4):** The claim of a "50% reduction in first-frame latency" is supported by Table 1, which lists Causal Forcing latency at 0.60s and Causal Forcing++ at 0.27s. The actual reduction is 55%. The claim of "50%" is a reasonable approximation, but given the precision of other metrics, stating "over 50%" or "55%" would be more rigorous.

3.  **Training Cost (Section 3.2 & Table 1):** The claim that causal CD reduces Stage 2 cost from ~11,600 to ~2,900 A800-GPU hours is directly supported by the "Time (Stage 2)" column in Table 1. The text links this to the "80K-video scale". The table does not explicitly label the rows with the dataset size, though the context implies it. To fully support the scalability claim, the table caption or row labels should explicitly confirm that these figures correspond to the 80K dataset mentioned in the text.

4.  **Causal DMD vs. CD (Section 3.3 & Table 1):** The claim that causal DMD suffers from exposure bias and yields lower quality than causal CD is supported by the "VisionReward" and "Total" scores in Table 1 (e.g., 2-step: CD Total 84.14 vs DMD Total 83.73; VisionReward 6.661 vs 6.108). The qualitative descriptions of "blurring" and "artifacts" in Figure captions (e.g., `Figures_tex/ablation.tex`) align with the quantitative drop in metrics, particularly in Dynamic Degree and VisionReward where DMD underperforms.

Overall, the claims are well-supported by the provided tables, with only minor issues regarding the precision of percentage reductions and the specific step-count context for performance deltas.
