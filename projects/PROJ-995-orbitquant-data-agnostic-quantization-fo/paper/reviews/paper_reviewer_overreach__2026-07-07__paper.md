---
action_items:
- id: 35695e5580f3
  severity: writing
  text: Abstract/Conclusion claim 'sets the state of the art' and 'only method' at
    W2A4. Table 1 shows OrbitQuant leads overall but AdaTSQ beats it on 'Two object'
    (FLUX-schnell W4A4). 'Only method' is true for tested baselines, but 'SOTA' implies
    universal dominance. Narrow to 'best among calibration-free methods' or 'best
    overall score on tested models'.
- id: 5aeea90dc083
  severity: writing
  text: Abstract claims 'no per-modality tuning' for image-to-video transfer. Section
    3.2 shows video results but doesn't confirm if RPBH permutation seeds were shared
    or re-sampled. If re-sampled, this is per-modality config. Clarify if exact same
    seeds/params were used across modalities to support the claim.
- id: 01443543e23e
  severity: writing
  text: Conclusion states 'supports usable 2-bit weights'. Table 1 shows Z-Image-Turbo
    drops from 0.754 (FP16) to 0.319 (W2A4), a >50% drop. 'Usable' is subjective here.
    Qualify as 'retains non-trivial performance' or acknowledge Z-Image-Turbo degradation
    to avoid overgeneralizing W2A4 robustness.
artifact_hash: d056dc4f21ae1b95e98f52ede135ede40ce7ffad195ba83894f4cf9d35e33f1a
artifact_path: projects/PROJ-995-orbitquant-data-agnostic-quantization-fo/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-07T04:51:49.532403Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several strong claims regarding the universality and state-of-the-art status of OrbitQuant that slightly exceed the scope of the provided experimental evidence.

First, the Abstract and Conclusion assert that OrbitQuant "sets the state of the art" and is "the only method" that produces usable images at W2A4. While Table 1 confirms that OrbitQuant outperforms the *tested* calibration-based baselines (SVDQuant, ViDiT-Q, etc.) which collapse to near-zero scores at W2A4, the claim of "state of the art" is slightly overstated when looking at W4A4 results. For instance, on FLUX.1-schnell W4A4, AdaTSQ achieves an Overall score of 0.680, while OrbitQuant scores 0.703. While OrbitQuant leads, the margin is not overwhelming, and on specific sub-tasks (e.g., "Two object" on FLUX.1-schnell), AdaTSQ (0.894) actually outperforms OrbitQuant (0.881). The rhetoric implies a blanket superiority that the data shows is conditional on the specific metric and model. The claim should be narrowed to "sets the state of the art among calibration-free methods" or "achieves the best overall GenEval score across the tested models and bit-widths."

Second, the Abstract claims the method "transfers from image to video with no per-modality tuning." The experiments in Section 3.2 and Table 2 demonstrate success on video models (Wan, CogVideoX), but the paper does not explicitly clarify if the random permutation seeds for the RPBH rotation were shared between image and video models or re-sampled. If the permutation is re-sampled for the video domain, this constitutes a form of per-modality configuration (even if not "calibration" in the traditional sense). To support the "no tuning" claim rigorously, the authors should confirm that the exact same random seeds/parameters were applied across modalities or clarify that "no tuning" strictly refers to the absence of data-dependent calibration.

Finally, the Conclusion states the method "supports usable 2-bit weights." While OrbitQuant significantly outperforms collapsed baselines at W2A4, the performance on Z-Image-Turbo drops from 0.754 (FP16) to 0.319 (W2A4). A >50% drop in GenEval score challenges the descriptor "usable" without qualification. The conclusion should either define "usable" (e.g., "retains non-trivial performance") or explicitly acknowledge the degradation on Z-Image-Turbo to avoid implying that W2A4 is equally robust across all architectures.

These are primarily rhetorical overreaches that can be fixed by tightening the language in the Abstract and Conclusion to match the specific boundaries of the experimental results.
