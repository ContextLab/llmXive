# Feature Specification: Evaluating the Impact of Code Duplication on LLM Code Understanding

**Feature Branch**: `001-evaluate-code-duplication-llm-understanding`  
**Created**: 2026-05-12  
**Status**: Draft  
**Input**: User description: "Evaluating the Impact of Code Duplication on LLM Code Understanding"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Compute Clone Density and Model Perplexity (Priority: P1)

As a researcher, I want to download a Python code corpus, compute syntactic clone density for each file using AST subtree matching, and measure token-level perplexity using a pre-trained language model, so that I can establish the core correlation data between code duplication and model understanding.

**Why this priority**: This is the foundational measurement capability without which no correlation analysis is possible. It represents the minimum viable research experiment that directly addresses the research question.

**Independent Test**: Can be fully tested by running the pipeline on a small sample (e.g., 10 files) and verifying that clone density scores and perplexity values are computed and stored correctly in CSV format.

**Acceptance Scenarios**:

1. **Given** a 500MB subset of the codeparrot/github-code dataset is available via HuggingFace Datasets, **When** the system processes Python files using streaming mode, **Then** clone density metrics and perplexity scores are computed for each code segment and stored in CSV format.
2. **Given** the Salesforce/codegen-350M-mono model is loaded in 8-bit quantization, **When** the system processes code segments, **Then** memory usage stays under 7GB and log-probability outputs are captured for perplexity calculation.
3. **Given** AST subtree matching is configured with a default threshold, **When** files are parsed using Python's built-in ast module, **Then** clone density values are computed without external dependencies.

---

### User Story 2 - Evaluate Bug Detection Accuracy and Calculate Correlation (Priority: P2)

As a researcher, I want to evaluate bug detection accuracy on a held-out human-eval subset and calculate Spearman's rank correlation between duplication density and both perplexity and accuracy metrics, so that I can quantify the relationship between code redundancy and model performance.

**Why this priority**: This builds upon the core measurement capability to produce the actual research findings (correlation coefficients) that answer the research question. It enables statistical validation of the expected results.

**Independent Test**: Can be fully tested by running the correlation analysis on pre-computed metrics and verifying that Spearman's correlation coefficients are calculated correctly with p-values.

**Acceptance Scenarios**:

1. **Given** clone density and perplexity metrics are stored in CSV format, **When** the system loads a 50-problem subset from human-eval, **Then** pass@1 accuracy is computed for each problem and correlated with duplication density.
2. **Given** correlation calculations are performed, **When** Spearman's rank correlation is computed, **Then** correlation coefficients and p-values are output for both perplexity and bug detection accuracy relationships.
3. **Given** statistical significance is evaluated, **When** p-values are calculated, **Then** results indicate significance at p < 0.05 threshold if correlation exists.

---

### User Story 3 - Perform Sensitivity Analysis and Generate Visualizations (Priority: P3)

As a researcher, I want to perform sensitivity analysis across multiple clone-detection thresholds and generate scatter plots with regression lines, so that I can verify result robustness and document findings for publication.

**Why this priority**: This enhances research validity and produces publication-ready outputs but is not required for initial correlation discovery. It supports reproducibility requirements and documentation needs.

**Independent Test**: Can be fully tested by running the sensitivity analysis with different threshold values and verifying that visualization outputs are generated correctly.

**Acceptance Scenarios**:

1. **Given** the correlation pipeline is complete, **When** sensitivity analysis is run across three clone-detection thresholds (0.7, 0.8, 0.9), **Then** correlation results are compared to verify robustness of findings.
2. **Given** correlation data is available, **When** scatter plots are generated using matplotlib, **Then** regression lines are overlaid and all plots are saved in a documented format.
3. **Given** all hyperparameters are configured, **When** the experiment completes, **Then** random seeds, clone detection thresholds, and all configuration parameters are documented for reproducibility.

---

### Edge Cases

- What happens when the HuggingFace dataset streaming encounters rate limiting or network interruptions during the 500MB download?
- How does the system handle Python files that cannot be parsed by the ast module (e.g., syntax errors, non-standard syntax)?
- What occurs if the codegen-350M-mono model fails to load in 8-bit quantization due to hardware constraints?
- How does the system behave when clone density is zero (no duplicates detected) for certain code segments?
- What happens when perplexity values are NaN or infinite due to numerical issues in log-probability calculations?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download a 500MB subset of the codeparrot/github-code dataset using the datasets library with streaming mode enabled
- **FR-002**: System MUST parse Python files using the built-in ast module to extract function bodies for AST subtree matching
- **FR-003**: System MUST compute syntactic clone density without external dependencies beyond Python standard library
- **FR-004**: System MUST load the Salesforce/codegen-350M-mono model in 8-bit quantization using bitsandbytes
- **FR-005**: System MUST compute token-level perplexity using the model's log-probability outputs for each code segment
- **FR-006**: System MUST evaluate bug detection accuracy on a held-out 50-problem subset from human-eval using pass@1 accuracy
- **FR-007**: System MUST calculate Spearman's rank correlation between duplication density and both perplexity and bug detection accuracy
- **FR-008**: System MUST store all intermediate metrics in CSV format for auditability and reproducibility

### Key Entities

- **CodeSegment**: Represents a discrete unit of Python code (function body) with attributes including file path, line numbers, and AST representation
- **CloneDensityMetric**: Represents the computed syntactic clone density for a code segment, including threshold value and matching count
- **ModelMetric**: Represents LLM performance measurement including perplexity value, log-probability outputs, and bug detection pass/fail status
- **CorrelationResult**: Represents statistical correlation output including Spearman coefficient, p-value, and sample size

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: System completes clone density computation and perplexity measurement on 500MB corpus within 24 hours on standard GHA runner resources
- **SC-002**: Memory usage stays under 7GB throughout model inference using 8-bit quantization
- **SC-003**: At least 1000 code segments are successfully processed with valid clone density and perplexity measurements
- **SC-004**: Correlation analysis produces statistically significant results (p < 0.05) or documents null findings with adequate statistical power
- **SC-005**: All hyperparameters, random seeds, and clone detection thresholds are documented for reproducibility verification

## Assumptions

- The codeparrot/github-code dataset is accessible via HuggingFace Datasets without authentication requirements
- Python's built-in ast module can parse all Python files in the selected corpus (files with syntax errors will be skipped)
- The Salesforce/codegen-350M-mono model is available on HuggingFace Model Hub
- GHA runners have sufficient disk space and RAM for the 500MB corpus download and processing
- The human-eval benchmark subset is accessible for bug detection evaluation
- GitHub Actions runners (ubuntu-latest) provide 2 vCPUs and 7GB RAM by default. The experiment is designed to operate within these constraints as specified in SC-002 (memory usage under 7GB). If larger resources are required, self-hosted runners or GitHub's larger runner tiers (e.g., ubuntu-latest-8-cores with 32GB RAM) may be provisioned.
- The system should document all files that cannot be parsed or processed in a failure log. A failure rate threshold of ≤10% is acceptable for research validity; if failures exceed this threshold, the experiment should be paused and the data source quality reviewed. This follows common practice in data processing pipelines where failures are documented for auditability rather than silently ignored.
- Files with syntax errors should be logged separately in a dedicated failure log (e.g., parse_failures.csv) containing file path, error message, and line number. This follows best practices for research reproducibility and auditability. Silently skipping files without logging would violate FR-008 (all intermediate metrics stored for auditability) and SC-005 (documentation for reproducibility verification).

### Verified Citations

- **DynaCode: A Dynamic Complexity-Aware Code Benchmark for Evaluating Large Language Models in Code Generation** (2025). Wenhao Hu, Jinhao Duan, C. Wei, Li Zhang, Yue-feng Zhang, et al.. Annual Meeting of the Association for Computational Linguistics. [https://doi.org/10.48550/arXiv.2503.10452](https://doi.org/10.48550/arXiv.2503.10452).
- **The Stack: 3 TB of permissively licensed source code** (2022). Denis Kocetkov, Raymond Li, Loubna Ben Allal, Jia Li, Chenghao Mou, et al.. Trans. Mach. Learn. Res.. [https://doi.org/10.48550/arXiv.2211.15533](https://doi.org/10.48550/arXiv.2211.15533).
