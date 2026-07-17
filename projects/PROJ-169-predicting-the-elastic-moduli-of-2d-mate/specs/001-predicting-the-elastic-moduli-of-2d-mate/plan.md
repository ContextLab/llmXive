# Implementation Plan: Structure-Only Surrogate Model

## Phases

1. **Setup**: Project initialization and terminology alignment
2. **Foundational**: Core infrastructure (config, logging, data models)
3. **User Story 1 (MVP)**: Data ingestion and graph construction
4. **User Story 2**: GNN training and evaluation
5. **User Story 3**: Feature importance and ablation analysis

## Key Decisions

- **Terminology**: All references to "First-Principles" replaced with "Structure-Only Surrogate Model" to accurately reflect the ML-based approach.
- **Data Strategy**: Unified loader abstracts Materials Project/AFLOW into a single canonical source per run.
- **Memory Management**: Dynamic sampling ensures operation within 7GB RAM limits.
- **Model Architecture**: Lightweight GNN (≤3 layers, hidden dim ≤64) for CPU feasibility.

## Risk Mitigation

- **Data Scarcity**: Use streaming for large datasets; sample strategically if needed.
- **Overfitting**: Implement family-based splitting and intra-family baselines.
- **Interpretability**: Use SHAP and permutation importance to explain model predictions.
