---
action_items:
- id: d8b7f2e5e743
  severity: science
  text: The manuscript references a 'High-Quality Data Curation Pipeline' (Sec 3.4)
    and 'Training Details' (Appendix) but provides no code artifacts, repository links,
    or data processing scripts. Without the actual implementation of the 4-stage pipeline
    (filtering, captioning, extraction, construction) and the training loops, the
    reproducibility of the 62K dataset and the 23.8 FPS claim cannot be verified.
- id: 1c3338064bc1
  severity: science
  text: The paper claims 'real-time' generation at 23.8 FPS on an H200 GPU (Table
    1), yet the experimental setup lacks a `requirements.txt`, `Dockerfile`, or specific
    environment configuration (e.g., CUDA version, specific Wan2.2 checkpoint hash).
    The 'Training-Free KV Cache Rescheduling' logic is described mathematically but
    not provided as executable code, making independent verification of the inference
    speed impossible.
- id: 1cbbdad221cb
  severity: science
  text: The 'HGC-Bench' benchmark is described as containing 240 samples with specific
    prompts (Appendix), but the dataset files (images, prompts, ground truth) are
    not included in the provided artifacts. Reproducibility requires the actual data
    files or a script to generate them, not just the prompt text.
artifact_hash: 8ac732f80d31fee19845b13e35eb49deeae5414cb6cb993b15f1b25017de2aa1
artifact_path: projects/PROJ-598-https-arxiv-org-abs-2605-15824/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T21:12:21.292544Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_code_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript presents a novel framework for human-garment video customization but fails to meet the basic standards of code quality and reproducibility required for a scientific publication in this domain. The review is limited to the provided LaTeX source, which contains no executable code, scripts, or data artifacts.

**Reproducibility from Scratch:**
The paper claims to train a model on a curated dataset of 62K triplets (Appendix, Sec 3.4) and achieve 23.8 FPS inference. However, there is no `main.py`, `train.py`, or `inference.py` provided. The "High-Quality Data Curation Pipeline" is described textually (using PySceneDetect, YOLOv8, UniMatch, Q-Align, Gemini-3.1) but the specific scripts, configuration files, and version pins for these dependencies are absent. Without the code to reproduce the data filtering and captioning stages, the 62K dataset cannot be reconstructed, rendering the training results irreproducible.

**Dependency Hygiene and Environment:**
The experimental setup mentions NVIDIA A100/H200 GPUs and the Wan2.2-5B-TI2V backbone. There is no `requirements.txt`, `environment.yml`, or `Dockerfile` to specify the exact versions of PyTorch, Transformers, Diffusers, or the specific Wan model checkpoint used. The claim of "real-time" performance is highly sensitive to the inference engine (e.g., vLLM, TensorRT) and quantization settings, none of which are documented in the code artifacts.

**Modularity and Tests:**
The "Training-Free KV Cache Rescheduling" is a core contribution (Sec 3.3), involving complex logic for `garment KV refresh`, `historical KV withdraw`, and `reference KV disentangle`. This logic is described via equations and figures but is not implemented in a modular, testable Python class. There are no unit tests verifying the cache management logic or the attention mask generation described in Sec 3.2.

**Recommendation:**
The authors must release the full codebase, including:
1.  Data processing scripts for the 4-stage pipeline.
2.  Training and inference scripts with exact dependency versions.
3.  The HGC-Bench dataset or a script to generate it.
4.  Unit tests for the KV cache rescheduling logic.
Without these, the paper's claims regarding efficiency and reproducibility cannot be validated.
