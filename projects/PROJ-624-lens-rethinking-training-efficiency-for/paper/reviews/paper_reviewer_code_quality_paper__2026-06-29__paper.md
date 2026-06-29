---
action_items:
- id: 9822a1c84f8f
  severity: science
  text: Include a code snapshot or ensure the linked repository contains complete
    training scripts, configs, and dependencies for reproducibility.
- id: 2a78fa169438
  severity: science
  text: Provide dependency management files (requirements.txt or environment.yml)
    to ensure environment reproducibility.
- id: bc709e5ee986
  severity: science
  text: Add unit tests for critical components (e.g., data preprocessing, loss functions)
    to verify code reliability.
artifact_hash: ee50a22651a80bef159316dc0dc914d3939b89b46e64d966972efb2307431ada
artifact_path: projects/PROJ-624-lens-rethinking-training-efficiency-for/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T04:12:31.322095Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_code_quality_paper
score: 0.0
verdict: minor_revision
---

The current submission package contains the paper LaTeX source and figures but lacks the executable code artifacts necessary for a comprehensive code quality review. As a code_quality_paper reviewer, my scope is limited to assessing the readability, modularity, test coverage, dependency hygiene, and reproducibility of the implementation that produced the results. Since no Python scripts, configuration files, or model definitions are included in the provided input, I cannot evaluate these aspects.

Specifically, the paper details complex training pipelines in Section 3 (Method), including pre-training on Lens-800M (Section 3.3), reinforcement learning with DiffusionNFT (Section 3.4), and few-step distillation (Section 3.4). However, without the corresponding training scripts (e.g., `train.py`, `rl_finetune.py`), data loading utilities, and hyperparameter configurations (e.g., `config.yaml`), it is impossible to verify the reproducibility of the reported compute efficiency claims or the correctness of the implementation. The reliance on an external GitHub link (`https://github.com/microsoft/Lens`) is insufficient for a self-contained review, as external links may change or be inaccessible.

To improve the submission for this lens, the authors should include a code snapshot in the supplementary material or ensure the repository is fully archived. Key missing components include:
1. **Dependency Management**: A `requirements.txt` or `environment.yml` file specifying exact versions of PyTorch, transformers, and other libraries to ensure environment reproducibility.
2. **Modularity**: The codebase should be structured into clear modules (e.g., `models/`, `data/`, `training/`, `utils/`) rather than monolithic scripts, facilitating maintenance and testing.
3. **Testing**: Unit tests for critical components (e.g., data preprocessing, loss functions, reward calculation) are needed to ensure code reliability.
4. **Documentation**: A `README.md` with instructions on how to reproduce the training and evaluation steps from scratch.

Without these artifacts, the code quality cannot be assessed, and the reproducibility of the training efficiency claims remains unverified from a software engineering perspective.
