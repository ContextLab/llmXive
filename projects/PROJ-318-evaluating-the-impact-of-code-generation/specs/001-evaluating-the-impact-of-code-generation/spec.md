# Feature Specification: Evaluating the Impact of Code Generation Models on Code Documentation Completeness

**Feature Branch**: `001-eval-code-doc-completeness`  
**Created**: 2024-05-22  
**Status**: Draft  
**Input**: User description: "Evaluating the Impact of Code Generation Models on Code Documentation Completeness"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Repository Data Extraction and Ground Truth Preparation (Priority: P1)

The system MUST download the top 20 Python repositories from the PyPI leaderboard, parse their source code using the `ast` module, and extract public method signatures along with their existing human-written docstrings to create a ground-truth dataset.

**Why this priority**: This is the foundational data layer. Without a verified, structured dataset of code signatures and human-written documentation, no generation or comparison can occur. This step defines the "truth" against which the LLM is measured.

**Independent Test**: Can be fully tested by running the extraction script on a single known repository (e.g., `requests`) and verifying that the output JSON contains the correct method signatures and non-empty human docstrings for public methods.

**Acceptance Scenarios**:

1. **Given** a list of valid GitHub repository URLs for the top 20 PyPI packages, **When** the extraction script runs, **Then** it must output a JSON file containing at least 500 unique public method signatures with their corresponding human-written docstrings.
2. **Given** a repository with mixed indentation or syntax errors in non-public files, **When** the `ast` parser processes the file, **Then** it must skip the malformed file and continue processing valid files without crashing.
3. **Given** a method with no existing docstring, **When** the parser extracts it, **Then** the `human_docstring` field in the output record must be explicitly set to `null` rather than an empty string.

---

### User Story 2 - LLM Docstring Generation with Resource Constraints (Priority: P2)

The system MUST load the `Salesforce/codegen-350M-mono` model in 4-bit quantization and generate docstrings for up to 1,000 extracted methods per repository using a fixed temperature of 0.2, ensuring the process completes within the 6-hour GitHub Actions time limit.

**Why this priority**: This implements the core experimental intervention. It transforms the ground-truth data into the "treatment" data (LLM-generated docs). It is prioritized second because it relies on the data layer (P1) being complete.

**Independent Test**: Can be tested by running the generation script on a subset of 50 methods and verifying that the output file contains generated text for each method, the model loaded successfully without CUDA errors, and the memory usage stayed below 7 GB.

**Acceptance Scenarios**:

1. **Given** a JSON input file with [deferred] method signatures, **When** the generation script executes, **Then** it must produce an output file where every input method has a corresponding `generated_docstring` field populated with text.
2. **Given** the GitHub Actions runner environment with no GPU, **When** the model loads, **Then** it must successfully initialize in CPU-only mode using 4-bit quantization without raising a "CUDA not available" error.
3. **Given** a timeout of 6 hours for the entire job, **When** the generation runs on 20 repositories (max [deferred] methods each), **Then** the process must complete and write the final results within 5 hours and 30 minutes to allow for analysis overhead.

---

### User Story 3 - Completeness Analysis and Statistical Comparison (Priority: P3)

The system MUST calculate a completeness score for each generated docstring by matching parameters against the AST-defined signature, compute semantic similarity using `sentence-transformers/all-MiniLM-L6-v2`, and perform a Wilcoxon signed-rank test to determine if the difference between human and LLM scores is statistically significant.

**Why this priority**: This delivers the research outcome. It answers the core question of the feature. It is P3 because it depends on the successful generation of data (P2) and the existence of ground truth (P1).

**Independent Test**: Can be tested by feeding a synthetic dataset of 100 pairs (50 perfect matches, 50 random mismatches) into the analysis module and verifying that the Wilcoxon test returns a p-value < 0.05 and the completeness scores align with the synthetic labels.

**Acceptance Scenarios**:

1. **Given** a pair of human and LLM docstrings for the same method signature, **When** the completeness algorithm runs, **Then** it must return a score between 0.0 and 1.0 representing the ratio of correctly described parameters.
2. **Given** a dataset of 20 repositories, **When** the statistical test runs, **Then** it must output a p-value and a test statistic indicating whether the null hypothesis (no difference in completeness) can be rejected at the α=0.05 level.
3. **Given** a scenario where the dataset size is small (e.g., < 30 pairs), **When** the test runs, **Then** it must log a warning that statistical power may be low but still proceed with the calculation.

### Edge Cases

- What happens when a method signature contains complex type hints (e.g., `List[Dict[str, Any]]`) that the LLM fails to parse correctly? The system must treat these as "unmatched" parameters in the completeness score but not crash.
- How does the system handle repositories where the `ast` module fails to parse files due to non-standard Python versions or experimental syntax? The system must skip the file and log a specific error code rather than failing the entire pipeline.
- What happens if the LLM generates a docstring that is completely empty or just whitespace? The completeness score must be calculated as 0.0, and the record must be flagged for manual review if the threshold is not met.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST extract public method signatures and human-written docstrings from the top 20 PyPI repositories using the Python `ast` module, ensuring that at least 1,000 methods are processed per repository. (See US-1)
- **FR-002**: System MUST load the `Salesforce/codegen-350M-mono` model using 4-bit quantization (`bitsandbytes`) and generate docstrings with a fixed temperature of 0.2 for every extracted method. (See US-2)
- **FR-003**: System MUST calculate a completeness score for each generated docstring by comparing the set of parameters described in the docstring against the set of parameters defined in the AST signature. (See US-3)
- **FR-004**: System MUST compute semantic similarity between human and LLM docstrings using the `sentence-transformers/all-MiniLM-L6-v2` model to validate content overlap beyond exact parameter matching. (See US-3)
- **FR-005**: System MUST perform a Wilcoxon signed-rank test on the paired completeness scores (Human vs. LLM) across all repositories and report the p-value to determine statistical significance at the α=0.05 level. (See US-3)
- **FR-006**: System MUST handle memory constraints by processing repositories sequentially or in small batches to ensure total RAM usage remains under 7 GB on the GitHub Actions runner. (See US-2)

### Key Entities

- **MethodSignature**: Represents a public method in a Python file, containing attributes for the method name, parameter list (names and types), and the source file path.
- **DocstringPair**: Represents a single data point containing the `MethodSignature`, the `human_docstring` (ground truth), and the `generated_docstring` (LLM output).
- **CompletenessScore**: A numerical value (0.0 to 1.0) representing the ratio of correctly described parameters in a `DocstringPair`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The difference in completeness scores between human-written and LLM-generated docstrings is measured against the null hypothesis of no difference using the Wilcoxon signed-rank test. (See FR-005)
- **SC-002**: The parameter description coverage rate is measured against the ground truth parameter list extracted via the `ast` module for each method. (See FR-003)
- **SC-003**: The semantic similarity of generated docstrings is measured against the human-written baseline using cosine similarity scores from the `sentence-transformers/all-MiniLM-L6-v2` model. (See FR-004)
- **SC-004**: The computational feasibility of the pipeline is measured against the GitHub Actions free-tier constraints (≤6 hours runtime, ≤7 GB RAM, CPU-only). (See FR-006)

## Assumptions

- The top 20 Python repositories on the PyPI leaderboard are accessible via the public GitHub API without requiring authentication tokens that expire during the 6-hour job window.
- The `Salesforce/codegen-350M-mono` model is available on Hugging Face and compatible with the `bitsandbytes` library for 4-bit quantization in a CPU-only environment (assuming the library falls back to CPU quantization or the model weights are small enough to fit in RAM).
- The `ast` module in Python 3.8+ is sufficient to parse all target repositories, assuming they adhere to standard Python syntax and do not rely on experimental or non-standard language extensions.
- The `sentence-transformers/all-MiniLM-L6-v2` model can be loaded and executed on the free-tier runner without requiring GPU acceleration, as it is a small model designed for CPU inference.
- The [deferred] method limit per repository is sufficient to provide a statistically significant sample size for the Wilcoxon signed-rank test, assuming the distribution of completeness scores is not heavily skewed.
- The `bitsandbytes` library supports 4-bit quantization on CPU; if not, the system assumes a fallback to standard 8-bit or full precision quantization that fits within the 7 GB RAM limit, potentially affecting generation speed but not correctness.
