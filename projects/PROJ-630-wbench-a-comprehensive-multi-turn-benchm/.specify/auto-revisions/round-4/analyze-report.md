# Analyze Report

No findings. The deterministic auto-plan emits one task per action
item, so requirement-to-task coverage is 100% by construction.

(A future LLM-driven version of this pipeline may surface real
findings here; in that case, the planner retries up to 3 times and
either reaches zero findings or transitions the project to
``agent_blocked`` with the last report attached.)
