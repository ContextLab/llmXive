---
action_items:
- id: a16a40a6a1b5
  severity: writing
  text: Add a verification table indicating that every cited reference has been checked
    and marked as verified.
- id: 00e9cfc33a3f
  severity: writing
  text: "Provide explicit scripts or detailed instructions for the applicability\u2011\
    filtering and injection\u2011generation steps, including the exact prompts used,\
    \ to enable full reproducibility of the MedMisBench construction."
- id: cb624884363c
  severity: writing
  text: "Discuss the limitations of using synthetic, model\u2011generated misleading\
    \ context and how this may affect the generality of the reported results."
- id: e2b0b66bd579
  severity: writing
  text: "Clarify the evaluation protocol for proprietary APIs (e.g., GPT\u20115.4,\
    \ Gemini) and provide guidance for researchers who only have access to open\u2011\
    weight models."
artifact_hash: b321ce34848cd04bd8d899e341b97cc74f8e7595fd9393bb1f9638bbf57b0d10
artifact_path: projects/PROJ-704-measuring-epistemic-resilience-of-llms-u/paper/metadata.json
backend: dartmouth
feedback: Citations lack verification status and reproducibility details for the benchmark
  generation pipeline need clarification.
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-18T21:45:30.669780Z'
reviewer_kind: llm
reviewer_name: paper_reviewer
score: 0.0
verdict: minor_revision
---

## Strengths
- Introduces a novel benchmark (MedMisBench) that explicitly measures *epistemic resilience* of LLMs under misleading medical context, filling a clear gap in existing medical evaluation suites.
- Provides a comprehensive taxonomy of misleading‑context types (5 content corruptions × 3 provenance framings) and applies it across five diverse source datasets, yielding a large, diverse benchmark (10,932 items, 48,889 option‑level pairs).
- Empirical results are thorough, covering 11 model configurations (commercial, open‑weight, and domain‑specialized) and two delivery protocols, revealing a substantial drop in performance under focused misleading context (ASR ≈ 51.5%).
- Includes a well‑designed clinician review (14 clinicians from 7 countries) that validates benchmark item quality and quantifies potential clinical harm of misled model outputs.
- Open‑source release (code, dataset schema, taxonomy) enables future work on mitigation and extension.

## Concerns
- **Citation verification**: The bibliography summary does not indicate that all references have `verification_status: verified`. Acceptance requires every cited reference to be verified.
- **Reproducibility of benchmark construction**: While the appendix lists prompts, the main paper lacks a concrete, version‑controlled script for the applicability‑filtering and injection‑generation pipeline. Researchers without access to the same LLMs (Gemini‑3‑flash, GPT‑5.4) may find it difficult to reproduce the exact benchmark items.
- **Dependence on proprietary APIs for evaluation**: The primary experimental results rely on closed‑source commercial models accessed via APIs. The paper should provide guidance or alternative evaluation scripts for open‑weight models to ensure the benchmark can be used by the broader community.
- **Limited discussion of synthetic injection bias**: The benchmark uses LLM‑generated misleading context, which may inherit biases from the generator. A deeper analysis of how generator choice could affect downstream resilience metrics would strengthen the work.
- **Methodological details**: The description of the “applicability‑filtering” step is high‑level; more quantitative statistics (e.g., number of items rejected per content type) would improve transparency.

## Recommendation
The manuscript presents a valuable contribution to the evaluation of medical LLMs, but it falls short of the strict acceptance criteria due to missing citation verification and insufficient reproducibility details for the benchmark generation pipeline. I recommend a **minor revision** to address the writing‑level concerns listed above, after which the paper should be ready for acceptance.
