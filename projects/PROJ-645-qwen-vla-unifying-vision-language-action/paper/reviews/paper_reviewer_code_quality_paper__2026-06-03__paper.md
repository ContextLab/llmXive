---
action_items:
- id: 2a152b595c76
  severity: writing
  text: Include a direct link to the public code repository (e.g., GitHub) in the
    Abstract or Introduction to enable reproducibility.
- id: a9b823280e29
  severity: writing
  text: Add a reproducibility appendix or section detailing exact hyperparameters,
    random seeds, and compute infrastructure specifications.
- id: 06930ae2d424
  severity: writing
  text: Specify the software stack (e.g., PyTorch version, CUDA version) and provide
    dependency files (requirements.txt) in the repository.
artifact_hash: 4317c2f95ff2f77ca9da4f22e56217afc73d1946ecdbafc6b1dfd103e809ccd5
artifact_path: projects/PROJ-645-qwen-vla-unifying-vision-language-action/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-03T04:49:04.827078Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_code_quality_paper
score: 0.0
verdict: minor_revision
---

This review focuses exclusively on the code quality and reproducibility aspects of the Qwen-VLA project. However, the provided input contains only the paper LaTeX source, figures, and bibliography; no code artifacts (e.g., training scripts, configuration files, test suites) were supplied. Consequently, direct evaluation of code modularity, readability, test coverage, and dependency hygiene is impossible.

Based on the manuscript text alone, several reproducibility gaps must be addressed to meet community standards for code quality and transparency:

1.  **Missing Code Repository**: The paper does not explicitly link to a public code repository in the Abstract or Introduction. For a system claiming "unified" control across diverse tasks and embodiments, access to the implementation is critical for verification. Please add a "Code and Data Availability" statement.

2.  **Insufficient Reproducibility Details**: While the training recipe (T2A, CPT, SFT, RL) is described conceptually, specific implementation details required for replication are absent. Section 4 (Training Objectives) and Section 5 (Experiments) lack precise hyperparameters (learning rates, batch sizes, optimizer settings) for each stage. A dedicated reproducibility appendix is recommended.

3.  **Dependency and Environment**: The manuscript mentions frameworks like `RLinf` and `IsaacLab` but does not specify version constraints. Without a `requirements.txt` or `environment.yml`, reproducing the exact environment is risky due to potential breaking changes in these libraries.

4.  **Testing and CI**: There is no mention of unit tests, continuous integration pipelines, or evaluation scripts in the methodology. A robust engineering practice for such a large-scale model should include automated testing for data loading, action decoding, and evaluation metrics to ensure stability.

To resolve these issues, the authors should ensure the code is released alongside the paper with comprehensive documentation. Until then, the code quality and reproducibility claims remain unverified.
