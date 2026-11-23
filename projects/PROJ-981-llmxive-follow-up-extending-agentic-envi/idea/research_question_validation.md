## Research-question validation

### Phenomenon-vs-method check

**Verdict**: concern

The question foregrounds a method constraint ("purely symbolic, operating without neural synthesis") rather than the underlying phenomenon: whether difficulty-structured curricula — and in particular curricula that target an agent's previously-made fallacies — improve multi-step reasoning stability and generalization in LLMs. The "no neural synthesis" framing makes the study read as a budget-feasibility demonstration rather than a scientific claim about curriculum design.

### Circularity check

**Verdict**: pass

Predictor source is the training curriculum (symbolically generated logic puzzles plus the Linguistics Olympiads corpus); the predicted variable is performance on a held-out test set drawn from a distinct source (different Olympiad year or separate logic dataset). The idea explicitly guards against train/test overlap, so the relationship is not mechanically guaranteed.

### Triviality check

**Verdict**: concern

A positive result (adaptive/error-targeted curricula improve stability and generalization) would be informative. But as framed, the null result is ambiguous: failure could be attributed to the symbolic generator's crudeness rather than to the curriculum hypothesis, because the question bundles "symbolic, no neural synthesis" into the claim. Unbundled, either outcome would be publishable; bundled, the null is confounded.

### Question-narrowing check

**Verdict**: fail

The question names implementation details (symbolic engine, no neural synthesis, CPU-tractability) as the object of inquiry. "Can method M, under constraint B, achieve outcome O" is an implementation question; the domain question is about how curriculum difficulty structure and error-targeted training shape LLM reasoning stability.

### Overall verdict

**Verdict**: validator_revise

[REVISED]
How does the structure of a training curriculum — static, adaptively difficulty-scaled, or targeted at the agent's previously-made logical errors — affect LLMs' multi-step reasoning stability and generalization to novel logic problems?
[/REVISED]

The reframing makes curriculum structure (a domain variable with three theoretically distinct conditions) the object of study, keeping the symbolic generator as a controlled, reproducible instrument rather than the claim itself. The existing methodology, tracks A/B/C, and evaluation protocol carry over unchanged.
