---
action_items:
- id: ea3ee48e1351
  severity: writing
  text: Code artifacts (repository, scripts, configs) not provided for review. Access
    to github.com/NVlabs/LongLive is required to evaluate code quality, modularity,
    tests, and reproducibility from scratch.
- id: 8bf3c15ad90c
  severity: writing
  text: Paper mentions custom CUDA/Triton kernels for NVFP4 but does not provide kernel
    source or build instructions. Reproducibility of the core infrastructure cannot
    be verified without code access.
- id: b6b577fbdd77
  severity: writing
  text: Implementation Details (Appendix E) lists hyperparameters but omits dependency
    versions (PyTorch, DeepSpeed, CUDA). Add a requirements.txt or environment.yml
    for reproducibility.
artifact_hash: 6191ec14b8389b89c96572533c3f6f5e9333a3f73e89fe363432c3a9d7429fb8
artifact_path: projects/PROJ-604-https-arxiv-org-abs-2605-18739/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-04T19:01:33.565993Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_code_quality_paper
score: 0.0
verdict: minor_revision
---

**Code Quality Review — Artifacts Not Available**

**Artifact Availability:** This review focuses on code quality (readability, modularity, tests, dependency hygiene, reproducibility), but the actual code repository is **not provided** in the review package. The paper references `github.com/NVlabs/LongLive` but I cannot access it. Per the contract lens, I cannot evaluate code quality without the code artifacts themselves.

**What Can Be Evaluated from Paper:**

1. **Implementation Transparency (Appendix E, lines 1–35):** The paper provides hyperparameters (learning rates, batch sizes, GPU counts, iterations), but omits dependency versions (PyTorch, DeepSpeed, CUDA, Triton). This hinders reproducibility from scratch.

2. **Kernel Claims:** The paper mentions "custom quantization and dequantization kernels together with dedicated CUDA kernels for NVFP4 GEMMs; for the RHT-enabled branch, we additionally use Triton kernels" (Section 2.2, lines 15–18). Without source code, I cannot verify:
   - Kernel modularity and separation of concerns
   - Memory management correctness
   - Test coverage for custom kernels
   - Build/install instructions

3. **Framework Dependencies:** The paper uses DeepSpeed-Ulysses, FlexAttention, and NVIDIA Blackwell-specific kernels. Dependency hygiene cannot be assessed without `requirements.txt` or `environment.yml`.

4. **Reproducibility:** The paper claims "NVFP4 AR training uses 1920 NVIDIA GB200 GPU hours" (Appendix E, line 28). Without access to training scripts, checkpoint formats, and data preprocessing pipelines, full reproducibility cannot be verified.

**Recommendations for Authors:**

1. **Provide Code Repository Access:** Include a public or review-access GitHub link with full source code, including custom CUDA/Triton kernels.

2. **Add Dependency Specification:** Include `requirements.txt` or `environment.yml` with exact package versions (PyTorch, DeepSpeed, CUDA, Triton, etc.).

3. **Document Build Instructions:** Provide a `README.md` with build instructions for custom kernels, including CUDA architecture flags for Blackwell GPUs.

4. **Test Coverage:** Include unit/integration tests for critical components (Balanced SP mask generation, NVFP4 quantization, KV-cache dequantization).

5. **Reproducibility Scripts:** Provide scripts to reproduce training and inference results from the paper tables (e.g., `scripts/train_ar.sh`, `scripts/eval_vbench.sh`).

Without these artifacts, the code quality review is necessarily limited to documentation analysis rather than actual code evaluation.
