# Implementation Plan: Reproduce & Validate StepAudio 2.5 Technical Report

**Branch**: `001-reproduce-stepaudio-2.5` | **Date**: 2024-05-21 | **Spec**: `specs/001-https-arxiv-org-abs-2605-23463/spec.md`
**Input**: Feature specification from `specs/001-https-arxiv-org-abs-2605-23463/spec.md`

## Summary

This feature executes a reproduction workflow for the StepAudio 2.5 Technical Report (arXiv:2605.23463) using vendored code located at `external/wenetspeech-testnet-long`. The primary technical approach is to orchestrate the execution of the `prepare.py` entry point within a constrained CPU-only CI environment (limited RAM, 2 cores), parse the `WenetSpeech_testnet_long.json` configuration, generate output artifacts (transcriptions, logs), and validate these against the paper's claimed metrics to produce a `validation_report.md`.

**Critical Note on Model Availability**: The arXiv ID `2605.23463` is future-dated (May 2026) and currently invalid. **Phase 0** includes a mandatory "Scope Definition" step. If a valid, existing model source (e.g., a real arXiv ID, HuggingFace repo, or GitHub release) matching the "StepAudio 2.5" claim is not found within a defined search window, the run MUST terminate with exit code `E_SCOPE_INVALID`. **No silent fallbacks** are permitted. If the scope is invalid, the project status is set to "Blocked".

**Critical Note on Compute Feasibility**: The plan explicitly acknowledges that modern ASR/TTS models often exceed significant RAM requirements. **Phase 0** includes a "Model Feasibility" check. If the vendored `prepare.py` requires GPU hardware or a model variant that cannot fit in 7GB RAM *without source modification*, the run MUST terminate with exit code `E_MODEL_MISSING`. The plan **does not** attempt to force quantization via environment variables, as this violates the "no modification" constraint (FR-001).

The plan strictly adheres to the spec's requirement for no code modification to the vendored source, relying instead on environment configuration and wrapper scripts for resource management and error handling.

## Technical Context

**Language/Version**: Python 3.11 (inferred from typical ASR/TTS stacks and `prepare.py` convention)
**Primary Dependencies**: `torch` (CPU-only), `scipy`/`librosa` (audio processing), `jsonschema` (validation), `pandas` (data handling). *Note: Specific versions deferred to `research.md` based on `requirements.txt` in the submodule.*
**Storage**: Filesystem (`output/` directory for artifacts, `external/` for submodule data).
**Testing**: `pytest` (for validation logic and contract checks).
**Target Platform**: Linux (GitHub Actions free-tier runner).
**Project Type**: CLI / Reproduction Pipeline.
**Performance Goals**: Complete execution within 6 hours; memory usage < 7GB; zero GPU dependency.
**Constraints**: CPU-only execution; no network authentication; strict adherence to `WenetSpeech_testnet_long.json` schema.
**Scale/Scope**: Processing the "testnet" subset of WenetSpeech (size [deferred] entries).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*Gates determined based on constitution file (referenced in project root).*

1.  **Principle I: SSoT (Single Source of Truth)**: The plan mandates capturing `run_metadata.json` (FR-004) and using the exact `prepare.py` from the submodule (FR-001) to ensure the run is reproducible and traceable to the source. The `run_metadata.json` now includes `statistical_method` and `strata_columns` to ensure the exact analysis path is recorded.
2.  **Principle II: No Silent Fallbacks**: The plan explicitly prohibits fallback to alternative models (e.g., Whisper) if StepAudio 2.5 is unavailable. Failure to locate the specific model or a valid scope triggers `E_SCOPE_INVALID` and halts the run, ensuring no silent substitution occurs.
3.  **Principle III: Reproducibility**: The plan mandates capturing `run_metadata.json` (FR-004) and using the exact `prepare.py` from the submodule (FR-001). The inclusion of `strata_columns` and `statistical_method` ensures that sampling and analysis choices are fully reproducible.
4.  **Principle IV: Transparency**: The `validation_report.md` (FR-005) will explicitly flag discrepancies and calibration offsets (or lack thereof) rather than hiding them. It will clearly state if a metric (like MOS) is unvalidated due to the lack of human evaluation.
5.  **Principle V: Real-call Testing**: The plan enforces explicit error codes (FR-006) and failure modes (Edge Cases) to prevent silent data corruption, aligning with the robustness principle.
6.  **Principle VI: Resource Stewardship**: The plan includes a "Compute Feasibility" section in `research.md` to validate that the model fits the 7GB RAM/2 CPU constraint, addressing the resource stewardship principle.

## Project Structure

### Documentation (this feature)

```text
specs/001-https-arxiv-org-abs-2605-23463/
├── plan.md              # This file
├── research.md          # Phase 0 output (Dataset strategy, feasibility analysis)
├── data-model.md        # Phase 1 output (Schema definitions for inputs/outputs)
├── quickstart.md        # Phase 1 output (How to run locally/CI)
├── contracts/           # Phase 1 output (YAML schemas for validation)
│   ├── wenetspeech-config.schema.yaml
│   ├── run-metadata.schema.yaml
│   └── validation-report.schema.yaml
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
# Option 1: Single project (Reproduction Pipeline)
external/
└── wenetspeech-testnet-long/  # Git Submodule (Vendored code)
    ├── prepare.py
    ├── WenetSpeech_testnet_long.json
    └── requirements.txt

src/
├── validation/
│   ├── runner.py          # Wrapper to execute prepare.py with error handling
│   ├── validator.py       # Logic to compare artifacts vs paper claims
│   └── metrics.py         # Extraction logic for WER/MOS/Latency
├── config/
│   └── paths.yaml         # Configuration for input/output paths
└── cli/
    └── main.py            # Entry point for the reproduction workflow

tests/
├── contract/
│   ├── test_schemas.py    # Validates output against contracts/*.schema.yaml
│   └── test_error_codes.py
└── integration/
    └── test_full_run.py   # Mocked integration test for the pipeline

output/                    # Generated artifacts (logs, results, reports)
├── run.log
├── run_metadata.json
├── results.json
└── validation_report.md
```

**Structure Decision**: A single-project structure is selected. The vendored code (`external/`) remains untouched as per FR-001. The `src/` directory contains the orchestration logic (wrapper, validation, CLI) that interacts with the vendored entry point without modifying it. This separation ensures the "faithful clone" requirement is met while allowing the project to add necessary CI/CD glue code.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | The scope is tightly bounded by the spec (reproduce one script, validate one paper). | N/A |

## Phase Breakdown

### Phase 0: Research, Feasibility & Scope Definition
*Goal: Confirm dataset fit, model feasibility on CPU, extract paper claims, and validate scope.*
1.  **Scope Definition**: Verify the validity of arXiv ID `2605.23463`. If invalid, search for an alternative verified source (HuggingFace, GitHub). If no valid source is found within the search window, terminate with `E_SCOPE_INVALID`.
2.  **Dataset Verification**: Confirm `WenetSpeech_testnet_long.json` contains the necessary fields (audio paths, **ground truth transcriptions**). **Crucially**, verify that the `transcription` field corresponds to the *official WenetSpeech test set annotations* (independent of the model's training). If the input JSON lacks these independent ground truths, the run halts with `E_MISSING_GROUND_TRUTH`.
    *   **Remote Check**: Verify that `audio_path` entries point to remote URLs (streaming) and NOT local bundled files. If local paths are detected that imply >14GB data bundling, terminate with `E_DISK_EXCEEDED`.
3.  **Model Feasibility**: Analyze `prepare.py` dependencies. Determine if the StepAudio model weights can be loaded on CPU (7GB RAM).
    *   **Strict Constraint**: If the script requires GPU (`device='cuda'`) or a model size >7GB *without* a pre-quantized variant provided in the submodule, the run halts with `E_MODEL_MISSING`. **No attempt to force quantization via environment variables is made**, as this violates FR-001.
4.  **Claim Extraction**: Parse the StepAudio 2.5 Technical Report to extract specific metrics (WER, MOS, Latency). **Note: For MOS, extract the specific proxy metric (e.g., DNSMOS) used in the paper or define a calibration strategy if the paper reports human MOS.**

### Phase 1: Design & Contracts
*Goal: Define data schemas and validation contracts.*
1.  **Schema Definition**: Create `contracts/wenetspeech-config.schema.yaml` (input), `contracts/run-metadata.schema.yaml` (output), and `contracts/validation-report.schema.yaml` (validation) to enforce data integrity. **The `run-metadata.schema.yaml` must include `strata_columns` and `statistical_method` to ensure reproducibility of sampling and analysis.**
2.  **Validation Logic Design**: Define the mapping between paper claims and output metrics. **Implement statistical testing:**
    *   If sample size N >= 30: Use Bootstrap Resampling (1000 iterations) for WER.
    *   If sample size N < 30: Use Exact Binomial Test for WER.
    *   For MOS: Compare DNSMOS P.835 against public baselines (e.g., Whisper). If the paper claims human MOS, flag as "Needs Clarification".
    *   Design the `validation_report.md` template to include calibration offsets for proxy metrics (if applicable) or explicit notes on inconclusive validation.
3.  **Error Handling Design**: Define the specific exit codes and error messages for `E_INVALID_INPUT`, `E_RESOURCE_LIMIT`, `E_NETWORK_TIMEOUT`, `E_MISSING_GROUND_TRUTH`, `E_SCOPE_INVALID`, `E_MODEL_MISSING`, and `E_DISK_EXCEEDED`.

### Phase 2: Implementation (Orchestration & Validation)
*Goal: Build the wrapper and validation scripts.*
1.  **Wrapper Script (`src/validation/runner.py`)**: Implement the execution of `prepare.py` with retry logic, memory monitoring, and metadata capture. **Include a pre-flight check to verify `transcription` fields exist in the input JSON; if missing, exit with `E_MISSING_GROUND_TRUTH`.**
    *   **Streaming Strategy**: If entries contain remote URLs, implement a chunked download mechanism that deletes files immediately after processing to stay within 14GB disk.
    *   **Sampling Trigger Logic**: If `total_entries > MAX_PROCESSABLE_ENTRIES` (defined in research.md), automatically trigger stratified sampling based on `speaker_id` and `duration`. Log `strata_columns` and `method` in `run_metadata.json`.
2.  **Validator (`src/validation/validator.py`)**: Implement the logic to parse output artifacts and compare them against the extracted paper claims. **Use the selected statistical method (Bootstrap or Exact Binomial) to calculate confidence intervals for WER. If the paper's claimed WER falls outside this interval, flag as 'Discrepancy'.**
3.  **Report Generator**: Generate `validation_report.md` with "Confirmed", "Discrepancy", or "Needs Clarification" tags. **For TTS, explicitly report the DNSMOS proxy score and note if the paper's claim was human MOS (making the validation inconclusive).**

### Phase 3: Verification
*Goal: Validate the pipeline against the spec.*
1.  **Contract Tests**: Run `pytest` against the generated schemas to ensure strict adherence.
2.  **Integration Test**: Execute the full pipeline on a small subset (if possible) or mock data to verify the flow from `prepare.py` to `validation_report.md`.
3.  **Resource Stress Test**: Verify the pipeline respects the 7GB RAM limit (using `ulimit` or Python memory profiling).

## Statistical Rigor Note

To ensure scientific soundness, the plan replaces heuristic thresholds with **statistical significance testing**:

*   **WER**:
    *   If N >= 30: Use **Bootstrap Resampling (1000 iterations)** to calculate a 95% confidence interval.
    *   If N < 30: Use **Exact Binomial Test** to calculate the p-value of the observed error rate against the paper's claim.
    *   A "Discrepancy" is only flagged if the paper's claimed WER falls outside the confidence interval or the p-value is < 0.05.
*   **MOS**:
    *   Acknowledge that MOS is a human metric. The validation will use **DNSMOS P.835** as a proxy.
    *   Compare the DNSMOS score against a **public baseline** (e.g., standard Whisper DNSMOS scores).
    *   If the paper claims human MOS, the status will be "Needs Clarification" with a note: "Human MOS cannot be validated via proxy; comparison against DNSMOS baseline only."
*   **Sampling**:
    *   If sampling is required, **stratified random sampling** based on `speaker_id` and `duration` will be used to ensure representativeness.
    *   The `strata_columns` and `method` will be logged in `run_metadata.json` to ensure reproducibility.