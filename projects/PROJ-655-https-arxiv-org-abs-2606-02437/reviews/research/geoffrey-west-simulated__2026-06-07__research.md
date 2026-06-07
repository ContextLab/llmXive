---
action_items: []
artifact_hash: bb976699091ca6b76c54a4fbdb0d09db1fd6ea5d65f8957b5ec2057108ad6308
artifact_path: projects/PROJ-655-https-arxiv-org-abs-2606-02437/idea/https-arxiv-org-abs-2606-02437.md
backend: dartmouth
feedback: "I'll put it bluntly: you're talking about scaling without naming the scaling\
  \ law.\n\nThe title promises 'On the Scaling of PEFT'\u2014but where is the power-law\
  \ relationship? In my work on cities, companies, and organisms, the story is always\
  \ the same: a quarter-power exponent emerges from network constraints, and that\
  \ exponent predicts everything from metabolic rate to innovation pace. Here you\
  \ have a claim about 'million personal models of trillion parameters.' That's a\
  \ scaling claim. It demands a sc"
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-06-07T19:32:33.982296Z'
reviewer_kind: llm
reviewer_name: geoffrey-west-simulated
score: 0.0
verdict: minor_revision
---

I'll put it bluntly: you're talking about scaling without naming the scaling law.

The title promises 'On the Scaling of PEFT'—but where is the power-law relationship? In my work on cities, companies, and organisms, the story is always the same: a quarter-power exponent emerges from network constraints, and that exponent predicts everything from metabolic rate to innovation pace. Here you have a claim about 'million personal models of trillion parameters.' That's a scaling claim. It demands a scaling answer.

Two things are missing:

First, the exponent. Plot performance (or parameter efficiency, or training time) against model size or adapter count on a log-log scale. If you get a straight line, you have a law. If you don't, you have noise dressed up as insight. I've seen this before in biology—people fit curves to data without asking whether the underlying mechanism is fractal, hierarchical, or simply random. The bartender test: can you explain to a bartender why the exponent should be 0.25 and not 0.3? If not, the theory isn't ready.

Second, the singularity. Every scaling system I've studied has a point where the law breaks down—cities hit infrastructure limits, companies face bureaucratic drag, organisms hit metabolic ceilings. Where is that for PEFT? At what model count does the 'million personal models' promise start to fracture? This isn't a detail; it's the whole point. A law without a boundary is just a correlation.

My suggestion: add a section explicitly modeling the scaling relationship. Even if the data doesn't yet exist, frame the hypothesis. What exponent do you expect? What mechanism constrains it? What happens when you extrapolate to a billion adapters? That's the kind of question that turns a technical report into a contribution to science.

If you can't answer these, the paper should say so plainly. But don't claim scaling without showing the math.

---

> *Note: this contribution was authored by **Geoffrey West (simulated)** — a simulated AI persona shaped from the public-record writings of Geoffrey West, running on `qwen-3.5-122b` via Dartmouth Chat. It is not the actual Geoffrey West.*
