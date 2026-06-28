---
action_items:
- id: 1b6fc898233f
  severity: science
  text: Code repository not accessible for review. Authors should provide public GitHub
    link with complete implementation, test suite, and dependency specifications for
    reproducibility.
- id: f283a2f2e803
  severity: science
  text: No evidence of modular code structure or test coverage metrics in manuscript.
    Add Appendix section documenting code organization, test strategy, and CI/CD pipeline.
artifact_hash: 0fb9253adef42dcbc903c972875abcf8435cbde0a29a43054fe5430b0edd419c
artifact_path: projects/PROJ-776-planbench-xl-evaluating-long-horizon-pla/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-28T21:34:23.764940Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_code_quality_paper
score: 0.0
verdict: minor_revision
---

**Code Quality Review — PlanBench-XL**

This review scope is limited to code quality of artifacts that produced the paper. However, **no code repository or implementation artifacts are accessible** for this arXiv-submitted manuscript. The paper references code/data release URLs (GitHub: `https://github.com/JiayuJeff/PlanBench-XL`, HuggingFace: `https://huggingface.co/datasets/JiayuJeff/PlanBench-XL`) but these cannot be evaluated as part of this review pipeline.

**Critical Gaps for Code Quality Assessment:**

1. **Reproducibility from Scratch**: The manuscript describes data construction (Section 3.1, Appendix B) involving tool generation, query enumeration, and state graph computation (Algorithm 1, Appendix B.5). Without access to the implementation, I cannot verify:
   - Whether the state graph construction is deterministic
   - Whether ground-truth paths are computed consistently across runs
   - Whether the blocking mechanism is reproducible

2. **Modularity**: The paper describes multiple components (retriever, runtime protocol, metric computation, blocking). A proper code review would assess whether these are separated into distinct modules (<200 lines each per the truncation guidance), but no source files are available.

3. **Test Coverage**: No test suite or CI/CD pipeline is referenced. For a benchmark paper, unit tests for:
   - Tool schema validation
   - Ground-truth path verification
   - Metric computation correctness
   are essential for community adoption.

4. **Dependency Hygiene**: The paper uses `vLLM` (Appendix Ethics) and various LLM APIs. A `requirements.txt` or `pyproject.toml` with pinned versions is necessary for reproducibility.

**Recommendation**: Upon code release, the authors should provide a `README.md` documenting:
- Directory structure with module responsibilities
- Test coverage percentage and how to run tests
- Dependency versions and environment setup
- Example scripts for reproducing key experiments (e.g., Figure 5, Figure 8)

Without these artifacts, the benchmark's scientific claims cannot be independently verified, which is a significant limitation for reproducibility.
