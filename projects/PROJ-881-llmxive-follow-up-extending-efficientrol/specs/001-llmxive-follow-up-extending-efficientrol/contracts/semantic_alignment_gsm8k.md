---
task: gsm8k
type: semantic_alignment
alignment:
 method: exact_match
 source_field: answer
 tokenization: whitespace
---

# Semantic Alignment Contract for GSM8K

This contract defines the alignment strategy for the GSM8K dataset used in the
Entropy‑Guided Validity Prediction study.

- **Task**: GSM8K (grade‑school math reasoning)
- **Alignment Type**: `semantic_alignment`
- **Method**: `exact_match` – a token is considered valid if it exactly matches the
 corresponding token from the ground‑truth `answer` field.
- **Source Field**: `answer` – the field in the GSM8K dataset containing the correct
 solution string.
- **Tokenization**: `whitespace` – tokens are obtained by splitting the answer
 string on whitespace characters.

The alignment is applied token‑wise to generated sequences, marking each token as
valid (`true`) when it matches the reference token at the same position, and
invalid (`false`) otherwise. This contract is consumed by the generation and
labeling pipeline to produce the ground‑truth validity labels.