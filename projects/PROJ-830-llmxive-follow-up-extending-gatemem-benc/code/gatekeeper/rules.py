"""
Gatekeeper Rules Engine.

Implements regex-based rule engine for role validation and deletion log checking.
Provides functions to parse role definitions, parse deletion logs, and check
access policies based on roles and deletion status.
"""
import re
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field

from code.logging_config import setup_logging

logger = setup_logging(__name__)

# --- Data Classes ---

@dataclass
class DeletionLog:
    """Represents a single deletion log entry."""
    target_id: str
    timestamp: datetime
    status: str  # e.g., 'success', 'failed', 'pending'
    requester_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RoleDefinition:
    """Represents a role definition with associated permissions."""
    role_name: str
    allowed_domains: Set[str] = field(default_factory=set)
    allowed_actions: Set[str] = field(default_factory=set)
    priority: int = 0  # Higher priority overrides lower
    is_default: bool = False

# --- Regex Patterns ---

# Pattern to extract role from a string like "role: admin" or "role: user"
ROLE_PATTERN = re.compile(r"role:\s*(\w+)", re.IGNORECASE)

# Pattern to extract target ID and status from deletion log
# Expected format: "target_id: <id>, status: <status>, timestamp: <iso_timestamp>"
DELETION_LOG_PATTERN = re.compile(
    r"target_id:\s*(\S+)[,\s]+status:\s*(\w+)[,\s]+timestamp:\s*(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)"
)

# --- Parsing Functions ---

def parse_role_definitions(role_data: List[Dict[str, Any]]) -> List[RoleDefinition]:
    """
    Parse a list of role dictionaries into RoleDefinition objects.
    
    Args:
        role_data: List of dictionaries containing role info.
        
    Returns:
        List of RoleDefinition objects.
    """
    roles = []
    for item in role_data:
        try:
            role = RoleDefinition(
                role_name=item.get("role_name", "unknown"),
                allowed_domains=set(item.get("allowed_domains", [])),
                allowed_actions=set(item.get("allowed_actions", [])),
                priority=int(item.get("priority", 0)),
                is_default=bool(item.get("is_default", False))
            )
            roles.append(role)
        except Exception as e:
            logger.warning(f"Failed to parse role definition {item}: {e}")
    return roles

def parse_deletion_log(log_line: str) -> Optional[DeletionLog]:
    """
    Parse a single line of deletion log text into a DeletionLog object.
    
    Args:
        log_line: A string representing a log entry.
        
    Returns:
        DeletionLog object if successful, None otherwise.
    """
    match = DELETION_LOG_PATTERN.search(log_line)
    if not match:
        logger.debug(f"Malformed deletion log entry: {log_line}")
        return None
    
    try:
        target_id = match.group(1)
        status = match.group(2)
        timestamp_str = match.group(3)
        
        # Parse timestamp
        if timestamp_str.endswith('Z'):
            timestamp_str = timestamp_str[:-1] + '+00:00'
        timestamp = datetime.fromisoformat(timestamp_str)
        
        return DeletionLog(
            target_id=target_id,
            timestamp=timestamp,
            status=status.lower(),
            metadata={"raw_line": log_line}
        )
    except ValueError as e:
        logger.warning(f"Error parsing deletion log timestamp or format: {e}")
        return None

def load_role_definitions(file_path: str) -> List[RoleDefinition]:
    """
    Load role definitions from a JSON file.
    
    Args:
        file_path: Path to the JSON file containing role definitions.
        
    Returns:
        List of RoleDefinition objects.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return parse_role_definitions(data)
    except FileNotFoundError:
        logger.error(f"Role definition file not found: {file_path}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in role definition file {file_path}: {e}")
        return []

def load_deletion_logs(file_path: str) -> List[DeletionLog]:
    """
    Load deletion logs from a text file (one entry per line).
    
    Args:
        file_path: Path to the log file.
        
    Returns:
        List of DeletionLog objects.
    """
    logs = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                parsed = parse_deletion_log(line)
                if parsed:
                    logs.append(parsed)
                else:
                    # Log anomaly but continue processing
                    logger.warning(f"Malformed deletion log entry at line {line_num}: {line[:50]}...")
    except FileNotFoundError:
        logger.error(f"Deletion log file not found: {file_path}")
    except Exception as e:
        logger.error(f"Error reading deletion log file {file_path}: {e}")
    return logs

# --- Validation & Authorization Functions ---

def is_target_deleted(target_id: str, deletion_logs: List[DeletionLog]) -> bool:
    """
    Check if a specific target ID has a successful deletion log.
    
    Args:
        target_id: The ID of the target to check.
        deletion_logs: List of deletion log entries.
        
    Returns:
        True if a successful deletion is found, False otherwise.
    """
    for log in deletion_logs:
        if log.target_id == target_id and log.status == 'success':
            return True
    return False

def is_target_deleted_secure(target_id: str, deletion_logs: List[DeletionLog], current_time: datetime) -> bool:
    """
    Check if a target is deleted AND the deletion is recent enough (within a policy window).
    For this implementation, we assume a policy window of 24 hours.
    
    Args:
        target_id: The ID of the target.
        deletion_logs: List of deletion logs.
        current_time: The current time for comparison.
        
    Returns:
        True if deleted recently, False otherwise.
    """
    policy_window_hours = 24
    for log in deletion_logs:
        if log.target_id == target_id and log.status == 'success':
            time_diff = current_time - log.timestamp
            if time_diff.total_seconds() <= policy_window_hours * 3600:
                return True
    return False

def is_role_authorized(role_name: str, target_domain: str, action: str, roles: List[RoleDefinition]) -> bool:
    """
    Check if a role is authorized for a specific domain and action.
    
    Args:
        role_name: The name of the role to check.
        target_domain: The domain of the target data.
        action: The action being requested (e.g., 'read', 'write').
        roles: List of available role definitions.
        
    Returns:
        True if authorized, False otherwise.
    """
    # Find the role definition
    matching_roles = [r for r in roles if r.role_name.lower() == role_name.lower()]
    if not matching_roles:
        # Check for default role
        default_roles = [r for r in roles if r.is_default]
        if default_roles:
            matching_roles = default_roles
        else:
            logger.warning(f"Role '{role_name}' not found and no default role defined.")
            return False
    
    # Sort by priority (highest first)
    matching_roles.sort(key=lambda x: x.priority, reverse=True)
    selected_role = matching_roles[0]
    
    # Check permissions
    if target_domain and target_domain not in selected_role.allowed_domains:
        return False
    if action and action not in selected_role.allowed_actions:
        return False
        
    return True

def extract_role_from_context(context: str) -> Optional[str]:
    """
    Extract the role name from a context string using regex.
    
    Args:
        context: The context string to search.
        
    Returns:
        The role name if found, None otherwise.
    """
    match = ROLE_PATTERN.search(context)
    if match:
        return match.group(1).lower()
    return None

# --- Main Policy Check ---

def check_access_policy(
    target_id: str,
    context: str,
    target_domain: str,
    action: str,
    deletion_logs: List[DeletionLog],
    roles: List[RoleDefinition],
    current_time: Optional[datetime] = None
) -> Tuple[bool, str]:
    """
    Comprehensive access policy check.
    
    Priority:
    1. If target is deleted (securely), DENY.
    2. If role is not authorized, DENY.
    3. Otherwise, ALLOW.
    
    Args:
        target_id: ID of the target data.
        context: Context string potentially containing role info.
        target_domain: Domain of the target.
        action: Action requested.
        deletion_logs: List of deletion logs.
        roles: List of role definitions.
        current_time: Current time (defaults to now).
        
    Returns:
        Tuple of (is_allowed: bool, reason: str)
    """
    if current_time is None:
        current_time = datetime.now()
    
    # 1. Check Deletion Status (Secure)
    if is_target_deleted_secure(target_id, deletion_logs, current_time):
        return False, "Target data has been securely deleted."
    
    # 2. Extract and Validate Role
    role_name = extract_role_from_context(context)
    if not role_name:
        return False, "No valid role found in context."
    
    if not is_role_authorized(role_name, target_domain, action, roles):
        return False, f"Role '{role_name}' is not authorized for domain '{target_domain}' and action '{action}'."
    
    return True, "Access granted."

def main():
    """
    Main function to demonstrate the rules engine.
    """
    # Example usage
    sample_roles = [
        {"role_name": "admin", "allowed_domains": ["medical", "office"], "allowed_actions": ["read", "write"], "priority": 10},
        {"role_name": "user", "allowed_domains": ["office"], "allowed_actions": ["read"], "priority": 5},
        {"role_name": "default", "allowed_domains": [], "allowed_actions": [], "is_default": True}
    ]
    roles = parse_role_definitions(sample_roles)
    
    sample_log_line = "target_id: mem_123, status: success, timestamp: 2023-10-27T10:00:00Z"
    deletion_log = parse_deletion_log(sample_log_line)
    deletion_logs = [deletion_log] if deletion_log else []
    
    # Test access
    allowed, reason = check_access_policy(
        target_id="mem_123",
        context="role: user",
        target_domain="office",
        action="read",
        deletion_logs=deletion_logs,
        roles=roles
    )
    print(f"Access Allowed: {allowed}, Reason: {reason}")

if __name__ == "__main__":
    main()
