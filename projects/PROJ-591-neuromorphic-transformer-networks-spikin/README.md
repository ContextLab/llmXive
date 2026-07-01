# Neuromorphic Transformer Networks: Spiking Neural Dynamics in Language Models

**Project ID**: PROJ-591-neuromorphic-transformer-networks-spikin

## Overview
This project implements spiking neural dynamics within transformer architectures to investigate energy-performance trade-offs in language modeling. We replace standard feed-forward layers with Leaky Integrate-and-Fire (LIF) neurons using snnTorch and evaluate against a baseline Transformer on WikiText-2.

## Research Question
Can spiking neural dynamics integrated into transformer architectures achieve comparable perplexity to baseline models while significantly reducing computational energy consumption, and what are the temporal coding characteristics of such networks?

## Key Features
- **Baseline Transformer**: 2-layer, 4-head architecture (~2M params)
- **Spiking Transformer**: LIF neurons with surrogate-gradient learning
- **Energy Measurement**: codeCarbon integration with wall-clock fallback
- **Temporal Coding**: Inter-spike interval variance, bits/spike, synchrony metrics
- **Statistical Analysis**: Paired t-tests with Bonferroni correction

## Project Structure
```
projects/PROJ-591-neuromorphic-transformer-networks-spikin/
├── README.md
├── idea/
│ ├── neuromorphic-transformer-networks-spikin.md
│ └── research_question_validation.md
├── specs/
│ └── 591-neuromorphic-transformer-spiking/
├── code/
│ ├── main.py
│ ├── data/
│ ├── metrics/
│ ├── models/
│ ├── analysis/
│ └── tests/
├── data/
│ ├── raw/
│ ├── processed/
│ └── logs/
├── state/
└── docs/
```

## Dependencies
See `requirements.txt` in project root for full dependency list.

## License
Research use only. See LICENSE file for details.
