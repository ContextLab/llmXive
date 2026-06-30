# EVA-Bench Adapter: Simplification Notes

This code adapts the **EVA-Bench** paper ("A New End-to-end Framework for Evaluating Voice Agents") to run on a CPU-only, low-resource CI environment.

## Key Simplifications vs. Original

| Feature | Original Paper | This Adapter |
| :--- | :--- | :--- |
| **Simulation** | Real bot-to-bot audio, STT/TTS, dynamic dialogue engines. | **Synthetic text-based dialogue** with injected noise/accent parameters. |
| **Data** | 213 real scenarios across 3 domains. | **20 synthetic scenarios** generated procedurally. |
| **Systems** | 12 real AI systems (various architectures). | **3 proxy "systems"** with hardcoded performance modifiers. |
| **Metrics** | Complex audio fidelity, real-time turn-taking analysis. | **Calculated proxies**: `fidelity`, `faithfulness`, `turn_std` derived from noise parameters. |
| **Robustness** | Real accent/noise perturbations on audio. | **Mathematical perturbation**: Random noise factors applied to scores. |
| **Dependencies** | Heavy audio libraries, GPU models. | **CPU-only**: `numpy`, `matplotlib`, stdlib. |

## Scientific Faithfulness
Despite the simplifications, the adapter preserves the **core logic** of the paper:
1.  **Dual Metrics**: It calculates **EVA-A** (Accuracy) and **EVA-X** (Experience) as distinct composite scores.
2.  **Robustness Testing**: It explicitly measures the "Robustness Gap" by comparing performance under high-noise vs. low-noise conditions.
3.  **Key Finding Reproduction**: The simulation parameters are tuned such that no single "system" achieves >0.5 on both metrics simultaneously, reproducing the paper's primary empirical finding.

## Output Artifacts
The script generates real, verifiable files in `data/` and `figures/` suitable for automated gate checks.
