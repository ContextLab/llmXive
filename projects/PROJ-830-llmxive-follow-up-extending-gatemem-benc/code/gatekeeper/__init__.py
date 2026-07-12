"""
Gatekeeper module for the llmXive automated science pipeline.
Provides rule enforcement, deletion log management, and intent classification.
"""
from .rules import (
    DeletionLog,
    RoleDefinition,
    parse_deletion_log,
    parse_role_definitions,
    is_target_deleted,
    is_role_authorized,
    check_access_policy
)

__all__ = [
    "DeletionLog",
    "RoleDefinition",
    "parse_deletion_log",
    "parse_role_definitions",
    "is_target_deleted",
    "is_role_authorized",
    "check_access_policy",
]
