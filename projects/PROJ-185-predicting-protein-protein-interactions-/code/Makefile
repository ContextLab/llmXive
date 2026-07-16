.PHONY: all evaluate enrich clean validate sensitivity reproducibility-check help

# Default target
all: validate
        @echo "Running full pipeline (Validation + US1: Co-expression PPI Prediction)..."
        python code/src/pipeline/download.py
        python code/src/pipeline/batch_correct.py
        python code/src/pipeline/confound_regression.py
        python code/src/pipeline/normalize.py
        python code/src/pipeline/filter.py
        python code/src/pipeline/correlation_raw.py
        python code/src/pipeline/fdr_correction.py
        python code/src/pipeline/correlation_extract.py
        python code/src/pipeline/mapping.py
        python code/src/pipeline/export_edges.py
        @echo "Pipeline complete. Run 'make validate' to check outputs."

# User Story 2: Evaluation against STRING
evaluate:
        @echo "Running Evaluation (US2)..."
        python code/src/pipeline/download_string.py
        python code/src/pipeline/negative_sampling.py
        python code/src/pipeline/aggregate_metrics.py
        python code/src/pipeline/evaluate.py
        python code/src/pipeline/baseline.py
        @echo "Evaluation complete."

# User Story 3: Functional Enrichment
enrich:
        @echo "Running Enrichment (US3)..."
        python code/src/pipeline/enrichment.py
        @echo "Enrichment complete."

# Sensitivity Analysis
sensitivity:
        @echo "Running Sensitivity Analysis..."
        python code/src/pipeline/sensitivity_analysis.py
        @echo "Sensitivity analysis complete."

# Reproducibility Check
reproducibility-check:
        @echo "Running Reproducibility Check..."
        @echo "Re-running pipeline with same seed and comparing outputs..."
        python code/src/pipeline/reproducibility_check.py
        @echo "Reproducibility check complete."

# Validation
validate:
        @echo "Running Validation..."
        python code/src/pipeline/validate.py
        @echo "Validation complete."

# Clean generated artifacts
clean:
        @echo "Cleaning up generated artifacts..."
        rm -rf results/*
        rm -rf data/interim/*
        rm -f pipeline.log
        @echo "Clean complete."

help:
        @echo "Available targets:"
        @echo "  all                   - Run the full prediction pipeline (US1)"
        @echo "  evaluate              - Run evaluation against STRING (US2)"
        @echo "  enrich                - Run functional enrichment (US3)"
        @echo "  sensitivity           - Run threshold sensitivity analysis"
        @echo "  reproducibility-check - Verify reproducibility of results"
        @echo "  validate              - Validate output schemas and files"
        @echo "  clean                 - Remove generated data and logs"
        @echo "  help                  - Show this help message"
