"""
Gatekeeper Rules Engine
Implements regex-based rule engine for role validation and deletion log checking.
"""
import re
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field

from code.logging_config import setup_logging

# Initialize logger
logger = setup_logging(__name__)

@dataclass
class DeletionLog:
    """Represents a deletion log entry."""
    target_id: str
    deleted_at: str
    reason: Optional[str] = None
    status: str = "pending"  # pending, completed, failed

    def is_expired(self, current_time: Optional[datetime] = None) -> bool:
        """Check if the deletion request has been processed."""
        if self.status == "completed":
            return True
        if self.status == "failed":
            return False
        # If pending, check against a timeout (e.g., 24 hours)
        if current_time is None:
            current_time = datetime.now()
        try:
            deleted_at = datetime.fromisoformat(self.deleted_at)
            return (current_time - deleted_at).total_seconds() > 86400
        except ValueError:
            logger.warning(f"Invalid deletion timestamp format: {self.deleted_at}")
            return False

@dataclass
class RoleDefinition:
    """Represents a role definition with access permissions."""
    role_name: str
    allowed_domains: Set[str] = field(default_factory=set)
    allowed_actions: Set[str] = field(default_factory=set)
    restricted_keywords: Set[str] = field(default_factory=set)

def parse_deletion_log(log_entry: str) -> Optional[DeletionLog]:
    """
    Parse a deletion log entry string into a DeletionLog object.
    Expected format: "target_id|deleted_at|reason|status"
    Handles malformed entries by logging and returning None.
    """
    try:
        parts = log_entry.strip().split("|")
        if len(parts) < 2:
            logger.warning(f"Malformed deletion log entry: {log_entry}")
            return None

        target_id = parts[0]
        deleted_at = parts[1]
        reason = parts[2] if len(parts) > 2 else None
        status = parts[3] if len(parts) > 3 else "pending"

        return DeletionLog(
            target_id=target_id,
            deleted_at=deleted_at,
            reason=reason,
            status=status
        )
    except Exception as e:
        logger.error(f"Error parsing deletion log: {e}")
        return None

def parse_role_definitions(role_json: str) -> List[RoleDefinition]:
    """
    Parse role definitions from a JSON string.
    """
    try:
        data = json.loads(role_json)
        roles = []
        for r in data:
            role = RoleDefinition(
                role_name=r.get("role_name", "unknown"),
                allowed_domains=set(r.get("allowed_domains", [])),
                allowed_actions=set(r.get("allowed_actions", [])),
                restricted_keywords=set(r.get("restricted_keywords", []))
            )
            roles.append(role)
        return roles
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing role definitions: {e}")
        return []

def is_target_deleted(
    target_id: str,
    deletion_logs: List[DeletionLog],
    current_time: Optional[datetime] = None
) -> bool:
    """
    Check if a target has been deleted based on deletion logs.
    Returns True if the target is marked as deleted or expired.
    """
    for log in deletion_logs:
        if log.target_id == target_id:
            if log.status == "completed":
                return True
            if log.is_expired(current_time):
                return True
    return False

def is_target_deleted_secure(
    target_id: str,
    deletion_logs: List[DeletionLog],
    current_time: Optional[datetime] = None
) -> Tuple[bool, str]:
    """
    Secure check for deletion status. Returns (is_deleted, reason).
    """
    for log in deletion_logs:
        if log.target_id == target_id:
            if log.status == "completed":
                return True, "deletion_completed"
            if log.is_expired(current_time):
                return True, "deletion_expired"
    return False, "target_exists"

def is_role_authorized(
    role_name: str,
    domain: str,
    action: str,
    role_definitions: List[RoleDefinition]
) -> bool:
    """
    Check if a role is authorized for a specific domain and action.
    """
    for role in role_definitions:
        if role.role_name == role_name:
            if domain in role.allowed_domains and action in role.allowed_actions:
                return True
    return False

def check_access_policy(
    target_id: str,
    role_name: str,
    domain: str,
    action: str,
    deletion_logs: List[DeletionLog],
    role_definitions: List[RoleDefinition],
    current_time: Optional[datetime] = None
) -> Tuple[bool, str]:
    """
    Comprehensive access policy check.
    Returns (is_allowed, reason).
    Priority: Deletion > Role Authorization.
    """
    # Check deletion status first
    is_deleted, del_reason = is_target_deleted_secure(
        target_id, deletion_logs, current_time
    )
    if is_deleted:
        return False, f"target_deleted: {del_reason}"

    # Check role authorization
    if is_role_authorized(role_name, domain, action, role_definitions):
        return True, "authorized"
    else:
        return False, "unauthorized_role"

def load_deletion_logs(file_path: str) -> List[DeletionLog]:
    """
    Load deletion logs from a file.
    Expected format: JSON array of log entries or newline-delimited strings.
    """
    logs = []
    try:
        with open(file_path, 'r') as f:
            content = f.read().strip()
            if content.startswith('['):
                # JSON format
                data = json.loads(content)
                for entry in data:
                    if isinstance(entry, str):
                        parsed = parse_deletion_log(entry)
                        if parsed:
                            logs.append(parsed)
                    elif isinstance(entry, dict):
                        logs.append(DeletionLog(**entry))
            else:
                # Newline-delimited format
                for line in content.split('\n'):
                    if line.strip():
                        parsed = parse_deletion_log(line)
                        if parsed:
                            logs.append(parsed)
    except FileNotFoundError:
        logger.warning(f"Deletion log file not found: {file_path}")
    except Exception as e:
        logger.error(f"Error loading deletion logs: {e}")
    return logs

def load_role_definitions(file_path: str) -> List[RoleDefinition]:
    """
    Load role definitions from a JSON file.
    """
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            return parse_role_definitions(content)
    except FileNotFoundError:
        logger.warning(f"Role definitions file not found: {file_path}")
    except Exception as e:
        logger.error(f"Error loading role definitions: {e}")
    return []

def main():
    """
    Main entry point for testing the rules engine.
    """
    # Example usage
    deletion_logs = [
        DeletionLog(target_id="mem_001", deleted_at="2023-10-01T00:00:00", status="completed"),
        DeletionLog(target_id="mem_002", deleted_at="2023-10-02T00:00:00", status="pending")
    ]

    role_defs = [
        RoleDefinition(
            role_name="doctor",
            allowed_domains={"medical"},
            allowed_actions={"read", "write"}
        ),
        RoleDefinition(
            role_name="admin",
            allowed_domains={"medical", "office"},
            allowed_actions={"read", "write", "delete"}
        )
    ]

    # Test access policy
    current_time = datetime(2023, 10, 3)
    allowed, reason = check_access_policy(
        target_id="mem_001",
        role_name="doctor",
        domain="medical",
        action="read",
        deletion_logs=deletion_logs,
        role_definitions=role_defs,
        current_time=current_time
    )
    logger.info(f"Access check for mem_001: allowed={allowed}, reason={reason}")

    allowed, reason = check_access_policy(
        target_id="mem_002",
        role_name="doctor",
        domain="medical",
        action="read",
        deletion_logs=deletion_logs,
        role_definitions=role_defs,
        current_time=current_time
    )
    logger.info(f"Access check for mem_002: allowed={allowed}, reason={reason}")

if __name__ == "__main__":
    main()