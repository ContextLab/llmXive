"""Live Reviser implementations for the convergence engine (spec 015 T054-T059).

Each ``Reviser`` implements the protocol from ``convergence.types`` and owns
the R2 phase for one reviewable step: takes the current artifacts + the
panel's concerns, returns updated artifacts + a per-concern response log.

This package replaces the ``_TodoReviser`` placeholders that the static
registry (``convergence.reviewspecs``) installs by default. The intended
construction pattern is:

    from llmxive.convergence.reviewspecs import reviewspec_for
    from llmxive.convergence.revisers.spec_reviser import build_spec_reviewspec

    spec = build_spec_reviewspec(backend=..., repo_root=..., project_id=...)
    # `spec` has the live SpecReviser as its `.reviser`; the registry's
    # static spec (reviewspec_for("clarified")) still has a TodoReviser.

The wiring layer (T058/T059) calls the build_* helpers to get a live
ReviewSpec for the engine.
"""
