# PROJ-908-llmxive-follow-up-extending-qwen-agentwo

**Project**: llmXive follow-up: extending "Qwen-AgentWorld: Language World Models for General Agents"

**Objective**: Implement an automated science pipeline to parse Qwen-AgentWorld source code, construct a deterministic state-transition oracle, extract logical rules from LLM reasoning traces, and quantify divergence between LLM behavior, extracted rules, and the ground truth oracle.

## Structure

- `code/`: Python implementation modules
- `data/`: Raw and processed data artifacts
- `specs/`: Design documents, contracts, and user stories
- `tests/`: Unit and integration tests
- `projects/`: Project-specific metadata (this directory)

## Quick Start

1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
2. Run the main pipeline:
 ```bash
 python code/main.py
 ```
3. View generated artifacts in `data/processed/`.

## License

Internal Research Use Only.
