---
action_items: []
artifact_hash: 847e9f8c2d88e19cd882110eb64b1edeb2503217a0391c45f71750651f0936bf
artifact_path: projects/PROJ-261-evaluating-the-impact-of-code-duplicatio/specs/001-evaluating-the-impact-of-code-duplicatio/spec.md
backend: dartmouth
feedback: 'I remember watching a graduate student debug a function that had been copy-pasted
  three times across a module. When I asked why, she said, ''It worked here, so it
  should work there.'' The question of code duplication is not merely about redundancy;
  it is about the pattern of human thought made manifest in syntax. This specification
  rightly seeks to correlate code clones with model perplexity, but I suggest a revision
  to the research question: distinguish between *syntactic* duplication (the copy-p'
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-05-22T13:48:35.931903Z'
reviewer_kind: llm
reviewer_name: dan-rockmore-simulated
score: 0.0
verdict: minor_revision
---

I remember watching a graduate student debug a function that had been copy-pasted three times across a module. When I asked why, she said, 'It worked here, so it should work there.' The question of code duplication is not merely about redundancy; it is about the pattern of human thought made manifest in syntax. This specification rightly seeks to correlate code clones with model perplexity, but I suggest a revision to the research question: distinguish between *syntactic* duplication (the copy-paste) and *semantic* duplication (the idea). An LLM might be confused by the former but grasp the latter, much like a reader recognizes a refrain in a song even when the notes are transposed. If we treat code as a cultural artifact rather than just data, the 'duplication' becomes a signal of shared intent, not just error.

Consider how stylometry analyzes authorship through the subtle fingerprints of syntax. Here, we should ask whether the model's confusion arises from the *presence* of the clone or the *context* in which it appears. A simple revision to the spec would be to introduce a 'semantic distance' metric alongside the density of clones. This would allow the model to learn that a repeated function in a library call is different from a repeated function in a logic branch. It is a small change, but it bridges the gap between the machine's eye for pattern and the human's eye for meaning.

---

> *Note: this contribution was authored by **Dan Rockmore (simulated)** — a simulated AI persona shaped from the public-record writings of Dan Rockmore, running on `qwen-3.5-122b` via Dartmouth Chat. It is not the actual Dan Rockmore.*
