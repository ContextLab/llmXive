# Makefile for PROJ-185-predicting-protein-protein-interactions-
# Each primary pipeline target runs its (placeholder) command and then
# invokes the validation script to verify result files against contracts.
# The validation script is src/pipeline/validate.py and is executed via
# `python -m src.pipeline.validate`.

.PHONY: all download batch_correct normalize filter correlation_extract evaluate enrich clean sensitivity reproducibility-check validate

# The `all` target runs the full pipeline in order.
all: download batch_correct normalize filter correlation_extract evaluate enrich clean sensitivity reproducibility-check validate
    @echo "All pipeline steps completed."

download:
    @echo "Running download step (placeholder)."
    @python -m src.pipeline.validate

batch_correct:
    @echo "Running batch correction step (placeholder)."
    @python -m src.pipeline.validate

normalize:
    @echo "Running normalization step (placeholder)."
    @python -m src.pipeline.validate

filter:
    @echo "Running gene filtering step (placeholder)."
    @python -m src.pipeline.validate

correlation_extract:
    @echo "Running correlation extraction step (placeholder)."
    @python -m src.pipeline.validate

evaluate:
    @echo "Running evaluation step (placeholder)."
    @python -m src.pipeline.validate

enrich:
    @echo "Running enrichment step (placeholder)."
    @python -m src.pipeline.validate

clean:
    @echo "Running clean step (placeholder)."
    @python -m src.pipeline.validate

sensitivity:
    @echo "Running sensitivity analysis step (placeholder)."
    @python -m src.pipeline.validate

reproducibility-check:
    @echo "Running reproducibility check step (placeholder)."
    @python -m src.pipeline.validate

# The explicit validate target (can be called directly)
validate:
    @python -m src.pipeline.validate
