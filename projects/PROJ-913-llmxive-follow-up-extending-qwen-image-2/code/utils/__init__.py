"""
Utils package initialization.
Exposes the seeding utility.
"""
from .seeding import set_global_seed, get_seed_context

__all__ = ["set_global_seed", "get_seed_context"]