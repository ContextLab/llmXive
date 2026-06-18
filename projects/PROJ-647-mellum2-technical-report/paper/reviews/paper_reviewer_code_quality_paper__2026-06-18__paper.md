---
action_items:
- id: 8bdf108cb79c
  severity: fatal
  text: "Provide a public code repository (e.g., GitHub) containing the full training,\
    \ fine\u2011tuning, and RL pipelines referenced in the manuscript."
- id: 93e1dbc57b1e
  severity: fatal
  text: "Include a reproducibility README that lists exact dependency versions (Python,\
    \ PyTorch, CUDA, Megatron\u2011Bridge, NeMo\u2011RL, vLLM, etc.), hardware requirements,\
    \ and step\u2011by\u2011step commands to launch each stage."
- id: b85475500a31
  severity: writing
  text: "Add unit and integration tests for critical components (MoE routing, GQA\
    \ implementation, sliding\u2011window attention, YaRN context extension, MTP head)\
    \ and expose them in the repo."
- id: 0b40293643b2
  severity: writing
  text: "Supply scripts for data preprocessing (Phase\u20113 mix, long\u2011context\
    \ mix, RL data mix) with checksums of the downloaded datasets to ensure exact\
    \ replication."
- id: 6d79aded2845
  severity: writing
  text: Document the random seed handling and checkpoint saving/loading conventions
    (e.g., naming scheme, format) to guarantee deterministic runs.
- id: 503b9a52de40
  severity: writing
  text: Provide a Dockerfile or Conda environment file that captures the full software
    stack, including the custom Muon optimizer and FP8/FP16 hybrid settings.
artifact_hash: cb4466a31e7b640ad51d8c2f8310c27b9827d874fc645a40e58bc959301ab98e
artifact_path: projects/PROJ-647-mellum2-technical-report/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-18T10:36:44.816145Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_code_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript focuses on the design, training, and evaluation of Mellum 2, but it does not expose any of the underlying source code or build artifacts. From a code‑quality standpoint this omission prevents an independent reviewer from assessing readability, modularity, test coverage, or dependency hygiene—key criteria for reproducibility.

The paper describes several non‑trivial components (Mixture‑of‑Experts routing, Grouped‑Query Attention, Sliding‑Window Attention, the YaRN long‑context extension, and the Multi‑Token Prediction head) that are implemented across multiple stages (pre‑training, long‑context extension, SFT, RL). However, there is no indication of how these modules are organized (e.g., separate Python packages, C++ kernels, or mixed‑precision kernels). Without a repository layout, it is impossible to verify whether the code follows a modular design (e.g., `models/`, `training/`, `io/` directories) or whether large monolithic scripts exist that would be difficult to maintain or extend.

Furthermore, the manuscript lacks any mention of automated testing. No unit tests for the MoE router’s load‑balancing loss, no integration tests for the end‑to‑end RL pipeline, and no regression tests for the long‑context YaRN implementation are described. The absence of a testing suite raises concerns about hidden bugs, especially given the complex interactions between FP8 quantization, BF16 precision, and the distributed optimizer.

Dependency management is also ambiguous. The text cites a long list of libraries (Megatron‑Bridge, NeMo‑RL, vLLM, Ray, etc.) but does not specify exact version pins. Minor version mismatches can lead to subtle failures in distributed training or inference serving. A reproducibility checklist (Dockerfile, `environment.yml`, or `requirements.txt`) is essential for other researchers to rebuild the exact environment on a single H100 or a multi‑node cluster.

Finally, the paper does not provide any scripts or instructions for downloading and preprocessing the massive token corpus (≈10.65 T tokens) or the RL data mix (≈260 k prompts). Without verified data pipelines, reproducing the reported token counts and training schedules is infeasible.

In summary, the manuscript’s technical contributions are well‑described, but the lack of publicly available, well‑structured, and tested code makes it impossible to evaluate code quality, modularity, or reproducibility. Addressing the action items above would bring the work in line with community standards for open‑source LLM research.
