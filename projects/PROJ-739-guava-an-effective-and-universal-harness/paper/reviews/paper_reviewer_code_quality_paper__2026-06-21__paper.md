---
action_items:
- id: a6b8ddac430b
  severity: fatal
  text: Provide a public code repository containing the full implementation of the
    Guava harness, tool APIs, data generation engine, and training pipelines.
- id: 0deb700d4154
  severity: fatal
  text: "Add a detailed README with step\u2011by\u2011step instructions to reproduce\
    \ the data collection (2K trajectories), supervised fine\u2011tuning, and GRPO\
    \ reinforcement learning, including exact command\u2011line invocations."
- id: 1876bb017b8b
  severity: fatal
  text: Specify all software dependencies (Python version, libraries, CUDA/cuDNN versions)
    in a requirements.txt or environment.yml file; consider providing a Dockerfile
    for containerised reproducibility.
- id: 68681832eb29
  severity: writing
  text: "Modularise the codebase: separate modules for (a) tool definitions, (b) harness\
    \ loop logic, (c) model inference wrappers, (d) training scripts, and (e) evaluation\
    \ scripts. Each module should be <200\u202FLOC and have a clear API."
- id: 8ddc78d6a239
  severity: writing
  text: "Include unit tests for each tool (e.g., grasp, move, align) and for the ReAct\u2011\
    style loop to verify correct request/response handling and error\u2011recovery\
    \ pathways."
- id: 5f4e2c6a9e3c
  severity: writing
  text: Remove duplicate LaTeX package imports (e.g., multiple \usepackage{tcolorbox}
    and \usepackage{wrapfig}) and consolidate style definitions to improve maintainability
    of the manuscript source.
- id: 09476c669b46
  severity: writing
  text: Document random seeds and any stochastic components (scene randomisation,
    perturbation generation) used during data collection so that exact trajectories
    can be regenerated.
- id: cf19397bc05a
  severity: writing
  text: "Provide scripts to automatically generate the evaluation tables and figures\
    \ (e.g., success\u2011rate CSV \u2192 LaTeX table, plot generation) to avoid manual\
    \ transcription errors."
artifact_hash: 305fa4e0caf5509b3ff951ed539855921f525d3dfdda7d54d245e51eb00f86f3
artifact_path: projects/PROJ-739-guava-an-effective-and-universal-harness/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-21T00:45:12.446318Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_code_quality_paper
score: 0.0
verdict: minor_revision
---

The review concentrates solely on the reproducibility and code quality of the Guava framework. While the manuscript is well‑organized and the experimental results are impressive, the paper does not provide any source code, build scripts, or environment specifications. Consequently, reviewers and future researchers cannot verify the claims, reproduce the 2 K simulation trajectories, or re‑run the two‑stage training pipeline (SFT + GRPO).

From the LaTeX source we also notice minor maintainability issues: duplicate `\usepackage{tcolorbox}` and `\usepackage{wrapfig}` statements, and a proliferation of custom commands that could be consolidated into a single style file. Although these do not affect the scientific content, they suggest a lack of systematic code hygiene that may extend to the (unreleased) implementation.

To satisfy reproducibility standards, the authors should release a clean, well‑documented codebase that includes:

1. **A public repository** with the full implementation of the Guava harness, tool APIs, data generation engine, and training pipelines.
2. **A detailed README** offering step‑by‑step instructions for reproducing data collection (2 K trajectories), supervised fine‑tuning, and GRPO reinforcement learning, including exact command‑line invocations.
3. **Dependency specifications** via `requirements.txt` or `environment.yml`, and preferably a Dockerfile to ensure environment consistency (Python version, library versions, CUDA/cuDNN, etc.).
4. **Modular code organization**: separate modules for (a) tool definitions, (b) harness loop logic, (c) model inference wrappers, (d) training scripts, and (e) evaluation scripts. Each module should be under 200 lines of code and expose a clear API.
5. **Unit and integration tests** for each tool (e.g., `grasp`, `move`, `align`) and for the ReAct‑style loop to verify correct request/response handling and error‑recovery pathways.
6. **Removal of duplicate LaTeX imports** and consolidation of style definitions to improve maintainability of the manuscript source.
7. **Documentation of random seeds** and any stochastic components (scene randomisation, perturbation generation) used during data collection, enabling exact regeneration of trajectories.
8. **Automation scripts** that generate the evaluation tables and figures directly from CSV or log files, avoiding manual transcription errors.

Providing these artifacts will greatly enhance the paper’s transparency, allow independent verification of the reported 75.6 % overall success rate, and facilitate future research building on the Guava harness. Until such resources are made available, the manuscript cannot be considered fully reproducible, justifying a minor‑revision decision.
