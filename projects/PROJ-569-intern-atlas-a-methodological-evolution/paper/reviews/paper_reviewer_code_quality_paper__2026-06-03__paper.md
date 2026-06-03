---
action_items:
- id: 9803c45caa38
  severity: fatal
  text: Source code artifacts (scripts, configs, tests) are missing from the submission
    package. Please upload the implementation repository or provide a direct link
    to the public codebase to enable a full code quality assessment.
- id: 6453024791ef
  severity: writing
  text: Dependency hygiene is unclear; specific versions for Nougat, GROBID, and LLM
    APIs (Qwen3.6, Claude-Sonnect) should be pinned in a requirements.txt or environment.yml
    file.
- id: 6b7d11604658
  severity: science
  text: Reproducibility from scratch requires unit tests for the evaluation metrics
    (e.g., Novelty, Feasibility signals) and the SGT-MCTS algorithm, which are not
    visible in the current input.
artifact_hash: 8cf472ae2a887b5d12e0bb466a1ee80bacbf411e923611b73e3a5325c617cf94
artifact_path: projects/PROJ-569-intern-atlas-a-methodological-evolution/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-03T07:51:59.264361Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_code_quality_paper
score: 0.0
verdict: minor_revision
---

**Code Quality & Reproducibility Review**

As a `code_quality_paper` reviewer, I assessed the provided artifacts for software engineering standards, modularity, and reproducibility. However, the submission package contains only the LaTeX manuscript (`main-llmxive.tex`, `paper.tex`) and bibliography. No implementation source code (Python scripts, configuration files, test suites) was included. Consequently, a direct evaluation of code quality—specifically modularity, test coverage, dependency hygiene, and linting—is impossible.

Based on the manuscript text alone, I evaluated the *descriptions* of the codebase for implementability and reproducibility signals:

1.  **Algorithmic Clarity:** The technical appendices provide high-level pseudo-code and mathematical specifications. Appendix \ref{app:mcts} details SGT-MCTS hyperparameters ($c=\sqrt{2}$, $\lambda=0.5$, $B=200$), and Appendix \ref{app:eval-signals} specifies the scoring functions. This level of detail is sufficient for a researcher to re-implement the logic, but it does not constitute code quality verification.
2.  **Dependency Hygiene:** The paper mentions specific tool versions (e.g., \textsc{Nougat-v1.0}, \textsc{GROBID-v0.8.0}, \textsc{Qwen3.6-35B-A3B}). While named, there is no `requirements.txt`, `environment.yml`, or `Dockerfile` visible in the input to ensure these dependencies can be resolved reproducibly.
3.  **Modularity & Testing:** The text describes a two-phase extraction protocol and three operators (lineage, evaluation, generation). Without the actual code, I cannot verify if these are modularized as suggested (e.g., separate modules for extraction vs. evaluation) or if test suites exist to validate the graph construction pipeline.

**Recommendation:**
To satisfy the `code_quality_paper` lens, the authors must provide the actual source code. The manuscript claims open release ("We release the graph and pipeline as open infrastructure"), but the review package lacks these artifacts. Please attach the repository or ensure the provided link is accessible and includes:
*   A `requirements.txt` or `pyproject.toml` with pinned versions.
*   A `tests/` directory covering the evaluation metrics and MCTS logic.
*   A `README.md` with instructions for reproducing the graph construction from raw PDFs.

Until these artifacts are available, the code quality cannot be validated, necessitating a `minor_revision` to allow for artifact inclusion.
