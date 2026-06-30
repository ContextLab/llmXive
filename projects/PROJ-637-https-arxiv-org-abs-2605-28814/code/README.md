# BES CPU Adapter

## Purpose
This code provides a **simplified, CPU-tractable adaptation** of the "Bidirectional Evolutionary Search" (BES) framework from the paper *Self-Improving Language Models with Bidirectional Evolutionary Search*.

## Approximations & Simplifications
To ensure the code runs within the strict CI constraints (2 CPU cores, ~7GB RAM, <25 mins, no GPU), the following significant simplifications were made:

1.  **Task Substitution**:
    *   **Original**: Complex geometric optimization (Circle Packing, Heilbronn Convex) requiring heavy numerical solvers and potentially LLM-based reasoning.
    *   **Adaptation**: A synthetic "Sum & Variance" optimization task. The goal is to find 5 numbers that sum to 10.0 with minimal variance. This preserves the *structure* of the optimization problem (constraint satisfaction + objective minimization) without the computational overhead.

2.  **Model Replacement**:
    *   **Original**: LLM-based candidate generation (expansion) and recombination (crossover).
    *   **Adaptation**: Purely algorithmic operators.
        *   *Expansion*: Gaussian mutation.
        *   *Crossover*: Arithmetic mean of parent vectors.
        *   *Selection*: Tournament selection based on a simple scalar fitness function.

3.  **Backward Search Approximation**:
    *   **Original**: Recursive LLM decomposition of goals into sub-goals.
    *   **Adaptation**: A deterministic "Split-and-Verify" heuristic. The global sum constraint is split into two half-sum constraints, providing dense intermediate feedback (satisfaction scores) similar to the paper's backward search mechanism.

4.  **Scale**:
    *   Population size: 20 (vs. potentially thousands in the original).
    *   Generations: 10 (vs. hundreds/thousands).
    *   This ensures the script completes in < 10 seconds.

## Artifacts Produced
*   `data/bes_results.json`: Contains the final best candidate, fitness score, and backward search satisfaction metrics.
*   `figures/evolution_plot.png`: A plot showing the convergence of the best score over generations.

## Running
Execute the single command:
```bash
python code/bes_cpu_adapter.py
```
No external dependencies beyond `numpy` and `matplotlib` (standard in most Python environments) are required. The script is self-contained.
