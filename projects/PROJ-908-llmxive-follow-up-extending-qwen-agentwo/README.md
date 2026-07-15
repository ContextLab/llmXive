# llmXive Follow-up: Extending "Qwen-AgentWorld"

**Project ID**: PROJ-908-llmxive-follow-up-extending-qwen-agentwo

## Overview
This project implements an automated science pipeline to extend the "Qwen-AgentWorld: Language World Models for General Agents" research. The goal is to construct a Ground Truth Oracle from source code, extract logical rules from LLM reasoning traces, and quantify divergence between the LLM, extracted rules, and the Oracle.

## Structure
- `code/`: Python implementation modules
- `data/`: Raw and processed data artifacts
- `specs/`: Design documents and contracts
- `tests/`: Unit and integration tests

## Getting Started
1. Initialize the project structure (Task T001).
2. Install dependencies (Task T002).
3. Run the main pipeline entry point: `python code/main.py`.

## User Stories
- **US1**: Ground Truth Oracle Construction (Priority P1)
- **US2**: Rule Extraction from Reasoning Traces (Priority P2)
- **US3**: Divergence Quantification and Classification (Priority P3)
