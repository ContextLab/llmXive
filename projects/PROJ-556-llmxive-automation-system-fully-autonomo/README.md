# llmXive Automation System

This project implements an automated science pipeline for hypothesis generation, novelty scoring, and reproducibility validation.

## Project Structure

- `code/`: Executable scripts and data generation artifacts
- `data/`: Datasets, generated results, and annotation queues
- `tests/`: Unit and integration tests
- `lit_search/`: Literature search indexes and results
- `src/`: Source code modules (agents, core logic, utils)
- `contracts/`: Schema definitions for data validation
- `specs/`: Feature specifications and design documents

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Run tests: `pytest tests/`

## Constraints

- All processing must be CPU-tractable
- All data must be real (no synthetic fabrication)
- Follow the task dependencies in `tasks.md`