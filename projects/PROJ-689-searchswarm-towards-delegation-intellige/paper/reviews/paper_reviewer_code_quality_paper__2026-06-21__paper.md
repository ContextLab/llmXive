---
action_items:
- id: efed8a04d1bc
  severity: fatal
  text: The submission does not include any source code, build scripts, or a public
    repository link for the SearchSwarm implementation, making reproducibility impossible.
- id: aa0680842b68
  severity: fatal
  text: "No dependency manifest (e.g., requirements.txt, environment.yml, or Dockerfile)\
    \ is provided; reviewers cannot verify that the model fine\u2011tuning pipeline\
    \ can be re\u2011run from scratch."
- id: 4c604d78f829
  severity: writing
  text: "The paper lacks a detailed description of the software architecture (module\
    \ boundaries, class responsibilities, and data flow) beyond high\u2011level figures,\
    \ preventing assessment of modularity and readability."
- id: 66d5510f02cf
  severity: fatal
  text: There is no test suite or evaluation script included; without unit/integration
    tests the correctness of data filtering, harness enforcement, and training loops
    cannot be validated.
- id: 469abc1ab742
  severity: writing
  text: "The appendix only contains prompt snippets; the actual code that implements\
    \ the harness, sub\u2011agent spawning, and context\u2011window management is\
    \ omitted, hindering code\u2011quality review."
artifact_hash: 23164a835e9fc14f10b36f04bd2aeba4213e5a3b759192c46a449dbfe25b61f3
artifact_path: projects/PROJ-689-searchswarm-towards-delegation-intellige/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-21T09:49:41.745872Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_code_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript focuses on the conceptual contribution of a delegation harness and reports strong benchmark numbers, but from a code‑quality perspective the submission is severely lacking. No source files, scripts, or repository URLs are provided, so the reviewer cannot inspect the implementation for readability, modularity, or test coverage. Critical components such as the harness logic that enforces the four delegation principles, the sub‑agent spawning mechanism, and the data‑filtering pipeline are described only in prose and in brief prompt listings (Appendix § \ref{sec:appendix-prompts}), without any accompanying code. This omission prevents verification that the system is organized into coherent modules (e.g., separate packages for model definition, training loop, I/O, and evaluation) and that naming conventions, docstrings, and type annotations follow best practices.

Reproducibility is another major concern. The paper mentions fine‑tuning a 30 B model with a learning‑rate schedule and batch size, yet it does not supply a dependency manifest (requirements.txt, conda environment, or Dockerfile) nor specify exact library versions (e.g., PyTorch, Transformers, DeepSpeed). Without this information, even if the code were released, reproducing the results would be error‑prone. Moreover, the experimental setup lacks a clear, version‑controlled evaluation script; the tables (e.g., Table \ref{tab:main-results}) present scores but do not indicate how the DeepSeek‑V4‑Flash judge was invoked, what random seeds were used, or whether multiple runs were averaged.

The absence of a test suite is especially problematic for a system that orchestrates multiple agents and tools. Unit tests for the harness’s enforcement of the four principles, integration tests for the `call_sub_agent` API, and regression tests for the filtering pipeline would provide confidence that the reported trajectories are generated correctly and that no hidden bugs (e.g., token‑budget leaks) exist. The paper also does not discuss continuous‑integration practices or code‑style checks, which are standard for ensuring maintainable codebases.

To bring the artifact up to community standards, the authors should release a public repository containing:
1. All source code (preferably in a modular layout such as `searchswarm/`, `training/`, `evaluation/`).
2. A complete dependency list and environment setup instructions.
3. Scripts to reproduce the data collection, filtering, and fine‑tuning steps, with fixed random seeds.
4. A comprehensive test suite covering harness logic, sub‑agent communication, and evaluation metrics.
5. Documentation (README, API docs) that explains how to run the system on new queries.

Providing these materials will enable a thorough code‑quality assessment, ensure reproducibility, and increase the impact of the SearchSwarm contribution.
