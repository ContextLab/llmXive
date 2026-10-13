# The Impact of Musical Training on Functional Connectivity in Adolescent Brains

This project implements a reproducible research pipeline to investigate how musical training during adolescence affects resting-state functional connectivity patterns, specifically within auditory, motor, and executive control networks.

## Project Structure

The project is organized into the following top-level directories:

- `code/`: Contains the implementation of the analysis pipeline, including data ingestion, preprocessing, statistical analysis, and visualization.
- `data/`: Stores all data artifacts, including raw NIfTI files, behavioral metadata, processed connectivity matrices, and final result tables.
- `tests/`: Contains the comprehensive test suite, including unit tests for individual modules and integration tests for the end-to-end pipeline.

## Overview

The pipeline supports two primary modes:
1. **Verification Mode**: Uses synthetic data to validate the software architecture and memory constraints.
2. **Analysis Mode**: Processes real neuroimaging data from verified sources (e.g., ABCD Study or HCP-Adolescents).

For detailed instructions on how to run the pipeline, please refer to `quickstart.md`.
