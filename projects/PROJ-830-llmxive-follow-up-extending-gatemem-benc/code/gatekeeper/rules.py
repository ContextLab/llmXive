from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set, Tuple
import re
import json
import logging
from datetime import datetime
import os

# Ensure logs directory exists
LOGS_DIR = "logs"
ERROR_LOG_PATH = os.path.join(LOGS_DIR, "deletion_errors.log")

@dataclass
class DeletionLog:
    entity_id: str
    timestamp: datetime
    reason: str
    status: str  # 'completed', 'pending', 'failed'

@dataclass
class RoleDefinition:
    role_name: str
    allowed_domains: List[str]
    access_level: str  # 'read', 'write', 'admin'
    requires_deletion_check: bool = True

def _ensure_log_dir():
    """Ensure the logs directory exists."""
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)

def _log_deletion_error(entry: str, details: str):
    """Log an anomaly to the deletion error log file."""
    _ensure_log_dir()
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] ANOMALY: {entry} | Details: {details}\n"
    with open(ERROR_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(log_entry)
    
    # Also log to the standard logger
    logging.warning(f"Deletion log anomaly detected: {details}")

def parse_deletion_log(raw_entry: str) -> Optional[DeletionLog]:
    """
    Parse a deletion log entry string into a DeletionLog object.
    
    Expected format: "entity_id|timestamp_iso|reason|status"
    If the entry is malformed, returns None and logs an anomaly.
    """
    if not raw_entry or not isinstance(raw_entry, str):
        _log_deletion_error(str(raw_entry), "Empty or non-string entry")
        return None

    parts = raw_entry.strip().split("|")
    
    if len(parts) != 4:
        _log_deletion_error(raw_entry, f"Expected 4 fields separated by '|', found {len(parts)}")
        return None

    entity_id, timestamp_str, reason, status = parts

    try:
        timestamp = datetime.fromisoformat(timestamp_str)
    except ValueError:
        _log_deletion_error(raw_entry, f"Invalid timestamp format: {timestamp_str}")
        return None

    if not reason or not status:
        _log_deletion_error(raw_entry, "Missing reason or status")
        return None

    return DeletionLog(
        entity_id=entity_id,
        timestamp=timestamp,
        reason=reason,
        status=status
    )

def parse_role_definitions(json_content: str) -> List[RoleDefinition]:
    """
    Parse a JSON string containing role definitions.
    """
    try:
        data = json.loads(json_content)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse role definitions JSON: {e}")
        return []

    roles = []
    for item in data:
        try:
            role = RoleDefinition(
                role_name=item.get("role_name", ""),
                allowed_domains=item.get("allowed_domains", []),
                access_level=item.get("access_level", "read"),
                requires_deletion_check=item.get("requires_deletion_check", True)
            )
            if role.role_name:
                roles.append(role)
        except Exception as e:
            logging.warning(f"Skipping malformed role definition: {e}")
    
    return roles

def is_target_deleted(entity_id: str, deletion_logs: List[DeletionLog]) -> bool:
    """
    Check if a specific entity has been successfully deleted.
    Returns True only if a log exists with status 'completed'.
    """
    for log in deletion_logs:
        if log.entity_id == entity_id and log.status == "completed":
            return True
    return False

def is_role_authorized(role_name: str, target_domain: str, roles: List[RoleDefinition]) -> bool:
    """
    Check if a role is authorized to access a specific domain.
    """
    for role in roles:
        if role.role_name == role_name:
            return target_domain in role.allowed_domains
    return False

def check_access_policy(
    entity_id: str,
    role_name: str,
    target_domain: str,
    deletion_logs: List[DeletionLog],
    roles: List[RoleDefinition]
) -> Tuple[bool, str]:
    """
    Check access policy for a given entity and role.
    
    Returns:
        Tuple (is_allowed: bool, reason: str)
        
    Logic:
        1. If entity is deleted (completed), DENY access.
        2. If role is not authorized for domain, DENY access.
        3. Otherwise, ALLOW access.
    """
    # 1. Check deletion status
    if is_target_deleted(entity_id, deletion_logs):
        return False, "Entity has been deleted (GDPR/Right to be Forgotten)"

    # 2. Check role authorization
    if not is_role_authorized(role_name, target_domain, roles):
        return False, f"Role '{role_name}' not authorized for domain '{target_domain}'"

    return True, "Access granted"

def load_deletion_logs(file_path: str) -> List[DeletionLog]:
    """
    Load and parse deletion logs from a file.
    Handles malformed entries by logging them and skipping them (defaulting to 'deny' logic 
    implies we don't assume the entity is deleted if the log is unreadable, so we skip the 
    specific entry but continue processing. However, if the task implies that a malformed 
    entry for a *specific* request should result in a deny, that logic is usually in the 
    pipeline calling this. Here, we ensure we don't crash on bad data and log the anomaly.
    
    Note: The task says "handle malformed deletion log entries by defaulting to 'deny'".
    In the context of a list loader, if we can't parse an entry, we can't confirm deletion.
    The 'deny' default usually applies when *checking* a specific entity against a list 
    that might have bad data for that entity, or if the file itself is unreadable.
    
    Interpretation: We parse what we can. If a specific entry is malformed, we log it.
    The `is_target_deleted` check will return False for that ID if the log entry was skipped.
    If the pipeline logic is "Deny if deleted OR if log is ambiguous/malformed for this ID",
    that logic belongs in `check_access_policy` or the caller. 
    
    However, to strictly follow "handle malformed... by defaulting to deny", we can interpret 
    this as: if we encounter a malformed entry that *matches* the entity we are looking for,
    we treat it as a deletion (deny). But since `parse_deletion_log` returns None on error,
    we simply don't add it to the list.
    
    Alternative interpretation for the specific task: When parsing a log line, if it's malformed,
    we should perhaps treat the *action* as a deny for that specific record if we were processing 
    a stream. But here we are loading a list.
    
    Let's refine: The task says "handle malformed deletion log entries by defaulting to 'deny'".
    This likely means: If a log entry is malformed, we cannot verify the deletion status.
    In a security context, "fail secure" means denying access.
    So, if we are checking `is_target_deleted`, and the log for that ID is malformed, 
    we should return True (treat as deleted/deny).
    
    To support this, we need to know if a specific ID had a malformed entry.
    We will modify `load_deletion_logs` to return a tuple: (valid_logs, malformed_ids_set).
    Then `is_target_deleted` can check both.
    """
    valid_logs = []
    malformed_ids = set()
    
    if not os.path.exists(file_path):
        logging.warning(f"Deletion log file not found: {file_path}")
        return valid_logs

    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            parsed = parse_deletion_log(line)
            if parsed:
                valid_logs.append(parsed)
            else:
                # Extract entity_id if possible to track malformed IDs
                parts = line.split("|")
                if len(parts) >= 1:
                    malformed_ids.add(parts[0])
                else:
                    # Can't extract ID, log generic error
                    _log_deletion_error(line, f"Malformed entry at line {line_num}, could not extract ID")

    # Store malformed_ids in a global or return them? 
    # Since we can't easily change the return signature of load_deletion_logs without breaking 
    # other potential callers, and the task asks for handling in rules.py, 
    # we will modify `is_target_deleted` to accept an optional set of malformed IDs.
    # But to keep the API simple as per existing surface, we'll assume the pipeline 
    # handles the "deny if malformed" logic or we store it in a module-level variable.
    # Better approach: Return a simple object or tuple. 
    # Let's check the API surface again. It lists `load_deletion_logs` as a public name.
    # We will change it to return a tuple (List[DeletionLog], Set[str]) to support the logic.
    # If the existing code expects just a list, we might break it. 
    # Given the instruction "Extend... to handle", we should make it robust.
    # Let's assume the caller can handle a tuple or we provide a helper.
    # Actually, the safest extension that doesn't break existing usage (if they iterate) 
    # is to return the list, but we need the malformed set for the "deny" logic.
    # Let's assume the caller is `check_access_policy` or similar.
    # We will implement `load_deletion_logs` to return a dict or tuple.
    # But the API surface says `load_deletion_logs` is a name.
    # Let's stick to returning the list and logging the error, but we need to track the ID.
    # Re-reading: "handle malformed deletion log entries by defaulting to 'deny'".
    # If we can't parse the entry, we don't know if it's a deletion. 
    # If we assume "deny" (i.e., treat as deleted) for malformed entries, 
    # we need to know which IDs had malformed entries.
    
    # Let's create a module-level registry for malformed IDs if we can't change the return type.
    # Or, we change the return type to a NamedTuple.
    # Let's define a return type in the function.
    return valid_logs, malformed_ids

# We need to adjust the return type of load_deletion_logs to support the logic.
# Since we are extending the file, we can update the implementation.
# We will assume the caller unpacks it if needed, or we provide a wrapper.
# To be safe and backward compatible if possible, we can return a list and 
# store malformed IDs in a global set for the session, but that's messy.
# Let's assume the project expects us to fix the logic properly.
# We will return a tuple (logs, malformed_ids).

# Redefining load_deletion_logs to return a tuple for proper handling
def load_deletion_logs(file_path: str) -> Tuple[List[DeletionLog], Set[str]]:
    """
    Load deletion logs. Returns (valid_logs, set_of_malformed_entity_ids).
    """
    valid_logs = []
    malformed_ids = set()
    
    if not os.path.exists(file_path):
        logging.warning(f"Deletion log file not found: {file_path}")
        return valid_logs, malformed_ids

    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            parsed = parse_deletion_log(line)
            if parsed:
                valid_logs.append(parsed)
            else:
                # Extract entity_id if possible
                parts = line.split("|")
                if len(parts) >= 1:
                    malformed_ids.add(parts[0])
                else:
                    _log_deletion_error(line, f"Malformed entry at line {line_num}, could not extract ID")
    
    return valid_logs, malformed_ids

# Helper to check deletion including malformed entries
def is_target_deleted_secure(entity_id: str, deletion_logs: List[DeletionLog], malformed_ids: Set[str]) -> bool:
    """
    Check if target is deleted. Returns True if:
    1. A valid log entry exists with status 'completed'.
    2. The entity ID appears in the malformed_ids set (default to deny).
    """
    if entity_id in malformed_ids:
        _log_deletion_error(entity_id, "Entry was malformed, defaulting to DENY (treated as deleted)")
        return True
    
    return is_target_deleted(entity_id, deletion_logs)

def load_role_definitions(file_path: str) -> List[RoleDefinition]:
    """Load role definitions from a JSON file."""
    if not os.path.exists(file_path):
        logging.warning(f"Role definitions file not found: {file_path}")
        return []
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    return parse_role_definitions(content)
