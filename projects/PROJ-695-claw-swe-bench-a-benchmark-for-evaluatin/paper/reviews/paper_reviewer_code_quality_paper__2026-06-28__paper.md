---
action_items:
- id: a59824046e09
  severity: science
  text: Code repository link lacks commit hash/version pinning. Add specific git commit
    SHA to ensure reproducibility of the exact benchmark version used in experiments.
- id: 17ee64b7f58f
  severity: science
  text: Appendix D describes harness implementations but provides no test coverage
    metrics. Add unit/integration test counts and coverage percentages for the adapter
    protocol and each claw.
- id: a8e8a32234e7
  severity: science
  text: Dependency specifications (UV, Docker images) need exact version pinning.
    Include requirements.txt, pyproject.toml, or Dockerfile with pinned versions for
    full reproducibility from scratch.
- id: 64843692b793
  severity: science
  text: Benchmark construction algorithm (Sec 4.2) describes objective function but
    omits exact coefficient values (cost_alpha, RANK_EPS, lambda). Add these to appendix
    for reproducibility.
artifact_hash: d91d9216ec1b23d5ae21a0d631e31b9f94ceb55943984c394279379a22a67899
artifact_path: projects/PROJ-695-claw-swe-bench-a-benchmark-for-evaluatin/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-28T17:54:56.388853Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_code_quality_paper
score: 0.0
verdict: minor_revision
---

**Code Quality Review — Claw-SWE-Bench**

This review focuses on the code quality of artifacts that produced the paper, specifically reproducibility, modularity, tests, and dependency hygiene as described in the manuscript.

**Reproducibility Concerns**

The paper states code is at `https://github.com/opensquilla/claw-swe-bench` (Abstract, Sec 1) but provides no commit hash or version tag. For a benchmark paper, this is critical: the exact code state must be pinned to ensure results are reproducible. Recommend adding a specific git SHA in the abstract or footnote.

The benchmark construction algorithm (Sec 4.2, Appendix F) describes a binary selection problem with L1, ranking, and cost terms but omits exact coefficient values. The text mentions `cost_alpha=1`, `RANK_EPS=0.03`, and `lambda=1.0` but these should be in a machine-readable config file or appendix table for exact reproduction.

**Modularity Assessment**

The adapter protocol (Sec 3.2) is well-architected with abstract methods (`create_agent`, `send_task`, `backup_session`, `delete_agent`, `get_docker_args`). This interface cleanly separates harness implementation from orchestration. However, the paper does not show the actual adapter implementation code or how the 5 claws implement these methods. Appendix D provides implementation notes but lacks code snippets showing the adapter wrapper for each harness.

**Testing Gap**

No mention of test coverage, unit tests, or integration tests for the adapter protocol or harness implementations. For a benchmark that will be used by others, test coverage metrics (e.g., "adapter protocol: 95% line coverage, 120 unit tests") should be reported. The harness configurations in Appendix D describe stopping conditions and tool inventories but not how these are validated.

**Dependency Hygiene**

The paper mentions UV-managed Python environments (Appendix D.2, D.4, D.5) and Docker containers (Sec 3.3) but does not provide exact version pinning. For reproducibility from scratch, the following should be documented:
- Python version (e.g., CPython 3.12.13 is mentioned but should be in a `pyproject.toml`)
- Docker image tags for each language's SWE-bench container
- UV lock file or `requirements.txt` with pinned versions

**Recommendations**

1. Pin the GitHub repository to a specific commit SHA in the paper
2. Add a `CODE_REPRODUCIBILITY.md` appendix with exact dependency versions
3. Report test coverage metrics for the adapter protocol
4. Include the benchmark construction config (objective coefficients) in machine-readable format
5. Provide code snippets for the adapter wrapper implementation (not just invocation commands)

These changes would significantly improve the code quality and reproducibility of the benchmark artifacts.
