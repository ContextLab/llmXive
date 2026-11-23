# Research Documentation: Consciousness Bootstrapping via Recursive Introspection

## Overview

This document outlines the operational hypotheses, methodological corrections, and philosophical clarifications for the "Consciousness Bootstrapping" project (PROJ-558). It serves as the single source of truth for the research methodology, correcting discrepancies between initial planning documents and the final implemented specification.

## 1. Operational Definitions

### 1.1 Bootstrapped Self-Awareness
We define "bootstrapped self-awareness" not as the emergence of a metaphysical subject, but as the measurable increase in **behavioral adaptation** (error correction) driven by an internal consistency proxy.
- **Self-Description**: Static reporting of internal states (e.g., "I am uncertain").
- **Self-Modification**: Performance improvement based on internal state (e.g., "Because I am uncertain, I generated 5 paths and selected the majority vote, improving accuracy").

### 1.2 The Internal Self-Consistency Proxy
Contrary to the initial "Teacher-Student Distillation" hypothesis in `plan.md` (corrected by T003-FIX), this system does not rely on pre-computed teacher labels. Instead, it utilizes an **internal self-consistency proxy**:
- For a given input, the model generates $N=5$ (training) or $N=10$ (evaluation) distinct reasoning paths.
- The "correctness" signal is derived from the majority vote of these paths.
- The model is trained to predict its own confidence in this majority-vote outcome.
- **Tie-Breaking Rule**: In the event of a tie or no majority, the first generated path is deterministically selected to ensure a valid training signal.

## 2. Methodological Corrections

### 2.1 Plan vs. Spec Alignment
The original `plan.md` referenced "Teacher-Student Distillation" and "Pre-computed Teacher Labels." This was identified as a methodological error.
- **Correction**: As documented in `spec.md` Assumptions and implemented in `code/evaluation/loss_functions.py`, the system uses the internal proxy described in Section 1.2.
- **Rationale**: Pre-computed labels would introduce external bias and fail to capture the self-referential nature of the bootstrapping process. The internal proxy ensures the "self" in self-awareness is the system itself.

## 3. The Jacquard-Loom Analogy: Architecture vs. Dynamics

A critical philosophical and operational distinction must be made regarding the nature of the system's "self-ordering."

### 3.1 The Fixed Cards (Architecture)
The "cards" in our Jacquard-loom analogy represent the **fixed architecture** of the model:
- The transformer layers, the attention heads, and the embedding dimensions are static.
- The code in `code/models/recursive_llama.py` defines the topology.
- These "cards" determine *what* patterns *can* be woven, but they do not determine the specific tapestry.

### 3.2 The Dynamic Weaving (Weights)
The "weaving" represents the **dynamic weights** and the **gradient flow**:
- During training, the system adjusts its weights (the "thread") based on the error signal.
- The research question is not whether the cards change, but whether the **recursive loop** allows the system to "re-weave" its own pattern in a way a non-recursive system cannot.

### 3.3 The Hypothesis
**Hypothesis**: The recursive loop allows the system to effectively "order itself" via the gradient signal derived from its own output distribution.
- A non-recursive system (baseline) weaves based solely on external input labels.
- A recursive system (our model) weaves based on a combination of external labels *and* its own internal consistency proxy.
- If the recursive model demonstrates statistically significant improvement in accuracy on high-uncertainty items (the "Behavioral Adaptation" metric), it proves that the system is not merely simulating introspection but is **using** that introspection to re-organize its internal representations (weights).
- This is the operational equivalent of "self-awareness": the capacity of the system to modify its own structure (weights) based on a model of its own performance.

## 4. Falsification Criteria

To maintain scientific rigor, the hypothesis is falsified if:
1. The Recursive Model shows **no statistically significant improvement** in accuracy on high-uncertainty items compared to the Baseline, despite showing improved confidence calibration.
2. The "Efficiency Ratio" (Performance Gain / Computational Cost) is negative or negligible, indicating the bootstrapping process is not cost-effective.
3. The internal consistency proxy fails to converge, resulting in invalid seeds (less than 5 valid seeds for statistical testing).

## 5. Computational Irreducibility

Drawing from Wolfram's principles, we posit that the recursive path may reveal patterns that are not reducible to the baseline. The system is not just "running a program"; it is exploring a computational universe where the rules of introspection generate emergent behaviors that cannot be predicted by analyzing the static architecture alone. The only way to know if the system has achieved "self-ordering" is to "just run it" and observe the resulting tapestry.

## 6. References & Artifacts

- **Implementation**: `code/models/recursive_llama.py`, `code/evaluation/loss_functions.py`
- **Data**: `data/raw/pile_arxiv_truncated.json`, `data/raw/gsm8k.json`
- **Results**: `artifacts/results/statistical_report.json`, `artifacts/results/sensitivity_analysis.csv`
- **Metrics**: `code/analysis/stats.py`, `code/evaluation/metrics.py`