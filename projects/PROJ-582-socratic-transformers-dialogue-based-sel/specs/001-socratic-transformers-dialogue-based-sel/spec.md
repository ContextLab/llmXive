# Specification: Socratic Transformers (PROJ-582)

## Problem Statement

This research investigates whether a language model can improve its reasoning capabilities
through a process of **evolutionary pressure** and **negative selection on belief**, rather than
explicit "self-teaching" or instruction-based learning.

Traditional "self-teaching" paradigms imply that a system can autonomously generate knowledge
or correct itself through an internal pedagogical loop. This specification reframes the
mechanism as a **selectionist process**:

1. **Variation**: The model generates multiple reasoning paths or answers to a given problem.
2. **Adversarial Critique (Selection Pressure)**: An internal or external mechanism generates
 "negative" signals by identifying logical contradictions, unsupported assumptions, or
 high-probability errors in the generated outputs. This mirrors the thymic selection of T-cells,
 where cells that fail specific tests are eliminated.
3. **Negative Selection on Belief**: Instead of "teaching" the model the correct answer,
 the system applies pressure to reject (or revise) beliefs that fail the adversarial check.
 The model learns to avoid the "belief space" associated with these rejected outputs.

This distinction addresses the philosophical concern that a machine cannot "originate"
knowledge (Ada Lovelace's constraint) but can execute ordered operations that simulate
the *outcome* of a selection process. The system does not "teach" itself; it undergoes
a computational selection pressure that filters out low-quality reasoning traces.

## Core Objectives

* **FR-001**: Implement a generative engine that produces static QA tuples and Socratic
 dialogue tuples (question, answer, critique, revised_answer) from source datasets.
* **FR-002**: The critique mechanism must dynamically identify logical contradictions
 and unsupported assumptions, acting as the source of "evolutionary pressure."
* **FR-003**: All training and inference must adhere to strict CPU/low-memory constraints
 (4-bit quantization, fallback models) to ensure reproducibility on free-tier infrastructure.
* **FR-006**: Statistical analysis must rigorously compare the "Selection" condition (adversarial
 critique) against "Static" and "Ablation" (neutral critique) baselines to isolate the
 effect of the negative selection pressure.
* **FR-007**: Implement an ablation study where the critique text is replaced with neutral
 placeholders of equivalent token length to verify that the improvement is due to the
 *content* of the selection signal, not merely the presence of additional tokens.
* **FR-008**: Enforce hard timeouts and OOM fallbacks to ensure the system operates
 within defined resource boundaries.

## Methodology

### Data Generation (US1)
The system will download GSM8K and MATH datasets. It will generate:
1. **Static Tuples**: Standard (Question, Answer) pairs.
2. **Dialogue Tuples**: (Question, Initial Answer, Critique, Revised Answer).
 The Critique serves as the **negative selection signal**, highlighting errors in the
 Initial Answer.
3. **Ablation Tuples**: Same as Dialogue Tuples, but the Critique is replaced with a
 neutral placeholder.

### Training & Evaluation (US2)
The model will be fine-tuned using LoRA on the generated datasets.
* **Condition A (Selection)**: Trained on Dialogue Tuples (Critique present).
* **Condition B (Ablation)**: Trained on Ablation Tuples (Neutral Critique).
* **Condition C (Static)**: Trained on Static Tuples.

Evaluation will measure accuracy on held-out GSM8K and MMLU STEM subsets.

### Analysis (US3)
Statistical tests (paired t-tests with Bonferroni correction) will determine if Condition A
significantly outperforms Conditions B and C, thereby validating the efficacy of the
**negative selection on belief** mechanism.

## Constraints & Assumptions

* **Compute**: Must run on free-tier CPU instances (7GB RAM limit).
* **Model**: Base model must support 4-bit quantization (e.g., via `bitsandbytes` or GGUF).
* **Philosophy**: The system is an engine executing ordered operations; it does not
 "originate" new truths but refines its output distribution through selection pressure.
* **Data**: All data must be sourced from real, public repositories (HuggingFace).

## Review Alignment

This specification explicitly incorporates feedback from **David Krakauer**, reframing
the adversarial component from "self-teaching" to "evolutionary pressure" and "negative
selection on belief," ensuring the terminology aligns with biological selection analogies
rather than pedagogical instruction.