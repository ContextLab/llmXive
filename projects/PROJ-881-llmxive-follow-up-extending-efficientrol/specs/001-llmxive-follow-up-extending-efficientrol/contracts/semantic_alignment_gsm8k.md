---
task: gsm8k
type: semantic_alignment
description: >
 Semantic alignment logic for labeling generated GSM8K tokens as valid or
 invalid against the canonical ground-truth solution provided by the GSM8K
 dataset (the "answer" field, including its final numeric answer after the
 "####" delimiter).
alignment:
 method: exact_match
 source_field: answer
 tokenization: whitespace
 target_field: generated_tokens
 label_field: validity
ground_truth_source:
 dataset: gsm8k
 config: main
 split: train
 field: answer
 final_answer_delimiter: "####"
validity_criteria: >
 A generated token is labeled "valid" (true) if, after whitespace
 tokenization of both the generated text and the canonical solution text,
 the token at position i matches the token at position i of the canonical
 solution. Tokens that deviate from the canonical solution at their
 position, or positions beyond the length of the canonical solution, are
 labeled "invalid" (false). The final numeric answer must additionally
 match the value after the "####" delimiter for the sequence-level
 validity flag to be true.
---

# Semantic Alignment Contract — GSM8K

## Purpose

This contract defines how token-level validity labels are produced for
GSM8K generation rollouts so that downstream entropy–validity correlation
analysis (User Story 3) uses a deterministic, reproducible labeling rule.

## Ground Truth

The GSM8K dataset (HuggingFace `gsm8k`, config `main`, split `train`)
provides, for each problem, a `question` string and an `answer` string.
The `answer` field contains the step-by-step worked solution followed by
a final line of the form `#### <number>` giving the canonical final
answer.

## Alignment Procedure

1. **Extract canonical solution**: read the `answer` field of the record.
 The full worked solution (excluding the `####` line) is the canonical
 solution text; the value after `####` is the canonical final answer.
2. **Tokenize**: both the canonical solution text and the generated text
 are tokenized by whitespace splitting (no subword tokenization is used
 for alignment purposes).
3. **Per-token labeling**: for each generated token index `i`:
 - If `i < len(canonical_tokens)` and
 `generated_tokens[i] == canonical_tokens[i]`, the token is labeled
 `valid` (true).
 - Otherwise the token is labeled `invalid` (false).
4. **Sequence-level flag**: the sequence is considered fully valid only if
 every generated token is valid AND the generated final numeric answer
 equals the canonical final answer after `####`.

## Edge Cases

- **Multiple valid phrasings**: GSM8K solutions are single canonical
 strings; per-token exact match against the single canonical solution is
 the alignment rule. No alternative paths are considered (unlike
 MiniGrid, which permits multiple valid paths).
- **Longer generations**: generated tokens beyond the canonical solution
 length are labeled invalid.
- **Numeric equivalence**: the final-answer comparison compares the exact
 numeric value (e.g., `42` matches `42` but not `42.0`), parsed as
 integers where possible, matching the GSM8K dataset convention.

## Output Schema

Each labeled record is written to JSONL with at least:

```json
{
 "prompt_id": "<id>",
 "task_type": "gsm8k",
 "tokens": ["..."],
 "validity_labels": [true, false],
 "validity": false
}
```

`validity_labels` has the same length as `tokens`; `validity` is the
sequence-level flag.
