---
artifact_hash: b4bbb587409bb8ce9fbc13953a4d6d307cbe54e41c3196b0506aac091594e206
artifact_path: projects/PROJ-566-mint-managed-infrastructure-for-training/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-05-17T14:56:06.768638Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_code_quality_paper
score: 0.0
verdict: minor_revision
---

**Code Quality Artifacts Missing for Reproducibility Review**

This review lens evaluates the implementation artifacts that produced the paper's results. The provided submission contains only LaTeX source files and compiled PDFs—no implementation code, tests, or reproducibility infrastructure is included. Per the paper's claims of public reproducibility paths (Section 1, contributions #4), the following code-quality artifacts are required but absent:

1. **Implementation Repository**: No link to the MinT codebase is provided in the paper. Section 1 states "MinT provides a Tinker-compatible API and uses mint-cookbook recipes" but no repository URL, commit hash, or version tag is specified for reproducibility.

2. **Dependency Manifest**: No `requirements.txt`, `pyproject.toml`, `environment.yml`, or Dockerfile is included. Section 5.2 describes serving experiments on Qwen3-30B with vLLM, Megatron, and PEFT, but exact dependency versions (e.g., vLLM commit, Megatron-LM fork, PyTorch version) are unspecified.

3. **Test Suite**: No test files are present. For a system claiming million-scale policy catalog management and distributed training, unit/integration tests for the adapter export path, cache tier logic, and cold-load scheduling are essential for quality assurance.

4. **CI/CD Configuration**: No workflow files demonstrate automated testing or reproducibility verification. The paper reports precise metrics (e.g., 8.5–8.7× loading speedup, 18.3× handoff reduction) but provides no mechanism to verify these measurements.

5. **Reproducibility Scripts**: Section 5 describes concurrent GRPO training and serving benchmarks but no scripts to reproduce the `eval_n3_schedule_timeline.png`, `eval_handoff_breakdown.png`, or `eval_moe_scale_curves.png` figures.

**Specific Recommendations**:

- Add a `CODE_REPOSITORY` field in the LaTeX metadata pointing to a public repository with version tag
- Include a `scripts/` directory with experiment reproduction scripts (e.g., `run_handoff_benchmark.py`, `run_cold_load_staircase.py`)
- Provide `requirements.txt` with pinned versions for all experimental dependencies
- Add a `tests/` directory with coverage for critical paths: adapter export, cache tier promotion, cold-load scheduling
- Include a `Dockerfile` or `docker-compose.yml` for environment reproducibility

Without these artifacts, the code quality and reproducibility claims in Section 1 cannot be evaluated. The paper should be revised to include implementation artifacts or provide explicit repository references with version-controlled snapshots.
