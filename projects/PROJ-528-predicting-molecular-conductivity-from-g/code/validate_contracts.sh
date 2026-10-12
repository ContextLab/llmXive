#!/usr/bin/env bash
# T001 verification: every contract schema self-validates (exit 0),
# then the scaffold splitter is exercised end-to-end on the real
# raw input file, writing train.csv / test.csv to data/processed/.
set -e
cd "$(dirname "$0")/.."

python code/validators.py --validate \
  specs/001-predicting-molecular-conductivity-from-g/contracts/input.schema.yaml \
  specs/001-predicting-molecular-conductivity-from-g/contracts/descriptor_schema.schema.yaml \
  specs/001-predicting-molecular-conductivity-from-g/contracts/dataset_schema.yaml \
  specs/001-predicting-molecular-conductivity-from-g/contracts/model_output_schema.yaml \
  specs/001-predicting-molecular-conductivity-from-g/contracts/model_results_schema.schema.yaml \
  specs/001-predicting-molecular-conductivity-from-g/contracts/feature_schema.yaml \
  specs/001-predicting-molecular-conductivity-from-g/contracts/analysis_summary_schema.yaml \
  specs/001-predicting-molecular-conductivity-from-g/contracts/sensitivity_schema.schema.yaml

python code/split.py --input data/raw/input.csv --test-fraction 0.5 --seed 42

echo "T001 verification passed."