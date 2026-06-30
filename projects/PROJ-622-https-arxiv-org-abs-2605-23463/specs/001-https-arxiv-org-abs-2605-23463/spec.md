# Feature Specification: Reproduce & Validate StepAudio 2.5 Technical Report

**Feature Branch**: `001-reproduce-stepaudio-2.5`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: StepAudio 2.5 Technical Report (arXiv:2605.23463) using vendored code at external/wenetspeech-testnet-long"

## User Scenarios & Testing

### User Story 1 - Execute Vendored Entry Point (Priority: P1)

The researcher MUST be able to trigger the execution of the vendored `prepare.py` script within the project environment to initiate the reproduction workflow. This is the foundational step; without successful execution, no artifacts can be generated or validated against the paper's claims.

**Why this priority**: This is the "Hello World" of the reproduction. If the code does not run, the project cannot proceed to validation or analysis. It validates the integration of the git submodule and the environment setup.

**Independent Test**: Running `python prepare.py` (or the detected entry point) in the project directory results in a non-zero exit code only if a genuine failure occurs, and produces at least one output file (log, intermediate data, or final artifact) in the designated output directory.

**Acceptance Scenarios**:

1. **Given** the submodule `wenetspeech-testnet-long` is cloned and the environment dependencies are installed, **When** the user executes the entry script `prepare.py`, **Then** the script completes without a fatal import error and generates a `run.log` or similar execution artifact.
2. **Given** the script is running, **When** it attempts to load the `WenetSpeech_testnet_long.json` configuration, **Then** it successfully parses the JSON and logs the loaded parameters to stdout/stderr.
3. **Given** the script encounters a missing dependency (e.g., a specific Python package not in `requirements.txt`), **When** it executes, **Then** it exits with a clear error code (non-zero) and prints a specific error message identifying the missing module.

---

### User Story 2 - Generate & Capture Real Artifacts (Priority: P2)

The system MUST produce tangible, non-empty artifacts (e.g., processed audio data, transcription results, or model output files) that correspond to the claims in the StepAudio 2.5 paper (ASR, TTS, or Realtime modes). These artifacts must be stored in the project's output directory.

**Why this priority**: The core value of a reproduction project is the generation of evidence. If the code runs but produces no data or empty files, the reproduction has failed. This story ensures the pipeline actually processes the input data defined in `WenetSpeech_testnet_long.json`.

**Independent Test**: After the script completes, the `output/` (or equivalent) directory contains at least one file with a size > 0 bytes, named according to the expected artifact format (e.g., `.json`, `.wav`, `.csv`).

**Acceptance Scenarios**:

1. **Given** the entry script has completed successfully, **When** the user inspects the designated output directory, **Then** at least one output file exists with a file size greater than 0 bytes.
2. **Given** the output file is a structured data format (e.g., JSON/CSV), **When** the file is parsed, **Then** it contains the expected keys/headers defined in the `WenetSpeech_testnet_long.json` schema (e.g., `transcription`, `audio_id`, `score`).
3. **Given** the script processes the WenetSpeech test set, **When** the output is generated, **Then** the number of processed entries in the output matches the number of entries in the input `WenetSpeech_testnet_long.json` (or a documented subset if sampling is applied).

---

### User Story 3 - Validate Against Paper Claims (Priority: P3)

The researcher MUST be able to compare the generated artifacts against the specific metrics or qualitative claims made in the StepAudio 2.5 Technical Report (e.g., "state-of-the-art results," "low-latency," "controllable synthesis"). This involves generating a validation report that flags discrepancies or confirms alignment.

**Why this priority**: This is the final verification step. It transforms raw execution into scientific validation. It ensures the reproduced results are not just "running code" but actually "reproducing the paper's findings."

**Independent Test**: A `validation_report.md` or similar artifact is generated that explicitly lists the paper's claimed metrics and the observed values from the run, marking them as "Confirmed," "Discrepancy," or "Needs Clarification."

**Acceptance Scenarios**:

1. **Given** the artifacts are generated, **When** the validation script runs, **Then** it extracts the primary metric (e.g., WER for ASR, MOS for TTS) from the output and compares it to the value reported in the paper's abstract or results table.
2. **Given** the paper claims "state-of-the-art" performance, **When** the validation report is generated, **Then** it includes a section comparing the reproduced metric against the baseline values cited in the paper.
3. **Given** a discrepancy is found between the reproduced metric and the paper's claim (e.g., >5% difference), **When** the report is generated, **Then** it flags this discrepancy with a `[NEEDS CLARIFICATION]` tag and suggests potential causes (e.g., data drift, hyperparameter mismatch).

### Edge Cases

- What happens if the `WenetSpeech_testnet_long.json` file is corrupted or empty? The system MUST fail gracefully with a specific error code (e.g., `E_INVALID_INPUT`) and a clear message, rather than crashing with a stack trace.
- How does the system handle network timeouts if the script attempts to download additional data (e.g., model weights) during execution? The system MUST retry up to 3 times with exponential backoff before failing the run.
- What happens if the hardware constraints (CPU-only, 7GB RAM) are exceeded during processing? The system MUST detect memory pressure and either fail with a `E_RESOURCE_LIMIT` error or automatically switch to a chunked processing mode if implemented.

## Requirements

### Functional Requirements

- **FR-001**: System MUST execute the vendored `prepare.py` script from the `external/wenetspeech-testnet-long` submodule without modification to the source code. (See US-1)
- **FR-002**: System MUST parse the `WenetSpeech_testnet_long.json` configuration file and use it to define the input data scope for the reproduction run. (See US-1)
- **FR-003**: System MUST generate output artifacts (e.g., logs, results files) in a designated `output/` directory that are non-empty and structurally valid. (See US-2)
- **FR-004**: System MUST capture execution metadata (start time, end time, exit code, environment version) in a `run_metadata.json` file for reproducibility auditing. (See US-2)
- **FR-005**: System MUST generate a `validation_report.md` that explicitly compares the reproduced metrics against the claims in the StepAudio 2.5 Technical Report (arXiv:2605.23463). (See US-3)
- **FR-006**: System MUST handle missing or corrupted input files by exiting with a non-zero code and a specific error message, preventing silent failures. (See US-1)

### Key Entities

- **Execution Run**: Represents a single invocation of the `prepare.py` script, containing metadata about the environment, input configuration, and output artifacts.
- **Reproduction Artifact**: The tangible output (data, logs, metrics) generated by the script, which serves as the evidence for validation.
- **Paper Claim**: A specific quantitative or qualitative assertion made in the StepAudio 2.5 Technical Report (e.g., "WER < X%", "Latency < Y ms") used as the reference for validation.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Execution success rate is measured against the requirement that the script completes with exit code 0. (See FR-001)
- **SC-002**: Artifact completeness is measured against the requirement that output files contain data corresponding to [deferred] of the input entries in `WenetSpeech_testnet_long.json`. (See FR-003)
- **SC-003**: Validation coverage is measured against the requirement that the `validation_report.md` addresses all primary metrics claimed in the paper's abstract and results section. (See FR-005)
- **SC-004**: Resource compliance is measured against the constraint that the entire run completes within the 6-hour CI limit and 7GB RAM limit without OOM errors. (See Assumptions)
- **SC-005**: Error handling efficacy is measured against the requirement that invalid inputs trigger a specific, documented error code rather than a generic crash. (See FR-006)

## Assumptions

- The vendored code in `external/wenetspeech-testnet-long` is a faithful, unmodified clone of the repository referenced in the paper and contains all necessary dependencies to run on a CPU-only environment.
- The `WenetSpeech_testnet_long.json` file contains valid, accessible paths to the WenetSpeech dataset or a representative subset that fits within the 14GB disk limit of the CI runner.
- The StepAudio 2.5 model weights (if required by `prepare.py`) are either bundled within the submodule or accessible via a public, stable URL that does not require authentication or GPU-specific downloads.
- The paper's claims regarding "state-of-the-art" results are based on standard benchmarks that can be approximated or validated using the provided testnet data without requiring the full training dataset.
- The `prepare.py` script is designed to run in a headless, non-interactive mode suitable for CI/CD execution.
- If the script requires a GPU for inference (common in audio models), the assumption is that the script has been modified or configured to run in a CPU-compatible mode (e.g., using `torch.device('cpu')`) or that the model is small enough to run on CPU within the 6-hour limit. **[NEEDS CLARIFICATION: Does the vendored `prepare.py` explicitly support CPU-only inference for the StepAudio 2.5 model, or does it require GPU hardware that is unavailable in the free CI tier?]**
