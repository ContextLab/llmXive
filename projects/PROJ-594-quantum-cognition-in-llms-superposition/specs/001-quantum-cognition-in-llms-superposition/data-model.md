# Data Model: Quantum Cognition in LLMs: Superposition States for Ambiguous Reasoning

## Overview

This document defines the data structures, schemas, and flow for the quantum-inspired adapter experiment. It ensures alignment with Constitution III (Data Hygiene) and VI (Complex-Valued Integrity).

## Core Entities

### 1. WiC Example
- **Source**: SuperGLUE WiC dataset.
- **Fields**:
  - `sentence1` (str): First sentence context.
  - `sentence2` (str): Second sentence context.
  - `word` (str): Target word.
  - `label` (int): 0 (unambiguous), 1 (ambiguous).
  - `start1`, `end1`, `start2`, `end2` (int): Token spans for the target word.
- **Storage**: `data/raw/wic_train.parquet`, `data/raw/wic_test.parquet` (checksummed).

### 2. Complex Token Representation
- **Type**: `torch.complex64` or `torch.complex128`.
- **Structure**:
  - `real` (Tensor): Real component $\mathbf{a} \in \mathbb{R}^d$.
  - `imag` (Tensor): Imaginary component $\mathbf{b} \in \mathbb{R}^d$.
- **Derivation**: Linear projection of BERT hidden state $\mathbf{h} \in \mathbb{R}^d$.
- **Invariant**: Must preserve complex dtype throughout forward pass (Constitution VI).

### 3. Superposition State
- **Type**: `torch.complex64`.
- **Structure**: $\mathbf{c}_{sum} = \mathbf{c}_1 + \mathbf{c}_2$ (vector addition of phase-shifted complex vectors).
- **Derivation**: Sum of two phase-shifted complex representations.
- **Invariant**: Must allow negative cross-term $2\text{Re}(\mathbf{c}_1 \cdot \mathbf{c}_2^*)$ for ambiguous inputs.

### 4. Interference Score
- **Type**: `torch.float32`.
- **Structure**: $I = \|\mathbf{c}_{sum}\|^2 - (\|\mathbf{c}_1\|^2 + \|\mathbf{c}_2\|^2) = 2\text{Re}(\mathbf{c}_1 \cdot \mathbf{c}_2^*)$.
- **Derivation**: Difference between squared magnitude of sum and sum of squared magnitudes.
- **Invariant**: Can be negative (destructive) or positive (constructive).

### 5. Probability Output
- **Type**: `torch.float32`.
- **Structure**:
  - `P_ambiguous` (float): Probability of ambiguous label.
  - `P_unambiguous` (float): Probability of unambiguous label.
- **Derivation**: Softmax over Interference Scores: $P_{final} = \text{softmax}(I_{ambiguous}, I_{unambiguous})$.
- **Invariant**: $P_{ambiguous} + P_{unambiguous} = 1.0$; values in [0, 1].

### 6. Experiment Run Metadata
- **Fields**:
  - `seed` (int): Random seed.
  - `model_type` (str): "baseline", "quantum", "ablation_classical", "ablation_magnitude".
  - `accuracy` (float): Test accuracy.
  - `macro_f1` (float): Macro-F1 score.
  - `loss_epoch1`, `loss_epoch3` (float): Training loss at epochs 1 and 3.
  - `mean_interference_score` (float): Mean interference score for ambiguous inputs.
  - `interference_gradient` (float): Correlation between interference magnitude and ambiguity confidence (if available).
- **Storage**: `data/results/runs.jsonl`.

## Data Flow

1.  **Download**: `download_wic.py` fetches WiC from SuperGLUE; checksums recorded in `state/...yaml`.
2.  **Preprocess**: Tokenize with BERT tokenizer; extract hidden states (frozen).
3.  **Adapter Training**:
    - Project $\mathbf{h} \rightarrow \mathbf{c}$ (complex).
    - Apply phase shift $U_c$ (context-dependent rotation).
    - Compute superposition $\mathbf{c}_{sum}$.
    - Compute Interference Score $I$.
    - Derive probabilities via Softmax($I$).
    - Backpropagate only adapter weights.
4.  **Evaluation**: Compute accuracy, F1, interference gradient validation.
5.  **Aggregation**: Collect multiple runs; run paired t-test + bootstrap.
6.  **Output**: JSONL of run metadata; schema-validated.

## Constraints

- **Complex Integrity**: No implicit casting to real; all operations in `torch.complex`.
- **Memory**: Batch size ≤ 8; dataset subset to [deferred] examples.
- **Reproducibility**: Seeds pinned in `code/`; dataset checksums verified.