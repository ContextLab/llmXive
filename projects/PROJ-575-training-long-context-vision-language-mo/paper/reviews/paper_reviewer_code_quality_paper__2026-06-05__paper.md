---
action_items:
- id: 3b9b34a1f2dc
  severity: science
  text: No training code repository or implementation artifacts provided for review.
    The paper describes training using VeOmni framework but no actual code is accessible
    for evaluation of reproducibility, modularity, or dependency hygiene.
- id: 847a344a3ae0
  severity: science
  text: Appendix A.2 mentions 8 H20 nodes (64 GPUs) training setup but no training
    scripts, data preprocessing pipelines, or evaluation code are included. Code should
    be released for full reproducibility.
artifact_hash: 64fda0b4c326e1fc50df1dd3551145b206b04e1dae0b0745067541ff9112fca2
artifact_path: projects/PROJ-575-training-long-context-vision-language-mo/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-05T10:58:32.302090Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_code_quality_paper
score: 0.0
verdict: minor_revision
---

**Code Quality Review — Artifacts Not Available**

This review lens focuses on code quality of the artifacts that produced the paper (readability, modularity, tests, dependency hygiene, reproducibility from scratch). However, **no training code repository or implementation artifacts were provided** with this arXiv-submitted manuscript.

**What is Missing:**
1. **Training scripts** — The paper describes training with VeOmni framework (Section 5.1, Appendix A.2) but no actual training code is accessible for review
2. **Data preprocessing pipelines** — Document pool construction (1.5M PDFs), OCR expert synthesis, and QA pair generation pipelines are described but not provided
3. **Evaluation code** — MMLongBench v1.1 and VLMEvalKit are cited but custom evaluation scripts for MM-NIAH, VTCBench, and long-video benchmarks are not included
4. **Reproducibility artifacts** — No `requirements.txt`, Dockerfile, or training checkpoints available

**Impact on Review:**
Without access to the actual codebase, I cannot evaluate:
- Code modularity and separation of concerns
- Test coverage for training pipelines
- Dependency management and version pinning
- Whether the 5B-token budget training recipe can be reproduced from scratch

**Recommendation:**
The authors should release the training code repository (or at minimum, the data synthesis scripts and training configuration files) to enable reproducibility verification. This is standard practice for ML papers claiming empirical results. The appendix provides detailed hyperparameters (Table A.1) but lacks executable artifacts.

Note: This review is limited to the code quality lens only. Other reviewers are assessing scientific claims, statistical analysis, and safety/ethics aspects separately.
