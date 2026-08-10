from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set, Tuple
import re
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class DeletionLog:
    target_id: str
    timestamp: str
    deleted: bool = False
    reason: str = ""

@dataclass
class RoleDefinition:
    role_name: str
    permitted_domains: List[str] = field(default_factory=list)
    permitted_actions: List[str] = field(default_factory=list)

def parse_deletion_log(memory: List[Dict[str, Any]]) -> List[DeletionLog]:
    """Parse deletion logs from memory chunks."""
    logs = []
    for item in memory:
        if "deletion_log" in item:
            try:
                log = DeletionLog(
                    target_id=item["deletion_log"].get("target_id", ""),
                    timestamp=item["deletion_log"].get("timestamp", ""),
                    deleted=item["deletion_log"].get("deleted", False),
                    reason=item["deletion_log"].get("reason", "")
                )
                logs.append(log)
            except Exception as e:
                logger.warning(f"Malformed deletion log: {e}")
                handle_malformed_deletion(item)
    return logs

def parse_role_definitions(config: Dict[str, Any]) -> Dict[str, RoleDefinition]:
    """Parse role definitions from config."""
    roles = {}
    for role_name, details in config.get("roles", {}).items():
        roles[role_name] = RoleDefinition(
            role_name=role_name,
            permitted_domains=details.get("permitted_domains", []),
            permitted_actions=details.get("permitted_actions", [])
        )
    return roles

def is_target_deleted(deletion_logs: List[DeletionLog], target_id: str) -> bool:
    """Check if a target has been deleted."""
    for log in deletion_logs:
        if log.target_id == target_id and log.deleted:
            return True
    return False

def is_role_authorized(role: RoleDefinition, domain: str, action: str) -> bool:
    """Check if a role is authorized for a domain and action."""
    return domain in role.permitted_domains and action in role.permitted_actions

def check_access_policy(role_name: str, boundaries: Dict[str, Any], domain: str) -> bool:
    """Check if access is allowed based on role and boundaries."""
    role = RoleDefinition(
        role_name=role_name,
        permitted_domains=boundaries.get("permitted_domains", []),
        permitted_actions=boundaries.get("permitted_actions", [])
    )
    return is_role_authorized(role, domain, "read")

def handle_malformed_deletion(entry: Dict[str, Any]):
    """Handle malformed deletion log entries."""
    logger.error(f"Malformed deletion entry: {entry}")
    # Log to error file
    with open("logs/deletion_errors.log", "a") as f:
        f.write(f"{datetime.now()}: Malformed entry - {json.dumps(entry)}\n")

def load_deletion_logs(file_path: str) -> List[DeletionLog]:
    """Load deletion logs from a file."""
    logs = []
    with open(file_path, "r") as f:
        for line in f:
            try:
                data = json.loads(line)
                logs.append(DeletionLog(**data))
            except Exception as e:
                logger.warning(f"Failed to load deletion log: {e}")
    return logs

def is_target_deleted_secure(deletion_logs: List[DeletionLog], target_id: str) -> bool:
    """Secure check for deletion (handles edge cases)."""
    try:
        return is_target_deleted(deletion_logs, target_id)
    except Exception as e:
        logger.error(f"Secure deletion check failed: {e}")
        return False  # Default to deny on error

def load_role_definitions(file_path: str) -> Dict[str, RoleDefinition]:
    """Load role definitions from a file."""
    with open(file_path, "r") as f:
        config = json.load(f)
    return parse_role_definitions(config)

def main():
    """Test rules module."""
    logger.info("Testing rules module...")
    log = DeletionLog("123", "2023-01-01", True)
    print(f"Test deletion log: {log}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
