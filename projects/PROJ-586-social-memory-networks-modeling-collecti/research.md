# Research Notes: Reviewer Feedback Integration

This document tracks the integration of critical feedback from domain experts (Geoffrey West, Eric Kandel, David Krakauer) into the Social Memory Networks research design and implementation.

## 1. Scaling Laws and Network Efficiency (Geoffrey West)

**Feedback Summary**:
Geoffrey West highlighted the parallel between urban infrastructure scaling and multi-agent memory systems. In cities, doubling population requires only ~85% more infrastructure (sublinear scaling, $N^{0.85}$) due to network effects. He questioned whether collective remembering in multi-agent systems obeys a similar law.

**Integration Actions**:
- **Added Scaling Analysis Phase (US-3)**: Implemented a dedicated user story to measure how memory accuracy (specialization index) and retrieval speed scale with agent count ($N=3, 5, 7$).
- **Power-Law Fitting**: Added `code/analysis/scaling.py` to fit power-law models to the observed metrics.
- **Hypothesis**: We test the null hypothesis that memory fidelity scales linearly ($N^1$) against the alternative that it scales sublinearly ($N^\beta, \beta < 1$), mirroring urban infrastructure efficiency.
- **Output**: `results/scaling_plot.pdf` visualizes the fitted curves and explicitly notes the limitation of 3 data points for robust power-law inference.

## 2. Biological Stability and "Computational CREB" (Eric Kandel)

**Feedback Summary**:
Eric Kandel drew a distinction between short-term memory (protein modification) and long-term memory (gene expression/new protein synthesis) in *Aplysia*. He asked for the computational equivalent of CREB-mediated transcription in our framework: what stabilizes a fleeting interaction into a lasting collective memory?

**Integration Actions**:
- **Memory Buffer Persistence**: Enhanced `code/memory/buffer.py` to distinguish between transient context window information and committed memory entries.
- **Commitment Threshold**: Implemented a heuristic in `code/agent/base_agent.py` where repeated retrieval of a specific fact across multiple turns triggers a "commit" action to the shared buffer, simulating the transition from short-term to long-term storage.
- **Stabilization Metric**: Added a "retention half-life" metric in `code/metrics/retrieval.py` to measure how long a committed fact remains retrievable after the initial interaction.

## 3. Adaptation and the Role of Forgetting (David Krakauer)

**Feedback Summary**:
David Krakauer reframed memory as a mechanism for adaptation rather than a warehouse. He emphasized that biological systems require forgetting to avoid noise paralysis. He suggested situating the work within the lineage of Luhmann’s social systems and Hutchins’ distributed cognition.

**Integration Actions**:
- **Forgetting Mechanism**: Implemented a decay function in `code/memory/buffer.py` where entries not accessed within a sliding window are pruned, preventing "noise paralysis" in the agent context.
- **Literature Review Update**: Expanded `specs/001-social-memory-networks/README.md` to explicitly cite Luhmann (self-producing communication loops) and Hutchins (distributed cognition), positioning the multi-agent ledger model as a computational instantiation of these theories.
- **Adaptation Metric**: Introduced a "context entropy" metric to measure the diversity of information agents are processing; high entropy with low retrieval efficiency is flagged as "noise paralysis."

## 4. Technical Constraints and Reproducibility

**Feedback Implementation**:
- **CPU-Only Baseline**: Adhered to the constraint of using CPU-only `transformers` (opt-125m) for the baseline experiments to ensure reproducibility on standard CI runners.
- **Synthetic Data Policy**: Removed all synthetic data generation for *inputs* (per spec FR-011). The system now relies on real dataset loaders (`code/data/loaders.py`) with synthetic fallbacks strictly limited to *structural* scaffolding (e.g., empty agent slots) when real data is unavailable, ensuring no fabrication of factual content.
- **Verification**: All scripts in `code/run_experiment.py` now validate that inputs are loaded from real sources before proceeding, raising an explicit error if data fabrication is detected.

## 5. Next Steps

- **Expand Scaling Range**: Future work will extend agent counts beyond $N=7$ to better constrain the power-law exponent $\beta$.
- **Long-term Memory Triggers**: Refine the "computational CREB" threshold based on empirical retrieval success rates.
- **Noise Thresholds**: Calibrate the forgetting decay rate to maximize adaptation speed while minimizing information loss.