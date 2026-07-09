# Research Process Documentation

## Methodology
This project investigates the relationship between brain network reconfiguration and recovery from mild traumatic brain injury (mTBI) using longitudinal resting-state fMRI data.

## Data Sources
- **Primary Source**: OpenNeuro datasets (e.g., `ds000006` or similar mTBI datasets).
- **Validation**: Independent clinical metrics (e.g., Return-to-Work status) searched via OpenNeuro metadata API.
- **Fallback**: Synthetic data generation for "Methodology Validation Mode" when real data is unavailable or insufficient.

## Analysis Pipeline

### Phase 1: Data Acquisition
- Download datasets using `code/data_ingestion.py`.
- Generate `data/results/manifest.csv` listing subjects, time points, and file paths.
- Handle missing time points and AAL atlas failures gracefully.

### Phase 2: Preprocessing
- Minimal confound regression using `nilearn`.
- AAL parcellation for region-of-interest extraction.
- Connectivity matrix computation (correlation-based).

### Phase 3: Graph Metrics
- Calculate Global Efficiency, Local Efficiency, and Modularity (Q).
- Apply proportional sparsity thresholding (FR-008).
- Store metrics in `data/results/metrics.json`.

### Phase 4: Statistical Modeling
- Fit Linear Mixed-Effects Model: `CognitiveScore ~ Efficiency + Modularity + Time + (1|Subject)`.
- Check for multicollinearity (VIF > 5) and apply PCA fallback if needed.
- Handle non-convergence by logging warnings and skipping subjects.

### Phase 5: Robustness & Validation
- Perform permutation testing (sufficient iterations) for empirical p-values.
- Conduct sensitivity analysis on correlation thresholds.
- Search for independent validation metrics; if none found, flag `validation_gap: true`.

### Phase 6: Reporting
- Generate `data/results/analysis_report.json` with all metrics, p-values, and compliance flags.
- Verify runtime (≤6h) and memory (≤6GB) constraints.

## Compliance & Constraints
- **FR-001**: Memory limit ≤6GB.
- **FR-002**: Compute Global/Local Efficiency and Modularity.
- **FR-003**: Fit LME model with specified formula.
- **FR-004**: Permutation testing for robustness.
- **FR-005**: Sensitivity analysis on thresholds.
- **FR-006**: Descriptive VIF report if PCA fails.
- **FR-007**: External validation or gap flagging.
- **FR-008**: Proportional sparsity thresholding.
- **FR-009**: Bootstrapping if n < 20.
- **SC-002**: Permutation iterations sufficient for p-value.
- **SC-003**: Sensitivity sweep outputs table.
- **SC-004**: Runtime ≤6h.
- **SC-005**: Memory ≤6GB.

## Execution Order
1. **Setup**: Initialize directory structure and dependencies.
2. **Foundational**: Configure logging, memory, and time monitors.
3. **User Story 1**: Data ingestion and preprocessing.
4. **User Story 2**: Graph metrics and statistical modeling.
5. **User Story 3**: Robustness validation and sensitivity reporting.
6. **Polish**: Documentation and cleanup.

## Validation
- Unit tests for memory monitoring, graph metrics, and collinearity checks.
- Integration tests for data ingestion and sensitivity analysis.
- End-to-end validation via `quickstart.md`.
