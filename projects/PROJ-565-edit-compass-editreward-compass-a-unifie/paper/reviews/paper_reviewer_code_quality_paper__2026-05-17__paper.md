---
artifact_hash: afa8fa72a7934c7df53d880056c75fcf5c3f630f18439721edf2b52c416ec85b
artifact_path: projects/PROJ-565-edit-compass-editreward-compass-a-unifie/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-05-17T14:48:54.549634Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_code_quality_paper
score: 0.0
verdict: minor_revision
---

**Code Quality Review — Artifacts Not Available**

This manuscript describes the Edit-Compass and EditReward-Compass benchmark suites for image editing and reward modeling. However, the **implementation code artifacts are not provided** with this review package. The review scope for code quality requires access to:

1. **Benchmark implementation code** (Python scripts for data generation, task construction)
2. **Evaluation pipeline code** (MLLM-as-judge scripts, scoring rubrics)
3. **Test suites** for reproducibility verification
4. **Dependency specifications** (requirements.txt, pyproject.toml, or similar)
5. **Data generation scripts** referenced in Appendix (e.g., algorithmic visual reasoning tasks)

**Specific Observations from Paper Text:**

- The paper references Python-based image reconstruction pipelines for Algorithmic Visual Reasoning tasks (Appendix, Section on Longest Word Discovery), but the code is not included
- Data construction strategies are described (Gemini 3 Pro, GPT-5.1 instruction generation), but no scripts or API wrappers are provided
- Evaluation metrics (Instruction Awareness, Visual Consistency, Visual Quality) are defined with formulas, but the scoring implementation is absent
- Table~\ref{tab:reward_model_benchmark_sampling_config} documents sampling configurations, but no configuration files or sampling code are available

**Required for Reproducibility:**

To enable independent verification of the benchmark results (29 image editing models, 21 reward models), the authors should provide:
- A public repository with full implementation code
- Docker or conda environment specifications for dependency hygiene
- Unit/integration tests for benchmark instance generation
- Scripts to regenerate the 2,388 Edit-Compass instances and 2,251 EditReward-Compass pairs

**Recommendation:**

Return `minor_revision` pending inclusion of code artifacts or a clear link to the public repository. Without these, reproducibility from scratch cannot be verified, which is a critical requirement for benchmark papers.
