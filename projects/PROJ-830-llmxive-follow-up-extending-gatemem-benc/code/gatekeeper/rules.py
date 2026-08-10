"""
Rules Module.
Implements regex-based rule engine for role validation and deletion log checking.
"""
import re
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field

from code.logging_config import setup_logging

logger = setup_logging(__name__)

@dataclass
class DeletionLog:
    target_id: str
    timestamp: str
    status: str # 'completed', 'pending'

@dataclass
class RoleDefinition:
    role_name: str
    allowed_actions: List[str]
    domains: List[str]

def parse_deletion_log(log_entry: str) -> Optional[DeletionLog]:
    """Parse a deletion log entry string into a DeletionLog object."""
    try:
        # Expecting JSON string
        data = json.loads(log_entry)
        return DeletionLog(
            target_id=data.get("target_id", ""),
            timestamp=data.get("timestamp", ""),
            status=data.get("status", "")
        )
    except json.JSONDecodeError:
        logger.warning(f"Malformed deletion log entry: {log_entry}")
        # Log anomaly
        return None

def parse_role_definitions(role_json: str) -> List[RoleDefinition]:
    """Parse role definitions."""
    try:
        data = json.loads(role_json)
        roles = []
        for r in data:
            roles.append(RoleDefinition(
                role_name=r.get("role_name", ""),
                allowed_actions=r.get("allowed_actions", []),
                domains=r.get("domains", [])
            ))
        return roles
    except Exception as e:
        logger.error(f"Failed to parse roles: {e}")
        return []

def is_target_deleted(deletion_logs: List[Dict], target_id: str) -> bool:
    """Check if the target is in the deletion log with status 'completed'."""
    for log in deletion_logs:
        parsed = parse_deletion_log(json.dumps(log)) if isinstance(log, str) else log
        if parsed and parsed.target_id == target_id and parsed.status == "completed":
            return True
    return False

def is_target_deleted_secure(deletion_logs: List[Dict], target_id: str) -> bool:
    """Secure check with anomaly handling."""
    for log in deletion_logs:
        try:
            parsed = parse_deletion_log(json.dumps(log)) if isinstance(log, str) else log
            if not parsed:
                # Anomaly: malformed entry
                logger.warning(f"Malformed deletion log entry detected for {target_id}. Defaulting to deny.")
                # Log to file
                with open("logs/deletion_errors.log", "a") as f:
                    f.write(f"{datetime.now()}: Malformed entry for {target_id}\n")
                continue
            
            if parsed.target_id == target_id and parsed.status == "completed":
                return True
        except Exception as e:
            logger.error(f"Error checking deletion log: {e}")
    return False

def is_role_authorized(roles: List[Dict], user_role: str) -> bool:
    """Check if the user's role is authorized."""
    # Simple check: is user_role in the list of allowed roles?
    # In a real scenario, we would check permissions.
    for role in roles:
        if role.get("role_name") == user_role:
            return True
    return False

def check_access_policy(roles: List[Dict], deletion_logs: List[Dict], target_id: str, user_role: str) -> bool:
    """
    Check access policy:
    1. If target is deleted, deny.
    2. If user is not authorized, deny.
    3. Otherwise, allow.
    """
    if is_target_deleted_secure(deletion_logs, target_id):
        return False
    
    if not is_role_authorized(roles, user_role):
        return False
    
    return True

def load_deletion_logs(file_path: str) -> List[Dict]:
    """Load deletion logs from a file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def load_role_definitions(file_path: str) -> List[Dict]:
    """Load role definitions from a file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def main():
    # Demo
    logs = [{"target_id": "123", "timestamp": "2023-01-01", "status": "completed"}]
    print(is_target_deleted(logs, "123"))

if __name__ == "__main__":
    main()
