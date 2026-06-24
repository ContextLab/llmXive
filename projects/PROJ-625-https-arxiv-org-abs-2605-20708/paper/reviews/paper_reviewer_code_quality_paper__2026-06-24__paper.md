---
action_items:
- id: aa7cbdb51714
  severity: fatal
  text: The submission does not include any source code, training scripts, or a reproducibility
    package; provide a public repository with the full implementation (model definition,
    data pipeline, training loop, evaluation scripts).
- id: 275b0f6c9633
  severity: fatal
  text: "Add a clear `README` that lists all required dependencies (exact package\
    \ versions, CUDA/cuDNN requirements) and step\u2011by\u2011step instructions to\
    \ reproduce the ImageNet experiments."
- id: 031dbafca540
  severity: writing
  text: 'Modularize the implementation: separate model architecture, routing module
    (DAR), and utility functions into distinct Python modules or packages rather than
    a single monolithic script.'
- id: 2650e7629bb0
  severity: writing
  text: Include unit and integration tests for the core components (e.g., DAR attention
    routing, chunked aggregation, RMSNorm) to ensure correctness and guard against
    regressions.
- id: a3fce83c8679
  severity: writing
  text: Provide a `setup.py`/`pyproject.toml` or `requirements.txt` with pinned versions
    to guarantee dependency hygiene across environments.
- id: 2b6803ef031a
  severity: writing
  text: Document the custom Triton kernels (fusion implementation) with comments,
    type hints, and a small benchmark script to verify performance claims.
- id: a634e6a669e8
  severity: writing
  text: If the code relies on external data (ImageNet), include scripts to download,
    preprocess, and verify the dataset checksum.
artifact_hash: 7a4bc7e64a39662319f7490ada4c2be57d6c20dd18ca5f1225c2e0b697bf14b3
artifact_path: projects/PROJ-625-https-arxiv-org-abs-2605-20708/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-24T18:01:06.766017Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_code_quality_paper
score: 0.0
verdict: minor_revision
---

The review focuses exclusively on the code‑quality aspects of the artifacts that underpin the paper “Rethinking Cross‑Layer Information Routing in Diffusion Transformers”. While the manuscript provides extensive experimental results and a thorough diagnostic study, the submission lacks any executable code or reproducibility package. Consequently, the core claims (e.g., 8.75× faster convergence, FID improvements) cannot be independently verified, which is a critical shortcoming for a work that introduces a new architectural component (Diffusion‑Adaptive Routing, DAR).

From a software‑engineering perspective, the provided LaTeX source is a single monolithic file (`main-llmxive.tex`) that embeds figures, tables, and the entire narrative. There is no accompanying Python implementation, no modular directory structure, and no build or execution scripts. This makes it impossible to assess readability, modularity, or test coverage. Moreover, the paper mentions a “fused Triton kernel” for the vertical aggregation, yet no source code, kernel definitions, or compilation instructions are supplied. Without these, reviewers cannot evaluate the claimed latency and memory savings, nor can they confirm numerical equivalence to the reference PyTorch implementation.

Reproducibility is further hampered by the absence of a dependency manifest. The manuscript references many external libraries (e.g., `torch`, `timm`, `triton`, `accelerate`) but does not specify version constraints, CUDA toolkit requirements, or hardware specifications beyond a generic “NVIDIA H20”. A reproducibility checklist should include exact package versions, a `requirements.txt` or `pyproject.toml`, and instructions for setting up the environment (conda or virtualenv). The lack of a `README` also means that potential users cannot locate the entry point for training or evaluation, nor understand how to configure the chunk size, query variant, or timestep injection options described in Sections 4–5.

Testing is another major gap. The paper introduces several non‑trivial components (softmax‑weighted depth aggregation, chunked summarization, dynamic query generation) that are prone to subtle bugs (e.g., numerical instability, gradient mismatches). Providing unit tests for each module, as well as integration tests that run a short training loop on a toy dataset, would greatly increase confidence in the implementation and facilitate future extensions.

In summary, the manuscript’s scientific contributions are promising, but the current submission fails to meet basic code‑quality standards required for reproducible research. The authors should release a well‑structured codebase with comprehensive documentation, dependency specifications, and tests before the paper can be accepted.
