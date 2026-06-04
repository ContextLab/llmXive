---
action_items:
- id: 4335f87f407e
  severity: writing
  text: Teaser Figure caption claims memory reduction from 35.4 GB, but Table 3 (tab:inference_progressive)
    shows 36.4 GB for BF16 baseline. Please align these numbers or specify the exact
    configuration for the 35.4 GB figure.
- id: f8e911468406
  severity: writing
  text: Section 2.2 states NVFP4 provides 'approximately 1.8x training speedup' without
    explicitly stating the baseline (BF16 Balanced SP). This conflicts with the Abstract's
    2.15x claim (vs BF16 w/ SP). Clarify the baseline to avoid confusion.
- id: 0b8fbbaf32af
  severity: writing
  text: The FPS claim (45.7 FPS) and E2E latency (36.3s for 64s video) imply different
    real-time factors depending on output frame rate. Clarify if FPS refers to model
    throughput or E2E system throughput to ensure accuracy.
artifact_hash: 6191ec14b8389b89c96572533c3f6f5e9333a3f73e89fe363432c3a9d7429fb8
artifact_path: projects/PROJ-604-https-arxiv-org-abs-2605-18739/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-04T18:55:19.862034Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The paper presents strong evidence for its efficiency claims, with tables generally supporting the reported speedups (e.g., Table 1 confirms the 2.15x training speedup). However, there are minor numerical inconsistencies and definitional ambiguities that require correction for factual accuracy.

First, the Teaser Figure caption states memory usage reduces from 35.4 GB to 19.4 GB. However, Table 3 (`tab:inference_progressive`) lists the BF16 baseline memory as 36.4 GB. Please align these figures or specify the exact configuration (e.g., video length, batch size) for the 35.4 GB claim to ensure consistency between the summary and experimental data.

Second, in Section 2.2, the text claims an "approximately 1.8x training speedup" for the NVFP4 stack. This figure corresponds to the comparison between NVFP4 Balanced SP (639.5s) and BF16 Balanced SP (1196.5s). However, the Abstract claims a "2.15x faster training" speedup, which compares NVFP4 Balanced SP against BF16 w/ SP (1372.9s). The Section 2.2 text should explicitly state "over BF16 Balanced SP" to distinguish it from the Abstract's claim and prevent confusion regarding the magnitude of the improvement.

Finally, the FPS metric requires clarification. The Teaser and Tables report 45.7 FPS, while the E2E generation time for a 64s video is 36.3s (Table 3). Depending on the output frame rate (e.g., 24fps vs 30fps), these metrics imply different real-time factors. Please clarify whether "FPS" refers to model throughput (frames generated per second of compute) or end-to-end system throughput, and ensure the calculation aligns with the reported E2E latency. These corrections will ensure all quantitative claims are precisely supported by the presented data.
