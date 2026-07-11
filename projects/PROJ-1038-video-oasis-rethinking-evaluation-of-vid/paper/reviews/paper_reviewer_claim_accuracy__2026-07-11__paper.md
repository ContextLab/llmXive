---
action_items:
- id: e824a18bb388
  severity: writing
  text: The paper makes several strong claims regarding the prevalence of "shortcuts"
    in video benchmarks and the resulting performance of state-of-the-art models.
    While the methodology for auditing benchmarks is sound, there are specific instances
    where the textual claims are not fully supported by the provided evidence or rely
    on unverifiable external resources. First, the claim in Section 4.2 that models
    perform "marginally above random guessing" is an overstatement given the data.
    The text cites a r
artifact_hash: f0c16b304e278e372ae68ce72c73490fb948c6f63a71aa660ad21d1de4b7a1fb
artifact_path: projects/PROJ-1038-video-oasis-rethinking-evaluation-of-vid/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-11T04:05:09.922633Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The paper makes several strong claims regarding the prevalence of "shortcuts" in video benchmarks and the resulting performance of state-of-the-art models. While the methodology for auditing benchmarks is sound, there are specific instances where the textual claims are not fully supported by the provided evidence or rely on unverifiable external resources.

First, the claim in Section 4.2 that models perform "marginally above random guessing" is an overstatement given the data. The text cites a random chance baseline of 25.6% and claims models are only slightly above this. However, Table 7 shows the lowest-performing open-source model (Video-R1) achieves 26.3%. A 0.7% margin is statistically fragile and arguably indistinguishable from noise without a significance test, making the phrase "marginally above" misleading. The authors should either soften this claim to "near random chance" or provide statistical evidence that the 0.7% gap is significant.

Second, the reliance on "GPT-5" and "o4-mini" for the consensus labeling in Section 4.1 is problematic. The bibliography lists "GPT-5" as a 2026 publication. As of the current review date, GPT-5 has not been publicly released or documented in a verifiable system card. Using a non-existent or unreleased model as a primary instrument for filtering the dataset (identifying the 122 samples requiring manual inspection) invalidates the reproducibility of the "video-native" challenge set. The authors must verify the actual model used (e.g., GPT-4o) and correct the citation, or explicitly state that these are hypothetical baselines, which would weaken the claim of a rigorous audit.

Finally, there is a minor numerical discrepancy in Section 3.2. The text states an average shortcut ratio of 92.7% under $c \ge 1$, but the arithmetic mean of the four values in Table 3 (95.6, 95.7, 85.8, 94.0) is 92.775%, which rounds to 92.8%. Given the paper's focus on precise auditing, this rounding error should be corrected. Additionally, Section 5.3 contains a LaTeX truncation error that cuts off the conclusion regarding RLVR reward designs, preventing the reader from verifying the authors' interpretation of the data.

These issues do not invalidate the core contribution of the Video-Oasis framework but require correction to ensure the claims are rigorously supported by the evidence presented.
