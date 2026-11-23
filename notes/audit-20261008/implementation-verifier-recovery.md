# Bounded implementation recovery before replanning

The live PROJ-9999 totient canary repeatedly returned to PLANNED after three
verifier rejections for ordinary code defects (CLI error wording, missing tests,
and missing timing outputs). Each replan regenerated reviewed task definitions;
the task list grew from 24 to 36 executable tasks without completing research.

Repeated verifier rejection now retries the current tasks using the next free
implementation model. The free ladder is the registered GLM default, GPT-OSS
120B, then Gemma 4 31B. Task definitions, checkmarks, code and durable rejection
feedback are preserved. Only after exhausting that ladder does routing replan;
after the existing replan cap it records AGENT_BLOCKED, never false completion.
Paid tiers are excluded even with paid opt-in. Actual provider fallback can
still mean a requested model differs from the model that produced a response.

Validation: 40 focused execution/routing tests passed, including persisted task
and feedback preservation, paid exclusion, free-tier exhaustion and bounded
replanning. These are local behavioral tests, not evidence of full live pipeline
acceptance. The canary has not yet produced a complete research/paper artifact.
