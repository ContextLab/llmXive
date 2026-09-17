import re
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field

from code.logging_config import setup_logging

# Initialize logger
logger = setup_logging("gatekeeper_rules")

@dataclass
class RoleDefinition:
    role_name: str
    allowed_domains: Set[str]
    restricted_actions: Set[str] = field(default_factory=set)

@dataclass
class DeletionLog:
    request_id: str
    target_id: str
    timestamp: datetime
    status: str  # 'pending', 'completed', 'failed'
    requester_role: str

# Schema pattern for valid deletion log entries
# Expected format: [DELETION] YYYY-MM-DD role status
DELETION_LOG_PATTERN = re.compile(r"^\[DELETION\]\s*\d{4}-\d{2}-\d{2}\s+\w+\s+\w+$")

def parse_role_definitions(role_data: List[Dict[str, Any]]) -> List[RoleDefinition]:
    """Parse raw role data into RoleDefinition objects."""
    roles = []
    for item in role_data:
        try:
            role = RoleDefinition(
                role_name=item.get("role_name", ""),
                allowed_domains=set(item.get("allowed_domains", [])),
                restricted_actions=set(item.get("restricted_actions", []))
            )
            roles.append(role)
        except Exception as e:
            logger.warning(f"Failed to parse role definition: {item}, error: {e}")
    return roles

def parse_deletion_log(log_lines: List[str]) -> List[DeletionLog]:
    """
    Parse deletion log lines into DeletionLog objects.
    Handles malformed entries by logging them and defaulting to 'deny' logic in caller.
    """
    logs = []
    for line_no, line in enumerate(log_lines, 1):
        line = line.strip()
        if not line:
            continue

        if DELETION_LOG_PATTERN.match(line):
            # Parse valid line: [DELETION] 2023-01-01 admin completed
            parts = line.split()
            # parts[0] is [DELETION], parts[1] is date, parts[2] is role, parts[3] is status
            try:
                date_str = parts[1]
                timestamp = datetime.strptime(date_str, "%Y-%m-%d")
                log_entry = DeletionLog(
                    request_id=f"req_{line_no}",
                    target_id="unknown", # Target ID not in this simple format, usually inferred
                    timestamp=timestamp,
                    status=parts[3],
                    requester_role=parts[2]
                )
                logs.append(log_entry)
            except ValueError as e:
                logger.warning(f"Malformed date in deletion log line {line_no}: {line} - {e}")
                # Log anomaly to logs/deletion_errors.log
                logger.error(f"Anomaly: Malformed entry at line {line_no}: {line}")
        else:
            # Malformed entry: does not match schema
            # Log anomaly to logs/deletion_errors.log
            logger.error(f"Anomaly: Malformed entry at line {line_no}: {line}")
            # Do not add to logs list; caller must handle this as a 'deny' scenario
            continue

    return logs

def load_role_definitions(path: str) -> List[RoleDefinition]:
    """Load role definitions from a JSON file."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return parse_role_definitions(data)
    except FileNotFoundError:
        logger.error(f"Role definitions file not found: {path}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in role definitions: {path}, error: {e}")
        return []

def load_deletion_logs(path: str) -> List[DeletionLog]:
    """Load deletion logs from a text file (JSONL or line-based)."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        return parse_deletion_log(lines)
    except FileNotFoundError:
        logger.warning(f"Deletion log file not found: {path}. Proceeding without deletion history.")
        return []
    except Exception as e:
        logger.error(f"Error reading deletion log file {path}: {e}")
        return []

def extract_role_from_context(context: str) -> Optional[str]:
    """Extract role from context string using regex."""
    # Pattern: "role: <role_name>" or "Role: <role_name>"
    match = re.search(r"role:\s*(\w+)", context, re.IGNORECASE)
    if match:
        return match.group(1)
    return None

def is_target_deleted(target_id: str, deletion_logs: List[DeletionLog], current_time: datetime) -> bool:
    """
    Check if a target ID has been successfully deleted in the logs.
    Returns True if found with status 'completed'.
    """
    for log in deletion_logs:
        # In a real scenario, target_id would match log.target_id
        # For this schema, we assume the log implies the target associated with the request
        # If the log status is 'completed', the target is considered deleted.
        if log.status == 'completed':
            return True
    return False

def is_target_deleted_secure(target_id: str, deletion_logs: List[DeletionLog], current_time: datetime) -> Tuple[bool, bool]:
    """
    Check deletion status with anomaly handling.
    Returns (is_deleted, is_anomaly_detected).
    If logs are missing or malformed (empty list after parsing), returns (False, True) to force deny.
    """
    if not deletion_logs:
        # If no logs exist or parsing failed completely (malformed), treat as anomaly
        # to ensure safety (deny access).
        return False, True

    for log in deletion_logs:
        if log.status == 'completed':
            return True, False
    return False, False

def is_role_authorized(role_name: str, allowed_roles: Set[str]) -> bool:
    """Check if a role is in the allowed set."""
    return role_name in allowed_roles

def check_access_policy(role_name: str, domain: str, allowed_roles: Set[str], allowed_domains: Set[str]) -> bool:
    """
    Check if a role is authorized to access a specific domain.
    Returns True if authorized, False otherwise.
    """
    if not is_role_authorized(role_name, allowed_roles):
        return False
    if domain not in allowed_domains:
        return False
    return True

def main():
    """Main entry point for testing rules."""
    logging.basicConfig(level=logging.INFO)
    
    # Test data
    test_role = {"role_name": "doctor", "allowed_domains": ["medical"], "restricted_actions": []}
    test_log_line = "[DELETION] 2023-10-01 doctor completed"
    test_malformed_line = "[DELETION] 2023-10-01 doctor" # Missing status
    
    roles = parse_role_definitions([test_role])
    logs = parse_deletion_log([test_log_line, test_malformed_line])
    
    print(f"Parsed Roles: {roles}")
    print(f"Parsed Logs: {logs}")
    print(f"Malformed lines should be logged and skipped.")

if __name__ == "__main__":
    main()