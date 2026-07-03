.PHONY: all clean setup data features train evaluate viz help

# Default target: Run the full pipeline
all: setup data features train evaluate viz
	@echo "Pipeline completed successfully."

# Setup: Ensure directories and environment are ready
setup:
	@echo "=== Setting up project environment ==="
	@mkdir -p data/raw data/processed data/artifacts figures
	@python -c "import sys; print(f'Python {sys.version}')"

# Data: Ingest raw data (API or fallback)
data:
	@echo "=== Ingesting data ==="
	python code/data/ingest.py

# Features: Compute descriptors and clean data
features:
	@echo "=== Engineering features ==="
	python code/data/features.py
	python code/data/clean.py
	python code/data/split.py

# Train: Train models and select best
train:
	@echo "=== Training models ==="
	python code/models/train.py

# Evaluate: Evaluate model performance
evaluate:
	@echo "=== Evaluating models ==="
	python code/models/evaluate.py

# Viz: Generate visualizations
viz:
	@echo "=== Generating visualizations ==="
	python code/viz/plots.py

# Clean: Remove generated files
clean:
	@echo "=== Cleaning artifacts ==="
	rm -rf data/raw/*.csv data/processed/*.csv data/artifacts/*.json data/artifacts/*.csv figures/*.png
	@echo "Clean complete."

# Help: Display this message
help:
	@echo "Available targets:"
	@echo "  all      - Run the full pipeline"
	@echo "  setup    - Setup directories and environment"
	@echo "  data     - Ingest raw data"
	@echo "  features - Engineer features and split data"
	@echo "  train    - Train models"
	@echo "  evaluate - Evaluate model performance"
	@echo "  viz      - Generate visualizations"
	@echo "  clean    - Remove generated artifacts"
	@echo "  help     - Show this help message"