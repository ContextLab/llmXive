# Design Document: llmXive Follow-up

## Overview
This project extends the "Weak-to-Strong Generalization" paper by validating signal transfer
across different model architectures (MoE and SSM) using Direct On-Policy Distillation.

## Architecture
- **Teacher**: Dense Transformer (pre/post-RL)
- **Students**:
 - MoE: Mixtral-8x7B
 - SSM: Mamba-1.3B

## Data Flow
1. Download AIME 2024 dataset
2. Preprocess prompts and reasoning steps
3. Split into train/holdout
4. Train students with implicit reward from teacher
5. Evaluate on held-out set with human-verified labels

## Memory Management
- CPU-only execution
- Int8 quantization
- Batch size = 1 with gradient accumulation
- Dynamic batch size reduction via MemoryMonitor
- Hard floor enforcer for batch_size=1

## Dependencies
- transformers, accelerate, peft
- scikit-learn, scipy, pandas, numpy
- psutil (memory monitoring)