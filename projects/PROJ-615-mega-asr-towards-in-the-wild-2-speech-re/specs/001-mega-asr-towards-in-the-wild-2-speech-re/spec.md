# Feature Specification: Mega-ASR Reproduction & Validation

**Feature Branch**: `615-mega-asr-reproduction`  
**Created**: 2026-05-23  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: Mega-ASR: Towards In-the-wild^2 Speech Recognition via Scaling up Real-world Acoustic Simulation. Code vendored at external/Voices-in-the-Wild-Bench."

## User Scenarios & Testing

### User Story 1 - Execute Inference Pipeline on Sample Data (Priority: P1)

**Description**: As a researcher, I need to run the `run_inference.py` script against the provided sample dataset (`data/examples.jsonl`) using the default CPU-compatible model configuration to verify the codebase executes without runtime errors and produces initial prediction artifacts.

**Why this priority**: This is the fundamental "smoke test." If the pipeline cannot execute on the provided sample data within the CI constraints (CPU-only, 7GB RAM), the entire project is non-viable. It validates the environment setup, dependency resolution, and basic I/O flow.

**Independent Test**: Run the script locally or in CI with the sample data; verify that a JSONL output file containing transcription results is generated and contains non-empty text fields.

**Acceptance Scenarios**:

1. **Given** the `Voices-in-the-Wild-Bench` submodule is cloned and dependencies are installed, **When** `scripts/run_inference.py` is executed with `--input data/examples.jsonl` and `--output results/sample_predictions.jsonl`, **Then** the process completes within 15 minutes, exits with code 0, and `results/sample_predictions.jsonl` contains at least 5 valid transcription records.
2. **Given** the environment has no GPU, **When** the script attempts to load the model, **Then** it successfully initializes the model on CPU (or a compatible fallback) and does not raise a CUDA/Device error.

---

### User Story 2 - Compute and Report Word Error Rate (WER) (Priority: P2)

**Description**: As a researcher, I need to run the `evaluate_predictions.py` script to compare the generated predictions against ground truth labels to calculate the Word Error Rate (WER) for the sample dataset, confirming the metric engine functions correctly.

**Why this priority**: Validation is the core purpose of this project. Without a functional metric calculation, we cannot verify if the "Mega-ASR" model actually performs better than baselines or matches the paper's claims. This establishes the quantitative baseline.

**Independent Test**: Run the evaluation script against the sample predictions and ground truth; verify that a summary report is generated containing a calculated WER value.

**Acceptance Scenarios**:

1. **Given** `results/sample_predictions.jsonl` exists with valid transcriptions, **When** `scripts/evaluate_predictions.py` is executed with `--predictions results/sample_predictions.jsonl` and `--ground_truth data/examples.jsonl`, **Then** the script outputs a summary to stdout containing a WER value (float) and exits with code 0.
2. **Given** a mismatch between prediction and ground truth length, **When** the evaluation runs, **Then** the script handles the tokenization alignment gracefully (no crash) and reports the calculated error rate.

---

### User Story 3 - Reproduce Paper Benchmark Results (Priority: P3)

**Description**: As a researcher, I need to run the full evaluation pipeline against the paper's specified benchmarks (e.g., VOiCES R4-B-F, NOIZEUS) using the full dataset (if size permits) or a statistically representative sample to confirm the reported WER reductions (e.g., [deferred] vs [deferred]).

**Why this priority**: This is the ultimate validation of the paper's claims. While P1 and P2 ensure the *code* works, P3 ensures the *science* is reproducible. It addresses the reviewer's concern about scaling laws by providing the data points for the accuracy vs. compute curve.

**Independent Test**: Execute the pipeline on the full benchmark subset; compare the resulting WER against the paper's reported numbers (within a tolerance of ±1.5% absolute WER).

**Acceptance Scenarios**:

1. **Given** the full benchmark dataset is accessible and fits within memory, **When** the inference and evaluation scripts are run end-to-end, **Then** the resulting WER for the Mega-ASR model on the VOiCES R4-B-F benchmark is ≤ 46.0% (paper reported a notable percentage).
2. **Given** the full dataset exceeds GB RAM, **When** the pipeline runs, **Then** it successfully processes the data in batches or via a sampled subset (as defined in Assumptions) and reports the WER for that specific subset with a clear label indicating "Sampled" to maintain scientific rigor.

---

### Edge Cases

- **Memory Overflow**: What happens if the full `Voices-in-the-Wild-2M` dataset is loaded into RAM? The system MUST handle this by streaming or batching, or by explicitly failing with a clear error message suggesting a sample size reduction.
- **Model Loading Failure**: How does the system handle a model checkpoint that is missing or corrupted? The system MUST raise a specific `FileNotFoundError` or `CorruptedCheckpointError` rather than a generic stack trace.
- **Audio Format Mismatch**: What happens if an audio file in the JSONL has an unsupported codec? The system MUST log the error for that specific record and continue processing the rest of the batch, rather than crashing the entire run.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST execute the `run_inference.py` script on CPU-only hardware without requiring CUDA or GPU acceleration (See US-1).
- **FR-002**: The system MUST process the input JSONL dataset and output a prediction JSONL file containing the `transcription` field for every valid audio entry (See US-1).
- **FR-003**: The system MUST calculate the Word Error Rate (WER) by comparing predictions against ground truth labels using standard Levenshtein distance alignment (See US-2).
- **FR-004**: The system MUST handle dataset sizes exceeding available RAM by implementing batch processing or explicit sampling, ensuring the job completes within the -hour CI limit. (See US-3).
- **FR-005**: The system MUST report the final WER metric alongside the specific benchmark name (e.g., "VOiCES R4-B-F") and the model variant used (See US-3).
- **FR-006**: The system MUST validate that all required variables (audio path, ground truth text, distortion type) are present in the input JSONL before processing (See US-2).

### Key Entities

- **AudioSample**: Represents a single entry in the benchmark dataset, containing the audio file path, ground truth transcription, and metadata (distortion type, category).
- **Prediction**: The output of the inference engine, containing the audio file reference and the generated transcription text.
- **MetricReport**: The aggregated result of the evaluation, containing the calculated WER, total samples processed, and benchmark identifier.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Inference latency per sample is measured against the total job limit., ensuring the full benchmark (or valid sample) completes within the time bound (See FR-001, US-1).
- **SC-002**: Memory usage peak is measured against the RAM limit of the free-tier runner., ensuring no OOM (Out of Memory) crashes occur (See FR-004, US-3).
- **SC-003**: Reproducibility accuracy is measured against the paper's reported WER values (e.g., [deferred] on VOiCES R4-B-F), with a tolerance of ±1.5% absolute WER (See FR-005, US-3).
- **SC-004**: Data integrity is measured against the input JSONL count, ensuring [deferred] of valid input records produce a corresponding output record (See FR-002, US-2).
- **SC-005**: Methodological validity is measured by the presence of a documented "Sampling Strategy" if the full dataset cannot fit, ensuring the reported WER is explicitly tied to the subset used (See FR-004, US-3).

## Assumptions

- The `Voices-in-the-Wild-Bench` repository contains a valid, pre-trained Mega-ASR model checkpoint that can be loaded without requiring re-training or fine-tuning, as the project scope is reproduction, not model creation.
- The "Voices-in-the-Wild-2M" dataset is too large to fit in the Sufficient RAM on the free-tier runner; therefore, the reproduction will rely on the `data/examples.jsonl` for P1/P2 validation and a statistically representative random sample (e.g., a sufficiently large number of records) for P3 benchmarking if the full set is required.
- The paper's reported WER values (e.g., [deferred]) are calculated using the exact same version of the WER metric implementation provided in the `src/voices_in_the_wild_bench/metrics/error_rate.py` file; any discrepancy > 1.5% is attributed to floating-point precision differences or dataset version drift.
- The inference model (Mega-ASR) is small enough to run on CPU within the -hour limit for a a sample of audio clips; if the model is too large, the project will default to evaluating a smaller subset (e.g., a limited number of clips) and explicitly note this limitation in the final report.
- The audio files in the dataset are in a standard format (WAV/MP3) compatible with the `librosa` or `torchaudio` backends available in the `requirements.txt`.
- The reviewer's concern regarding "allometric scaling" (accuracy vs. compute) will be addressed by reporting the WER for the specific sample size used, acknowledging that a full scaling law analysis is outside the scope of a single reproduction run but the data points will be collected for future analysis.
