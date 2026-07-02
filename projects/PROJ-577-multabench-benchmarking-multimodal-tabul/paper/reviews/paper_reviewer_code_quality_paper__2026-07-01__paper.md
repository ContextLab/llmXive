---
action_items:
- id: fff5af01479d
  severity: science
  text: The paper claims to release code and data (S1, S5) but provides no repository
    structure, dependency list (requirements.txt/pyproject.toml), or reproducibility
    script (e.g., run_curation.sh). Without a manifest of dependencies (specific versions
    of PyTorch, LoRA, DINOv3, e5, LightGBM, etc.) and a clear entry point, the benchmark
    cannot be reproduced from scratch.
- id: ca20c4b42aa7
  severity: science
  text: The curation pipeline involves fine-tuning encoders (LoRA) and running 5 tabular
    learners across 40 datasets with 5 seeds. The paper mentions 'cost-effectiveness'
    but lacks a documented workflow for parallelization, checkpointing, or resuming
    interrupted runs. A missing or non-atomic checkpointing strategy risks data loss
    and makes the 32K token output budget for implementation tasks unmanageable if
    the code is monolithic.
- id: 3fb4ce932c3f
  severity: science
  text: The appendix details hyperparameters (LR, batch size, LoRA rank) but does
    not specify the random seed management strategy for the entire pipeline (data
    loading, model init, training). Reproducibility requires a single seed controller
    or a documented seed propagation mechanism across all 5 learners and 5 seeds per
    dataset.
artifact_hash: 28e097e31933ecce294eb34fd92a9e53c4dcbbab117fcc0a77af75a314777084
artifact_path: projects/PROJ-577-multabench-benchmarking-multimodal-tabul/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T20:51:07.906945Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_code_quality_paper
score: 0.0
verdict: minor_revision
---

The paper presents a significant benchmarking effort (MulTaBench) but fails to meet the standard for code quality and reproducibility required for a dataset/benchmark paper. While the methodology is described in prose, the "artifacts that produced the paper" (the codebase) are not described in a way that allows a third party to reconstruct the environment or the execution flow.

**Reproducibility & Dependency Hygiene:**
The paper states in Section 1 and the Checklist that code and data are available via a GitHub link and Kaggle. However, the LaTeX source contains no reference to a `requirements.txt`, `pyproject.toml`, or `environment.yml`. For a benchmark involving specific versions of `dinov3`, `e5`, `lora`, `lightgbm`, `catboost`, and `tabpfn`, the absence of a dependency manifest is a critical failure. A reviewer cannot verify if the results are reproducible without knowing the exact library versions used, as small changes in embedding models or tabular learners can alter the "Target-Aware" gains.

**Modularity & Workflow:**
The curation pipeline described (fine-tuning encoders, projecting with PCA, running 5 learners, 5 seeds, 4 conditions) is computationally intensive. The paper mentions "cost-effectiveness" but provides no insight into the software architecture. Is the code a monolithic script? Is there a job scheduler integration (e.g., SLURM, Ray)? Without a description of the code structure (e.g., `src/curation/`, `src/encoders/`, `src/learners/`), it is impossible to assess modularity. If the implementation is a single 1000-line script, it violates the principle of modularity and will likely hit token limits during any future implementation or debugging tasks.

**Data & Checkpointing:**
The pipeline involves fine-tuning encoders on the training split. The paper does not mention how these fine-tuned weights are stored or reused. If the code re-fine-tunes the encoder for every fold or every learner, the computational cost is multiplied unnecessarily. A robust codebase would cache the fine-tuned embeddings. The lack of mention of a caching strategy or checkpointing mechanism suggests a potential flaw in the experimental design's efficiency and reproducibility.

**Actionable Recommendations:**
1.  **Release a Dependency Manifest:** Provide a `requirements.txt` or `pyproject.toml` in the supplementary material or repository, listing exact versions of all critical libraries.
2.  **Document the Code Structure:** Include a brief `README.md` excerpt in the appendix or repository link describing the directory structure and the main entry point (e.g., `python run_curation.py --config config.yaml`).
3.  **Specify Seed Management:** Explicitly state how random seeds are managed across the pipeline to ensure bitwise reproducibility.
4.  **Describe Checkpointing:** Clarify if fine-tuned encoder weights are cached to avoid redundant computation across folds/learners.

Without these artifacts, the benchmark cannot be independently verified or extended, which is the primary goal of a benchmark paper.
