# Makefile for Additive Manufacturing Porosity Prediction Pipeline
# This Makefile orchestrates the pipeline execution and includes checks for degenerate datasets.

.PHONY: all download preprocess train analyze clean help

# Configuration
PYTHON := python
CODE_DIR := code
DATA_DIR := data
RESULTS_DIR := results
MODELS_DIR := models

# Default target
all: check_degenerate download preprocess train analyze

# Helper target to ensure directories exist
ensure_dirs:
	@mkdir -p $(DATA_DIR)/raw $(DATA_DIR)/processed $(RESULTS_DIR)/reports $(RESULTS_DIR)/plots $(MODELS_DIR)/artifacts

# Check for degenerate dataset before proceeding
check_degenerate: ensure_dirs
	@echo "Checking for degenerate dataset status..."
	@$(PYTHON) $(CODE_DIR)/orchestration_check.py
	@echo "Degenerate check passed. Proceeding to download."

# Download raw data
download: check_degenerate
	@echo "Downloading dataset..."
	@$(PYTHON) $(CODE_DIR)/download_data.py
	@echo "Download complete."

# Preprocess data (mapping, imputation, feature engineering, normalization)
preprocess: download
	@echo "Preprocessing data..."
	@$(PYTHON) $(CODE_DIR)/preprocess.py
	@echo "Preprocessing complete."

# Train models
train: preprocess
	@echo "Training models..."
	@$(PYTHON) $(CODE_DIR)/train_models.py
	@echo "Training complete."

# Analyze explainability
analyze: train
	@echo "Running explainability analysis..."
	@$(PYTHON) $(CODE_DIR)/analyze_explainability.py
	@echo "Analysis complete."

# Clean generated artifacts
clean:
	@echo "Cleaning artifacts..."
	@rm -rf $(DATA_DIR)/raw/* $(DATA_DIR)/processed/* $(RESULTS_DIR)/* $(MODELS_DIR)/artifacts/*
	@rm -f $(DATA_DIR)/processed/degenerate_flag.json
	@rm -f results/reports/pipeline_start.json results/reports/pipeline_end.json
	@echo "Clean complete."

# Run full pipeline with timer (SC-003 compliance)
run_pipeline:
	@$(PYTHON) $(CODE_DIR)/run_pipeline_with_timer.py

help:
	@echo "Available targets:"
	@echo "  all              - Run the full pipeline (Check -> Download -> Preprocess -> Train -> Analyze)"
	@echo "  check_degenerate - Check for degenerate dataset and halt if found"
	@echo "  download         - Download the raw dataset"
	@echo "  preprocess       - Preprocess the data"
	@echo "  train            - Train the models"
	@echo "  analyze          - Run explainability analysis"
	@echo "  clean            - Remove generated artifacts"
	@echo "  run_pipeline     - Run the full pipeline with timing (SC-003)"
	@echo "  help             - Show this help message"