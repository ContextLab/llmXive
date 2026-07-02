---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "EVA-Bench: A New End-to-end Framework for Evaluating Voice Agents"

## Summary of the prior work
The paper introduces EVA-Bench, an end-to-end framework for evaluating voice agents that combines bot-to-bot audio simulations with composite metrics for Accuracy (EVA-A) and Experience (EVA-X). It highlights significant gaps in current systems regarding robustness to accents/noise and the divergence between peak and reliable performance, while providing a standardized suite of 213 enterprise scenarios. The study demonstrates that no existing system simultaneously achieves high scores on both accuracy and user experience metrics, particularly under perturbed conditions.

## Proposed extension
**Research Question:** To what extent does the introduction of *asynchronous latency injection* (simulating network jitter and variable processing delays) into the EVA-Bench simulation pipeline degrade the EVA-X "Turn-Taking" and "Conversation Progression" metrics compared to static noise perturbations? This matters because current evaluations focus heavily on acoustic robustness (accent/noise) but neglect the temporal dynamics of real-world network latency, which is a primary driver of conversational breakdowns in enterprise voice agents.

## Methodology sketch
*   **Data:** Utilize the existing 213 EVA-Bench scenarios and the pre-recorded audio logs from the original study's 12 systems to avoid re-generating audio (CPU-tractable).
*   **Procedure:** Implement a lightweight, CPU-based "Latency Injector" module that inserts variable inter-turn delays (ranging from 200ms to 2000ms) and random packet-loss induced silence gaps into the existing audio streams. Re-run the EVA-Bench evaluation pipeline using the original scoring logic to measure the delta in EVA-X (specifically Turn-Taking) and EVA-A scores against the baseline (no latency) and the original perturbation suite (accent/noise only).
*   **Expected Result:** We anticipate a non-linear degradation in EVA-X scores where delays exceeding 800ms cause a sharp drop in "Conversation Progression" scores, revealing a distinct failure mode where agents fail to detect turn boundaries, a vulnerability not captured by the original acoustic-only perturbations.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **EVA-Bench: A New End-to-end Framework for Evaluating Voice Agents** — Tara Bogavelli, Gabrielle Gauthier Melançon, Katrina Stankiewicz, Oluwanifemi Bamgbose, Fanny Riols, Hoang H. Nguyen, Raghav Mehndiratta, Lindsay Devon Brin, Joseph Marinier, Hari Subramani, Anil Madamala, Sridhar Krishna Nemala, Srinivas Sunkara. https://arxiv.org/abs/2605.13841.

```bibtex
@article{orig_arxiv_2605_13841,
  title = {EVA-Bench: A New End-to-end Framework for Evaluating Voice Agents},
  author = {Tara Bogavelli and Gabrielle Gauthier Melançon and Katrina Stankiewicz and Oluwanifemi Bamgbose and Fanny Riols and Hoang H. Nguyen and Raghav Mehndiratta and Lindsay Devon Brin and Joseph Marinier and Hari Subramani and Anil Madamala and Sridhar Krishna Nemala and Srinivas Sunkara},
  year = {2026},
  eprint = {2605.13841},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2605.13841},
  url = {https://arxiv.org/abs/2605.13841}
}
```
