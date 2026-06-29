---
action_items:
- id: 97e49a89b8fa
  severity: science
  text: Training command in Appendix (tcolorbox py1, line ~380) has omitted config
    lines preventing full reproducibility. All hyperparameters must be visible.
- id: b40f636b24de
  severity: science
  text: No dependency specifications (requirements.txt, environment.yml) visible in
    paper or supplementary materials. Hardware configuration incomplete.
- id: bfcb79bed61f
  severity: science
  text: No test suite or validation scripts visible. Cannot verify reproducibility
    of reported results without access to evaluation code.
artifact_hash: 86f3dbb1aa547b2619e2d0068122fd6e86cb21c5f6980bdd3810b1ffe64d94e9
artifact_path: projects/PROJ-597-https-arxiv-org-abs-2605-11739/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T03:33:27.491907Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_code_quality_paper
score: 0.0
verdict: minor_revision
---

## Code Quality Review

This review focuses exclusively on the code quality and reproducibility artifacts that produced the paper. As this is an arXiv-ingested third-party manuscript, I cannot access the actual code repository (anonymous 4open.science link in abstract, GitHub link in Section 1).

### Reproducibility Concerns

**Training Command Incompleteness** (Section: Preliminaries and Experimental Setup, tcolorbox `py1`):
The OPD training command shows `... config lines omitted ...` which prevents exact reproduction. For NeurIPS reproducibility standards, all hyperparameters must be visible:
- Batch size, gradient accumulation, effective batch size
- Learning rate schedule details
- KL penalty coefficients
- Clip values for GRPO/DAPO

**Dependency Hygiene**:
No `requirements.txt`, `environment.yml`, or `pyproject.toml` visible in the paper or supplementary materials. The paper mentions running on "8× or 32× H20 96GB GPUs" but does not specify:
- PyTorch version
- verl framework version
- CUDA/cuDNN versions
- Python version

**Test Coverage**:
No test suite, validation scripts, or evaluation harness visible. The NeurIPS Checklist (Section: NeurIPS Paper Checklist, item 4) claims reproducibility but does not provide:
- Unit tests for EffOPD extrapolation logic
- Integration tests for the validation-based step selection
- Regression tests for the 3× speedup claim

### Recommendations

1. **Publish complete training configuration** in a `config.yaml` or similar file alongside the code
2. **Add dependency specification** with pinned versions for all critical packages
3. **Include evaluation scripts** that reproduce the main figures (Fig. 5, Fig. 6)
4. **Add test coverage** for the EffOPD extrapolation acceptance logic (the 50-sample validation set selection)

Without these artifacts, the code quality cannot be fully assessed, and reproducibility from scratch is not guaranteed.
