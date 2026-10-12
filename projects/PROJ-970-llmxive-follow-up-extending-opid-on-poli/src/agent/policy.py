"""Thin wrapper that re‑exports the baseline policy implementation.

The actual implementation resides in ``code/agent/policy.py``.
"""

from importlib import import_module

_policy_mod = import_module('code.agent.policy')
BaselinePolicy = _policy_mod.BaselinePolicy
BaselinePolicyConfig = _policy_mod.BaselinePolicyConfig
create_baseline_policy = _policy_mod.create_baseline_policy
main = _policy_mod.main
