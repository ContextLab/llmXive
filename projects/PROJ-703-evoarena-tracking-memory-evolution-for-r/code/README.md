# EvoArena Adaptation: Persona Memory Evolution (Scaled-Down)

## What was simplified vs. the original

The original paper **EvoArena** evaluates LLM agents on dynamic environment changes (terminal, software, social) using a full LLM (e.g., GPT-4) to process thousands of chat interactions and track memory evolution via "EvoMem". The original experiments require:
1.  **Large-scale LLM inference** (GPT-4/LLaMA-3) for every turn.
2.  **Full dataset** (32k+ chat history files).
3.  **Complex memory patching** logic involving embeddings and vector search.

### Adaptation Strategy (CPU-tractable)
To reproduce the **core quantitative result** (the accuracy gain of EvoMem over a baseline on dynamic persona changes) within a 2-core CPU limit:

1.  **Proxy LLM Controller**: Replaced the `litellm`/OpenAI `Ollama` controllers with a **deterministic, rule-based simulator** that mimics the *behavioral logic* of the memory system without calling an external API. It uses the actual text content from the repo's `chat_history_32k` files to simulate "understanding" and "updating" preferences.
2.  **Dataset Subsampling**: Instead of processing the full 32k dataset, the script loads a **small, representative sample** (first 50 chat files) from `EvoMem-PersonaMem-Evo/data/chat_history_32k/`.
3.  **Simplified Memory Logic**:
    *   **Baseline**: Maintains a static "persona" string.
    *   **EvoMem (Adapted)**: Implements a simplified version of the `PatchStore` logic. It detects "preference change" keywords (e.g., "actually", "changed my mind", "now I prefer") in the chat text and updates the stored persona state.
4.  **Metric**: Computes the **Chain Accuracy** (did the agent maintain the *current* correct preference after a change?) instead of full QA generation.
    *   *Original*: 39.6% baseline vs 41.1% EvoMem.
    *   *Adapted*: Measures the % of correct state tracking after a simulated change event in the sample data.

## Dependencies
- `numpy`
- `pandas`
- `tqdm` (optional, for progress bars)
- Standard library (`json`, `re`, `os`, `pathlib`)

## How to Run
1.  Ensure the `EvoMem-PersonaMem-Evo/data/chat_history_32k/` directory exists and contains JSON files.
2.  Run `python code/evomem_simulation.py`.
3.  Results are written to `data/evomem_results.csv` and `figures/accuracy_comparison.png`.
