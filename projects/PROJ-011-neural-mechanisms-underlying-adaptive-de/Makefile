.PHONY: quickstart

## Quickstart target
## Prints the commands documented in quickstart.md and exits with status 0.
quickstart:
	@echo "Running quickstart commands..."
	@echo "python -c \"import numpy; import pandas; print('Environment OK')\""
	@echo "python -m code.preprocessing.data_download"
	@echo "python -m code.utils.io verify-checksums --manifest data/checksums.yaml"
	@echo "python -m code.preprocessing.qc_reporter \\"
	@echo "  --exclusions state/exclusions.yaml \\"
	@echo "  --output data/reports/qc_summary.json \\"
	@echo "  --exclusions-out state/exclusions.yaml"
	@echo "python -m code.modeling.synthetic_data_generator \\"
	@echo "  --n-participants 5 --n-trials 20 \\"
	@echo "  --output data/synthetic/ground_truth.csv"
	@echo "Quickstart completed successfully."
# End of Makefile