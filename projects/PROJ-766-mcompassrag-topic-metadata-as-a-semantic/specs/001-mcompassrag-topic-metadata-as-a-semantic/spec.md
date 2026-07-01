# Feature Specification: MCompassRAG: Topic Metadata as a Semantic Compass for Paragraph-Level Retrieval

**Feature Branch**: `766-mcompassrag-topic-metadata-as-a-semantic`  
**Created**: 2024-05-22  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: MCompassRAG: Topic Metadata as a Semantic Compass for Paragraph-Level Retrieval"

## User Scenarios & Testing

### User Story 1 - End-to-End Execution on CPU-Only Runner (Priority: P1)

**Journey**: As a researcher, I need to execute the MCompassRAG pipeline (indexing, topic modeling, retriever training, and inference) on the provided GitHub Actions free-tier runner (2 CPU, ~7 GB RAM, no GPU) to confirm the codebase is functional and does not rely on unavailable hardware (CUDA/GPU).

**Why this priority**: The project is a reproduction effort. If the code cannot run on the target CI environment due to GPU dependencies (e.g., `load_in_8bit`, CUDA imports), the project is dead on arrival. This is the gatekeeper requirement.

**Independent Test**: Trigger the `scripts/setup.sh` and `scripts/run_rag.sh` (or equivalent entry points) in a fresh CI environment. Verify the process exits with code 0 and produces output logs without `ImportError: No module named 'torch.cuda'` or similar hardware-specific exceptions.

**Acceptance Scenarios**:

1. **Given** a fresh GitHub Actions runner (free tier, CPU only), **When** the setup script installs dependencies from `requirements.txt`, **Then** the installation completes without errors related to CUDA or GPU-specific binaries.
2. **Given** the environment is ready, **When** the main pipeline script (`src/run.py`) is invoked with default configuration, **Then** the process completes successfully (exit code 0) without triggering out-of-memory (OOM) errors or GPU device checks.
3. **Given** the pipeline runs, **When** the execution finishes, **Then** log artifacts confirm the execution path did not attempt to load models onto a GPU device (e.g., no logs showing "cuda:0").

---

### User Story 2 - Artifact Generation and Validation (Priority: P2)

**Journey**: As a validator, I need the pipeline to generate concrete artifacts (retrieval logs, intermediate embeddings, or summary metrics) that can be compared against the paper's claims to confirm the system is actually processing data and not failing silently.

**Why this priority**: Successful execution (US-1) is necessary but not sufficient. The system must produce real data artifacts to be considered a valid reproduction.

**Independent Test**: Run the pipeline and verify the existence of output files in the `data/` or `outputs/` directory (as defined by the repo) that contain non-empty, non-placeholder data (e.g., JSON logs with actual retrieval scores).

**Acceptance Scenarios**:

1. **Given** the pipeline has completed execution, **When** I inspect the output directory, **Then** at least one artifact file (e.g., `retrieval_results.json`, `topic_embeddings.pt`, or `metrics.csv`) exists and contains >100 bytes of data.
2. **Given** the artifacts exist, **When** I parse the retrieval results, **Then** the data contains valid numerical scores (e.g., cosine similarity or rank) and document IDs, not null or placeholder strings.
3. **Given** the pipeline runs against a subset of the data, **When** the run finishes, **Then** the log output explicitly states the number of queries processed and documents retrieved, matching the input configuration.

---

### User Story 3 - Performance Baseline Reporting (Priority: P3)

**Journey**: As a researcher, I need the system to output a summary of latency and retrieval efficiency metrics (Information Efficiency) to enable a preliminary comparison with the paper's claim of "5x lower latency" and "[deferred] IE improvement" (even if only on a small subset).

**Why this priority**: The paper's core contribution is performance improvement. While a full-scale benchmark might be too heavy for the free tier, a partial metric report is required to validate the *direction* of the results.

**Independent Test**: Execute the pipeline with a small, fixed subset of the benchmark data (e.g., 50 queries) and capture the reported latency and retrieval scores.

**Acceptance Scenarios**:

1. **Given** a subset of 50 queries is processed, **When** the inference phase completes, **Then** the system outputs a summary table or log entry containing "Average Latency" and "Retrieval Score" (or equivalent metric).
2. **Given** the metrics are reported, **When** I review the output, **Then** the latency is measured in seconds (or milliseconds) and is a finite number < 60 seconds per query (ensuring it fits within the 6h CI window).
3. **Given** the results are generated, **When** I compare them to the paper's abstract, **Then** the spec documents the observed values and flags whether they are within an order of magnitude of the claimed "5x lower latency" (noting that full statistical significance is deferred to the research phase).

---

### Edge Cases

- **What happens when the dataset is too large for 7 GB RAM?** The system MUST automatically sample a subset of the data (e.g., first [deferred] documents) or raise a clear configuration error before OOM occurs, rather than crashing the runner.
- **How does the system handle missing external dependencies (e.g., OpenRouter API for data generation)?** If the code attempts to call an external API for training data generation (as seen in `data_gen/openrouter_client.py`), the system MUST either use a pre-generated local cache or skip the generation step with a clear warning, ensuring the reproduction can proceed without external network calls during the validation phase.
- **What happens if a topic model fails to converge?** The system MUST log the failure and continue with a fallback configuration (e.g., random initialization or default topics) rather than halting the entire pipeline, allowing the retrieval component to be tested in isolation.

## Requirements

### Functional Requirements

- **FR-001**: System MUST execute the MCompassRAG pipeline (`src/run.py`) on a CPU-only environment without requiring CUDA or GPU acceleration, ensuring all model loading defaults to CPU (See US-1).
- **FR-002**: System MUST generate and persist retrieval artifacts (e.g., JSON logs, CSV metrics, or embedding files) to the designated output directory upon successful completion of the inference step (See US-2).
- **FR-003**: System MUST handle dataset size constraints by either automatically sampling the input data to fit within ~7 GB RAM or explicitly failing with a "Dataset Too Large" error message that suggests a configuration change (See US-2).
- **FR-004**: System MUST report execution metrics including query count, processing time per query, and retrieval scores in the final log output to enable performance validation (See US-3).
- **FR-005**: System MUST gracefully handle missing external API dependencies (e.g., OpenRouter) by utilizing local cached data or skipping the data generation phase without crashing the pipeline (See US-2).

### Key Entities

- **RetrievalArtifact**: The output file containing retrieval results, including query ID, retrieved document IDs, similarity scores, and latency metrics.
- **TopicModelConfig**: The configuration object defining the topic modeling parameters (e.g., number of topics, model type like ETM or CWTM) used to generate the semantic compass.
- **BenchmarkSubset**: A sampled portion of the full benchmark dataset used to ensure the analysis fits within the CI runner's memory and time constraints.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Pipeline execution success rate is measured against the requirement that the job completes with exit code 0 on the GitHub Actions free-tier runner (See US-1).
- **SC-002**: Artifact validity is measured by verifying that the generated output files contain >100 bytes of data and valid numerical retrieval scores (See US-2).
- **SC-003**: Resource compliance is measured by confirming the peak memory usage remains < 7 GB and total execution time is < 6 hours for the validation run (See US-3).
- **SC-004**: Metric reporting completeness is measured by the presence of at least three distinct performance metrics (latency, retrieval score, query count) in the final log output (See US-3).

## Assumptions

- The provided `external/MCompassRAG` repository contains a `requirements.txt` that is compatible with CPU-only execution and does not strictly require GPU-specific packages (e.g., `torch` with CUDA support) to function, or the environment can fallback to CPU.
- The benchmark datasets referenced in the configuration files are either included in the repository or can be downloaded automatically without exceeding the 14 GB disk limit of the free-tier runner.
- The "LLM-teacher distillation" step mentioned in the paper is either pre-computed in the provided codebase or can be bypassed/simulated for the purpose of this validation run, as running a full LLM distillation on a CPU-only free runner is infeasible.
- The `scripts/setup.sh` and `scripts/run_rag.sh` entry points are functional and correctly configured to run the pipeline with minimal user intervention.
- The project assumes that a full statistical validation of the "[deferred] IE improvement" claim is out of scope for this initial reproduction spec; the focus is on functional correctness and the ability to produce *some* results comparable to the paper's methodology.
