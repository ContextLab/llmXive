---
action_items:
- id: a8f00d6cb2c5
  severity: writing
  text: Provide direct links to the source code repository (e.g., GitHub) in the manuscript
    and ensure public access for reproducibility.
- id: 10e4a265c9b5
  severity: writing
  text: Specify exact software dependency versions (e.g., PyTorch, torchaudio, transformers)
    in Appendix or a requirements.txt file.
- id: 151626da6e5a
  severity: science
  text: Include random seeds for the simulation pipeline (Section 3) and RL training
    (Section 4) to ensure deterministic results.
artifact_hash: b76830428db6f31ab0213200b5916231003e882ec498765fb220acf8020a5333
artifact_path: projects/PROJ-615-mega-asr-towards-in-the-wild-2-speech-re/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-11T02:20:02.670196Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_code_quality_paper
score: 0.0
verdict: minor_revision
---

This review evaluates the code quality and reproducibility of the artifacts described in the manuscript. As this is an arXiv-ingested paper, no actual code repositories or build artifacts were provided for direct inspection. Consequently, the evaluation is limited to the reproducibility information present in the text and the clarity of the methodology descriptions.

**Reproducibility from Scratch (Section 3 & Appendix):**
The manuscript describes the `Voices-in-the-wild-2M` construction pipeline (Section 3) and the `DG-WGPO` training loop (Section 4) with mathematical rigor. However, critical implementation details required to reproduce the simulation environment are missing. Specifically:
1.  **Dependency Hygiene:** Appendix "Training and Implementation Details" lists hyperparameters (learning rates, batch sizes) but omits the software environment. There is no mention of the PyTorch version, CUDA toolkit, or specific ASR libraries (e.g., `speechbrain`, `funasr`) used for the baseline comparisons. Without a `requirements.txt` or `environment.yml`, dependency conflicts may prevent exact reproduction.
2.  **Simulation Determinism:** Section 3.2 describes the "Reality-grounded composition" of 54 scenarios. It mentions an "agentic check" but does not specify the random seeds or the logic for the "physical plausibility" check. To ensure reproducibility, the random seed used for the spectrogram-level code-based simulation must be fixed and reported.
3.  **Reward Implementation:** The `Dual-Granularity Dynamic Reward` (Equation 5-8) is defined mathematically. However, the text does not reference the specific library or script used to compute the `WER` and `LCS` metrics during RL training. Different `wer` implementations (e.g., `jiwer` vs. `g2p`) can yield different scores, affecting the policy gradient updates.

**Modularity & Artifacts:**
The paper references external repositories (e.g., `github.com/xzf-thu/Voices-in-the-Wild-Bench`), but these are not verified in this context. The manuscript does not provide a `Dockerfile` or `Singularity` recipe for the training environment, which is standard for large-scale ASR experiments to ensure environment consistency.

**Recommendations:**
To satisfy code quality standards for reproducibility, the authors should:
1.  Include a `requirements.txt` or `conda` environment export in the supplementary material.
2.  Explicitly state the random seeds used for data simulation and model initialization.
3.  Provide a link to the exact commit hash of the code used to generate the results, rather than just a general repository URL.
4.  Clarify the `WER` calculation library and version used in the RL reward loop.

Without these artifacts, independent verification of the `DG-WGPO` training stability and the `Voices-in-the-wild-2M` generation process remains impossible.
