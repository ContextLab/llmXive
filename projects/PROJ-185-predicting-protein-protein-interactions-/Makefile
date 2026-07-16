.PHONY: all evaluate enrich clean validate sensitivity reproducibility-check help

all: ## Run the full pipeline
	@echo "Running full pipeline..."
	python -m src.cli.run_pipeline

evaluate: ## Evaluate predictions against STRING
	@echo "Running evaluation..."
	python -m src.pipeline.evaluate

enrich: ## Perform GO enrichment analysis
	@echo "Running GO enrichment..."
	python -m src.pipeline.enrichment

clean: ## Remove generated results and intermediate data
	@echo "Cleaning results and data directories..."
	rm -rf results/* data/*

validate: ## Validate output files against contracts
	@echo "Running validation..."
	python -m src.pipeline.validate

sensitivity: ## Run threshold sensitivity analysis
	@echo "Running sensitivity analysis..."
	python -m src.pipeline.sensitivity

reproducibility-check: ## Verify reproducibility of pipeline runs
	@echo "Running reproducibility check..."
	python -m src.pipeline.reproducibility_check

help:
	@echo "Available make targets:"
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?##"}; {printf "  %-20s %s\n", $$1, $$2}'
