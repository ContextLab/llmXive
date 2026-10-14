# The Impact of Musical Training on Functional Connectivity in Adolescent Brains

This research project investigates how musical training during adolescence affects resting-state functional connectivity patterns, specifically within the auditory, motor, and executive control networks. The pipeline implements a robust approach to data ingestion, confound matching, and network-based statistical analysis.

## Project Layout

The project is organized into the following top-level folders:
- `code/`: Contains the complete analysis pipeline, including data loaders, preprocessing scripts, statistical modules, and the main entry point.
- `data/`: Stores all project artifacts, including raw data (where applicable), processed subject tables, connectivity matrices, and final result CSVs.
- `tests/`: Contains the test suite, including unit tests for individual modules and integration tests for the end-to-end pipeline.

## Requirements
- Python 3.11+
- Dependencies are listed in `code/requirements.txt`.

## Getting Started
For detailed instructions on how to set up the environment and run the pipeline in either verification (synthetic) or analysis (real data) mode, please refer to the `quickstart.md` file.
