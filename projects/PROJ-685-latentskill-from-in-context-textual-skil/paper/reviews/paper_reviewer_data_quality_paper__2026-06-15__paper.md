---
action_items:
- id: f33df4ff750d
  severity: writing
  text: The 171K GitHub-crawled skill documents lack explicit license declarations
    in appendix/training_details.tex. Reproducibility requires confirming these repos
    allow derivative model training.
- id: c5d2f16d1c5a
  severity: science
  text: Out-of-distribution skill sources in appendix/ood_skill_sources.tex (Table
    1) point to live GitHub repos without archival links. Link rot risks make OOD
    evaluation irreproducible.
- id: 3772d513496d
  severity: writing
  text: Benchmark dataset versions (ALFWorld, Search-QA subsets) are not versioned
    in sections/experiments.tex. Exact split definitions and dataset releases must
    be specified for replication.
artifact_hash: a8058c08d3783326623ffd4fe82cc98eaea95cd3e37911390d531e390197b756
artifact_path: projects/PROJ-685-latentskill-from-in-context-textual-skil/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-15T04:51:08.357660Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

This review focuses exclusively on data provenance, licensing, and version control as they pertain to the reproducibility of the LatentSkill framework. The manuscript presents significant gaps in data quality documentation that must be addressed before publication.

First, the pretraining corpus consists of "approximately 171K deduplicated skill documents crawled from GitHub" (Appendix: Training Details). While the source (GitHub) is identified, the specific licenses of these repositories are not disclosed. GitHub repositories vary widely in permissiveness (e.g., MIT vs. proprietary). Without explicit confirmation that the crawled data permits training commercial or research models, the data provenance is legally ambiguous. This is a critical compliance risk that requires clarification in `appendix/training_details.tex`.

Second, the Out-of-Distribution (OOD) evaluation relies on skills collected from specific public GitHub repositories listed in `appendix/ood_skill_sources.tex` (Table `tab:ood_sources`). These are live URLs without persistent archival identifiers (e.g., DOIs or Zenodo snapshots). If any of these repositories are deleted, made private, or modified, the OOD evaluation results become irreproducible. This constitutes a link rot vulnerability. To ensure long-term data quality, the authors should archive these skill collections or provide commit hashes for the exact versions used.

Third, the benchmark datasets (ALFWorld, NQ, HotpotQA, etc.) mentioned in `sections/experiments.tex` are referenced only by name. Standard benchmarks often have multiple versions or split configurations. The paper does not specify the exact dataset release versions or the specific seed used for random sampling (e.g., "500 examples from each dataset" in `appendix/evaluation_details.tex`). Without these version controls, exact replication of the training and evaluation splits is not possible.

Finally, while a code link is provided in the abstract, the license of the released code artifact is not stated within the text. For a data-centric framework, the license of the generated skill weights and the training pipeline must be explicit to ensure users understand the terms of reuse.

Addressing these data quality issues will strengthen the paper's reproducibility and legal robustness.
