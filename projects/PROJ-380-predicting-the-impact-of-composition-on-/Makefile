# Makefile for PROJ-380: Predicting the Impact of Composition on Shear Modulus
# Orchestration entry point for the full pipeline (FR-010)

.PHONY: all setup data features split validate train evaluate importance clean help

# Default target: Run the full pipeline
all: setup data features split validate train evaluate importance
	@echo "Pipeline execution completed successfully."
	@echo "Check 'artifacts/' for reports and 'data/' for processed datasets."

# Setup: Ensure directories and configuration exist
setup:
	@echo ">>> Step 1/9: Setting up directories and configuration..."
	@python code/setup_data_dirs.py

# Data Ingestion: Fetch raw data (Materials Project or Synthetic fallback)
data:
	@echo ">>> Step 2/9: Ingesting raw data..."
	@python code/data/ingest.py

# Cleaning: Filter for BMG phase and standardize units
clean:
	@echo ">>> Step 3/9: Cleaning and filtering data..."
	@python code/data/clean.py

# Feature Engineering: Calculate descriptors and handle collinearity
features:
	@echo ">>> Step 4/9: Calculating features and handling collinearity..."
	@python code/data/features.py

# Splitting: Stratified split by alloy family
split:
	@echo ">>> Step 5/9: Splitting dataset..."
	@python code/data/split.py

# Validation: Ensure no missing target values
validate:
	@echo ">>> Step 6/9: Validating target variable..."
	@python code/data/validate_target.py

# Training: Train models with grid search
train:
	@echo ">>> Step 7/9: Training models..."
	@python code/models/train.py

# Evaluation: Statistical comparison and hybrid validation
evaluate:
	@echo ">>> Step 8/9: Evaluating models..."
	@python code/models/evaluate.py

# Importance: Feature importance and visualization
importance:
	@echo ">>> Step 9/9: Analyzing feature importance..."
	@python code/models/importance.py

# Clean: Remove generated data and artifacts
clean:
	@echo ">>> Cleaning generated artifacts..."
	@rm -rf data/processed/* data/artifacts/* artifacts/*
	@echo "Clean complete."

# Help: Display available targets
help:
	@echo "Available targets:"
	@echo "  all        - Run the full pipeline (default)"
	@echo "  setup      - Initialize directories"
	@echo "  data       - Ingest raw data"
	@echo "  clean      - Clean and filter data"
	@echo "  features   - Engineer features"
	@echo "  split      - Split dataset"
	@echo "  validate   - Validate target"
	@echo "  train      - Train models"
	@echo "  evaluate   - Evaluate models"
	@echo "  importance - Analyze feature importance"
	@echo "  clean      - Remove generated files"