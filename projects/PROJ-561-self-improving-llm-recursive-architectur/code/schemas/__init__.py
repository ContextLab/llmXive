"""
Schema definitions for the self-improving LLM pipeline.
"""
from .modification_proposal import ModificationProposal, ModificationType

__all__ = [
    "ModificationProposal",
    "ModificationType"
]