"""Agent package.

Contains the policy implementation, the OPID routing logic and the injector
used throughout the experiments.
"""

# Export the public API of the agent package
from .opid_router import OPIDRouter, OPIDRouterConfig, main as opid_router_main  # noqa: F401
from .policy import (
    BaselinePolicy,
    BaselinePolicyConfig,
    create_baseline_policy,
    main as policy_main,
)  # noqa: F401
from .opid_injector import (
    OPIDInjector,
    OPIDInjectorConfig,
    main as opid_injector_main,
)  # noqa: F401

__all__ = [
    "OPIDRouter",
    "OPIDRouterConfig",
    "BaselinePolicy",
    "BaselinePolicyConfig",
    "create_baseline_policy",
    "OPIDInjector",
    "OPIDInjectorConfig",
]
