.PHONY: all clean validate evaluate enrich sensitivity reproducibility-check help

PYTHON := python
PYTEST := pytest

all: validate
	@echo "Running full pipeline..."
	$(PYTHON) code/src/cli/run_pipeline.py --norm-method TPM --threshold 0.75 --seed 42
	$(MAKE) post-validate

clean:
	@echo "Cleaning generated artifacts..."
	@rm -rf results/* data/cache state/*
	@echo "Clean complete."

validate:
	@echo "Validating project structure and configuration..."
	$(PYTHON) code/ci/check_skeleton_ci.py
	$(PYTHON) code/src/pipeline/validate.py

evaluate:
	@echo "Running evaluation..."
	$(PYTHON) code/src/cli/run_pipeline.py evaluate --seed 42
	$(MAKE) post-validate

enrich:
	@echo "Running enrichment analysis..."
	$(PYTHON) code/src/cli/run_pipeline.py enrich --seed 42
	$(MAKE) post-validate

sensitivity:
	@echo "Running sensitivity analysis..."
	$(PYTHON) code/src/cli/run_pipeline.py sensitivity --seed 42
	$(MAKE) post-validate

reproducibility-check:
	@echo "Running reproducibility check..."
	$(PYTHON) code/src/pipeline/reproducibility_check.py --seed 42

post-validate:
	@echo "Running post-target validation..."
	$(PYTHON) code/src/pipeline/validate.py

help:
	@echo "Available targets:"
	@echo "  all                  - Run full pipeline"
	@echo "  clean                - Remove generated artifacts"
	@echo "  validate             - Validate project structure"
	@echo "  evaluate             - Run evaluation step"
	@echo "  enrich               - Run enrichment step"
	@echo "  sensitivity          - Run sensitivity analysis"
	@echo "  reproducibility-check - Check reproducibility"
	@echo "  help                 - Show this help message"