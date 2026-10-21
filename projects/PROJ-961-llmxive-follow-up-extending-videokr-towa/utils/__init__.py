"""
Top-level utils package to expose submodules located in `code/utils`.
This wrapper allows imports such as `utils.config` and `utils.entity_linker`
to resolve correctly when the `code` directory is not automatically on
`sys.path` (e.g., during pytest execution).
"""
# The package is intentionally left empty; submodules are provided
# in sibling files that re-export the implementations from `code.utils`.
