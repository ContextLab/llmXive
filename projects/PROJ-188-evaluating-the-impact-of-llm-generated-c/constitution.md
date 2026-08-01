# Constitution: Automated Science Pipeline

## Version: 2.0.0

### Principle I: Scientific Integrity
All research outputs must be reproducible, transparent, and based on real data. Synthetic data may only be used for testing infrastructure, never for final analysis.

### Principle II: Model Accountability
All LLM-generated content must be traceable to its source model and configuration.

### Principle III: Data Sovereignty
All data used in the pipeline must be sourced from verified, programmatically accessible repositories.

### Principle IV: Statistical Rigor
All statistical analyses must use appropriate models for the data type (e.g., Binomial family for binary outcomes).

### Principle V: Transparency
All assumptions, limitations, and methodological deviations must be documented in the final report.

### Principle VI: Iterative Improvement
The pipeline must be updated based on empirical results and governance feedback.

### Principle VII: Controlled Explanation Generation
All LLM-generated explanations MUST be produced using TinyLlama-1.1B (primary for CPU feasibility) or CodeLlama-7B (fallback) via the HuggingFace `transformers` library with a fixed token limit of 200 and pinned random seeds.

### Principle VIII: Governance Compliance
All tasks must adhere to the decisions recorded in the governance amendment log.