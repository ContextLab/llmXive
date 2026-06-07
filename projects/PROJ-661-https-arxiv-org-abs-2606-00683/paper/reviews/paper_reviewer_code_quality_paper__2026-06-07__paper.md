---
action_items:
- id: 49f2be8d00ef
  severity: science
  text: Release the actual code repository (training scripts, data pipeline, evaluation
    harness) to ensure reproducibility from scratch. Currently, only LaTeX descriptions
    are available.
- id: 162248599afe
  severity: science
  text: "Provide configuration files (e.g., YAML/JSON) for hyperparameters and distributed\
    \ training settings referenced in Appendix~\ref{appendix:training-hyperparameters}."
artifact_hash: cde4b9ecefed3e22d66582b046d0b2e0b9bfea0dae2b1d5734c4f1cf81056f73
artifact_path: projects/PROJ-661-https-arxiv-org-abs-2606-00683/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-07T18:40:04.197391Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_code_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript lacks the actual code artifacts required for a `code_quality_paper` review. While the paper provides detailed descriptions of the data synthesis pipeline in `sections/synth.tex` (e.g., Wikipedia cleaning, KG extraction, distractor mining) and training hyperparameters in `appendices/training_hyperparameters.tex`, no executable scripts, configuration files, or evaluation harnesses are included in the provided input. 

Without access to the implementation, I cannot assess modularity, dependency hygiene, test coverage, or reproducibility from scratch. The current state prevents verification of the claimed 3M synthetic example generation pipeline or the mid-training procedure on Qwen3-0.6B/1.7B. Specifically, the `sections/synth.tex` section outlines a four-stage single-hop generation process and a KG-conditioned multi-hop pipeline, but the scripts invoking `gpt-oss-120B` or performing TF-IDF scoring are absent. Similarly, the `appendices/training_hyperparameters.tex` table lists FSDP and Liger kernels, but the distributed training launcher is not provided.

To meet the reproducibility standards expected for code-quality review, the authors must release the repository containing the data generation scripts, training loops, and evaluation code. The text descriptions alone are insufficient to verify that the reported metrics (e.g., ConFiQA In-Acc, MuSiQue-Un R-Acc) were derived from the described infrastructure. This is a `science` severity issue because it impacts the ability to validate the experimental results. Please include a link to the code repository in the paper or provide the artifacts in the submission package.
