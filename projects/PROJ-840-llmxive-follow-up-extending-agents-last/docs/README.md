# llmXive: Automated Science Pipeline

**Project ID**: PROJ-840-llmxive-follow-up-extending-agents-last

## Overview

This project implements an automated science pipeline to analyze "Agents' Last Exam" (ALE) execution traces. It focuses on identifying failure modes (State Persistence vs. Reasoning Deficit), applying context-checkpointing interventions, and statistically validating the improvements using McNemar's test.

## Features

- **Automated Failure Classification**: Uses local LLMs to classify failure modes with deterministic seed pinning.
- **Context Checkpointing**: Implements a wrapper to regenerate state summaries at configurable intervals (N=1, 3, 5).
- **Statistical Significance**: Performs paired binary outcome analysis to validate intervention efficacy.
- **Sensitivity Analysis**: Tests robustness across different checkpointing frequencies.

## Architecture

- **Code**: `code/` contains the core logic, modularized by user story (Classification, Intervention, Analysis).
- **Data**: `data/` stores raw traces, golden subsets, and processed results.
- **Tests**: `tests/` includes unit and integration tests for validation.
- **Docs**: `docs/` holds documentation and final reports.

## Quick Start

See [`docs/quickstart.md`](docs/quickstart.md) for installation and execution instructions.

## License

[Insert License Here]
