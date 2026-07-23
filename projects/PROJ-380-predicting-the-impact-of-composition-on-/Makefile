# Makefile for llmXive Automated Science Pipeline
# Project: PROJ-380-predicting-the-impact-of-composition-on-

.PHONY: all clean test lint format setup run-ingest run-train run-eval help

# Default target
all: setup run-ingest run-train run-eval

# Initialize project structure and dependencies
setup:
    @echo "Setting up project structure..."
    python code/setup_data_dirs.py
    @echo "Setup complete."

# Clean generated data and artifacts
clean:
    @echo "Cleaning data and artifacts..."
    rm -rf data/raw/*
    rm -rf data/processed/*
    rm -rf data/artifacts/*
    rm -rf figures/*
    rm -rf state/projects/*.yaml
    @echo "Clean complete."

# Run linting
lint:
    @echo "Running linter..."
    ruff check code/
    @echo "Linting complete."

# Run formatter
format:
    @echo "Running formatter..."
    black code/
    @echo "Formatting complete."

# Run tests
test:
    @echo "Running tests..."
    pytest tests/ -v

# Run data ingestion pipeline
run-ingest:
    @echo "Running data ingestion..."
    python code/data/ingest.py
    python code/data/clean.py
    python code/data/features.py
    python code/data/split.py
    @echo "Ingestion pipeline complete."

# Run model training
run-train:
    @echo "Running model training..."
    python code/models/train.py
    @echo "Training complete."

# Run model evaluation
run-eval:
    @echo "Running model evaluation..."
    python code/models/evaluate.py
    @echo "Evaluation complete."

# Generate report
run-report:
    @echo "Generating model report..."
    python code/models/generate_report.py

help:
    @echo "Available targets:"
    @echo "  all         - Run full pipeline (setup, ingest, train, eval)"
    @echo "  setup       - Initialize project structure"
    @echo "  clean       - Remove generated files"
    @echo "  lint        - Run linter"
    @echo "  format      - Run formatter"
    @echo "  test        - Run tests"
    @echo "  run-ingest  - Run data ingestion pipeline"
    @echo "  run-train   - Run model training"
    @echo "  run-eval    - Run model evaluation"
    @echo "  run-report  - Generate model report"
    @echo "  help        - Show this help message"
