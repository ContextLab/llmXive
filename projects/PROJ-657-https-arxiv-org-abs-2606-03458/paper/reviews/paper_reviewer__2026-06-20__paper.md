---
action_items:
- id: d3141463e020
  severity: writing
  text: 'Provide a complete bibliography with entries for every citation used in the
    manuscript and ensure each entry has verification_status: verified.'
- id: ecda44e77007
  severity: writing
  text: Add a detailed description of the pseudo-decode evaluation protocol (block
    size, quantization schedule, random seeds) to improve reproducibility.
- id: 0ef8d5a2cc91
  severity: writing
  text: Expand the limitations section to discuss applicability to architectures without
    a KV-Cache and potential impact on the generality of the proposed method.
artifact_hash: 41b8c942a61f2cf7279ecdca15cbc48d6d8be293f3b82fe8c5a5b6e8c4e01484
artifact_path: projects/PROJ-657-https-arxiv-org-abs-2606-03458/paper/metadata.json
backend: dartmouth
feedback: Missing verified bibliography entries; requires citation verification.
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-20T04:34:57.051912Z'
reviewer_kind: llm
reviewer_name: paper_reviewer
score: 0.0
verdict: minor_revision
---

## Strengths
- The paper tackles the under‑explored issue of error accumulation in KV‑Cache quantization during long‑horizon decoding, which is crucial for test‑time scaling and reasoning tasks.
- The proposed **KVarN** method combines Hadamard incoherence processing with a Sinkhorn‑inspired dual‑scaling variance normalization, directly addressing token‑wise magnitude errors.
- Comprehensive experiments across multiple models (Qwen3‑4B, Llama‑3.1‑8B, Phi‑4) and benchmarks (MATH500, AIME24, HumanEval, IF‑Eval, line‑retrieval) show consistent improvements over strong baselines (KIVI, QuaRot, TurboQuant, etc.).
- Introduction of a “pseudo‑decode” proxy to simulate error accumulation provides a useful evaluation tool, supported by clear visualizations (Figures 1‑5).
- Runtime overhead is minimal (≈0.18 % extra latency), and the method remains calibration‑free, making it practical for deployment.

## Concerns
- **Bibliography missing**: The compiled PDF contains many citations, but the supplied bibliography summary is empty and no verification status is provided. Acceptance requires all references to be verified.
- **Reproducibility details**: The pseudo‑decode protocol is described conceptually, but concrete hyper‑parameters (e.g., block size = 128, number of Sinkhorn iterations, random seeds) are only briefly mentioned. A more explicit algorithmic description would aid replication.
- **Scope of applicability**: The limitations section notes that models without a KV‑Cache are unsupported, but the paper could benefit from a brief discussion of how the method might be adapted (or why it cannot) to emerging architectures such as state‑space models or latent‑attention variants.
- Minor typographical inconsistencies (e.g., “KV‑Cache” vs. “KV‑cache”, missing spaces after commas) that can be cleaned up.

## Recommendation
The manuscript presents a novel and well‑validated contribution to KV‑Cache quantization for reasoning tasks. However, the lack of a verified bibliography and the need for clearer reproducibility details prevent it from being ready for publication in its current form. I recommend a **minor revision** to address the writing‑level concerns listed above. Once the bibliography is completed and the evaluation protocol is fully specified, the paper should meet the criteria for acceptance.
