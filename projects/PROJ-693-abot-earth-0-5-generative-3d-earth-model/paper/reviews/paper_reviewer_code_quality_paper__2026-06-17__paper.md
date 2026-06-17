---
action_items:
- id: 4cf9904e1a63
  severity: writing
  text: The submission provides only LaTeX source; no source code, build scripts,
    or dependency specifications for the generative model are included, making reproducibility
    impossible.
- id: cc49b084fe82
  severity: writing
  text: All implementation is embedded in a single monolithic .tex file (e.g., main-llmxive.tex)
    without modular organization of code, configuration, or data pipelines, hindering
    readability and maintainability.
- id: 162b144e5480
  severity: writing
  text: There are no test suites, unit tests, or validation scripts accompanying the
    described data pipeline and model training; this prevents verification of correctness.
- id: e5d944c5b326
  severity: writing
  text: "Dependency hygiene is absent \u2013 no requirements.txt, environment.yml,\
    \ Dockerfile, or conda environment specification is provided for the Python/C++\
    \ components implied by the method."
- id: 605515c83ee6
  severity: writing
  text: "Reproducibility instructions (e.g., data download URLs, preprocessing steps,\
    \ training hyper\u2011parameters, hardware requirements) are missing from the\
    \ manuscript and supplementary material."
- id: 6d79e58d15a0
  severity: writing
  text: "Large binary assets (e.g., pretrained model checkpoints, trillion\u2011scale\
    \ Gaussian primitive datasets) are referenced but no guidance is given on how\
    \ to obtain or generate them."
artifact_hash: 889d5a8e39acbdaa7baa4d1b8f93a551383f0dbc1ede3c36f50fc7a5e7bb8167
artifact_path: projects/PROJ-693-abot-earth-0-5-generative-3d-earth-model/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-17T06:18:26.454689Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_code_quality_paper
score: 0.0
verdict: minor_revision
---

The review focuses exclusively on the code‑quality aspects of the artifacts that would underpin the reported research. The supplied material consists solely of LaTeX source files (main‑llmxive.tex, sections/*.tex, and a handful of table/figure TeX fragments). No actual implementation code (Python, C++, scripts, or notebooks) is present, nor are there any build or execution instructions.

From a software‑engineering standpoint this raises several critical issues:

1. **Absence of Source Code** – The paper describes a complex pipeline (data collection, 3DGS reconstruction, multi‑LOD generation, large‑scale deployment) but provides no corresponding source files. Without the code, readers cannot verify algorithmic details, reproduce experiments, or extend the system.

2. **Monolithic Document Structure** – All methodological descriptions are embedded directly in the LaTeX manuscript. There is no modular organization (e.g., separate modules for data preprocessing, model training, inference, post‑processing). This makes the code base (were it present) hard to navigate and maintain.

3. **Missing Dependency Specification** – No `requirements.txt`, `environment.yml`, or Dockerfile is supplied. The paper references a variety of third‑party libraries (e.g., Gaussian splatting, vision‑language models, distributed GPU training) but without a declared dependency list the exact software stack cannot be reconstructed.

4. **Lack of Testing Infrastructure** – No unit tests, integration tests, or validation scripts are provided. For a system that claims to process trillions of Gaussian primitives and operate at planetary scale, a rigorous testing suite is essential to catch bugs and ensure stability.

5. **Reproducibility Gaps** – Critical details such as dataset download URLs, preprocessing pipelines, hyper‑parameter values, and hardware configurations (GPU model, memory limits) are only described in prose. There is no reproducibility checklist, nor are there scripts to automate the end‑to‑end pipeline from raw satellite imagery to a generated 3D tile.

6. **Large Asset Handling** – The manuscript mentions “hundreds of billions of Gaussian primitives” and “trillion‑scale datasets” but does not provide any guidance on storage formats, chunking strategies, or how to obtain pretrained model checkpoints. This omission makes it impossible for an external party to even attempt a scaled‑down replication.

Given these shortcomings, the manuscript cannot be evaluated for code quality or reproducibility. The authors should release the full source repository, include clear build and environment specifications, provide a minimal test suite, and supply scripts (or at least detailed pseudo‑code) that enable a third party to reproduce the core components of ABot‑Earth 0.5.
