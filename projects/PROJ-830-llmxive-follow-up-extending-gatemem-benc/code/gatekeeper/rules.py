import re
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field

from code.logging_config import setup_logging

# Initialize logger
logger = setup_logging("gatekeeper.rules")

@dataclass
class DeletionLog:
    """Represents a deletion request log entry."""
    log_id: str
    timestamp: datetime
    target_id: str
    status: str  # 'completed', 'pending', 'failed'
    reason: Optional[str] = None

@dataclass
class RoleDefinition:
    """Represents a role definition with access policies."""
    role_name: str
    allowed_domains: Set[str]
    allowed_targets: Set[str]
    restrictions: Dict[str, Any] = field(default_factory=dict)

def parse_role_definitions(role_text: str) -> List[RoleDefinition]:
    """
    Parse role definitions from a text block.
    Expects lines like: "role: admin | domains: medical,office | targets: user_data"
    """
    roles = []
    pattern = re.compile(
        r"role:\s*(\w+)\s*\|\s*domains:\s*([^\|]+)\s*\|\s*targets:\s*(.+)",
        re.IGNORECASE
    )
    
    for line in role_text.splitlines():
        line = line.strip()
        if not line:
            continue
        
        match = pattern.match(line)
        if match:
            role_name = match.group(1)
            domains = {d.strip().lower() for d in match.group(2).split(",")}
            targets = {t.strip() for t in match.group(3).split(",")}
            
            roles.append(RoleDefinition(
                role_name=role_name,
                allowed_domains=domains,
                allowed_targets=targets
            ))
        else:
            logger.warning(f"Malformed role definition line: {line}")
    
    return roles

def parse_deletion_log(log_text: str) -> List[DeletionLog]:
    """
    Parse deletion logs from a text block.
    Expects lines like: "log_id: 123 | timestamp: 2023-01-01T00:00:00 | target: user_456 | status: completed"
    
    Handles malformed entries by logging the error and defaulting to 'deny' status for the entry,
    effectively treating the target as non-deleted (safe default) but flagging the anomaly.
    """
    logs = []
    pattern = re.compile(
        r"log_id:\s*(\w+)\s*\|\s*timestamp:\s*([^\|]+)\s*\|\s*target:\s*([^\|]+)\s*\|\s*status:\s*(\w+)",
        re.IGNORECASE
    )
    
    for line_num, line in enumerate(log_text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        
        match = pattern.match(line)
        if match:
            try:
                timestamp_str = match.group(2).strip()
                # Attempt to parse timestamp
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                
                logs.append(DeletionLog(
                    log_id=match.group(1),
                    timestamp=timestamp,
                    target_id=match.group(3).strip(),
                    status=match.group(4).strip().lower()
                ))
            except ValueError as e:
                logger.error(f"Malformed deletion log entry at line {line_num}: {line}. Error: {e}. Defaulting to 'deny' status (safe).")
                # Anomaly handling: Log to specific file and default to 'deny' (treat as not deleted)
                _log_anomaly_to_file(line, line_num, str(e))
                # Create a dummy entry with 'deny' status to ensure the logic handles it safely
                logs.append(DeletionLog(
                    log_id=f"malformed_{line_num}",
                    timestamp=datetime.now(),
                    target_id=match.group(3).strip() if match.group(3) else "unknown",
                    status="deny" # Default to deny for safety
                ))
        else:
            # Completely malformed line that doesn't match pattern
            logger.error(f"Malformed deletion log entry at line {line_num}: {line}. Skipping.")
            _log_anomaly_to_file(line, line_num, "Pattern mismatch")
    
    return logs

def _log_anomaly_to_file(line: str, line_num: int, error_reason: str):
    """
    Logs anomaly details to logs/deletion_errors.log.
    """
    log_dir = "logs"
    log_file_path = f"{log_dir}/deletion_errors.log"
    
    try:
        import os
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        with open(log_file_path, "a", encoding="utf-8") as f:
            timestamp = datetime.now().isoformat()
            f.write(f"[{timestamp}] ANOMALY at line {line_num}: {error_reason}\n")
            f.write(f"  Content: {line}\n")
            f.write("-" * 40 + "\n")
    except Exception as e:
        logger.error(f"Failed to write anomaly to log file: {e}")

def load_role_definitions(file_path: str) -> List[RoleDefinition]:
    """Load role definitions from a JSON file."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        roles = []
        for item in data:
            roles.append(RoleDefinition(
                role_name=item['role_name'],
                allowed_domains=set(item.get('allowed_domains', [])),
                allowed_targets=set(item.get('allowed_targets', [])),
                restrictions=item.get('restrictions', {})
            ))
        return roles
    except FileNotFoundError:
        logger.error(f"Role definitions file not found: {file_path}")
        return []
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in role definitions file: {file_path}")
        return []

def load_deletion_logs(file_path: str) -> List[DeletionLog]:
    """Load deletion logs from a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logs = []
        for item in data:
            logs.append(DeletionLog(
                log_id=item['log_id'],
                timestamp=datetime.fromisoformat(item['timestamp']),
                target_id=item['target_id'],
                status=item['status'],
                reason=item.get('reason')
            ))
        return logs
    except FileNotFoundError:
        logger.error(f"Deletion logs file not found: {file_path}")
        return []
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in deletion logs file: {file_path}")
        return []

def is_target_deleted(target_id: str, deletion_logs: List[DeletionLog], current_time: datetime) -> bool:
    """
    Check if a target has been successfully deleted based on logs.
    Returns True only if a log entry exists with status 'completed'.
    """
    for log in deletion_logs:
        if log.target_id == target_id and log.status == 'completed':
            return True
    return False

def is_target_deleted_secure(target_id: str, deletion_logs: List[DeletionLog], current_time: datetime) -> Tuple[bool, bool]:
    """
    Secure check for deletion with time validity.
    Returns True only if deletion is completed and within a valid window (if applicable).
    For now, simply checks completion status.
    """
    return is_target_deleted(target_id, deletion_logs)

def extract_role_from_context(context: str) -> Optional[str]:
    """
    Extract role from context string using regex.
    Pattern: "role: <role_name>"
    """
    pattern = re.compile(r"role:\s*(\w+)", re.IGNORECASE)
    match = pattern.search(context)
    if match:
        return match.group(1)
    return None

def is_role_authorized(role_name: str, target_id: str, roles: List[RoleDefinition]) -> bool:
    """
    Check if a role is authorized to access a specific target.
    """
    for role in roles:
        if role.role_name.lower() == role_name.lower():
            # Check if target is in allowed_targets
            if target_id in role.allowed_targets:
                return True
            return False
    return False

def check_access_policy(
    role_name: str,
    target_id: str,
    domain: str,
    roles: List[RoleDefinition],
    deletion_logs: List[DeletionLog]
) -> Tuple[bool, str]:
    """
    Comprehensive access policy check.
    Returns (is_allowed, reason)
    
    Logic:
    1. Check if target is deleted (if so, deny).
    2. Check if role is authorized for the target.
    3. Check domain restrictions.
    """
    # 1. Check deletion status
    if is_target_deleted(target_id, deletion_logs):
        return False, "Target has been deleted"

    # 2. Check role authorization
    if not is_role_authorized(role_name, target_id, roles):
        return False, f"Role '{role_name}' not authorized for target '{target_id}'"

    # 3. Check domain (if role has domain restrictions)
    for role in roles:
        if role.role_name.lower() == role_name.lower():
            if role.allowed_domains and domain.lower() not in role.allowed_domains:
                return False, f"Domain '{domain}' not allowed for role '{role_name}'"
            break

    return True, "Access granted"

def main():
    """Main entry point for testing the rules module."""
    # Example usage
    role_text = """
    role: doctor | domains: medical | targets: patient_records
    role: admin | domains: medical,office | targets: all
    """
    
    log_text = """
    log_id: 1 | timestamp: 2023-01-01T10:00:00 | target: patient_123 | status: completed
    log_id: 2 | timestamp: 2023-01-02T11:00:00 | target: patient_456 | status: pending
    """
    
    roles = parse_role_definitions(role_text)
    logs = parse_deletion_log(log_text)
    
    print(f"Parsed {len(roles)} roles and {len(logs)} logs.")
    
    # Test access
    allowed, reason = check_access_policy("doctor", "patient_123", "medical", roles, logs)
    print(f"Access for doctor on patient_123: {allowed} - {reason}")
    
    allowed, reason = check_access_policy("doctor", "patient_456", "medical", roles, logs)
    print(f"Access for doctor on patient_456: {allowed} - {reason}")

if __name__ == "__main__":
    main()