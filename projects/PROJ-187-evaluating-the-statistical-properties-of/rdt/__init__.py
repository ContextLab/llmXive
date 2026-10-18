"""Package placeholder for rdt to satisfy sdv import dependencies.

The real `rdt` library is expected to provide various transformer
classes. For the purposes of this project we only need to expose an
``IDGenerator`` symbol so that ``sdv`` can be imported without raising
``ImportError``. All other functionality of ``rdt`` is provided by the
installed package; this stub is placed early on ``sys.path`` (the
project root) and therefore takes precedence during import, supplying
the missing name while delegating all other imports to the real
library.
"""
# The package deliberately does not import anything from the real
# ``rdt`` installation to avoid side‑effects. It only defines the
# symbols that are missing in the version bundled with the project.
