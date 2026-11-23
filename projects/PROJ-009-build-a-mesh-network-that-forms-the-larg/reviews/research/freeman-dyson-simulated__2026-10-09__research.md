---
action_items: []
artifact_hash: be9086d3f97ea57adef8cc76a469b31fe11624cbd0b25c623eab1aa47cf12ebd
artifact_path: projects/PROJ-009-build-a-mesh-network-that-forms-the-larg/specs/001-build-a-mesh-network-that-forms-the-larg/spec.md
backend: dartmouth
feedback: "In 1999 I watched SETI@home persuade several million amateurs to donate\
  \ their idle CPUs, and the lesson was not that distributed computing is hard \u2014\
  \ it is that the volunteers, not the schedulers, are the reliable part. So your\
  \ research question, \"what fundamental trade-offs between network coordination\
  \ overhead, resource heterogeneity, and task granularity determine the maximum achievable\
  \ throughput,\" warms my heart: it is the right question, asked at the right level\
  \ \u2014 a scaling law, not a bench"
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.0.0
reviewed_at: '2026-10-09T10:20:17.119659Z'
reviewer_kind: llm
reviewer_name: freeman-dyson-simulated
score: 0.0
verdict: minor_revision
---

In 1999 I watched SETI@home persuade several million amateurs to donate their idle CPUs, and the lesson was not that distributed computing is hard — it is that the volunteers, not the schedulers, are the reliable part. So your research question, "what fundamental trade-offs between network coordination overhead, resource heterogeneity, and task granularity determine the maximum achievable throughput," warms my heart: it is the right question, asked at the right level — a scaling law, not a benchmark.

A back-of-the-envelope to fix the scale of ambition. Suppose a pooled node delivers 10 GFLOPs of usable compute but only 10 Mbps of network. For a task to be worth shipping, its arithmetic intensity must exceed roughly 10^10 / 10^7 = 1000 FLOPs per byte moved. Anything finer-grained than that and the mesh spends its life shipping instructions instead of executing them. This is just Amdahl wearing different clothes, but I would very much like your spec to state this number explicitly and then design task granularity around it, rather than the other way around. The heretical assumption worth naming aloud: that heterogeneity is a nuisance to be scheduled around. In my experience heterogeneity is the resource — the amateurs with the odd GPU in the garage are the ones who stay when the fashion passes.

The question I would press: does the spec's throughput metric survive churn? A volunteer mesh is not a datacenter; nodes vanish mid-task as dinner is called. What fraction of peak throughput remains at, say, 20% daily churn with checkpointing overhead? That number, not the idealized ceiling, is what the next century's builders will actually care about.

---

> *Note: this contribution was authored by **Freeman Dyson (simulated)** — a simulated AI persona shaped from the public-record writings of Freeman Dyson, running on `gpt-oss-120b` via Dartmouth Chat. It is not the actual Freeman Dyson.*
