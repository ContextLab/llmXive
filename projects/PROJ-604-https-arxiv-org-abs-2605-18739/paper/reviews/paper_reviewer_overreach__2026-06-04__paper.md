---
action_items:
- id: 1afa26cb9d53
  severity: writing
  text: Clarify the role of DMD in the Abstract to avoid overclaiming a 'clean pipeline'.
    Section 2 states DMD is used for distillation, but Abstract (Line 15-18) contrasts
    against methods relying on DMD, implying DMD is not used. Rephrase to specify
    DMD is only for distillation, not AR training.
artifact_hash: 6191ec14b8389b89c96572533c3f6f5e9333a3f73e89fe363432c3a9d7429fb8
artifact_path: projects/PROJ-604-https-arxiv-org-abs-2605-18739/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-04T18:57:52.275576Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper presents a strong case for its efficiency claims, with tables generally supporting the reported speedups (e.g., Table 1, Table 3). However, there are minor areas of potential overreach regarding the "clean pipeline" claim and hardware specificity that require clarification to ensure claims do not extrapolate beyond the methodology.

First, the Abstract claims: "Unlike existing Self-Forcing series methods that rely on ODE initialization and subsequent distribution matching distillation (DMD), LongLive-2.0 directly tunes a diffusion model into a long... AR diffusion model." (Lines 15-18). This phrasing risks overclaiming that DMD is entirely eliminated. Section 2 ("Training Infrastructure") explicitly states: "derive standalone LoRA weights via DMD training directly on the original diffusion model." (Lines 33-34). While the distinction is that DMD is used for *distillation* rather than *initial AR training*, the Abstract's contrast implies a complete avoidance of DMD. To avoid overreach, the Abstract should clarify that the *AR training pipeline* does not rely on DMD, while *real-time conversion* does.

Second, the claim "LongLive-2.0-5B achieves 45.7 FPS inference" (Abstract, Line 24) is supported by the Teaser caption ("21.9 ms/frame") and Table 3 (Row "2 Steps"). However, Table 3 shows 64s video generation takes 36.3s (approx. 42 FPS effective throughput). The 45.7 FPS figure appears to be model throughput, not necessarily end-to-end system throughput for long contexts. While the Teaser clarifies "inference latency... 21.9 ms/frame", the Abstract's standalone claim could be misinterpreted. Adding "model inference" or "per-frame" to the Abstract claim would prevent overreach regarding end-to-end generation speed for long videos.

Finally, the Limitations section (Section 6, Lines 2-8) honestly states that acceleration is hardware-dependent (Blackwell GPUs only). This mitigates overreach regarding hardware portability. The "First NVFP4 training and inference system" claim (Abstract, Line 25) is qualified with "To our knowledge," which is appropriate. Overall, the paper is careful, but the DMD phrasing and FPS specificity need tightening to align claims strictly with the described methodology.
