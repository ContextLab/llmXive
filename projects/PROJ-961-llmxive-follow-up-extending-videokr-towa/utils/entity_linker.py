"""
Wrapper module that re-exports the deterministic entity linking utilities.
The core implementation lives in `code/utils/entity_linker.py`. This file
simply imports the public symbols so that imports like
`from utils.entity_linker import link_dataframe` work in environments
where the `code` package is not automatically on the import path (e.g.,
during pytest collection).
"""
from code.utils.entity_linker import (  # noqa: F401
    EntityLinker,
    create_entity_linker,
    link_dataframe,
)