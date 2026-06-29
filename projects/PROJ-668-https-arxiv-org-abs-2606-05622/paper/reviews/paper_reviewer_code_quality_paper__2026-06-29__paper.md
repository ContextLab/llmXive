---
action_items:
- id: a17efd5daddb
  severity: science
  text: Code repository (https://github.com/JiayuJeff/AdaPlanBench) not accessible
    for review. Cannot verify modularity, test coverage, dependency management, or
    reproducibility scripts. Authors should provide direct repository access or include
    code quality documentation in submission.
- id: 6858b08d6d48
  severity: science
  text: Paper mentions vLLM dependency (Section 2, Ethics) but no requirements.txt
    or environment specification visible in provided materials. Reproducibility from
    scratch cannot be verified.
artifact_hash: 4c1448d6284f48048906ba145a0a228414d922f3ed6467261dd793143d8d0ecf
artifact_path: projects/PROJ-668-https-arxiv-org-abs-2606-05622/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T08:39:20.316072Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_code_quality_paper
score: 0.0
verdict: minor_revision
---

**Code Quality Review — AdaPlanBench**

This review is constrained by the arXiv ingestion pipeline: the actual code repository is not accessible for direct inspection. The paper references a GitHub repository (https://github.com/JiayuJeff/AdaPlanBench) and HuggingFace dataset (https://huggingface.co/datasets/JiayuJeff/AdaPlanBench), but I cannot evaluate the following code quality dimensions:

1. **Modularity & Structure**: The paper describes a multi-component pipeline (rewriter, filter, planners, extractor, merger, checker — Section "Environment Construction Algorithm"), but I cannot verify whether these are implemented as separate modules or monolithic scripts. A 600-line `dpgmm.py`-style monolith mixing model class + training + logging + I/O would violate modern code quality standards.

2. **Test Coverage**: No test files or coverage metrics are visible in the provided materials. The paper claims 307 tasks with 240 human-annotated trajectories, but there is no evidence of automated test suites validating constraint-checking logic or rubric scoring consistency.

3. **Dependency Hygiene**: The paper mentions vLLM for open-source model execution (Ethics statement) and NVIDIA H100 GPUs (Experiment Setup), but no `requirements.txt`, `pyproject.toml`, or Dockerfile is provided. This prevents reproducibility from scratch.

4. **Reproducibility Artifacts**: While the paper provides prompt templates (Figures 10-14) and rubric definitions (Table 5), the actual evaluation harness code is not inspectable. Confidence intervals (Table 4) and ablation studies (Tables 2-3) cannot be independently verified without access to the evaluation pipeline.

**Recommendations for Revision**:
- Include a `CODE_QUALITY.md` or `REPRODUCIBILITY.md` in the repository documenting module structure, test coverage percentage, and dependency versions.
- Provide a `requirements.txt` or `environment.yml` with pinned versions for all dependencies (vLLM, transformers, etc.).
- Add a `tests/` directory with unit tests for constraint-checking logic and rubric scoring functions.
- Consider splitting any monolithic evaluation scripts into modular components (e.g., `evaluator/`, `constraints/`, `metrics/`) to improve maintainability.

Without repository access, code quality assessment remains incomplete. This is a minor revision requirement, not a fatal flaw, as the paper's scientific claims are otherwise well-supported.
