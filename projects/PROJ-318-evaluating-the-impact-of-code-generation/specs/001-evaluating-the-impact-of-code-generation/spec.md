# Feature Specification: Evaluating the Impact of Code Generation Models on Code Documentation Completeness

**Feature Branch**: `001-eval-code-doc-completeness`  
**Created**: 2024-05-22  
**Status**: Draft  
**Input**: User description: "Evaluating the Impact of Code Generation Models on Code Documentation Completeness"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Repository Data Extraction and Ground Truth Preparation (Priority: P1)

The system MUST download a representative set of top Python repositories from the **PyPI leaderboard via the PyPI JSON API** (or a static HuggingFace dataset mirror), **clone each repository via the GitHub API** to obtain the source tree, parse their source code using the `ast` module, extract public method signatures and existing human-written docstrings, **truncate the list to a maximum of 1,000 methods per repository**, and output a structured JSON dataset.

**Why this priority**: This is the foundational data layer. Without a verified, structured dataset of code signatures and human-written documentation, no generation or comparison can occur. This step defines the structural reference against which the LLM is measured. *Selection bias limitation*: top‑N PyPI packages may have unusually high documentation quality; we mitigate this by **stratified sampling across popularity tiers** (see FR-010).

**Independent Test**: Can be fully tested by running the extraction script on a single known repository (e.g., `requests`) and verifying that the output JSON contains the correct method signatures, non‑empty human docstrings (if present), and the row count does not exceed 1,000.

**Acceptance Scenarios**:

1. **Given** a list of valid PyPI package names for the top‑tier packages, **When** the extraction script runs, **Then** it must output a JSON file containing **at most 1,000** unique public method signatures per repository, with the total count logged and verified (row count ≤ 1,000). *(See FR-001, FR-007)*
2. **Given** a repository with mixed indentation or syntax errors in non‑public files, **When** the `ast` parser processes the file, **Then** it must skip the malformed file and continue processing valid files without crashing.
3. **Given** a method with no existing docstring, **When** the parser extracts it, **Then** the `human_docstring` field in the output record must be explicitly set to `null` rather than an empty string.

---

### User Story 2 - LLM Docstring Generation with Resource Constraints (Priority: P2)

The system MUST load the **`Salesforce/codegen-350M-mono`** model using low‑bit quantization (`bitsandbytes`) **and generate docstrings with a fixed temperature = 0.2** for every extracted method, **using only the method signature as prompt** (no surrounding code). The generation must complete within the GitHub Actions time limit (including a safety buffer).

**Why this priority**: This implements the core experimental intervention. It transforms the ground‑truth data into the "treatment" data (LLM‑generated docs). It is prioritized second because it relies on the data layer (P1) being complete.

**Independent Test**: Can be tested by running the generation script on a subset of 50 methods and verifying that the output file contains generated text for each method, the model loaded successfully without CUDA errors, and the memory usage remained within acceptable limits as logged.

**Acceptance Scenarios**:

1. **Given** a JSON input file with up to 1,000 method signatures, **When** the generation script executes, **Then** it must produce an output file where every input method has a corresponding `generated_docstring` field populated with text. *(See FR-002)*
2. **Given** the GitHub Actions runner environment with no GPU, **When** the model loads, **Then** it must successfully initialize in CPU‑only mode (verifying `torch.cuda.is_available()` returns False OR `model.device == cpu`) and stay within reasonable RAM limits as monitored via `/proc/self/status`. *(See FR-006)*
3. **Given** a timeout of several hours for the entire job, **When** the generation runs on multiple repositories (max [deferred] methods each), **Then** the process must complete and write the final results within 6 hours (including a safety buffer). *(See SC-004)*

---

### User Story 3 - Parameter Coverage Analysis and Statistical Comparison (Priority: P3)

The system MUST calculate a **Parameter Coverage Score** for each docstring (both human and generated) by matching parameters against the AST‑defined signature, compute semantic similarity using `sentence-transformers/all-MiniLM-L6-v2` (as an auxiliary style metric), and perform a **Wilcoxon signed‑rank test on per‑repository aggregated scores** to determine if the difference between **Existing Human** and **LLM** scores is statistically significant.

**Why this priority**: This delivers the research outcome. It answers the core question of the feature. It is P3 because it depends on the successful generation of data (P2) and the existence of ground truth (P1).

**Independent Test**: Can be tested by feeding a synthetic dataset of a sizable collection of pairs (balanced between perfect matches and random mismatches) into the analysis module and verifying that the Wilcoxon test returns a p‑value < 0.05 and the coverage scores align with the synthetic labels.

**Acceptance Scenarios**:

1. **Given** a pair of human and LLM docstrings for the same method signature, **When** the coverage algorithm runs, **Then** it must return a score calculated as: `(count of parameters in AST signature that appear as named parameters in the docstring) / (total parameters in AST signature)`, using the deterministic matching rule defined in FR-018, resulting in a value between 0.0 and 1.0. *(See FR-003)*
2. **Given** a dataset of 20 repositories, **When** the statistical test runs, **Then** it must output a p‑value and a test statistic indicating whether the null hypothesis (no difference in coverage) can be rejected at the α=0.05 level (p‑value < 0.05 indicates significance). *(See FR-014, SC-006)*
3. **Given** a scenario where the dataset size is small (e.g., < 30 pairs), **When** the test runs, **Then** it must log a warning that statistical power may be low but still proceed with the calculation. *(See FR-009)*

### Edge Cases

- What happens when a method signature contains complex type hints (e.g., `List[Dict[str, Any]]`) that the LLM fails to parse correctly? The system must treat these as "unmatched" parameters in the coverage score but not crash.
- How does the system handle repositories where the `ast` module fails to parse files due to non‑standard Python versions or experimental syntax? The system must skip the file and log a specific error code rather than failing the entire pipeline.
- What happens if the LLM generates a docstring that is completely empty or just whitespace? The coverage score must be calculated as 0.0, and the record must be **automatically flagged** (added to a `flagged_records.json` report) when the score is below 0.2. *(See FR-008)*
- What happens if the PyPI API rate limits are hit? The system must implement a retry mechanism with exponential backoff (max 5 retries, backoff factor 2) before failing the job. *(See FR-007)*

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST extract public method signatures and human‑written docstrings from the top N PyPI repositories using the Python `ast` module, **truncate the list to a maximum of 1,000 methods per repository**, and verify the output JSON row count is ≤ 1,000 and logged. (See US-1) (See FR-016)
- **FR-002**: System MUST load the `Salesforce/codegen-350M-mono` model using low‑bit quantization (`bitsandbytes`) and generate docstrings **with temperature = 0.2**, prompting **only the method signature** (no surrounding code). (See US-2)
- **FR-003**: System MUST calculate a **Parameter Coverage Score** for each docstring (both human and generated) as `(# parameters appearing in docstring) / (total # parameters)`, using the deterministic matching rule defined in FR-018. This metric captures structural parameter‑name coverage only; completeness beyond name presence is out of scope. (See US-3)
- **FR-004**: System MUST compute semantic similarity between human and LLM docstrings using the compact `sentence-transformers/all-MiniLM-L6-v2` model. This is an **auxiliary metric** to detect style overlap and potential hallucinations, **not** a primary validator of completeness (per Constitution Principle VI). (See US-3)
- **FR-005**: System MUST perform a Wilcoxon signed‑rank test on **per‑repository aggregated Parameter Coverage Scores** (mean human vs. mean LLM per repo) and report the p‑value to determine statistical significance at α = 0.05. (See US-3)
- **FR-006**: System MUST handle memory constraints by processing repositories sequentially or in small batches, monitoring RAM via `/proc/self/status`, and ensuring total peak RAM usage remains within acceptable limits on the GitHub Actions runner. (See US-2)
- **FR-007**: System MUST implement an exponential backoff retry mechanism for PyPI API calls (with a limited number of retries and a multiplicative backoff factor) and log each retry attempt. Failure after all retries aborts the job with a clear error message. (See US-1)
- **FR-008**: System MUST treat empty or whitespace‑only generated docstrings as having a coverage score of 0.0 and **automatically flag** any record whose coverage score falls below 0.2 by adding it to a `flagged_records.json` report. No manual review step is required. (See US-3, Edge Cases)
- **FR-009**: System MUST emit a warning in the analysis log when the total number of paired method records is **< 30**, indicating low statistical power, but still proceed with the Wilcoxon test. (See US-3)
- **FR-010**: System MUST mitigate selection bias by performing **stratified sampling** across at least three popularity tiers (high, medium, low) within the top‑20 PyPI list, ensuring each tier contributes ≥ 5 repositories. Tier boundaries are defined by download‑count percentiles: high = ≥ 80th percentile, medium = 40th–80th percentile, low = < 40th percentile. (See US-1)
- **FR-011**: System MUST compute a **Description Coverage Score** for each docstring, defined as the average number of non‑stop‑word tokens per documented parameter (excluding the parameter name itself); tokenisation uses `nltk.word_tokenize`, English stop‑word list from NLTK, lower‑casing, and removal of punctuation. A score ≥ 5 tokens is considered satisfactory. (See US-3)
- **FR-012**: System MUST construct the generation prompt **solely from the method signature** (name, parameters, return annotation) to avoid leaking documentation content into the model input. (See US-2)
- **FR-013**: System MUST acknowledge the circularity limitation that high parameter‑name coverage may stem from the model copying the visible signature; this limitation is documented in the analysis report. (See US-3)
- **FR-014**: System MUST aggregate Parameter Coverage Scores per repository (mean human, mean LLM) before statistical testing to respect independence assumptions across methods. (See US-3)
- **FR-015**: System MUST assign a coverage score of 0.0 for any method where `human_docstring` is `null` and include this in both per‑method and per‑repository aggregates. (See US-3)
- **FR-016**: System MUST clone each selected repository via the **GitHub REST API** (or GitHub GraphQL API) after obtaining its PyPI metadata, ensuring the exact source code version is used for AST parsing. (See US-1)
- **FR-017**: System MUST conduct a human‑evaluation sampling study on a random subset of docstring pairs, asking annotators to rate overall documentation completeness on a Likert scale; the average rating will be reported as an independent validation of completeness. (See US-3)
- **FR-018**: System MUST consider a parameter “appearing in the docstring” if, after lower‑casing and stripping surrounding punctuation, the exact parameter name token is present as a separate word in the docstring text. Matching is case‑insensitive and token‑exact; substrings do not count. (See FR-003)

### Key Entities

- **MethodSignature**: Represents a public method in a Python file, containing attributes for the method name, parameter list (names and types), and the source file path.
- **DocstringPair**: Represents a single data point containing the `MethodSignature`, the `human_docstring` (existing human text, potentially `null`), and the `generated_docstring` (LLM output).
- **ParameterCoverageScore**: A numerical value (0.0 to 1.0) representing the ratio of AST‑defined parameters that appear as named parameters in the docstring. (Structural coverage only)
- **DescriptionCoverageScore**: A numerical value representing average token richness per documented parameter (≥ 5 tokens considered satisfactory).

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The primary evidence of documentation completeness is the **Description Coverage Score** (≥ 5 tokens per parameter for ≥ 80 % of methods) as defined in FR‑011. (See FR-011, SC-005)
- **SC-002**: The **Parameter Coverage Score** is measured per method against the ground‑truth parameter list extracted via the `ast` module. (See FR-003)
- **SC-003**: The semantic similarity of generated docstrings is measured against the human‑written baseline using cosine similarity scores from the `sentence-transformers/all-MiniLM-L6-v2` model (auxiliary style metric only). (See FR-004)
- **SC-004**: The computational feasibility of the pipeline is measured against the GitHub Actions free‑tier constraints (≤ 6 hours runtime including a short buffer, ≤ 7 GB RAM, CPU‑only). (See FR-006)
- **SC-005**: Description Coverage Score ≥ 5 tokens per parameter for **≥ 80 % of methods** (computed over the entire dataset; the required count is `floor(0.8 × total_methods)`). (See FR-011)
- **SC-006**: Wilcoxon test performed on per‑repository aggregated scores (n = 20) to respect independence; results reported with test statistic and p‑value. (See FR-014)
- **SC-007**: Human‑evaluation average Likert rating ≥ 4.0 on the sampled subset indicates that LLM‑generated documentation is comparable to human documentation in overall completeness. (See FR-017)

## Assumptions

- A selection of prominent Python repositories on the PyPI leaderboard are accessible via the public PyPI JSON API without requiring authentication tokens that expire during the job window.
- The `Salesforce/codegen-350M-mono` model is available on Hugging Face and compatible with the `bitsandbytes` library for low‑bit quantization in a CPU‑only environment (assuming the library falls back to CPU quantization or the model weights are small enough to fit in RAM).
- The `ast` module in modern Python versions is sufficient to parse all target repositories, assuming they adhere to standard Python syntax and do not rely on experimental or non‑standard language extensions.
- The `sentence-transformers/all-MiniLM-L6-v2` model can be loaded and executed on the free‑tier runner without requiring GPU acceleration, as it is a small model designed for CPU inference.
- The existing human docstrings in the target repositories may be incomplete or outdated; the primary metric measures **narrative richness** (Description Coverage Score) while Parameter Coverage Score is auxiliary.
- The `bitsandbytes` library supports 4‑bit quantization on CPU; if not, the system assumes a fallback to standard low‑bit or full‑precision quantization that fits within the available RAM limit, potentially affecting generation speed but not correctness.
- Stratified sampling across popularity tiers (high, medium, low) reduces selection bias and ensures broader representativeness.
