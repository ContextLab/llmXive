---
action_items:
- id: 5b3f4dac220d
  severity: writing
  text: "Provide a public code repository containing the full implementation of the\
    \ MiniMax Sparse Attention kernels (CUDA/HIP), training loops, and inference scripts.\
    \ Include a clear README with step\u2011by\u2011step instructions to reproduce\
    \ the 109B\u2011parameter experiments."
- id: 4536f41a2438
  severity: writing
  text: "Add a dependency manifest (e.g., requirements.txt or conda environment.yml)\
    \ that pins exact versions of all Python packages, CUDA toolkit, and any third\u2011\
    party libraries used (e.g., FlashAttention, TileLang)."
- id: d17463533ff7
  severity: writing
  text: "Modularize the kernel source files: split the large monolithic GPU kernel\
    \ code (currently described only in the paper) into logical modules such as `index_topk.cu`,\
    \ `sparse_attention.cu`, `kl_loss.cu`, and a thin C++/Python wrapper. Each module\
    \ should be <200\u202FLOC and documented."
- id: 4930c0db3f37
  severity: writing
  text: "Introduce unit tests for each kernel component (e.g., correctness of the\
    \ exp\u2011free Top\u2011K selection, KV\u2011outer vs Q\u2011outer iteration,\
    \ KL\u2011loss gradient). Tests should run on a CI platform and verify numerical\
    \ equivalence to a reference dense implementation on small toy inputs."
- id: 6866f3ff08a6
  severity: writing
  text: "Provide a reproducibility script that downloads the pre\u2011training data\
    \ subset used for the pilot 10B\u2011parameter experiments, builds the kernels,\
    \ and runs a short end\u2011to\u2011end training run (e.g., 1\u202FM tokens) to\
    \ verify that loss curves match the figures in the appendix."
- id: 9dbcfc03bcb6
  severity: writing
  text: Document the build process for the custom kernels (e.g., required nvcc flags,
    supported GPU architectures, any custom PTX or JIT steps). Include fallback instructions
    for systems without the exact GPU model.
artifact_hash: f00725508246b024cf4aa3c534e6f6afc166e2aa03bee30b44dd04e950f05991
artifact_path: projects/PROJ-701-minimax-sparse-attention/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-17T16:27:25.655415Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_code_quality_paper
score: 0.0
verdict: minor_revision
---

The review focuses exclusively on the reproducibility and software engineering aspects of the artifacts that underpin the MiniMax Sparse Attention (MSA) paper.

**Readability & Modularity**  
The manuscript supplies detailed algorithmic descriptions but does not include the actual source code for the GPU kernels, training loops, or inference utilities. The only code‑like artifacts are LaTeX macros and algorithm pseudocode (Algorithm 1). Without concrete files, it is impossible to assess code style, naming conventions, or modular decomposition. The description of the Top‑K kernel, KV‑outer iteration, and two‑phase forward pass suggests a non‑trivial implementation, yet the paper treats these as monolithic black boxes. For a large‑scale system, best practice is to expose each logical component in its own source file (e.g., `index_topk.cu`, `sparse_attention.cu`, `kl_loss.cu`) and keep each module under ~200 LOC to aid review and maintenance.

**Testing**  
No unit or integration tests are provided. Sparse attention kernels are highly sensitive to edge cases (e.g., causal masking, variable block sizes, extreme token lengths). The paper presents empirical speed‑up numbers but lacks any verification that the kernels produce numerically identical results to a dense baseline on small inputs. Adding a lightweight test suite that cross‑checks against a reference implementation would greatly increase confidence in correctness and facilitate future contributions.

**Dependency Hygiene**  
There is no explicit list of software dependencies (Python packages, CUDA version, compiler flags, third‑party libraries such as FlashAttention or TileLang). This omission hampers reproducibility: a reader cannot know whether the kernels rely on a specific CUDA toolkit patch, a particular cuBLAS version, or custom PTX. Pinning exact versions in a `requirements.txt` or `environment.yml` is essential for deterministic builds.

**Reproducibility from Scratch**  
The paper claims that MSA can be trained from scratch on a 3 T‑token budget, yet the submission does not contain any scripts to launch pre‑training, nor does it provide the small‑scale pilot dataset used in the appendix. A reproducibility package should include:
1. A data‑prep script that extracts a manageable subset of the pre‑training corpus (e.g., a few GB).
2. A training driver (`train.py`) that configures the model architecture (block size, `k`, warm‑up schedule) via a YAML/JSON config.
3. A checkpoint‑loading utility to demonstrate the “continued‑pretraining” (CPT) conversion path.

**Build & Execution Documentation**  
The kernel design section mentions several low‑level optimizations (register‑level min‑heap, shared‑memory bank mapping, persistent grid launches). However, there is no build script (e.g., `setup.py` or CMakeLists) that captures the required `nvcc` flags, compute capability targets, or environment variables. Documentation should also describe how to compile and link the kernels with the surrounding PyTorch or JAX code, and how to fall back to a reference implementation on unsupported hardware.

**Overall Assessment**  
While the algorithmic contribution is well articulated, the supporting software artifacts are insufficient for independent verification or downstream adoption. The lack of concrete code, tests, and dependency specifications prevents reproducibility and hampers community uptake. Addressing the action items above will bring the artifact quality to the standard expected for large‑scale systems papers.
