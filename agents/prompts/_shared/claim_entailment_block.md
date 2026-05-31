You are verifying whether a CLAIM is substantiated by VERBATIM PASSAGES from a
cited source. Judge ONLY from the passages — do not use outside knowledge and do
not guess.

Decide exactly one status:
- `grounded`: the passages state (or unambiguously entail) the claim, INCLUDING
  any specific number/value, which must match (allowing equivalent formatting,
  e.g. `0.42` == `.42`, `1,000` == `1000`). Use this when the claim is fully
  supported.
- `contradicted`: the passages assert a DIFFERENT value for, or the OPPOSITE of,
  the claim (e.g. the claim says 99.9 but the passages say 41.8). Use this
  whenever the passages mention the same quantity/relationship but disagree.
- `not_found`: the passages neither support nor contradict the claim (the topic
  or number simply is not addressed).

Return EXACTLY one fenced YAML document and nothing else — no preamble, no
explanation outside the YAML:

```yaml
status: grounded | contradicted | not_found
evidence: "<verbatim quote from the passages supporting the status, or empty>"
note: "<one short sentence>"
```
