# Feature Specification: llmXive follow-up: extending "Code2LoRA: Hypernetwork-Generated Adapters for Code Language Models under Software Evolution"

**Feature Branch**: `001-ast-based-adapter-generation`  
**Created**: 2026-07-03  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending Code2LoRA to replace neural encoders with static analysis"

## User Scenarios & Testing

### User Story 1 - Generate Adapter via AST Features (Priority: P1)

A researcher or CI/CD operator needs to generate a repository-specific LoRA adapter for a code evolution task using only static syntactic features, without relying on heavy neural embedding models. This allows the process to run on standard CPU-only CI runners (e.g., GitHub Actions free tier) with minimal latency.

**Why this priority**: This is the core value proposition of the project. If the system cannot generate adapters using AST features, the efficiency gains and feasibility for resource-constrained environments are lost. It directly addresses the research gap regarding the sufficiency of syntactic metrics.

**Independent Test**: The system can be tested by running the feature extractor on a single repository, generating an adapter, and verifying the adapter file exists and is loadable by the base LLM, independent of the accuracy results.

**Acceptance Scenarios**:

1. **Given** a valid Python repository with commit history, **When** the system processes the repository through the AST feature extractor and hypernetwork, **Then** a LoRA adapter file (`.safetensors` or `.bin`) is generated within the job timeout of the CI runner (max several hours) and the generation time is measured against the baseline neural-encoder generation time.
2. **Given** a repository with complex inheritance structures, **When** the AST parser processes the files, **Then** the feature vector includes depth-of-inheritance metrics without raising a parsing error.
3. **Given** the base Code2LoRA checkpoint is loaded, **When** the new AST-based projection layer is applied, **Then** the system outputs a valid adapter configuration compatible with the base model's architecture.

---

### User Story 2 - Evaluate Adapter Performance on Assertion Tasks (Priority: P2)

A researcher needs to evaluate the generated adapter's performance on code evolution tasks (specifically assertion completion) to determine if the AST-based approach retains sufficient semantic fidelity compared to the neural baseline.

**Why this priority**: This validates the scientific hypothesis. Without performance evaluation, the efficiency gain is meaningless if the model cannot perform the task. This is the primary metric for "accuracy" in the research question.

**Independent Test**: The system can be tested by loading the generated adapter and running it against the test subset of RepoPeftBench, recording the exact-match scores independently of the generation speed.

**Acceptance Scenarios**:

1. **Given** a generated AST-based adapter, **When** it is applied to the test set of RepoPeftBench assertion-completion tasks, **Then** the system outputs an exact-match score for each task.
2. **Given** a baseline neural-encoder adapter, **When** both adapters are evaluated on the same test set, **Then** the system produces a paired comparison report showing the performance delta.
3. **Given** a task requiring deep semantic reasoning (e.g., complex API chaining), **When** the AST-based adapter is used, **Then** the system records the failure mode as a classification from a predefined taxonomy (e.g., 'Syntax Error', 'Semantic Mismatch', 'Timeout') and logs the specific assertion that failed.

---

### User Story 3 - Perform Sensitivity Analysis on Feature Complexity (Priority: P3)

A researcher needs to determine the minimum set of AST features required to maintain acceptable performance (e.g., >80% of baseline) to optimize the trade-off between feature extraction complexity and adapter quality.

**Why this priority**: This addresses the "to what extent" part of the research question. It ensures the solution is not just "works" but is optimized, identifying the threshold where adding more complexity yields diminishing returns.

**Independent Test**: The system can be tested by running the evaluation pipeline multiple times with different feature subsets (e.g., only cyclomatic complexity vs. full AST graph) and comparing the resulting scores.

**Acceptance Scenarios**:

1. **Given** a set of feature subsets ranging from minimal (token counts) to complex (control-flow graphs), **When** the system generates and evaluates adapters for each subset, **Then** a sensitivity curve is produced showing accuracy vs. feature complexity.
2. **Given** a target accuracy threshold of 80% of the baseline accuracy recorded in SC-002, **When** the sensitivity analysis runs, **Then** the system identifies the minimal feature set that meets or exceeds this threshold.
3. **Given** a specific feature (e.g., import graph degree centrality), **When** it is removed from the feature vector, **Then** the system reports the specific drop in exact-match score to quantify its contribution.

---

### Edge Cases

- **AST Parser Failure**: If the AST parser fails on non-standard Python syntax or malformed code, the system MUST skip the file, log a warning with the filename and error, and proceed with the remaining files.
- **Memory Overflow**: If the repository size exceeds the available RAM during feature vector construction, the system MUST abort the current job, log a specific "Memory Limit Exceeded" error, and suggest a batch-processing strategy.
- **Incompatible Checkpoint**: If the base LLM checkpoint provided is incompatible with the hypernetwork architecture, the system MUST abort immediately, log the specific incompatibility reason, and prevent adapter generation.

## Requirements

### Functional Requirements

- **FR-001**: System MUST parse Python source files using the standard `ast` and `tokenize` modules to extract syntactic metrics (cyclomatic complexity, depth of inheritance, import graph centrality, token histograms) without requiring external dependencies or GPU acceleration (See US-1).
- **FR-002**: System MUST replace the baseline neural repository encoder in the Code2LoRA pipeline with a small Multi-Layer Perceptron (MLP) with ReLU activations that maps AST feature vectors to the original embedding dimension size (See US-1).
- **FR-003**: System MUST freeze the base LLM and GRU-based hypernetwork weights from the pre-trained checkpoint and retrain only the new MLP projection layer and hypernetwork output layers using task-specific cross-entropy loss (See US-1, US-2).
- **FR-004**: System MUST evaluate generated adapters on the RepoPeftBench Python subset (assertion-completion tasks) and record exact-match scores and inference latency in milliseconds (See US-2).
- **FR-005**: System MUST perform a sensitivity analysis by varying the AST feature set complexity (e.g., removing control-flow edges) and report the resulting change in exact-match scores to identify the minimum viable feature set (See US-3).
- **FR-006**: System MUST operate within the constraints of the GitHub Actions free tier environment (≤2 cores, 7 GB RAM, 6 hours job timeout) to ensure feasibility for standard CI runners (See US-1, US-2).
- **FR-007**: System MUST handle AST parsing failures by skipping the affected file, logging a warning with the filename and error message, and continuing processing of remaining files (See Edge Cases).
- **FR-008**: System MUST handle memory overflow by aborting the current job, logging a "Memory Limit Exceeded" error, and preventing partial adapter generation (See Edge Cases).
- **FR-009**: System MUST handle incompatible base checkpoints by aborting immediately, logging the specific incompatibility reason, and preventing adapter generation (See Edge Cases).

### Key Entities

- **Repository**: A collection of Python source files with commit history, serving as the input for feature extraction.
- **Feature Vector**: A fixed-length numerical representation of a file or repository derived from AST metrics.
- **Adapter**: The generated LoRA weight matrix specific to a repository, used to fine-tune the base LLM.
- **Test Case**: An assertion-completion task from RepoPeftBench used to evaluate adapter performance.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Adapter generation latency is measured against the baseline neural-encoder generation time to confirm a reduction of at least one order of magnitude (See US-1).
- **SC-002**: Exact-match scores on RepoPeftBench assertion-completion tasks are measured against the original CodeLoRA neural-encoder baseline to quantify the performance gap attributable to the lack of semantic features (See US-2).
- **SC-003**: The minimum feature set required to maintain >80% of baseline accuracy is measured against the full AST feature set to determine the optimal complexity threshold (See US-3).
- **SC-004**: Memory usage and runtime of the full pipeline are measured against the GitHub Actions free-tier limits (standard RAM capacity, 6 hours) to ensure feasibility (See US-1, US-2).
- **SC-005**: Statistical significance of the performance difference between AST-based and neural-based adapters is measured using a Wilcoxon signed-rank test to validate the observed drop is not due to chance, accounting for repository correlations (See US-2).

## Assumptions

- The RepoPeftBench dataset is accessible via the official repository or Zenodo mirror and contains the necessary Python subset with commit histories.
- The base Code2LoRA checkpoint and hypernetwork weights are available and compatible with the modified architecture.
- The `ast` and `tokenize` modules in Python are sufficient to extract all required syntactic metrics without needing external parsers for complex or non-standard syntax.
- The available RAM on the CI runner is sufficient to hold the base LLM (frozen), the hypernetwork, and the feature vectors for the sampled repositories simultaneously.
- The MLP projection layer can effectively map the fixed-length AST feature vectors to the original embedding dimension to approximate semantic manifolds better than a linear projection.
- The performance drop observed (if any) is primarily due to the lack of semantic information in AST features, not implementation errors in the feature extraction or projection layers.
- The RepoPeftBench test set is representative of general code evolution tasks and can be used to validate the sufficiency of syntactic metrics.