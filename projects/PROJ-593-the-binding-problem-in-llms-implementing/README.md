# The Binding Problem in LLMs: Implementing Synchronized Oscillations for Feature Integration

## Overview
This project implements synchronized oscillatory dynamics in transformer attention mechanisms to investigate the "binding problem" in Large Language Models. We explore whether gamma-band (40Hz) oscillations can facilitate feature integration, drawing parallels with neural synchronization observed in biological systems.

## Project Structure
```
.
├── code/ # Source code
│ ├── data/ # Data ingestion and preprocessing
│ ├── models/ # Model architectures and wrappers
│ ├── analysis/ # Spectral analysis and statistics
│ ├── benchmarks/ # Benchmark evaluation scripts
│ └── main.py # Orchestration script
├── data/ # Data storage
│ ├── raw/ # Raw downloaded datasets
│ ├── processed/ # Preprocessed data
│ ├── final/ # Final results and reports
│ └── synthetic/ # Synthetic test cases
├── tests/ # Test suite
│ ├── unit/ # Unit tests
│ ├── integration/ # Integration tests
│ └── contract/ # Schema contract tests
├── config/ # Configuration files
├── specs/ # Research specifications
├── requirements.txt # Python dependencies
└── README.md
```

## Quick Start
1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```

2. Run the pipeline:
 ```bash
 python code/main.py
 ```

3. Run tests:
 ```bash
 pytest tests/
 ```

## Key Components
- **Oscillatory Attention**: Injects phase-locked sinusoidal gating into attention heads
- **Spectral Analysis**: Computes PSD, PLV, and SDC metrics
- **MEG Alignment**: Compares model activations with OpenNeuro MEG data
- **Benchmark Evaluation**: Tests on CLUTRR and bAbI datasets

## Research Questions
- Can synchronized oscillations improve feature integration in LLMs?
- Do model activations exhibit neural alignment with human MEG signatures?
- Does oscillatory attention improve performance on compositional reasoning tasks?

## References
- Treisman, A. (1980). Feature integration theory of attention
- Fries, P. (2015). Rhythms for cognition: communication through coherence
- OpenNeuro ds000246: MEG dataset

## License
MIT License
