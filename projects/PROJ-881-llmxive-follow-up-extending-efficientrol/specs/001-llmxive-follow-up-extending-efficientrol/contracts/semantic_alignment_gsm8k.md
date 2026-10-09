---
task: gsm8k
type: semantic_alignment
alignment:
 method: exact_match
 source_field: answer
 tokenization: whitespace
---
# Semantic Alignment Contract for GSM8K

This contract defines the semantic alignment strategy for the GSM8K dataset.
Tokens are aligned using exact string matching on the `answer` field,
with whitespace tokenization.