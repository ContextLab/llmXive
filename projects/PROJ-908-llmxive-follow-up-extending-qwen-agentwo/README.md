# PROJ-908-llmxive-follow-up-extending-qwen-agentwo

**Project**: llmXive follow-up: extending "Qwen-AgentWorld: Language World Models for General Agents"

**Description**: This project implements an automated science pipeline to parse the Qwen-AgentWorld source code, extract a deterministic state-transition oracle, derive logical rules from LLM reasoning traces, and quantify divergence between the LLM, extracted rules, and the ground truth oracle.

## Structure

- `code/`: Python modules for the pipeline (oracle, rules, analysis, utils).
- `data/`: Raw and processed data artifacts.
- `specs/`: Feature specifications, data models, and contracts.
- `tests/`: Unit and integration tests.
- `projects/`: Sub-projects if applicable (this is the root for this specific task).

## Prerequisites

- Python 3.9+
- `requirements.txt` (see root or `code/` directory)

## Quick Start

1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
2. Run the main pipeline:
 ```bash
 python code/main.py
 ```

## User Stories

- **US1**: Ground Truth Oracle Construction (P1)
- **US2**: Rule Extraction from Reasoning Traces (P2)
- **US3**: Divergence Quantification and Classification (P3)
