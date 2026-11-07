# Top‑level package for command‑line entry points.
# The modules in ``src`` are thin wrappers that delegate to the
# implementation located under ``code/src``.  This layout allows the
# quick‑start commands (e.g. ``python -m src.verify_requirements``) to
# resolve correctly without restructuring the existing code base.
