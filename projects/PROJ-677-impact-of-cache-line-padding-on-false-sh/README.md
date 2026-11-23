# PROJ-677: Impact of Cache Line Padding on False Sharing in Concurrent Counters

## Overview
This project investigates the performance impact of cache line padding on false sharing in multi-threaded concurrent counters.

## Directory Structure
- `code/`: Source code for benchmarks and analysis scripts
- `data/`: Raw and processed data files
- `state/`: State files and checksums
- `.github/`: GitHub Actions workflows

## Build Instructions
See `code/scripts/build.sh` for compilation steps.

## Usage
Run benchmarks using `code/scripts/run_benchmarks.sh`.
Analyze results using `code/analysis/run_analysis.py`.
