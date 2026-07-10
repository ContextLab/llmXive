---
action_items:
- id: dc420a891b1f
  severity: writing
  text: The paper makes several strong comparative claims in Section 6 (Evaluation)
    that require tighter alignment with the provided data. Specifically, the claim
    of "state-of-the-art" performance in Section 6.1 is slightly ambiguous regarding
    the inclusion of closed-source models (Wan~2.6, Seedance, Veo), which are listed
    in Table 1 but not explicitly excluded in the text's summary of the TI2V results.
    While the authors likely mean "SOTA among open-source," the phrasing "securing
    the top spot" could mi
artifact_hash: 9ee70f69980a19ab6b09b1ef85c408bba9d6c20db5c959c0faf89cac5e30112c
artifact_path: projects/PROJ-1026-scaling-mixture-of-experts-video-pretrai/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-10T03:01:04.382051Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The paper makes several strong comparative claims in Section 6 (Evaluation) that require tighter alignment with the provided data. Specifically, the claim of "state-of-the-art" performance in Section 6.1 is slightly ambiguous regarding the inclusion of closed-source models (Wan~2.6, Seedance, Veo), which are listed in Table 1 but not explicitly excluded in the text's summary of the TI2V results. While the authors likely mean "SOTA among open-source," the phrasing "securing the top spot" could mislead a reader into thinking it beats all listed baselines.

Furthermore, the specific numerical claim of a "Physics-IQ Verified score of 40.4" in Section 6.2 is not present in any table or figure caption in the provided text; it appears only in the prose. Given that the paper relies heavily on visualizations (bar charts) for benchmark results, this specific number should be explicitly tabulated or cited from a specific figure data point to ensure reproducibility and verification. The comparison to Cosmos~3 (39.5) also needs to be clearly distinguished from the RBench scores in Table 1 to avoid confusion between different benchmark metrics.

Finally, the assertion in Section 5.1 that the FP8 "Speed-First" serving mode has "limited observed impact on video generation quality" is a load-bearing claim for the paper's efficiency argument. However, Section 6 does not present a specific quality degradation metric (e.g., a drop in FID or a specific user study result comparing FP8 vs. BF16 outputs) to substantiate this. Without this data, the claim remains an unsupported qualitative observation. These issues are primarily matters of precision and evidence alignment rather than fundamental scientific flaws, warranting a minor revision to clarify the scope of claims and ensure all quantitative assertions are backed by visible data.
