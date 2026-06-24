---
action_items:
- id: a04c8937eb10
  severity: writing
  text: "Provide a public code repository containing the full training, inference,\
    \ and data\u2011annotation pipelines (e.g., MolmoMotion\u20111M generation, model\
    \ architecture, and downstream transfer scripts)."
- id: 2f52934bad4c
  severity: writing
  text: "Refactor large monolithic source files (e.g., the 600+\u2011line model implementation\
    \ in the appendix) into smaller, logically\u2011grouped modules (data loading,\
    \ model definition, training loop, evaluation) to stay within typical token limits\
    \ and improve readability."
- id: b1c2e34f8d1b
  severity: writing
  text: "Add a clear dependency manifest (requirements.txt or environment.yml) with\
    \ exact version pins for all third\u2011party libraries (e.g., Molmo2, ViPE, AllTracker,\
    \ SAM\u202F3, DiT)."
- id: 4f58d6a86dd9
  severity: writing
  text: "Include reproducibility instructions: data download scripts, preprocessing\
    \ steps, random seed settings, and hardware requirements for each experiment (pretraining,\
    \ fine\u2011tuning, robotics transfer, video generation)."
- id: 79ac030b5a86
  severity: writing
  text: "Supply a suite of unit and integration tests for critical components (e.g.,\
    \ 3D lifting, trajectory filtering, flow\u2011matching loss) and CI configuration\
    \ to ensure they run automatically."
- id: 1e62054cd774
  severity: writing
  text: Document the expected input/output formats for each module (e.g., JSON/YAML
    spec for query points, coordinate serialization, prompt format) and provide example
    files.
artifact_hash: 43d44b1b7f12aef158eaf0787875484ea72c6860cf8af3c796e4579ec99e55ab
artifact_path: projects/PROJ-741-molmomotion-forecasting-point-trajectori/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-24T15:40:40.582181Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_code_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript focuses on a novel task (goal‑conditioned 3D point motion forecasting) and presents extensive experimental results, but it does not include any of the actual code that produced these results. From a code‑quality standpoint this omission prevents any assessment of readability, modularity, testing, dependency hygiene, or reproducibility.

**Readability & Modularity**  
All implementation details are embedded in the LaTeX appendix (e.g., Sections A.3–A.6). The description of the data‑annotation pipeline, model architecture, and training hyper‑parameters is presented as prose rather than as concrete source files. This makes it impossible to verify whether the code follows best practices such as clear naming, separation of concerns, or documentation strings. Large monolithic blocks (e.g., the flow‑matching objective and inference description) would likely exceed typical token limits if placed in a single script; they should be split into dedicated modules (e.g., `data/pipeline.py`, `model/arch.py`, `train/loop.py`).

**Testing**  
No unit or integration tests are mentioned. Critical components—3‑D point lifting, trajectory filtering, and the flow‑matching decoder—are error‑prone and would benefit from deterministic tests (e.g., synthetic data with known ground truth). Without a test suite, regressions cannot be detected, and reviewers cannot verify correctness.

**Dependency Hygiene**  
The paper lists many external tools (Molmo2, ViPE, AllTracker, SAM 3, DiT, Qwen3, etc.) but does not provide a manifest with exact version numbers. This hampers reproducibility because minor version changes can alter model behavior or data‑pipeline outputs.

**Reproducibility**  
The experimental section describes training schedules (e.g., “40 K steps”, “10 K steps”) and hardware (16 × H100 GPUs) but lacks scripts to automate data download, preprocessing, and training. Random seed settings, mixed‑precision flags, and distributed training configurations are only briefly mentioned in prose. A reproducibility checklist (data URLs, checksum verification, command‑line arguments) is essential for others to replicate the results.

**Recommendations**  
To bring the project to an acceptable code‑quality level, the authors should open a public repository (e.g., GitHub) containing:
1. Structured source code with clear module boundaries.
2. `requirements.txt`/`environment.yml` with pinned versions.
3. `README.md` detailing step‑by‑step reproduction instructions, including hardware requirements and expected runtimes.
4. Automated scripts for data acquisition, annotation, training, and evaluation.
5. A comprehensive test suite integrated with CI (GitHub Actions or similar).

Providing these artifacts will enable a full assessment of code quality, ensure that the impressive empirical results are trustworthy, and facilitate future research building on this work.
