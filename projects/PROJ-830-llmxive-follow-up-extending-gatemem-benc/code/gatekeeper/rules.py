"""
Gatekeeper Rules Engine
Implements regex-based rule engine for role validation and deletion log checking.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
import re
import json
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class DeletionLog:
    """Represents a single deletion log entry."""
    target_id: str
    timestamp: datetime
    reason: Optional[str] = None
    requester_id: Optional[str] = None
    is_valid: bool = True
    error_message: Optional[str] = None

@dataclass
class RoleDefinition:
    """Represents a role definition with permissions."""
    role_name: str
    allowed_domains: Set[str] = field(default_factory=set)
    allowed_targets: Set[str] = field(default_factory=set)
    denied_targets: Set[str] = field(default_factory=set)
    requires_deletion_check: bool = True
    priority: int = 0  # Higher priority rules evaluated first

def parse_deletion_log(log_entry: Dict[str, Any]) -> DeletionLog:
    """
    Parse a deletion log entry from a dictionary.
    
    Args:
        log_entry: Dictionary containing deletion log data
        
    Returns:
        DeletionLog object with parsed data
        
    Raises:
        ValueError: If the log entry is malformed and cannot be parsed
    """
    required_fields = ['target_id', 'timestamp']
    
    # Validate required fields
    for field_name in required_fields:
        if field_name not in log_entry:
            raise ValueError(f"Missing required field: {field_name}")
    
    # Parse timestamp
    timestamp_str = log_entry['timestamp']
    try:
        # Try ISO format first
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        # Try common alternative formats
        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M:%S']:
            try:
                timestamp = datetime.strptime(timestamp_str, fmt)
                break
            except ValueError:
                continue
        else:
            raise ValueError(f"Unable to parse timestamp: {timestamp_str}")
    
    return DeletionLog(
        target_id=str(log_entry['target_id']),
        timestamp=timestamp,
        reason=log_entry.get('reason'),
        requester_id=log_entry.get('requester_id'),
        is_valid=True
    )

def parse_role_definitions(role_defs: List[Dict[str, Any]]) -> List[RoleDefinition]:
    """
    Parse a list of role definitions.
    
    Args:
        role_defs: List of dictionaries containing role definition data
        
    Returns:
        List of RoleDefinition objects
    """
    roles = []
    for idx, role_data in enumerate(role_defs):
        if 'role_name' not in role_data:
            logger.warning(f"Skipping malformed role definition at index {idx}: missing role_name")
            continue
        
        # Convert string lists to sets, handling both comma-separated and list formats
        def parse_set(value):
            if isinstance(value, str):
                return set(item.strip() for item in value.split(',') if item.strip())
            elif isinstance(value, list):
                return set(str(item) for item in value)
            return set()
        
        role = RoleDefinition(
            role_name=str(role_data['role_name']),
            allowed_domains=parse_set(role_data.get('allowed_domains', [])),
            allowed_targets=parse_set(role_data.get('allowed_targets', [])),
            denied_targets=parse_set(role_data.get('denied_targets', [])),
            requires_deletion_check=bool(role_data.get('requires_deletion_check', True)),
            priority=int(role_data.get('priority', 0))
        )
        roles.append(role)
    
    # Sort by priority (highest first)
    roles.sort(key=lambda r: r.priority, reverse=True)
    return roles

def is_target_deleted(target_id: str, deletion_logs: List[DeletionLog]) -> bool:
    """
    Check if a target has been marked for deletion.
    
    Args:
        target_id: The ID of the target to check
        deletion_logs: List of deletion log entries
        
    Returns:
        True if the target has been deleted, False otherwise
    """
    for log in deletion_logs:
        if log.is_valid and log.target_id == target_id:
            return True
    return False

def is_role_authorized(role_name: str, target_id: str, domain: str, 
                     role_definitions: List[RoleDefinition]) -> bool:
    """
    Check if a role is authorized to access a specific target in a domain.
    
    Args:
        role_name: The name of the role to check
        target_id: The ID of the target being accessed
        domain: The domain context of the access request
        role_definitions: List of role definitions
        
    Returns:
        True if the role is authorized, False otherwise
    """
    # Find matching role definition
    matching_role = None
    for role in role_definitions:
        if role.role_name == role_name:
            matching_role = role
            break
    
    if not matching_role:
        # Unknown role is denied by default
        logger.warning(f"Unknown role encountered: {role_name}")
        return False
    
    # Check domain restriction
    if matching_role.allowed_domains and domain not in matching_role.allowed_domains:
        logger.debug(f"Role {role_name} not authorized for domain {domain}")
        return False
    
    # Check explicit denial
    if target_id in matching_role.denied_targets:
        logger.debug(f"Target {target_id} explicitly denied for role {role_name}")
        return False
    
    # Check explicit allowance (if allowed_targets is specified)
    if matching_role.allowed_targets and target_id not in matching_role.allowed_targets:
        logger.debug(f"Target {target_id} not in allowed list for role {role_name}")
        return False
    
    return True

def check_access_policy(role_name: str, target_id: str, domain: str,
                      deletion_logs: List[DeletionLog],
                      role_definitions: List[RoleDefinition]) -> Dict[str, Any]:
    """
    Comprehensive access policy check.
    
    Args:
        role_name: The name of the role requesting access
        target_id: The ID of the target being accessed
        domain: The domain context
        deletion_logs: List of deletion log entries
        role_definitions: List of role definitions
        
    Returns:
        Dictionary with access decision and details:
        {
            'allowed': bool,
            'reason': str,
            'checks': Dict[str, Any]
        }
    """
    result = {
        'allowed': False,
        'reason': '',
        'checks': {}
    }
    
    # Check 1: Deletion status (highest priority)
    is_deleted = is_target_deleted(target_id, deletion_logs)
    result['checks']['deletion_check'] = {
        'is_deleted': is_deleted,
        'passed': not is_deleted
    }
    
    if is_deleted:
        result['reason'] = f"Target {target_id} has been marked for deletion"
        logger.info(f"Access denied: Target {target_id} is deleted")
        return result
    
    # Check 2: Role authorization
    is_authorized = is_role_authorized(role_name, target_id, domain, role_definitions)
    result['checks']['role_authorization'] = {
        'is_authorized': is_authorized,
        'passed': is_authorized
    }
    
    if not is_authorized:
        result['reason'] = f"Role {role_name} is not authorized for target {target_id} in domain {domain}"
        logger.info(f"Access denied: Role {role_name} not authorized")
        return result
    
    # All checks passed
    result['allowed'] = True
    result['reason'] = "Access granted"
    logger.debug(f"Access granted for role {role_name} to target {target_id}")
    
    return result

def load_deletion_logs(log_file_path: str) -> List[DeletionLog]:
    """
    Load deletion logs from a JSON file.
    
    Args:
        log_file_path: Path to the JSON file containing deletion logs
        
    Returns:
        List of DeletionLog objects
    """
    logs = []
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if isinstance(data, list):
            for entry in data:
                try:
                    log = parse_deletion_log(entry)
                    logs.append(log)
                except (ValueError, KeyError) as e:
                    logger.warning(f"Skipping malformed deletion log entry: {e}")
        elif isinstance(data, dict):
            # Handle case where data is a single object or has a specific key
            entries = data.get('logs', data.get('deletion_logs', [data]))
            for entry in entries:
                try:
                    log = parse_deletion_log(entry)
                    logs.append(log)
                except (ValueError, KeyError) as e:
                    logger.warning(f"Skipping malformed deletion log entry: {e}")
                    
    except FileNotFoundError:
        logger.warning(f"Deletion log file not found: {log_file_path}")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in deletion log file {log_file_path}: {e}")
        
    return logs

def load_role_definitions(config_file_path: str) -> List[RoleDefinition]:
    """
    Load role definitions from a JSON or YAML file.
    
    Args:
        config_file_path: Path to the configuration file
        
    Returns:
        List of RoleDefinition objects
    """
    try:
        with open(config_file_path, 'r', encoding='utf-8') as f:
            if config_file_path.endswith('.yaml') or config_file_path.endswith('.yml'):
                import yaml
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
                
        role_defs = data.get('roles', data) if isinstance(data, dict) else data
        return parse_role_definitions(role_defs)
        
    except FileNotFoundError:
        logger.error(f"Role definitions file not found: {config_file_path}")
        return []
    except (json.JSONDecodeError, yaml.YAMLError) as e:
        logger.error(f"Error parsing role definitions file {config_file_path}: {e}")
        return []