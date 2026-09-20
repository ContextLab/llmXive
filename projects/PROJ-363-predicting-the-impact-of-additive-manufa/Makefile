.PHONY: all download preprocess check_degenerate train analyze clean

# Main entry point
all: check_degenerate preprocess train analyze

# Phase 1: Download Data
download:
	@echo "=== Phase 1: Downloading Data ==="
	python code/download_data.py

# Phase 2: Preprocessing
preprocess:
	@echo "=== Phase 2: Preprocessing Data ==="
	python code/preprocess.py

# Phase 3: Orchestration Check (Halt if Degenerate)
# This must run AFTER preprocess (which writes the flag if needed)
# and BEFORE train/analyze.
check_degenerate:
	@echo "=== Phase 3: Checking for Degenerate Dataset ==="
	python code/orchestration_check.py

# Phase 4: Train Models
train:
	@echo "=== Phase 4: Training Models ==="
	python code/train_models.py

# Phase 5: Analyze Explainability
analyze:
	@echo "=== Phase 5: Analyzing Explainability ==="
	python code/analyze_explainability.py

# Clean generated artifacts
clean:
	@echo "Cleaning up generated files..."
	rm -rf data/processed/*.csv data/processed/*.json
	rm -rf models/artifacts/*.pkl
	rm -rf results/reports/*.json
	rm -rf results/plots/*.png
	rm -f state.yaml
	@echo "Cleanup complete."