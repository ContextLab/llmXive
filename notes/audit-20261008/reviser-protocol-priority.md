# Revision response protocol priority (2026-10-09)

The original canary's task replanning repeatedly emitted unusable JSON despite the delimited-artifact contract. The shared revisers reuse authoring system prompts: tasker Mode B requires a JSON-only object, clarifier requires JSON-only, and the research implementer requires YAML-only. Their user messages instead require a small JSON change-log plus verbatim delimited artifact bodies. The lower-priority message was contradicting the system output contract.

The shared revision backend entry point now states the active convergence protocol at system priority, explicitly replacing only the authoring output format and retaining scientific/editing requirements. Initial authoring, legacy paths, and the separate YAML self-consistency audit are unchanged. Parser validation is unchanged.

Validation: 52 protocol/self-consistency tests and 71 revision integration/unit checks pass. A live GPT-OSS fixture returned the required delimited artifact in 5.191 seconds, preserved quotes, a backslash regex, task IDs, and the parameter set, and addressed the literal concern ID. Exact output is in `reviser-protocol-live.json`. This small protocol probe is not full pipeline acceptance or proof that malformed replies cannot recur.

Related to recurring issues #1474 and #1139.
