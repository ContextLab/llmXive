# Feature Specification: Evaluating the Impact of Code Generation Models on Code Documentation Completeness

**Feature Branch**: `001-eval-code-doc-completeness`  
**Created**: 2024-05-22  
**Status**: Draft  
**Input**: User description: "Evaluating the Impact of Code Generation Models on Code Documentation Completeness"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Repository Data Extraction and Ground Truth Preparation (Priority: P1)

The system MUST download a representative set of top Python repositories from the PyPI leaderboard. (via the PyPI JSON API or a static HuggingFace dataset mirror), parse their source code using the `ast` module, extract public method signatures and existing human-written docstrings, **truncate the list to a maximum of 1,000 methods per repository**, and output a structured JSON dataset.

**Why this priority**: This is the foundational data layer. Without a verified, structured dataset of code signatures and human-written documentation, no generation or comparison can occur. This step defines the structural reference against which the LLM is measured.

**Independent Test**: Can be fully tested by running the extraction script on a single known repository (e.g., `requests`) and verifying that the output JSON contains the correct method signatures, non-empty human docstrings (if present), and [deferred] rows (or fewer if the repo has less) with a logged count.

**Acceptance Scenarios**:

1. **Given** a list of valid GitHub repository URLs for the top 20 PyPI packages, **When** the extraction script runs, **Then** it must output a JSON file containing **at most 1,000** unique public method signatures per repository, with the total count logged and verified (row count ≤ 1,000).
2. **Given** a repository with mixed indentation or syntax errors in non-public files, **When** the `ast` parser processes the file, **Then** it must skip the malformed file and continue processing valid files without crashing.
3. **Given** a method with no existing docstring, **When** the parser extracts it, **Then** the `human_docstring` field in the output record must be explicitly set to `null` rather than an empty string.

---

### User Story 2 - LLM Docstring Generation with Resource Constraints (Priority: P2)

The system MUST load the `Salesforce/codegen-350M-mono` model in 4-bit quantization and generate docstrings for the **truncated list of up to 1,000 methods per repository** using a fixed temperature of 0.2, ensuring the process completes within the GitHub Actions time limit (including a safety buffer).

**Why this priority**: This implements the core experimental intervention. It transforms the ground-truth data into the "treatment" data (LLM-generated docs). It is prioritized second because it relies on the data layer (P1) being complete.

**Independent Test**: Can be tested by running the generation script on a subset of 50 methods and verifying that the output file contains generated text for each method, the model loaded successfully without CUDA errors, and the memory usage remained within acceptable limits as logged.

**Acceptance Scenarios**:

1. **Given** a JSON input file with up to 1,000 method signatures, **When** the generation script executes, **Then** it must produce an output file where every input method has a corresponding `generated_docstring` field populated with text.
2. **Given** the GitHub Actions runner environment with no GPU, **When** the model loads, **Then** it must successfully initialize in CPU-only mode (verifying `torch.cuda.is_available()` returns False OR `model.device == cpu`) and stay under 7 GB RAM as monitored via `/proc/self/status`.
3. **Given** a timeout of 6 hours for the entire job, **When** the generation runs on 20 repositories (max [deferred] methods each), **Then** the process must complete and write the final results within 6 hours (including a 15-minute safety buffer).

---

### User Story 3 - Parameter Coverage Analysis and Statistical Comparison (Priority: P3)

The system MUST calculate a **Parameter Coverage Score** for each generated docstring by matching parameters against the AST-defined signature, compute semantic similarity using `sentence-transformers/all-MiniLM-L6-v2` (as an auxiliary style metric), and perform a Wilcoxon signed-rank test to determine if the difference between **Existing Human** and **LLM** scores is statistically significant.

**Why this priority**: This delivers the research outcome. It answers the core question of the feature. It is P3 because it depends on the successful generation of data (P2) and the existence of ground truth (P1).

**Independent Test**: Can be tested by feeding a synthetic dataset of 100 pairs (50 perfect matches, 50 random mismatches) into the analysis module and verifying that the Wilcoxon test returns a p-value < 0.05 and the coverage scores align with the synthetic labels.

**Acceptance Scenarios**:

1. **Given** a pair of human and LLM docstrings for the same method signature, **When** the coverage algorithm runs, **Then** it must return a score calculated as: `(count of parameters in AST signature that appear as named parameters in the docstring) / (total parameters in AST signature)`, resulting in a value between 0.0 and 1.0.
2. **Given** a dataset of 20 repositories, **When** the statistical test runs, **Then** it must output a p-value and a test statistic indicating whether the null hypothesis (no difference in coverage) can be rejected at the α=0.05 level (p-value < 0.05 indicates significance).
3. **Given** a scenario where the dataset size is small (e.g., < 30 pairs), **When** the test runs, **Then** it must log a warning that statistical power may be low but still proceed with the calculation.

### Edge Cases

- What happens when a method signature contains complex type hints (e.g., `List[Dict[str, Any]]`) that the LLM fails to parse correctly? The system must treat these as "unmatched" parameters in the coverage score but not crash.
- How does the system handle repositories where the `ast` module fails to parse files due to non-standard Python versions or experimental syntax? The system must skip the file and log a specific error code rather than failing the entire pipeline.
- What happens if the LLM generates a docstring that is completely empty or just whitespace? The coverage score must be calculated as 0.0, and the record must be flagged for manual review if the threshold is not met.
- What happens if the PyPI API rate limits are hit? The system must implement a retry mechanism with exponential backoff (a limited number of retries with increasing intervals) before failing the job.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST extract public method signatures and human-written docstrings from the top 20 PyPI repositories using the Python `ast` module, **truncate the list to a maximum of 1,000 methods per repository**, and verify the output JSON row count is ≤ 1,000 and logged. (See US-1)
- **FR-002**: System MUST load the `Salesforce/codegen-mono` model using 4-bit quantization (`bitsandbytes`) and generate docstrings with a fixed temperature of 0.2 for every extracted method. (See US-2)
- **FR-003**: System MUST calculate a **Parameter Coverage Score** for each generated docstring by computing the ratio: `(count of parameters in AST signature that appear as named parameters in the docstring) / (total parameters in AST signature)`. This is the **primary metric** for the hypothesis. (See US-3)
- **FR-004**: System MUST compute semantic similarity between human and LLM docstrings using the `sentence-transformers/all-MiniLM-L6-v2` model. This is an **auxiliary metric** to detect style overlap and potential hallucinations, **not** a primary validator of completeness (per Constitution Principle VI). (See US-3)
- **FR-005**: System MUST perform a Wilcoxon signed-rank test on the paired Parameter Coverage Scores (Existing Human vs. LLM) across all repositories and report the p-value to determine statistical significance at the α=0.05 level (p-value < 0.05 indicates significance). (See US-3)
- **FR-006**: System MUST handle memory constraints by processing repositories sequentially or in small batches, monitoring RAM via `/proc/self/status`, and ensuring total peak RAM usage remains within acceptable limits on the GitHub Actions runner. (See US-2)

### Key Entities

- **MethodSignature**: Represents a public method in a Python file, containing attributes for the method name, parameter list (names and types), and the source file path.
- **DocstringPair**: Represents a single data point containing the `MethodSignature`, the `human_docstring` (existing human text, potentially incomplete), and the `generated_docstring` (LLM output).
- **ParameterCoverageScore**: A numerical value (0.0 to 1.0) representing the ratio of AST-defined parameters that appear as named parameters in the docstring. (Note: This measures structural coverage, not semantic completeness).

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The difference in Parameter Coverage Scores between Existing Human and LLM-generated docstrings is measured against the null hypothesis of no difference using the Wilcoxon signed-rank test (p-value < 0.05 indicates significance). (See FR-005)
- **SC-002**: The Parameter Coverage Rate is measured against the ground truth parameter list extracted via the `ast` module for each method (structural reference only). (See FR-003)
- **SC-003**: The semantic similarity of generated docstrings is measured against the human-written baseline using cosine similarity scores from the `sentence-transformers/all-MiniLM-L6-v2` model (auxiliary style metric only). (See FR-004)
- **SC-004**: The computational feasibility of the pipeline is measured against the GitHub Actions free-tier constraints (≤6 hours runtime including 15-minute buffer, ≤7 GB RAM, CPU-only). (See FR-006)

## Assumptions

- The top 20 Python repositories on the PyPI leaderboard are accessible via the public GitHub API or PyPI JSON API without requiring authentication tokens that expire during the 6-hour job window.
- The `Salesforce/codegen-350M-mono` model is available on Hugging Face and compatible with the `bitsandbytes` library for 4-bit quantization in a CPU-only environment (assuming the library falls back to CPU quantization or the model weights are small enough to fit in RAM).
- The `ast` module in Python 3.8+ is sufficient to parse all target repositories, assuming they adhere to standard Python syntax and do not rely on experimental or non-standard language extensions.
- The `sentence-transformers/all-MiniLM-L6-v2` model can be loaded and executed on the free-tier runner without requiring GPU acceleration, as it is a small model designed for CPU inference.
- The existing human docstrings in the target repositories may be incomplete or outdated; the metric measures **relative structural coverage** (Human vs. LLM) against the AST, not absolute "completeness" against an ideal standard.
- The `bitsandbytes` library supports 4-bit quantization on CPU; if not, the system assumes a fallback to standard 8-bit or full precision quantization that fits within the 7 GB RAM limit, potentially affecting generation speed but not correctness.