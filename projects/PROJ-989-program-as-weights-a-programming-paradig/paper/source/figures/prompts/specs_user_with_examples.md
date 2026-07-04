Produce STRICT JSON with the schema: {"specs": [{"spec": string, "category": string, "difficulty": string}]}.
Generate {{num}} diverse specs for the category: {{category}}.
Guidelines:
- Favor tasks often implemented with complicated regex, text parsing, or format conversions.
- Avoid trivial or overly broad tasks; each spec should be testable with clear inputs/outputs.
- Keep each spec concise (a few sentences) but include a few concrete input/output examples.
- Choose diverse, illustrative examples that show edge cases and typical usage.
- category must be "{{category}}" for all specs.
- difficulty in {easy, medium, hard}.
Return ONLY JSON.