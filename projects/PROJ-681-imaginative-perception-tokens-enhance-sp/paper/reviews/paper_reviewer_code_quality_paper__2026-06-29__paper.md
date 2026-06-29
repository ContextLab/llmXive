---
action_items:
- id: 3fef1919064b
  severity: science
  text: Code artifacts (training scripts, data pipelines, evaluation code) are not
    provided in the submission. For reproducibility, include a code repository with
    requirements.txt, training/evaluation scripts, and data preprocessing pipelines.
- id: cdbeb09eb5a1
  severity: science
  text: No test suite or validation scripts are visible. Add unit/integration tests
    for data curation pipelines (AI2-THOR, Habitat, Matterport3D) and model training
    loops to ensure correctness.
- id: 33db4f1c18a8
  severity: writing
  text: Dependency hygiene cannot be assessed without a requirements.txt or environment.yml.
    Document all Python packages, versions, and CUDA/cuDNN requirements for reproducibility.
artifact_hash: c5de9734fccbfd100241f7fc8603c599264726354d7ecbedd4d657c0e121782f
artifact_path: projects/PROJ-681-imaginative-perception-tokens-enhance-sp/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T10:18:09.904284Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_code_quality_paper
score: 0.0
verdict: minor_revision
---

This review focuses exclusively on code quality of the artifacts that produced the paper. However, the submission contains only the LaTeX manuscript, figures, and bibliography — no code artifacts are provided for evaluation.

**Critical Missing Artifacts:**
1. **Training/evaluation scripts**: The paper describes training BAGEL and Qwen2.5-VL models with IPT (Section `supp_vlms`), but no training code is visible. Without `train.py`, `eval.py`, or similar scripts, reproducibility from scratch is impossible.

2. **Data curation pipelines**: Sections `supp_data_pt`, `supp_data_pet`, and `supp_data_mvc` describe complex data generation from AI2-THOR, Habitat, Matterport3D, and ScanNet++. The actual Python scripts for path sampling, raycasting, TIFA filtering, and question generation are not provided.

3. **Dependency specification**: No `requirements.txt`, `environment.yml`, or `setup.py` is included. The paper mentions GPT-5.1, Qwen-Image-Edit, VQ-VAE/VQ-GAN, and various benchmarks — all require specific package versions for reproducibility.

4. **Test suite**: No test files are visible. Data curation pipelines with geometric filters (e.g., "0.4% image area", "150px margin", "±0.2m ground-level height" in `supp_data_pet`) should have unit tests to verify correctness.

5. **Reproducibility documentation**: No `README.md` with setup instructions, data download links, or training commands. The arXiv submission should include a link to a public code repository (e.g., GitHub) as done in similar works (e.g., `https://github.com/cvpr-org/author-kit` cited in bibliography).

**Recommendation**: For a complete code quality review, the authors should provide a code repository containing:
- Modular training/evaluation scripts (<200 lines each, per truncation guidance)
- Data preprocessing pipelines with tests
- Dependency specification files
- Reproducibility documentation with exact commands to reproduce Table~\ref{tab:pt_breakdown} and other results

Without these artifacts, the paper cannot be independently verified or reproduced, which is a significant limitation for a machine learning paper claiming empirical results.
