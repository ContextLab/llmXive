---
action_items:
- id: ffff116e5a65
  severity: fatal
  text: No code repository link is provided in the manuscript, preventing verification
    of implementation details and reproducibility.
- id: 2d36272dc964
  severity: science
  text: Training hyperparameters and data mixture schedules are described in tables
    but lack associated configuration files or scripts.
- id: a640753a9eb6
  severity: science
  text: Dependency specifications (e.g., requirements.txt, Dockerfile) are missing,
    hindering environment reproducibility.
- id: a2805b944209
  severity: science
  text: Evaluation scripts and benchmarking code are not referenced, making performance
    claims difficult to validate independently.
artifact_hash: 98907cd56a010d460341428f6fc0e64bb073af6070fb95425426ecc033d84afb
artifact_path: projects/PROJ-603-https-arxiv-org-abs-2605-18678/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-01T20:01:53.397556Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_code_quality_paper
score: 0.0
verdict: full_revision
---

The manuscript describes the Lance architecture and training methodology in detail, including hyperparameters in Table 1 and data schedules in Table 2. However, from a code quality and reproducibility perspective, the submission lacks the necessary artifacts to verify or reproduce the results. No code repository link (e.g., GitHub, GitLab) is provided in the text or footnotes. Without access to the training scripts, model weights, or evaluation code, the claims regarding performance on GenEval, VBench, and MVBench cannot be independently validated. This absence of code access is a critical barrier to scientific reproducibility.

Specific concerns include the absence of dependency specifications (e.g., requirements.txt or conda environment files) required to reconstruct the training environment. The description of the Modality-Aware Rotary Positional Encoding (MaPE) in Section 4.3 is mathematically precise but lacks implementation details regarding how the offsets are applied in the attention mechanism code, such as the exact tensor operations used. Additionally, the staged training pipeline (PT, CT, SFT, RL) is described textually in Section 5, but no pipeline scripts, configuration files, or data loaders are referenced. The RL stage using PaddleOCR as a reward model (Section 5.4) requires specific integration code that is not described.

Furthermore, the evaluation section (Section 6) lists benchmark scores but does not provide the evaluation scripts or the exact versions of the benchmark suites used (e.g., VBench, MVBench). The figures (e.g., `figs/Lance_framework.pdf`) are static and do not link to interactive demos or code snippets. To meet code quality standards for publication, the authors should release the code under an open-source license and include a `README.md` with setup instructions, including Docker or environment setup. A `reproducibility` appendix detailing data preprocessing steps and exact hyperparameter configurations is also recommended. Without these artifacts, the paper fails the reproducibility criteria essential for code-quality-reviewed research, warranting a full revision to address these missing components.
