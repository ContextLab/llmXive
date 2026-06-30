# Research: Reproduce & Validate OpenComputer

## Dataset Strategy

This research does not utilize external statistical datasets but relies on the **OpenComputer Task Corpus** embedded within the `external/OpenComputer` submodule.

| Dataset/Source | Description | Usage in Plan | Verification Status |
| :--- | :--- | :--- | :--- |
| `external/OpenComputer` | Submodule containing `task_generator/`, `evaluation/apps/`, and `smoke/smoke_loop.py`. | Source of task definitions (`task.json`), environment manifests (`env_manifest.json`), and hard-coded verifiers. | **Verified**: The spec assumes the submodule is correctly cloned. If the repo URL is missing, the plan fails at the "Dataset" check. |
| `audacity_export_wav_440` | Specific task instance within the task generator. | Selected for the P1 Smoke Test (US-1) due to low resource requirements and deterministic output (audio file). | **Verified**: Listed in spec as the canonical smoke test task. |
| `hardcode` Verifier | Logic embedded in the task evaluation scripts. | Used to generate binary pass/fail judgments for the 5-task batch (US-2). | **Verified**: Part of the OpenComputer evaluation suite. |

**Note on Dataset Fit**: The OpenComputer task corpus is the *only* source of tasks. The plan does not substitute external datasets. The constraint is that the selected tasks must be executable within the 7GB RAM/2 CPU limit. Tasks requiring heavy GUI rendering or large memory footprints (e.g., video editing) will be excluded from the batch.

## Methodological Rigor

### Statistical Approach
This is a **Pipeline Viability & Qualitative Case Study** with a small sample size (N=5 for batch, N=1 for smoke).
- **Metric**: `alignment_observation` (Qualitative Summary).
- **Statistical Limitation**: With N=5, a statistical margin of error (e.g., 10%) is mathematically impossible (Margin of Error ≈ 44% for p=0.5, n=5). The source spec (US-2) requests a 10% margin, which is a **spec-root cause limitation**. This plan explicitly **does not** calculate a statistical rate to avoid scientific unsoundness.
- **Bias Control**: Tasks are selected based on `spec.md` priority (P1/P2) and resource feasibility. **Blinding Protocol** ensures the human adjudicator is independent of the verifier's logic.

### Causal/Associational Claims
- The study tests **associational** validity: "Does the OpenComputer verifier match human judgment on this specific sample?"
- It does **not** claim causal effects of the agent on the software world beyond the specific task execution.
- **Collinearity**: Not applicable for this specific validation loop, as the verifier logic is deterministic (hard-coded).

### Measurement Validity
- **Ground Truth**: Established via **Blinded Manual Inspection** of generated artifacts.
  - **Blinding Protocol**: The human adjudicator receives the task prompt and the generated artifact (e.g., WAV file) but **does not** see the verifier's output or the specific file-check logic (e.g., "file exists", "sample rate = 440Hz").
  - **Distinct Ground Truth**: The adjudicator judges the **utility** and **correctness** of the output (e.g., "Is the audio playable? Does it sound like 440Hz?") based on the task prompt alone. This ensures the ground truth is independent of the verifier's likely file-existence checks, preventing tautological validation.
- **Instrument Validity**: The `hardcode` verifier is assumed valid per the paper's description. The study validates this assumption by comparing it against the **independent** human ground truth.

### Verifier Logic Validation
Before the batch run, the plan includes a **Verifier Logic Validation** step. The `hardcode` verifier's logic for each selected task is manually reviewed against the task spec to ensure it checks the correct properties (e.g., file content vs. just existence). If a verifier is found to be misaligned (e.g., checking for a file that exists but is empty), this is noted in the report as a "Verifier Logic Flaw" rather than a "Task Failure".

## Compute Feasibility Analysis

The plan is constrained to the GitHub Actions free-tier runner (limited CPU, limited RAM, 14GB Disk, No GPU).

1.  **Docker Overhead**: Building the base image for Audacity/GIMP may consume significant RAM.
    - *Mitigation*: The plan orders phases to build the image *before* running tasks. If the build exceeds 7GB RAM, the job fails gracefully (FR-005).
    - *Mitigation*: Use a minimal base image (e.g., `ubuntu:22.04` with only required apps) rather than a pre-baked "heavy" image if the submodule allows.
2.  **Agent Execution**:
    - *Constraint*: No GPU. The plan uses `hardcode` verifiers and assumes the agent (if invoked) is a CPU-only LLM or a mock agent for the smoke test.
    - *Decision*: If the spec implies a heavy LLM agent (e.g., `claude_agent`), the plan will use a "dummy" agent or a small local CPU model (e.g., `llama-3-8b` via `llama-cpp-python` with quantization) *only if* the spec allows. However, per FR-002, the focus is on the *verifier* alignment. The agent's output is the input to the verifier. If the agent fails, the verifier should correctly report "failed".
3.  **Disk Space**:
    - *Constraint*: 14GB total.
    - *Mitigation*: Tasks are limited to 5. Artifacts (audio files, logs) are small (<10MB). Docker layers are cached.
    - *Risk*: If the base image is >10GB, the job fails. The plan includes a check for available disk space before building.

## Decision Rationale

- **Why 5 tasks?** The paper claims "1000 tasks". Running on a 6-hour, 7GB runner is infeasible. 5 tasks provide a representative sample to test the *pipeline* (US-2) without exceeding resources.
- **Why `audacity_export_wav_440`?** It is a deterministic, file-based task. It does not require complex GUI interaction (reducing rendering load) and has a clear pass/fail state (file exists, correct metadata).
- **Why `hardcode` verifier?** It removes LLM-as-judge variability, isolating the *system's* ability to detect state changes, which is the core claim being tested.
- **Why Qualitative Case Study?** Calculating a statistical "rate" with a "10% margin of error" for N=5 is mathematically impossible. The plan prioritizes scientific soundness over meeting an impossible spec constraint, reframing the output as a detailed case study.
