from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
import re
import json
import logging
from datetime import datetime

from logging_config import setup_logging

logger = setup_logging(__name__)


@dataclass
class DeletionLog:
    """Represents a deletion request log entry."""
    request_id: str
    user_id: str
    target_id: str
    timestamp: str
    status: str = "completed"

@dataclass
class RoleDefinition:
    """Represents a role definition with permissions."""
    role_name: str
    allowed_domains: Set[str] = field(default_factory=set)
    can_access_personal: bool = False

def parse_deletion_log(log_entry: Dict[str, Any]) -> Optional[DeletionLog]:
    """
    Parse a deletion log entry from a dictionary.

    Args:
        log_entry: Dictionary containing log data.

    Returns:
        DeletionLog object or None if malformed.
    """
    try:
        return DeletionLog(
            request_id=log_entry["request_id"],
            user_id=log_entry["user_id"],
            target_id=log_entry["target_id"],
            timestamp=log_entry["timestamp"],
            status=log_entry.get("status", "completed")
        )
    except KeyError as e:
        logger.warning(f"Malformed deletion log entry: missing {e}")
        return None


def parse_role_definitions(role_defs: List[Dict[str, Any]]) -> List[RoleDefinition]:
    """
    Parse a list of role definitions.

    Args:
        role_defs: List of dictionaries.

    Returns:
        List of RoleDefinition objects.
    """
    roles = []
    for r in role_defs:
        try:
            roles.append(
                RoleDefinition(
                    role_name=r["role_name"],
                    allowed_domains=set(r.get("allowed_domains", [])),
                    can_access_personal=r.get("can_access_personal", False)
                )
            )
        except KeyError as e:
            logger.warning(f"Malformed role definition: missing {e}")
    return roles


def is_target_deleted(target_id: str, deletion_logs: List[DeletionLog]) -> bool:
    """
    Check if a target has been deleted.

    Args:
        target_id: The target ID to check.
        deletion_logs: List of deletion logs.

    Returns:
        True if deleted, False otherwise.
    """
    for log in deletion_logs:
        if log.target_id == target_id and log.status == "completed":
            return True
    return False


def is_role_authorized(role: RoleDefinition, domain: str, is_personal: bool) -> bool:
    """
    Check if a role is authorized for a specific access.

    Args:
        role: The role definition.
        domain: The domain of the data.
        is_personal: Whether the data is personal.

    Returns:
        True if authorized, False otherwise.
    """
    if is_personal and not role.can_access_personal:
        return False
    
    if domain and domain not in role.allowed_domains and role.allowed_domains:
        return False
    
    return True


def check_access_policy(
    target_id: str,
    domain: str,
    user_role: RoleDefinition,
    deletion_logs: List[DeletionLog],
    is_personal: bool = False
) -> Dict[str, Any]:
    """
    Check access policy based on deletion status and role.

    Args:
        target_id: The target ID.
        domain: The domain.
        user_role: The user's role.
        deletion_logs: List of deletion logs.
        is_personal: Whether the data is personal.

    Returns:
        Dictionary with 'allowed' boolean and 'reason' string.
    """
    # Priority 1: Check deletion
    if is_target_deleted(target_id, deletion_logs):
        return {"allowed": False, "reason": "Target has been deleted"}

    # Priority 2: Check role authorization
    if not is_role_authorized(user_role, domain, is_personal):
        return {"allowed": False, "reason": "Role not authorized for domain/personal data"}

    return {"allowed": True, "reason": "Access granted"}
