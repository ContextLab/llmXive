# llmXive v2.0: Complete Redesign and Architectural Overhaul (Refined)

**Project ID**: LLMX-2024-001  
**Date**: 2025-07-06  
**Status**: Design Phase - Refined  
**Contributors**: Claude (Sonnet 4), Jeremy Manning  
**Reviewer**: Gemini (via Claude Code)

## Executive Summary

This document outlines a comprehensive, security-focused redesign of the llmXive system based on expert review feedback. The refined v2.0 architecture introduces a hybrid database-filesystem approach, robust security measures, and a phased implementation strategy to minimize migration risks while maximizing scalability and maintainability.

## Key Architectural Changes from Initial Design

### 1. **Hybrid Database-Filesystem Architecture**
- **Database**: SQLite/PostgreSQL for metadata, status, dependencies, and metrics
- **Filesystem**: For large artifacts (code, data, papers, documents)
- **Benefits**: Transactional integrity, efficient querying, better performance

### 2. **Security-First Design**
- Secure API backend (no direct filesystem access from web)
- Code execution disabled by default
- Comprehensive secret management
- Path traversal attack prevention

### 3. **Phased Migration Strategy**
- Parallel v1/v2 operation during transition
- Incremental project migration with validation
- No "big bang" system switchover

## Revised Architecture

### 1. **Database Schema**

```sql
-- Projects table
CREATE TABLE projects (
    id VARCHAR(255) PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    status ENUM('backlog', 'ready', 'in_progress', 'review', 'completed', 'archived') NOT NULL,
    priority ENUM('low', 'medium', 'high', 'critical') NOT NULL,
    created_date TIMESTAMP NOT NULL,
    last_updated TIMESTAMP NOT NULL,
    estimated_completion DATE,
    filesystem_path VARCHAR(500) NOT NULL,
    version INTEGER DEFAULT 2,  -- v1 or v2 project
    INDEX idx_status (status),
    INDEX idx_priority (priority),
    INDEX idx_updated (last_updated)
);

-- Project contributors
CREATE TABLE project_contributors (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    project_id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    role ENUM('primary_researcher', 'supervisor', 'reviewer', 'collaborator') NOT NULL,
    type ENUM('ai', 'human') NOT NULL,
    contributions JSON,  -- ["design", "implementation", "analysis"]
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    INDEX idx_project_contributor (project_id, name)
);

-- Project phases
CREATE TABLE project_phases (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    project_id VARCHAR(255) NOT NULL,
    phase_name ENUM('idea', 'technical_design', 'implementation_plan', 'implementation', 'paper', 'review') NOT NULL,
    status ENUM('pending', 'in_progress', 'completed', 'blocked') NOT NULL,
    progress DECIMAL(3,2) DEFAULT 0.00,  -- 0.00 to 1.00
    completed_date TIMESTAMP NULL,
    artifacts JSON,  -- ["technical_design/main.md", "implementation_plan/main.md"]
    reviews_required INTEGER DEFAULT 0,
    reviews_completed INTEGER DEFAULT 0,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    UNIQUE KEY unique_project_phase (project_id, phase_name),
    INDEX idx_phase_status (phase_name, status)
);

-- Project dependencies
CREATE TABLE project_dependencies (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    project_id VARCHAR(255) NOT NULL,
    depends_on_project_id VARCHAR(255) NOT NULL,
    dependency_type ENUM('builds_on', 'collaborates_with', 'requires', 'blocks') NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_project_id) REFERENCES projects(id) ON DELETE CASCADE,
    UNIQUE KEY unique_dependency (project_id, depends_on_project_id, dependency_type)
);

-- Project metrics
CREATE TABLE project_metrics (
    project_id VARCHAR(255) PRIMARY KEY,
    lines_of_code INTEGER DEFAULT 0,
    test_coverage DECIMAL(4,3) DEFAULT 0.000,
    paper_pages INTEGER DEFAULT 0,
    citations INTEGER DEFAULT 0,
    reproducibility_score DECIMAL(4,3) DEFAULT 0.000,
    last_calculated TIMESTAMP NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- Task execution log
CREATE TABLE task_executions (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    project_id VARCHAR(255) NOT NULL,
    task_type VARCHAR(100) NOT NULL,
    model_id VARCHAR(100) NOT NULL,
    personality VARCHAR(100),
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP NULL,
    status ENUM('running', 'completed', 'failed', 'cancelled') NOT NULL,
    error_message TEXT NULL,
    artifacts_created JSON,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    INDEX idx_task_status (status, started_at)
);
```

### 2. **Secure API Backend Architecture**

```
api_backend/
├── src/
│   ├── controllers/
│   │   ├── projects_controller.py
│   │   ├── artifacts_controller.py
│   │   ├── tasks_controller.py
│   │   └── auth_controller.py
│   ├── services/
│   │   ├── project_service.py
│   │   ├── artifact_service.py
│   │   ├── security_service.py
│   │   └── filesystem_service.py
│   ├── models/
│   │   ├── database_models.py
│   │   └── validation_schemas.py
│   ├── middleware/
│   │   ├── auth_middleware.py
│   │   ├── rate_limiting.py
│   │   └── security_headers.py
│   └── utils/
│       ├── path_validator.py
│       ├── encryption.py
│       └── audit_logger.py
├── config/
│   ├── security_config.yaml
│   ├── api_config.yaml
│   └── database_config.yaml
└── tests/
    ├── security_tests/
    ├── integration_tests/
    └── performance_tests/
```

#### **Secure Path Validation**

```python
import os
import re
from pathlib import Path
from typing import Optional

class SecurePathValidator:
    """Prevents path traversal attacks and ensures safe filesystem access"""
    
    def __init__(self, base_project_dir: str):
        self.base_dir = Path(base_project_dir).resolve()
        self.allowed_extensions = {
            '.md', '.txt', '.py', '.js', '.yaml', '.yml', '.json',
            '.tex', '.pdf', '.png', '.jpg', '.jpeg', '.svg',
            '.csv', '.tsv', '.h5', '.pkl', '.npz'
        }
        self.forbidden_patterns = [
            r'\.\./',  # Parent directory traversal
            r'~/',     # Home directory access
            r'/etc/',  # System directory access
            r'/var/',  # System directory access
            r'/usr/',  # System directory access
        ]
    
    def validate_project_path(self, project_id: str, relative_path: str) -> Optional[Path]:
        """Validate and resolve a project-relative path safely"""
        
        # Sanitize project ID
        if not re.match(r'^[A-Za-z0-9\-_]+$', project_id):
            raise SecurityError("Invalid project ID format")
        
        # Check for forbidden patterns
        for pattern in self.forbidden_patterns:
            if re.search(pattern, relative_path):
                raise SecurityError(f"Forbidden path pattern detected: {pattern}")
        
        # Construct and resolve the full path
        project_dir = self.base_dir / project_id
        full_path = (project_dir / relative_path).resolve()
        
        # Ensure the resolved path is still within the project directory
        if not str(full_path).startswith(str(project_dir)):
            raise SecurityError("Path traversal attack detected")
        
        # Check file extension
        if full_path.suffix.lower() not in self.allowed_extensions:
            raise SecurityError(f"File type not allowed: {full_path.suffix}")
        
        return full_path if full_path.exists() else None

class SecurityError(Exception):
    """Custom exception for security violations"""
    pass
```

### 3. **Authentication and Authorization System**

```python
from enum import Enum
from typing import Set, Dict, Any

class Role(Enum):
    ADMIN = "admin"
    RESEARCHER = "researcher" 
    REVIEWER = "reviewer"
    VIEWER = "viewer"

class Permission(Enum):
    # Project permissions
    CREATE_PROJECT = "create_project"
    DELETE_PROJECT = "delete_project"
    MODIFY_PROJECT = "modify_project"
    VIEW_PROJECT = "view_project"
    
    # Task permissions
    EXECUTE_TASK = "execute_task"
    CANCEL_TASK = "cancel_task"
    
    # Review permissions
    SUBMIT_REVIEW = "submit_review"
    APPROVE_REVIEW = "approve_review"
    
    # System permissions
    MANAGE_MODELS = "manage_models"
    MANAGE_USERS = "manage_users"
    VIEW_SYSTEM_LOGS = "view_system_logs"

class RolePermissions:
    ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
        Role.ADMIN: {
            Permission.CREATE_PROJECT, Permission.DELETE_PROJECT, Permission.MODIFY_PROJECT, Permission.VIEW_PROJECT,
            Permission.EXECUTE_TASK, Permission.CANCEL_TASK,
            Permission.SUBMIT_REVIEW, Permission.APPROVE_REVIEW,
            Permission.MANAGE_MODELS, Permission.MANAGE_USERS, Permission.VIEW_SYSTEM_LOGS
        },
        Role.RESEARCHER: {
            Permission.CREATE_PROJECT, Permission.MODIFY_PROJECT, Permission.VIEW_PROJECT,
            Permission.EXECUTE_TASK, Permission.CANCEL_TASK,
            Permission.SUBMIT_REVIEW
        },
        Role.REVIEWER: {
            Permission.VIEW_PROJECT,
            Permission.SUBMIT_REVIEW, Permission.APPROVE_REVIEW
        },
        Role.VIEWER: {
            Permission.VIEW_PROJECT
        }
    }
    
    @classmethod
    def has_permission(cls, role: Role, permission: Permission) -> bool:
        return permission in cls.ROLE_PERMISSIONS.get(role, set())

class AuthenticationService:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
    
    def authenticate_user(self, username: str, password: str) -> Optional[str]:
        """Authenticate user and return session token"""
        # Implementation would use secure password hashing
        # and potentially integrate with external auth providers
        pass
    
    def authorize_action(self, session_token: str, permission: Permission) -> bool:
        """Check if user has permission for a specific action"""
        session = self.active_sessions.get(session_token)
        if not session:
            return False
        
        user_role = Role(session['role'])
        return RolePermissions.has_permission(user_role, permission)
```

### 4. **Enhanced Model Security Configuration**

```yaml
# models/registry/claude-3.5-sonnet.md (security section)
security_configuration:
  code_execution:
    enabled: false  # SECURE BY DEFAULT
    allowed_languages: []
    sandbox_enabled: true
    execution_timeout: 30
    memory_limit: "512MB"
  
  file_access:
    read_only: true
    allowed_directories: ["project_files", "shared_resources"]
    forbidden_paths: ["/etc", "/var", "/usr", "~"]
    max_file_size: "100MB"
  
  external_access:
    internet_access: false  # Default to no internet
    allowed_domains: []
    rate_limits:
      requests_per_minute: 10
      requests_per_hour: 100
  
  sensitive_data:
    scan_for_secrets: true
    block_api_keys: true
    block_passwords: true
    block_personal_info: true

audit_configuration:
  log_all_interactions: true
  log_file_access: true
  log_code_execution: true
  retention_days: 365
```

### 5. **Secret Management System**

```python
import os
import json
from cryptography.fernet import Fernet
from typing import Dict, Any, Optional

class SecretManager:
    """Secure secret management for API keys and sensitive configuration"""
    
    def __init__(self, encryption_key: Optional[str] = None):
        self.encryption_key = encryption_key or os.environ.get('LLMXIVE_ENCRYPTION_KEY')
        if not self.encryption_key:
            raise ValueError("Encryption key must be provided via environment variable LLMXIVE_ENCRYPTION_KEY")
        
        self.cipher = Fernet(self.encryption_key.encode())
        self.secrets_cache: Dict[str, Any] = {}
    
    def store_secret(self, key: str, value: str, encrypted_file_path: str) -> None:
        """Store an encrypted secret to file"""
        encrypted_value = self.cipher.encrypt(value.encode())
        
        # Load existing secrets or create new file
        secrets = {}
        if os.path.exists(encrypted_file_path):
            secrets = self.load_secrets_file(encrypted_file_path)
        
        secrets[key] = encrypted_value.decode()
        
        with open(encrypted_file_path, 'w') as f:
            json.dump(secrets, f)
    
    def get_secret(self, key: str, encrypted_file_path: str) -> Optional[str]:
        """Retrieve and decrypt a secret"""
        cache_key = f"{encrypted_file_path}:{key}"
        if cache_key in self.secrets_cache:
            return self.secrets_cache[cache_key]
        
        secrets = self.load_secrets_file(encrypted_file_path)
        encrypted_value = secrets.get(key)
        
        if not encrypted_value:
            return None
        
        decrypted_value = self.cipher.decrypt(encrypted_value.encode()).decode()
        self.secrets_cache[cache_key] = decrypted_value
        
        return decrypted_value
    
    def load_secrets_file(self, encrypted_file_path: str) -> Dict[str, str]:
        """Load and parse encrypted secrets file"""
        if not os.path.exists(encrypted_file_path):
            return {}
        
        with open(encrypted_file_path, 'r') as f:
            return json.load(f)

# Usage example
secret_manager = SecretManager()

# Store secrets (typically done during setup)
secret_manager.store_secret(
    "anthropic_api_key", 
    "sk-ant-xxxxx", 
    "config/encrypted_secrets.json"
)

# Retrieve secrets (during operation)
api_key = secret_manager.get_secret(
    "anthropic_api_key", 
    "config/encrypted_secrets.json"
)
```

### 6. **Enhanced Validation Engine with Dependency Checking**

```python
import networkx as nx
from typing import List, Dict, Set, Tuple

class DependencyValidator:
    """Validates project dependencies and detects circular dependencies"""
    
    def __init__(self):
        self.dependency_graph = nx.DiGraph()
    
    def build_dependency_graph(self, projects: List[Dict]) -> None:
        """Build a directed graph of project dependencies"""
        self.dependency_graph.clear()
        
        # Add all projects as nodes
        for project in projects:
            self.dependency_graph.add_node(project['id'])
        
        # Add dependency edges
        for project in projects:
            project_id = project['id']
            dependencies = project.get('dependencies', [])
            
            for dep in dependencies:
                dep_project_id = dep.get('depends_on_project_id')
                if dep_project_id and self.dependency_graph.has_node(dep_project_id):
                    self.dependency_graph.add_edge(project_id, dep_project_id)
    
    def detect_circular_dependencies(self) -> List[List[str]]:
        """Detect and return all circular dependency cycles"""
        try:
            # NetworkX will raise an exception if cycles exist
            cycles = list(nx.simple_cycles(self.dependency_graph))
            return cycles
        except nx.NetworkXError:
            return []
    
    def get_dependency_order(self) -> List[str]:
        """Get topologically sorted order for project processing"""
        try:
            return list(nx.topological_sort(self.dependency_graph))
        except nx.NetworkXError as e:
            # Circular dependency detected
            cycles = self.detect_circular_dependencies()
            raise ValidationError(f"Circular dependencies detected: {cycles}")
    
    def validate_dependency_integrity(self, projects: List[Dict]) -> ValidationResult:
        """Comprehensive dependency validation"""
        errors = []
        warnings = []
        
        self.build_dependency_graph(projects)
        
        # Check for circular dependencies
        cycles = self.detect_circular_dependencies()
        if cycles:
            for cycle in cycles:
                errors.append(f"Circular dependency detected: {' -> '.join(cycle + [cycle[0]])}")
        
        # Check for missing dependencies
        for project in projects:
            project_id = project['id']
            dependencies = project.get('dependencies', [])
            
            for dep in dependencies:
                dep_project_id = dep.get('depends_on_project_id')
                if dep_project_id and not self.dependency_graph.has_node(dep_project_id):
                    errors.append(f"Project {project_id} depends on non-existent project {dep_project_id}")
        
        # Check for orphaned projects (no dependents and not essential)
        essential_projects = {'PROJ-000-base-framework'}  # Define essential projects
        
        for node in self.dependency_graph.nodes():
            if (node not in essential_projects and 
                self.dependency_graph.in_degree(node) == 0 and 
                self.dependency_graph.out_degree(node) == 0):
                warnings.append(f"Project {node} has no dependencies or dependents")
        
        return ValidationResult(
            checker='dependency',
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
```

### 7. **Notification System**

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from enum import Enum

class NotificationType(Enum):
    REVIEW_REQUIRED = "review_required"
    PHASE_COMPLETED = "phase_completed"
    TASK_FAILED = "task_failed"
    PROJECT_CREATED = "project_created"
    DEPENDENCY_BLOCKED = "dependency_blocked"

class NotificationChannel(ABC):
    @abstractmethod
    async def send_notification(self, recipients: List[str], message: str, data: Dict[str, Any]) -> bool:
        pass

class EmailNotificationChannel(NotificationChannel):
    def __init__(self, smtp_config: Dict[str, str]):
        self.smtp_config = smtp_config
    
    async def send_notification(self, recipients: List[str], message: str, data: Dict[str, Any]) -> bool:
        # Implementation for email notifications
        pass

class SlackNotificationChannel(NotificationChannel):
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    async def send_notification(self, recipients: List[str], message: str, data: Dict[str, Any]) -> bool:
        # Implementation for Slack notifications
        pass

class NotificationService:
    def __init__(self):
        self.channels: Dict[str, NotificationChannel] = {}
        self.notification_rules: Dict[NotificationType, Dict[str, Any]] = {}
    
    def register_channel(self, name: str, channel: NotificationChannel) -> None:
        self.channels[name] = channel
    
    async def notify(self, notification_type: NotificationType, project_id: str, data: Dict[str, Any]) -> None:
        """Send notifications based on type and configured rules"""
        rules = self.notification_rules.get(notification_type, {})
        
        if not rules.get('enabled', False):
            return
        
        message = self.generate_message(notification_type, project_id, data)
        recipients = await self.get_recipients(notification_type, project_id, data)
        
        for channel_name in rules.get('channels', []):
            channel = self.channels.get(channel_name)
            if channel:
                await channel.send_notification(recipients, message, data)
    
    def generate_message(self, notification_type: NotificationType, project_id: str, data: Dict[str, Any]) -> str:
        """Generate notification message based on type and data"""
        templates = {
            NotificationType.REVIEW_REQUIRED: "Project {project_id} requires review for {phase}",
            NotificationType.PHASE_COMPLETED: "Project {project_id} completed phase {phase}",
            NotificationType.TASK_FAILED: "Task {task_type} failed for project {project_id}: {error}",
        }
        
        template = templates.get(notification_type, "Notification for project {project_id}")
        return template.format(project_id=project_id, **data)
    
    async def get_recipients(self, notification_type: NotificationType, project_id: str, data: Dict[str, Any]) -> List[str]:
        """Determine notification recipients based on project and notification type"""
        # Query database for project contributors and their notification preferences
        # Return list of email addresses or user IDs
        pass
```

## Revised Implementation Plan

### **MVP Phase (8-10 weeks)**
**Goal**: Establish foundation with immediate value

1. **Database and API Backend (Weeks 1-3)**
   - Set up database schema
   - Implement secure API backend
   - Create basic authentication system
   - Implement path validation and security measures

2. **Project Migration System (Weeks 3-4)**
   - Build robust migration scripts with validation
   - Implement parallel v1/v2 operation
   - Create rollback mechanisms
   - Test migration on sample projects

3. **Basic Website Integration (Weeks 5-6)**
   - Update website to use secure API
   - Implement project browsing with v1/v2 support
   - Basic artifact viewing
   - Simple search functionality

4. **Core Validation Framework (Weeks 7-8)**
   - Implement structure and dependency validation
   - Set up automated testing suite
   - Create CI/CD pipeline for system itself
   - Basic notification system

### **Full System Phase (12-16 additional weeks)**

5. **Enhanced Orchestrator (Weeks 9-12)**
   - Complete task management system
   - Model registry and selection
   - Personality system implementation
   - Advanced validation rules

6. **Advanced Features (Weeks 13-16)**
   - Complete migration of all v1 projects
   - Advanced search and analytics
   - Comprehensive notification system
   - Performance optimization

7. **Production Hardening (Weeks 17-20)**
   - Security audit and penetration testing
   - Performance testing and optimization
   - Documentation and training
   - Production deployment

8. **Monitoring and Maintenance (Weeks 21-24)**
   - Monitoring and alerting setup
   - User feedback integration
   - Bug fixes and refinements
   - Feature enhancements based on usage

## Critical Security Measures

### 1. **Defense in Depth**
- API gateway with rate limiting
- Input validation at multiple layers
- Principle of least privilege
- Secure defaults for all configurations

### 2. **Audit and Compliance**
- Comprehensive audit logging
- Regular security assessments
- Compliance with data protection regulations
- Incident response procedures

### 3. **Model Security**
- Code execution disabled by default
- Sandboxed execution environments when needed
- Regular security updates for model configurations
- Monitoring for suspicious activities

## Risk Mitigation Strategies

### **Migration Risks**
- **Parallel Operation**: Run v1 and v2 simultaneously during transition
- **Incremental Migration**: Migrate projects one at a time with validation
- **Rollback Capability**: Maintain ability to revert individual projects
- **Data Backup**: Comprehensive backup strategy before any migration

### **Performance Risks**
- **Database Optimization**: Proper indexing and query optimization
- **Caching Strategy**: Multi-layer caching for frequently accessed data
- **Load Testing**: Comprehensive performance testing before deployment
- **Monitoring**: Real-time performance monitoring and alerting

### **Security Risks**
- **Security-First Design**: Security considerations in every component
- **Regular Audits**: Automated and manual security assessments
- **Incident Response**: Prepared response procedures for security incidents
- **User Training**: Security awareness training for all users

## Success Metrics (Revised)

### **MVP Success Criteria**
- All existing projects successfully migrated with zero data loss
- Website loads project data 5x faster than current system
- Zero security vulnerabilities in penetration testing
- User satisfaction score > 4.0/5 for new project browsing

### **Full System Success Criteria**
- Project creation time < 30 seconds
- Task execution performance within 20% of current system
- 99.9% system uptime
- Zero critical security incidents in first 6 months

## Conclusion

This refined design addresses the critical architectural, security, and implementation concerns identified in the initial review. The hybrid database-filesystem approach provides the performance and reliability needed for scale, while the security-first design ensures the system can be safely operated in production environments.

The phased implementation approach minimizes risk while delivering immediate value through improved project organization and performance. The comprehensive validation and notification systems ensure the platform maintains integrity and keeps users engaged throughout the research process.

## Research Pipeline Dependency Management

### Pipeline Workflow Schema

The research pipeline follows a strict dependency hierarchy that ensures quality and completeness at each stage:

```yaml
pipeline_stages:
  idea_generation:
    dependencies: []
    outputs: ["initial_idea"]
    requirements:
      - any_model_or_human: true
    
  technical_design:
    dependencies: ["initial_idea"]
    outputs: ["technical_design_document"]
    requirements:
      - input_artifact: "initial_idea"
      - model_capability: "technical_writing"
    
  design_review:
    dependencies: ["technical_design_document"]
    outputs: ["design_review"]
    requirements:
      - input_artifact: "technical_design_document"
      - reviewer_qualification: "design_review_capable"
    
  design_revision:
    dependencies: ["technical_design_document"]
    optional_dependencies: ["design_review+"]
    outputs: ["revised_technical_design"]
    requirements:
      - input_artifact: "technical_design_document"
      - optional_input: "design_reviews"
    
  review_signoff:
    dependencies: ["design_review"]
    outputs: ["signed_review"]
    requirements:
      - input_artifact: "positive_review"
      - authority: "signoff_capable"
    
  implementation_planning:
    dependencies: ["technical_design_document"]
    gate_requirements:
      - signed_positive_reviews: 5.0  # 5 points minimum
      - review_scoring:
          llm_positive_review: 0.5
          human_positive_review: 1.0
    outputs: ["implementation_plan"]
    
  literature_review:
    dependencies: ["implementation_plan"]
    requirements:
      - input_artifact: "implementation_plan"
      - capability: "internet_access"
    outputs: ["literature_review"]
    
  code_implementation:
    dependencies: ["implementation_plan"]
    requirements:
      - input_artifact: "implementation_plan"
      - model_capability: "code_generation"
    outputs: ["code_base"]
    
  data_generation:
    dependencies: []
    requirements:
      - capability: "internet_access OR code_capable OR existing_codebase"
    outputs: ["dataset"]
    
  code_quality_checks:
    dependencies: ["code_base"]
    requirements:
      - input_artifact: "code_base"
      - capability: "sandboxed_execution"
    outputs: ["code_quality_report"]
    
  data_quality_checks:
    dependencies: ["dataset"]
    requirements:
      - input_artifact: "dataset" 
      - capability: "sandboxed_execution"
    outputs: ["data_quality_report"]
    
  statistical_analysis:
    dependencies: ["code_base", "dataset"]
    requirements:
      - input_artifact: "code_base AND dataset"
      - capability: "code_execution"
    outputs: ["figures", "statistical_results"]
    
  paper_writing:
    dependencies: ["implementation_plan", "literature_review"]
    optional_dependencies: ["code_base", "dataset", "figures", "statistical_results"]
    requirements:
      - input_artifact: "implementation_plan AND literature_review"
      - model_capability: "scientific_writing"
    outputs: ["research_paper"]
    
  paper_review:
    dependencies: ["research_paper"]
    outputs: ["paper_review"]
    requirements:
      - input_artifact: "research_paper"
      - reviewer_qualification: "paper_review_capable"
    
  paper_revision:
    dependencies: ["research_paper"]
    optional_dependencies: ["paper_review+"]
    outputs: ["revised_paper"]
    
  paper_review_signoff:
    dependencies: ["paper_review"]
    outputs: ["signed_paper_review"]
    requirements:
      - input_artifact: "positive_paper_review"
      - authority: "signoff_capable"
    
  project_completion:
    dependencies: ["research_paper"]
    gate_requirements:
      - signed_positive_paper_reviews: 5.0  # 5 points minimum
    outputs: ["completed_project"]
```

### Enhanced Database Schema for Dependencies

```sql
-- Task dependencies tracking
CREATE TABLE task_dependencies (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    task_id VARCHAR(255) NOT NULL,
    depends_on_task_id VARCHAR(255) NOT NULL,
    dependency_type ENUM('required', 'optional', 'gate_requirement') NOT NULL,
    minimum_score DECIMAL(3,2) DEFAULT NULL,  -- For gate requirements
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    INDEX idx_task_deps (task_id),
    INDEX idx_dependency_type (dependency_type)
);

-- Task outputs and artifacts
CREATE TABLE task_artifacts (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    task_id VARCHAR(255) NOT NULL,
    artifact_type VARCHAR(100) NOT NULL,
    artifact_path VARCHAR(500) NOT NULL,
    artifact_status ENUM('pending', 'in_progress', 'completed', 'approved') NOT NULL,
    quality_score DECIMAL(4,3) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    INDEX idx_artifact_type (artifact_type),
    INDEX idx_artifact_status (artifact_status)
);

-- Review scoring and signoffs
CREATE TABLE review_scores (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    review_id VARCHAR(255) NOT NULL,
    reviewer_type ENUM('human', 'ai') NOT NULL,
    reviewer_id VARCHAR(255) NOT NULL,
    score DECIMAL(3,2) NOT NULL,  -- 0.00 to 1.00
    is_positive BOOLEAN NOT NULL,
    is_signed_off BOOLEAN DEFAULT FALSE,
    signed_off_by VARCHAR(255) DEFAULT NULL,
    signed_off_at TIMESTAMP DEFAULT NULL,
    points_value DECIMAL(3,2) NOT NULL,  -- 0.5 for AI, 1.0 for human
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_review_scoring (review_id, is_positive, is_signed_off),
    INDEX idx_reviewer (reviewer_type, reviewer_id)
);

-- Pipeline gates and requirements
CREATE TABLE pipeline_gates (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    project_id VARCHAR(255) NOT NULL,
    stage_name VARCHAR(100) NOT NULL,
    gate_type ENUM('review_points', 'artifact_exists', 'capability_check') NOT NULL,
    requirement_value DECIMAL(10,2) NOT NULL,
    current_value DECIMAL(10,2) DEFAULT 0.00,
    is_satisfied BOOLEAN DEFAULT FALSE,
    last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    INDEX idx_project_gates (project_id, stage_name),
    INDEX idx_gate_satisfaction (is_satisfied, stage_name)
);
```

### Dependency Resolution Engine

```python
from enum import Enum
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
import networkx as nx

class DependencyType(Enum):
    REQUIRED = "required"
    OPTIONAL = "optional" 
    GATE_REQUIREMENT = "gate_requirement"

class TaskStatus(Enum):
    PENDING = "pending"
    READY = "ready"  # Dependencies satisfied
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"  # Dependencies not satisfied
    COMPLETED = "completed"

@dataclass
class TaskDependency:
    task_id: str
    depends_on: str
    dependency_type: DependencyType
    minimum_score: Optional[float] = None
    artifact_type: Optional[str] = None

@dataclass
class GateRequirement:
    stage_name: str
    requirement_type: str
    minimum_value: float
    current_value: float = 0.0
    
class DependencyResolver:
    """Manages task dependencies and pipeline gates"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.dependency_graph = nx.DiGraph()
        self.pipeline_stages = self.load_pipeline_definition()
        
    def build_dependency_graph(self, project_id: str) -> None:
        """Build dependency graph for a specific project"""
        tasks = self.get_project_tasks(project_id)
        self.dependency_graph.clear()
        
        # Add all tasks as nodes
        for task in tasks:
            self.dependency_graph.add_node(
                task['id'], 
                status=task['status'],
                task_type=task['task_type'],
                artifacts=task.get('artifacts', [])
            )
        
        # Add dependency edges
        dependencies = self.get_project_dependencies(project_id)
        for dep in dependencies:
            self.dependency_graph.add_edge(
                dep['depends_on_task_id'],
                dep['task_id'],
                dependency_type=dep['dependency_type'],
                minimum_score=dep.get('minimum_score')
            )
    
    def get_ready_tasks(self, project_id: str) -> List[Dict]:
        """Get all tasks that are ready to be executed"""
        self.build_dependency_graph(project_id)
        ready_tasks = []
        
        for task_id in self.dependency_graph.nodes():
            if self.is_task_ready(task_id):
                task_data = self.dependency_graph.nodes[task_id]
                ready_tasks.append({
                    'id': task_id,
                    'task_type': task_data['task_type'],
                    'status': task_data['status']
                })
        
        return ready_tasks
    
    def is_task_ready(self, task_id: str) -> bool:
        """Check if a task is ready to be executed"""
        task_data = self.dependency_graph.nodes[task_id]
        
        # Skip if already completed or in progress
        if task_data['status'] in ['completed', 'in_progress']:
            return False
        
        # Check all required dependencies
        for predecessor in self.dependency_graph.predecessors(task_id):
            edge_data = self.dependency_graph.edges[predecessor, task_id]
            dep_type = edge_data.get('dependency_type', 'required')
            
            if dep_type == 'required':
                if not self.is_dependency_satisfied(predecessor, task_id, edge_data):
                    return False
        
        # Check gate requirements
        if not self.check_gate_requirements(task_id):
            return False
            
        return True
    
    def is_dependency_satisfied(self, dep_task_id: str, task_id: str, edge_data: Dict) -> bool:
        """Check if a specific dependency is satisfied"""
        dep_task = self.dependency_graph.nodes[dep_task_id]
        
        # Basic completion check
        if dep_task['status'] != 'completed':
            return False
        
        # Check minimum score requirements
        minimum_score = edge_data.get('minimum_score')
        if minimum_score:
            actual_score = self.get_task_quality_score(dep_task_id)
            if actual_score < minimum_score:
                return False
        
        return True
    
    def check_gate_requirements(self, task_id: str) -> bool:
        """Check if all gate requirements are satisfied for a task"""
        task_data = self.dependency_graph.nodes[task_id]
        task_type = task_data['task_type']
        
        # Get gate requirements for this task type
        stage_config = self.pipeline_stages.get(task_type, {})
        gate_requirements = stage_config.get('gate_requirements', {})
        
        for gate_name, requirement in gate_requirements.items():
            if not self.is_gate_satisfied(task_id, gate_name, requirement):
                return False
        
        return True
    
    def is_gate_satisfied(self, task_id: str, gate_name: str, requirement: Dict) -> bool:
        """Check if a specific gate requirement is satisfied"""
        if gate_name == 'signed_positive_reviews':
            current_points = self.calculate_review_points(task_id)
            required_points = requirement
            return current_points >= required_points
        
        # Add more gate types as needed
        return True
    
    def calculate_review_points(self, task_id: str) -> float:
        """Calculate total review points for a task"""
        query = """
        SELECT SUM(points_value) as total_points
        FROM review_scores rs
        JOIN task_artifacts ta ON rs.review_id = ta.id
        WHERE ta.task_id = %s 
        AND rs.is_positive = TRUE 
        AND rs.is_signed_off = TRUE
        """
        
        result = self.db.execute(query, (task_id,)).fetchone()
        return result['total_points'] or 0.0
    
    def get_blocking_dependencies(self, task_id: str) -> List[Dict]:
        """Get list of dependencies that are blocking a task"""
        blocking_deps = []
        
        for predecessor in self.dependency_graph.predecessors(task_id):
            edge_data = self.dependency_graph.edges[predecessor, task_id]
            
            if not self.is_dependency_satisfied(predecessor, task_id, edge_data):
                dep_task = self.dependency_graph.nodes[predecessor]
                blocking_deps.append({
                    'task_id': predecessor,
                    'task_type': dep_task['task_type'],
                    'status': dep_task['status'],
                    'dependency_type': edge_data.get('dependency_type'),
                    'reason': self.get_blocking_reason(predecessor, task_id, edge_data)
                })
        
        return blocking_deps
    
    def get_blocking_reason(self, dep_task_id: str, task_id: str, edge_data: Dict) -> str:
        """Get human-readable reason why a dependency is blocking"""
        dep_task = self.dependency_graph.nodes[dep_task_id]
        
        if dep_task['status'] != 'completed':
            return f"Task not completed (status: {dep_task['status']})"
        
        minimum_score = edge_data.get('minimum_score')
        if minimum_score:
            actual_score = self.get_task_quality_score(dep_task_id)
            if actual_score < minimum_score:
                return f"Quality score too low ({actual_score:.2f} < {minimum_score:.2f})"
        
        return "Unknown blocking reason"
    
    def update_task_status(self, task_id: str, new_status: TaskStatus) -> None:
        """Update task status and trigger dependency recalculation"""
        # Update in database
        self.db.execute(
            "UPDATE tasks SET status = %s WHERE id = %s",
            (new_status.value, task_id)
        )
        
        # Update dependency graph
        if self.dependency_graph.has_node(task_id):
            self.dependency_graph.nodes[task_id]['status'] = new_status.value
            
        # Check if any downstream tasks are now ready
        self.propagate_status_changes(task_id)
    
    def propagate_status_changes(self, task_id: str) -> None:
        """Check downstream tasks that might now be ready"""
        for successor in self.dependency_graph.successors(task_id):
            if self.is_task_ready(successor):
                self.update_task_status(successor, TaskStatus.READY)
    
    def get_task_quality_score(self, task_id: str) -> float:
        """Get quality score for a completed task"""
        query = """
        SELECT AVG(quality_score) as avg_score
        FROM task_artifacts 
        WHERE task_id = %s AND quality_score IS NOT NULL
        """
        
        result = self.db.execute(query, (task_id,)).fetchone()
        return result['avg_score'] or 0.0
    
    def validate_pipeline_integrity(self, project_id: str) -> Dict:
        """Validate entire pipeline for circular dependencies and consistency"""
        self.build_dependency_graph(project_id)
        
        issues = []
        
        # Check for circular dependencies
        try:
            cycles = list(nx.simple_cycles(self.dependency_graph))
            if cycles:
                issues.append({
                    'type': 'circular_dependency',
                    'description': f"Circular dependencies detected: {cycles}"
                })
        except nx.NetworkXError:
            pass
        
        # Check for orphaned tasks
        for node in self.dependency_graph.nodes():
            if (self.dependency_graph.in_degree(node) == 0 and 
                self.dependency_graph.out_degree(node) == 0):
                task_data = self.dependency_graph.nodes[node]
                if task_data['task_type'] != 'idea_generation':  # Ideas can be orphaned
                    issues.append({
                        'type': 'orphaned_task',
                        'task_id': node,
                        'description': f"Task {node} has no dependencies or dependents"
                    })
        
        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'task_count': self.dependency_graph.number_of_nodes(),
            'dependency_count': self.dependency_graph.number_of_edges()
        }
```

### Integration with Orchestrator

```python
class EnhancedOrchestrator:
    def __init__(self, config_path: str):
        self.config = ConfigManager(config_path)
        self.project_manager = ProjectManager(self.config)
        self.task_manager = TaskManager(self.config)
        self.model_manager = ModelManager(self.config)
        self.personality_manager = PersonalityManager(self.config)
        self.validation_engine = ValidationEngine(self.config)
        self.dependency_resolver = DependencyResolver(self.config.db_connection)
        
    async def execute_project_cycle(self, project_id: str) -> Dict[str, Any]:
        """Execute one complete cycle with dependency checking"""
        
        # Get all ready tasks based on dependencies
        ready_tasks = self.dependency_resolver.get_ready_tasks(project_id)
        
        if not ready_tasks:
            # No tasks ready - check what's blocking
            all_tasks = self.get_project_tasks(project_id)
            blocking_info = {}
            
            for task in all_tasks:
                if task['status'] in ['pending', 'blocked']:
                    blocking_deps = self.dependency_resolver.get_blocking_dependencies(task['id'])
                    if blocking_deps:
                        blocking_info[task['id']] = blocking_deps
            
            return {
                'tasks_executed': 0,
                'blocking_dependencies': blocking_info,
                'next_action': 'resolve_dependencies'
            }
        
        # Execute ready tasks
        results = []
        for task in ready_tasks:
            try:
                # Select appropriate model and personality
                model = await self.model_manager.select_model(task)
                personality = await self.personality_manager.get_personality(task, model)
                
                # Execute task
                result = await self.task_manager.execute_task(task, model, personality)
                results.append(result)
                
                # Update task status and propagate changes
                if result['status'] == 'completed':
                    self.dependency_resolver.update_task_status(
                        task['id'], 
                        TaskStatus.COMPLETED
                    )
                
            except Exception as e:
                # Mark task as blocked and continue
                self.dependency_resolver.update_task_status(
                    task['id'], 
                    TaskStatus.BLOCKED
                )
                results.append({
                    'task_id': task['id'],
                    'status': 'failed',
                    'error': str(e)
                })
        
        return {
            'tasks_executed': len([r for r in results if r['status'] == 'completed']),
            'results': results,
            'next_ready_tasks': self.dependency_resolver.get_ready_tasks(project_id)
        }
```

## Next Steps

1. **Stakeholder Approval**: Review and approve refined architecture with dependency management
2. **Security Review**: Detailed security assessment of proposed measures
3. **MVP Scoping**: Finalize exact scope and timeline for MVP phase including dependency engine
4. **Team Assembly**: Recruit development team with security expertise
5. **Infrastructure Setup**: Establish development and staging environments

---

*This refined design incorporates expert feedback and represents a production-ready architecture for llmXive v2.0.*