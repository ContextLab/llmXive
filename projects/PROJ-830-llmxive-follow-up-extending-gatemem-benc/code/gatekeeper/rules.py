from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
import re
import json
import logging
from datetime import datetime

# Configure logger for this module
logger = logging.getLogger(__name__)

@dataclass
class DeletionLog:
    """
    Represents a record of a user's request to delete specific data.
    Used to enforce the 'Right to be Forgotten'.
    """
    user_id: str
    target_type: str  # e.g., 'memory', 'profile', 'interaction'
    target_id: str    # Specific identifier of the content to be deleted
    request_date: str # ISO format date string
    status: str = "pending" # pending, completed, rejected
    reason: Optional[str] = None

    def is_expired(self, current_time: datetime, retention_days: int = 30) -> bool:
        """Check if the deletion request has passed its retention window."""
        try:
            req_date = datetime.fromisoformat(self.request_date)
            delta = current_time - req_date
            return delta.days > retention_days
        except (ValueError, TypeError):
            # If date parsing fails, assume not expired to be safe
            return False

@dataclass
class RoleDefinition:
    """
    Defines access permissions for a specific role.
    Supports explicit allow/deny lists for targets or patterns.
    """
    role_name: str
    # List of regex patterns that are explicitly allowed
    allowed_patterns: List[str] = field(default_factory=list)
    # List of regex patterns that are explicitly denied
    denied_patterns: List[str] = field(default_factory=list)
    # Default behavior if no pattern matches: 'allow' or 'deny'
    default_policy: str = "deny"

    def __post_init__(self):
        # Compile regex patterns for performance
        self._compiled_allowed = []
        self._compiled_denied = []
        for p in self.allowed_patterns:
            try:
                self._compiled_allowed.append(re.compile(p, re.IGNORECASE))
            except re.error as e:
                logger.warning(f"Invalid allowed regex in role {self.role_name}: {p} ({e})")
        for p in self.denied_patterns:
            try:
                self._compiled_denied.append(re.compile(p, re.IGNORECASE))
            except re.error as e:
                logger.warning(f"Invalid denied regex in role {self.role_name}: {p} ({e})")

    def matches_allowed(self, text: str) -> bool:
        for pattern in self._compiled_allowed:
            if pattern.search(text):
                return True
        return False

    def matches_denied(self, text: str) -> bool:
        for pattern in self._compiled_denied:
            if pattern.search(text):
                return True
        return False

    def check_access(self, text: str) -> bool:
        """
        Determines if access is granted based on the text content.
        Logic:
        1. If matches denied list -> False
        2. If matches allowed list -> True
        3. Else -> default_policy
        """
        if self.matches_denied(text):
            return False
        if self.matches_allowed(text):
            return True
        return self.default_policy.lower() == "allow"

def parse_deletion_log(log_entry: Dict[str, Any]) -> Optional[DeletionLog]:
    """
    Parses a dictionary entry from the raw dataset into a DeletionLog object.
    Handles missing fields gracefully.
    """
    try:
        user_id = log_entry.get('user_id') or log_entry.get('user-id', 'unknown')
        target_type = log_entry.get('target_type') or log_entry.get('type', 'unknown')
        target_id = log_entry.get('target_id') or log_entry.get('id', '')
        request_date = log_entry.get('request_date') or log_entry.get('date', datetime.now().isoformat())
        status = log_entry.get('status', 'completed')
        reason = log_entry.get('reason')

        if not target_id:
            logger.warning("Deletion log entry missing target_id, skipping.")
            return None

        return DeletionLog(
            user_id=str(user_id),
            target_type=str(target_type),
            target_id=str(target_id),
            request_date=str(request_date),
            status=str(status),
            reason=reason
        )
    except Exception as e:
        logger.error(f"Failed to parse deletion log entry: {e}")
        return None

def parse_role_definitions(role_config: Dict[str, Any]) -> List[RoleDefinition]:
    """
    Parses a configuration dictionary into a list of RoleDefinition objects.
    Expects a list of role configs or a dictionary mapping role names to configs.
    """
    roles = []
    if isinstance(role_config, list):
        for r in role_config:
            if isinstance(r, dict):
                name = r.get('role_name') or r.get('name')
                if not name:
                    continue
                roles.append(RoleDefinition(
                    role_name=name,
                    allowed_patterns=r.get('allowed_patterns', []),
                    denied_patterns=r.get('denied_patterns', []),
                    default_policy=r.get('default_policy', 'deny')
                ))
    elif isinstance(role_config, dict):
        for name, config in role_config.items():
            if isinstance(config, dict):
                roles.append(RoleDefinition(
                    role_name=name,
                    allowed_patterns=config.get('allowed_patterns', []),
                    denied_patterns=config.get('denied_patterns', []),
                    default_policy=config.get('default_policy', 'deny')
                ))
    return roles

def is_target_deleted(
    query_text: str,
    deletion_logs: List[DeletionLog],
    current_time: Optional[datetime] = None
) -> bool:
    """
    Checks if the query text matches any active deletion log.
    Uses simple substring matching or regex if target_id contains special chars.
    Prioritizes active (non-expired) logs.
    """
    if not current_time:
        current_time = datetime.now()

    query_lower = query_text.lower()

    for log in deletion_logs:
        if log.status != "completed":
            continue
        
        if log.is_expired(current_time):
            continue

        # Check if the query text contains the target_id
        # We treat target_id as a literal string to avoid accidental regex matches
        # unless the target_id itself looks like a pattern (heuristic: contains * or .)
        target_id = log.target_id
        
        # Simple containment check
        if target_id.lower() in query_lower:
            logger.info(f"Deletion match found: target '{target_id}' in query.")
            return True

        # If target_id looks like a regex pattern (contains metacharacters)
        # try to match it (safely)
        if any(c in target_id for c in ['.', '*', '+', '?', '[', ']', '^', '$']):
            try:
                pattern = re.compile(re.escape(target_id), re.IGNORECASE) # Escape first to be safe? 
                # Actually, if the ID is a pattern, we might want to use it directly.
                # But for safety in a rule engine, usually IDs are literals.
                # Let's stick to literal match for stability unless explicitly marked.
                # However, if the data source provides regex patterns as IDs:
                # pattern = re.compile(target_id, re.IGNORECASE)
                # if pattern.search(query_text): return True
                pass
            except re.error:
                pass

    return False

def is_role_authorized(
    role_name: str,
    query_text: str,
    role_definitions: List[RoleDefinition]
) -> bool:
    """
    Checks if a specific role is authorized to access the content described by query_text.
    Returns False if role is not found (default deny).
    """
    matching_roles = [r for r in role_definitions if r.role_name == role_name]
    
    if not matching_roles:
        logger.warning(f"Role '{role_name}' not found in definitions.")
        return False

    # If multiple definitions exist (unlikely but possible), use the first one
    role = matching_roles[0]
    
    return role.check_access(query_text)

def check_access_policy(
    query_text: str,
    user_role: str,
    deletion_logs: List[DeletionLog],
    role_definitions: List[RoleDefinition],
    current_time: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Main entry point for the deterministic rule engine.
    
    Logic Flow:
    1. Check Deletion Logs first (Highest Priority). If deleted -> DENY.
    2. Check Role Definitions. If authorized -> ALLOW.
    3. Default -> DENY.
    
    Returns a dictionary with 'allowed' (bool) and 'reason' (str).
    """
    if current_time is None:
        current_time = datetime.now()

    # Priority 1: Deletion Log Enforcement
    if is_target_deleted(query_text, deletion_logs, current_time):
        return {
            "allowed": False,
            "reason": "Target found in active deletion log (Right to be Forgotten).",
            "check_type": "deletion_log"
        }

    # Priority 2: Role-Based Access Control
    if is_role_authorized(user_role, query_text, role_definitions):
        return {
            "allowed": True,
            "reason": f"Role '{user_role}' authorized for this content.",
            "check_type": "role_definition"
        }

    # Default Deny
    return {
        "allowed": False,
        "reason": f"Role '{user_role}' not authorized or default deny policy applied.",
        "check_type": "default_deny"
    }