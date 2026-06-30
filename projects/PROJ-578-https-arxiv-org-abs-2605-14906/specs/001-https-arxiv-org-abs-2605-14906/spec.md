# Feature Specification: Reproduce & Validate MemLens Benchmark

**Feature Branch**: `578-reproduce-memlens-benchmark`  
**Created**: 2026-05-21  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: MemLens: Benchmarking Multimodal Long-Term Memory in Large Vision-Language Models"

## User Scenarios & Testing

### User Story 1 - Execute MemLens Evaluation Pipeline on CPU (Priority: P1)

The research engineer MUST be able to trigger the vendored MemLens evaluation scripts (`eval.py` or `scripts/run_eval.sh`) against a subset of the benchmark data using only CPU resources, resulting in the generation of valid JSON result artifacts without requiring GPU acceleration.

**Why this priority**: This is the foundational step. Without a successful, reproducible execution of the codebase on the target CI environment (free-tier CPU), no validation of the paper's claims can occur. It validates the "reproduction" aspect of the project.

**Independent Test**: Can be fully tested by running the entry point script with a small, mocked or subset dataset configuration and verifying the presence of output JSON files containing evaluation metrics.

**Acceptance Scenarios**:

1. **Given** the `MEMLENS` submodule is cloned and dependencies are installed, **When** the evaluation script is invoked with a CPU-only flag and a small data subset (e.g., 10 questions), **Then** the process completes within 60 minutes and outputs a `results.json` file containing non-null metric values.
2. **Given** a standard GitHub Actions free-tier runner (2 CPU, 7GB RAM), **When** the full evaluation logic is invoked on a [deferred] sample of the dataset, **Then** the process does not crash due to out-of-memory (OOM) errors and produces a summary report file.

---

### User Story 2 - Validate Visual Evidence Dependency (Priority: P2)

The research engineer MUST be able to run the specific "image-ablation" experiment defined in the paper, where visual evidence images are programmatically removed from the input context, and confirm that model accuracy on image-dependent questions drops significantly (targeting the <2% accuracy claim).

**Why this priority**: This validates the core scientific claim of the paper: that solving these tasks genuinely requires visual evidence. It moves beyond "does the code run" to "does the code prove the hypothesis."

**Independent Test**: Can be tested by comparing the accuracy metrics of a model run with full multimodal input versus a run where image inputs are replaced with empty strings or null tokens, specifically on the subset of questions marked as having image evidence.

**Acceptance Scenarios**:

1. **Given** a model capable of answering the benchmark questions, **When** the evaluation is run on the "image-evidence" subset with images present, **Then** the recorded accuracy is > 2%.
2. **Given** the same model and questions, **When** the evaluation is run with images removed (ablation), **Then** the recorded accuracy drops to ≤ 2% for the specified subset, matching the paper's ablation claim.

---

### User Story 3 - Reproduce Scaling & Memory Ability Trends (Priority: P3)

The research engineer MUST be able to generate a summary report that categorizes model performance across the five defined memory abilities (information extraction, multi-session reasoning, etc.) and at least two context lengths (e.g., 32K vs 128K) to verify the degradation trend described in the paper.

**Why this priority**: This confirms the "benchmarking" utility of the tool. It ensures the system can handle the varying context lengths and ability classifications required to reproduce the paper's main figures.

**Independent Test**: Can be tested by aggregating results from multiple evaluation runs with different context window configurations and verifying that the output table/JSON reflects the expected performance degradation for long-context LVLMs.

**Acceptance Scenarios**:

1. **Given** a set of evaluated models, **When** results are aggregated by "memory ability" type, **Then** the output report contains distinct performance metrics for all five defined abilities.
2. **Given** evaluations run at 32K and 256K token contexts, **When** performance is compared, **Then** the report explicitly flags the performance drop for long-context LVLMs as the context length increases.

### Edge Cases

- **What happens when** the external API (e.g., OpenAI, Anthropic) rate-limits the evaluation script? The system MUST implement a retry mechanism with exponential backoff (a limited number of attempts, a base delay) and log the failure without crashing the entire batch.
- **How does the system handle** corrupted or missing image files in the dataset? The system MUST skip the specific question with a warning log entry rather than terminating the entire evaluation process.
- **What happens when** the memory usage exceeds 7GB during the processing of a 256K context window? The system MUST detect the memory pressure and automatically switch to a chunked processing mode or terminate gracefully with a specific "OOM" error code to prevent CI job hanging.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST execute the `eval.py` entry point with a `--cpu-only` configuration to ensure no CUDA/GPU dependencies are invoked during the benchmark run (See US-1).
- **FR-002**: The system MUST implement an image-ablation mode that programmatically replaces image inputs with null/empty tokens for the evaluation subset to verify visual dependency (See US-2).
- **FR-003**: The system MUST support configurable context length windows (specifically K, 64K, 128K, 256K) to reproduce the scaling analysis (See US-3).
- **FR-004**: The system MUST categorize and output results separately for the five defined memory abilities: information extraction, multi-session reasoning, temporal reasoning, knowledge update, and answer refusal (See US-3).
- **FR-005**: The system MUST implement a retry mechanism with exponential backoff for external API calls to handle rate limiting without halting the entire benchmark (See Edge Cases).
- **FR-006**: The system MUST log memory usage peaks during execution and gracefully handle Out-Of-Memory (OOM) conditions by terminating the specific job with a distinct error code (See Edge Cases).

### Key Entities

- **Evaluation Run**: A single execution instance of the benchmark on a specific model, context length, and data subset, producing a unique JSON artifact.
- **Memory Ability**: A categorical label (e.g., "multi-session reasoning") assigned to each question, used to aggregate performance metrics.
- **Context Window**: The token length limit (e.g., 32K, 256K) defining the amount of conversation history provided to the model.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Reproducibility of the evaluation pipeline is measured against the successful generation of non-empty `results.json` artifacts from the `MEMLENS` entry point on a CPU-only runner (See FR-001).
- **SC-002**: Validation of the visual dependency claim is measured against the observed accuracy drop (targeting <2%) in the image-ablation subset compared to the full-multimodal baseline (See FR-002).
- **SC-003**: Scaling trend verification is measured against the presence of performance degradation metrics in the output report when comparing 32K vs 256K context lengths (See FR-003).
- **SC-004**: Methodological robustness is measured against the successful completion of the benchmark on a [deferred] data sample without OOM crashes, confirming CPU feasibility (See FR-006).
- **SC-005**: Data validity is measured against the successful categorization of [deferred] of evaluated questions into the five defined memory ability types (See FR-004).

## Assumptions

- The vendored `MEMLENS` codebase is syntactically correct and compatible with the Python version specified in `requirements.txt` (likely Python 3.10+) on the CI runner.
- The dataset files referenced in the code (e.g., JSONL files) are present in the submodule or accessible via the provided download scripts; if missing, the run will fail with a "File Not Found" error rather than a logic error.
- External API keys (for models like GPT-4, Claude, etc.) are provided via environment variables; if not present, the evaluation will skip those models or fail with a clear authentication error.
- The RAM limit of the free-tier runner is sufficient for processing a [deferred] sample of the 256K context data; if the full dataset is attempted, the job may exceed memory limits (handled by FR-006).
- The paper's claim of "cross-modal token counting" is implemented correctly in the `data.py` module, and the token counts align with the paper's definitions (tens of thousands to hundreds of thousands).
- The evaluation metrics (accuracy, refusal rates) are calculated using the `llm_judge.py` module as defined in the paper, without requiring manual intervention for score calculation.
