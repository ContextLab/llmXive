# llmXive v2.0: Enhanced Dependency Management System

**Project ID**: LLMX-2024-001-DEPS  
**Date**: 2025-07-06  
**Status**: Design Phase - Enhanced  
**Contributors**: Claude (Sonnet 4), Jeremy Manning, Gemini (Expert Review)  
**Parent Document**: llmXive_v2_redesign_refined.md

## Overview

This document provides an enhanced dependency management system design that addresses the expert feedback from Gemini CLI review. The system incorporates production-ready features including distributed locking, circuit breaker patterns, performance optimizations, and comprehensive security measures.

## Enhanced Pipeline Workflow Schema

### Core Pipeline with Parallel Execution Support

```yaml
pipeline_stages:
  idea_generation:
    dependencies: []
    outputs: ["initial_idea"]
    requirements:
      - any_model_or_human: true
    parallel_eligible: false
    max_instances: 1
    
  technical_design:
    dependencies: ["initial_idea"]
    outputs: ["technical_design_document"]
    requirements:
      - input_artifact: "initial_idea"
      - model_capability: "technical_writing"
    retry_policy:
      max_attempts: 3
      backoff_strategy: "exponential"
      fallback_tasks: ["simplified_technical_design"]
    parallel_eligible: false
    
  design_review:
    dependencies: ["technical_design_document"]
    outputs: ["design_review"]
    requirements:
      - input_artifact: "technical_design_document"
      - reviewer_qualification: "design_review_capable"
    parallel_eligible: true
    max_parallel_instances: 5
    
  design_revision:
    dependencies: ["technical_design_document"]
    optional_dependencies: ["design_review+"]
    outputs: ["revised_technical_design"]
    requirements:
      - input_artifact: "technical_design_document"
      - optional_input: "design_reviews"
    parallel_eligible: false
    
  review_signoff:
    dependencies: ["design_review"]
    outputs: ["signed_review"]
    requirements:
      - input_artifact: "positive_review"
      - authority: "signoff_capable"
    parallel_eligible: true
    max_parallel_instances: 3
    
  implementation_planning:
    dependencies: ["technical_design_document"]
    gate_requirements:
      - signed_positive_reviews: 5.0
      - review_scoring:
          llm_positive_review: 0.5
          human_positive_review: 1.0
    outputs: ["implementation_plan"]
    parallel_eligible: false
    
  literature_review:
    dependencies: ["implementation_plan"]
    requirements:
      - input_artifact: "implementation_plan"
      - capability: "internet_access"
    outputs: ["literature_review"]
    parallel_eligible: true
    can_execute_with: ["code_implementation", "data_generation"]
    
  code_implementation:
    dependencies: ["implementation_plan"]
    requirements:
      - input_artifact: "implementation_plan"
      - model_capability: "code_generation"
    outputs: ["code_base"]
    parallel_eligible: true
    can_execute_with: ["literature_review", "data_generation"]
    
  code_testing:
    dependencies: ["code_base"]
    requirements:
      - input_artifact: "code_base"
      - capability: "code_execution"
    outputs: ["test_suite", "test_results"]
    parallel_eligible: false
    
  data_generation:
    dependencies: ["implementation_plan"]
    requirements:
      - capability: "internet_access OR code_capable OR existing_codebase"
    outputs: ["dataset"]
    parallel_eligible: true
    can_execute_with: ["code_implementation", "literature_review"]
    
  data_validation:
    dependencies: ["dataset"]
    requirements:
      - input_artifact: "dataset"
      - capability: "data_analysis"
    outputs: ["data_quality_report"]
    parallel_eligible: false
    
  code_quality_checks:
    dependencies: ["code_base", "test_suite"]
    requirements:
      - input_artifact: "code_base AND test_suite"
      - capability: "sandboxed_execution"
    outputs: ["code_quality_report"]
    parallel_eligible: false
    
  data_quality_checks:
    dependencies: ["dataset", "data_validation"]
    requirements:
      - input_artifact: "dataset AND data_quality_report"
      - capability: "sandboxed_execution"
    outputs: ["validated_dataset"]
    parallel_eligible: false
    
  statistical_analysis:
    dependencies: ["code_base", "validated_dataset", "code_quality_checks"]
    requirements:
      - input_artifact: "code_base AND validated_dataset"
      - quality_gate: "code_quality_score >= 0.8"
    outputs: ["figures", "statistical_results"]
    parallel_eligible: false
    
  ethics_review:
    dependencies: ["implementation_plan"]
    optional_dependencies: ["dataset", "code_base"]
    requirements:
      - ethics_required: true
      - reviewer_qualification: "ethics_review_capable"
    outputs: ["ethics_approval"]
    parallel_eligible: false
    
  paper_writing:
    dependencies: ["implementation_plan", "literature_review"]
    optional_dependencies: ["code_base", "statistical_results", "ethics_approval"]
    requirements:
      - input_artifact: "implementation_plan AND literature_review"
      - model_capability: "scientific_writing"
    outputs: ["research_paper"]
    parallel_eligible: false
    
  paper_review:
    dependencies: ["research_paper"]
    outputs: ["paper_review"]
    requirements:
      - input_artifact: "research_paper"
      - reviewer_qualification: "paper_review_capable"
    parallel_eligible: true
    max_parallel_instances: 5
    
  paper_revision:
    dependencies: ["research_paper"]
    optional_dependencies: ["paper_review+"]
    outputs: ["revised_paper"]
    parallel_eligible: false
    
  paper_review_signoff:
    dependencies: ["paper_review"]
    outputs: ["signed_paper_review"]
    requirements:
      - input_artifact: "positive_paper_review"
      - authority: "signoff_capable"
    parallel_eligible: true
    
  project_completion:
    dependencies: ["research_paper"]
    gate_requirements:
      - signed_positive_paper_reviews: 5.0
    outputs: ["completed_project"]
    parallel_eligible: false
```

## Enhanced Database Schema

### Core Tables with Security and Performance Enhancements

```sql
-- Enhanced task dependencies with constraints
CREATE TABLE task_dependencies (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    task_id VARCHAR(255) NOT NULL,
    depends_on_task_id VARCHAR(255) NOT NULL,
    dependency_type ENUM('required', 'optional', 'gate_requirement') NOT NULL,
    minimum_score DECIMAL(3,2) DEFAULT NULL CHECK (minimum_score BETWEEN 0.0 AND 1.0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255) NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    CONSTRAINT check_no_self_dependency CHECK (task_id != depends_on_task_id),
    CONSTRAINT check_minimum_score_range CHECK (minimum_score IS NULL OR minimum_score BETWEEN 0.0 AND 1.0),
    INDEX idx_task_deps (task_id, dependency_type),
    INDEX idx_dependency_lookup (depends_on_task_id, dependency_type),
    UNIQUE KEY unique_dependency (task_id, depends_on_task_id, dependency_type)
);

-- Enhanced task artifacts with path validation
CREATE TABLE task_artifacts (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    task_id VARCHAR(255) NOT NULL,
    artifact_type VARCHAR(100) NOT NULL,
    artifact_path VARCHAR(500) NOT NULL,
    artifact_status ENUM('pending', 'in_progress', 'completed', 'approved', 'rejected') NOT NULL,
    quality_score DECIMAL(4,3) DEFAULT NULL CHECK (quality_score BETWEEN 0.0 AND 1.0),
    file_hash VARCHAR(64) DEFAULT NULL,  -- For integrity checking
    file_size BIGINT DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by VARCHAR(255) NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    CONSTRAINT check_path_format CHECK (artifact_path REGEXP '^[a-zA-Z0-9/_.-]+$'),
    INDEX idx_artifact_type_status (artifact_type, artifact_status),
    INDEX idx_task_artifacts_composite (task_id, artifact_status, created_at),
    INDEX idx_quality_score (quality_score) WHERE quality_score IS NOT NULL
);

-- Enhanced review scores with data integrity
CREATE TABLE review_scores (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    review_id VARCHAR(255) NOT NULL,
    reviewer_type ENUM('human', 'ai') NOT NULL,
    reviewer_id VARCHAR(255) NOT NULL,
    score DECIMAL(3,2) NOT NULL CHECK (score BETWEEN 0.0 AND 1.0),
    is_positive BOOLEAN NOT NULL,
    is_signed_off BOOLEAN DEFAULT FALSE,
    signed_off_by VARCHAR(255) DEFAULT NULL,
    signed_off_at TIMESTAMP DEFAULT NULL,
    points_value DECIMAL(3,2) NOT NULL,
    review_text TEXT,
    confidence_score DECIMAL(3,2) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_points_consistency CHECK (
        (reviewer_type = 'human' AND points_value = 1.0) OR
        (reviewer_type = 'ai' AND points_value = 0.5)
    ),
    CONSTRAINT check_signoff_logic CHECK (
        (is_signed_off = FALSE) OR 
        (is_signed_off = TRUE AND signed_off_by IS NOT NULL AND signed_off_at IS NOT NULL)
    ),
    INDEX idx_review_scores_composite (review_id, is_positive, is_signed_off, points_value),
    INDEX idx_reviewer_lookup (reviewer_type, reviewer_id),
    INDEX idx_signoff_status (is_signed_off, signed_off_at)
);

-- Pipeline gates with enhanced tracking
CREATE TABLE pipeline_gates (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    project_id VARCHAR(255) NOT NULL,
    stage_name VARCHAR(100) NOT NULL,
    gate_type ENUM('review_points', 'artifact_exists', 'capability_check', 'quality_threshold') NOT NULL,
    requirement_value DECIMAL(10,2) NOT NULL,
    current_value DECIMAL(10,2) DEFAULT 0.00,
    is_satisfied BOOLEAN DEFAULT FALSE,
    last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    check_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    next_check_at TIMESTAMP DEFAULT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    INDEX idx_project_gates (project_id, stage_name),
    INDEX idx_gate_satisfaction (is_satisfied, stage_name),
    INDEX idx_next_check (next_check_at) WHERE next_check_at IS NOT NULL,
    UNIQUE KEY unique_project_stage_gate (project_id, stage_name, gate_type)
);

-- Task execution locks for concurrency control
CREATE TABLE task_execution_locks (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    task_id VARCHAR(255) NOT NULL,
    locked_by VARCHAR(255) NOT NULL,
    locked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    lock_type ENUM('execution', 'dependency_check', 'status_update') NOT NULL,
    metadata JSON DEFAULT NULL,
    INDEX idx_task_locks (task_id, lock_type),
    INDEX idx_lock_expiry (expires_at),
    INDEX idx_locked_by (locked_by)
);

-- Dependency resolution cache
CREATE TABLE dependency_cache (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    project_id VARCHAR(255) NOT NULL,
    cache_key VARCHAR(255) NOT NULL,
    cache_data JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    cache_version INTEGER DEFAULT 1,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    INDEX idx_cache_lookup (project_id, cache_key),
    INDEX idx_cache_expiry (expires_at),
    UNIQUE KEY unique_project_cache (project_id, cache_key)
);
```

## Production-Ready Dependency Resolution Engine

### Core Engine with Optimizations

```python
import asyncio
import redis
import time
import logging
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import networkx as nx
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class DependencyType(Enum):
    REQUIRED = "required"
    OPTIONAL = "optional"
    GATE_REQUIREMENT = "gate_requirement"

class TaskStatus(Enum):
    PENDING = "pending"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"

class CircuitBreakerState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

@dataclass
class TaskLock:
    task_id: str
    locked_by: str
    expires_at: float
    lock_type: str

class ConcurrencyError(Exception):
    pass

class CircuitBreakerError(Exception):
    pass

class SecurityError(Exception):
    pass

class DistributedDependencyResolver:
    """Production-ready dependency resolver with distributed locking and circuit breaker"""
    
    def __init__(self, db_connection, redis_client, config):
        self.db = db_connection
        self.redis = redis_client
        self.config = config
        
        # Circuit breaker configuration
        self.failure_threshold = config.get('failure_threshold', 5)
        self.recovery_timeout = config.get('recovery_timeout', 60)
        self.failure_count = 0
        self.last_failure_time = None
        self.circuit_state = CircuitBreakerState.CLOSED
        
        # Cache configuration
        self.cache_ttl = config.get('cache_ttl', 300)  # 5 minutes
        self.max_graph_size = config.get('max_graph_size', 10000)
        
        # Performance monitoring
        self.performance_metrics = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'lock_timeouts': 0,
            'circuit_breaker_trips': 0
        }
        
    async def get_ready_tasks(self, project_id: str, user_id: str) -> List[Dict]:
        """Get ready tasks with distributed locking and caching"""
        # Input validation
        self._validate_inputs(project_id, user_id)
        
        # Circuit breaker check
        await self._check_circuit_breaker()
        
        # Rate limiting
        await self._check_rate_limit(user_id)
        
        self.performance_metrics['total_requests'] += 1
        
        try:
            # Try cache first
            cached_result = await self._get_cached_ready_tasks(project_id)
            if cached_result is not None:
                self.performance_metrics['cache_hits'] += 1
                return cached_result
            
            self.performance_metrics['cache_misses'] += 1
            
            # Use distributed lock for consistency
            async with self._project_lock(project_id):
                ready_tasks = await self._calculate_ready_tasks(project_id)
                await self._cache_ready_tasks(project_id, ready_tasks)
                
                # Audit logging
                await self._log_dependency_check(project_id, user_id, len(ready_tasks))
                
                return ready_tasks
                
        except Exception as e:
            await self._handle_circuit_breaker_failure()
            logger.error(f"Error getting ready tasks for project {project_id}: {e}")
            raise
    
    @asynccontextmanager
    async def _project_lock(self, project_id: str, timeout: int = 30):
        """Distributed lock using Redis"""
        lock_key = f"project_lock:{project_id}"
        lock_value = f"{time.time()}_{id(self)}"
        
        # Acquire lock
        acquired = await self.redis.set(
            lock_key, lock_value, 
            nx=True, ex=timeout
        )
        
        if not acquired:
            self.performance_metrics['lock_timeouts'] += 1
            raise ConcurrencyError(f"Could not acquire lock for project {project_id}")
        
        try:
            yield
        finally:
            # Release lock only if we still own it
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """
            await self.redis.eval(lua_script, 1, lock_key, lock_value)
    
    async def _check_circuit_breaker(self):
        """Circuit breaker pattern implementation"""
        if self.circuit_state == CircuitBreakerState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.circuit_state = CircuitBreakerState.HALF_OPEN
                logger.info("Circuit breaker moving to half-open state")
            else:
                raise CircuitBreakerError("Dependency resolver circuit breaker is open")
    
    async def _handle_circuit_breaker_failure(self):
        """Handle failures for circuit breaker"""
        self.failure_count += 1
        
        if self.failure_count >= self.failure_threshold:
            self.circuit_state = CircuitBreakerState.OPEN
            self.last_failure_time = time.time()
            self.performance_metrics['circuit_breaker_trips'] += 1
            logger.warning(f"Circuit breaker tripped after {self.failure_count} failures")
    
    async def _calculate_ready_tasks(self, project_id: str) -> List[Dict]:
        """Calculate ready tasks using optimized queries"""
        # Single optimized query instead of multiple round trips
        query = """
        WITH task_blocking_deps AS (
            SELECT 
                t.id,
                t.task_type,
                t.status,
                COUNT(CASE 
                    WHEN td.dependency_type = 'required' 
                    AND (dt.status != 'completed' OR 
                         (td.minimum_score IS NOT NULL AND 
                          COALESCE(dt_artifacts.avg_quality, 0) < td.minimum_score))
                    THEN 1 
                END) as blocking_count
            FROM tasks t
            LEFT JOIN task_dependencies td ON t.id = td.task_id
            LEFT JOIN tasks dt ON td.depends_on_task_id = dt.id
            LEFT JOIN (
                SELECT task_id, AVG(quality_score) as avg_quality
                FROM task_artifacts 
                WHERE quality_score IS NOT NULL
                GROUP BY task_id
            ) dt_artifacts ON dt.id = dt_artifacts.task_id
            WHERE t.project_id = %s
            GROUP BY t.id, t.task_type, t.status
        ),
        gate_status AS (
            SELECT 
                pg.stage_name,
                SUM(CASE WHEN pg.is_satisfied THEN 1 ELSE 0 END) as satisfied_gates,
                COUNT(*) as total_gates
            FROM pipeline_gates pg
            WHERE pg.project_id = %s
            GROUP BY pg.stage_name
        )
        SELECT 
            tbd.id,
            tbd.task_type,
            tbd.status,
            tbd.blocking_count,
            COALESCE(gs.satisfied_gates, 0) as satisfied_gates,
            COALESCE(gs.total_gates, 0) as total_gates
        FROM task_blocking_deps tbd
        LEFT JOIN gate_status gs ON tbd.task_type = gs.stage_name
        WHERE tbd.status IN ('pending', 'ready', 'blocked')
        AND tbd.blocking_count = 0
        AND (gs.total_gates IS NULL OR gs.satisfied_gates = gs.total_gates)
        ORDER BY 
            CASE tbd.task_type
                WHEN 'idea_generation' THEN 1
                WHEN 'technical_design' THEN 2
                WHEN 'design_review' THEN 3
                ELSE 4
            END
        """
        
        cursor = await self.db.execute(query, (project_id, project_id))
        results = await cursor.fetchall()
        
        ready_tasks = []
        for row in results:
            # Additional validation for parallel execution
            if await self._can_execute_parallel(row['id'], row['task_type']):
                ready_tasks.append({
                    'id': row['id'],
                    'task_type': row['task_type'],
                    'status': row['status'],
                    'priority': self._calculate_task_priority(row['task_type'])
                })
        
        return ready_tasks
    
    async def _can_execute_parallel(self, task_id: str, task_type: str) -> bool:
        """Check if task can be executed in parallel"""
        # Get stage configuration
        stage_config = self.config.get('pipeline_stages', {}).get(task_type, {})
        
        if not stage_config.get('parallel_eligible', False):
            return True  # No parallel restrictions
        
        max_instances = stage_config.get('max_parallel_instances', 1)
        
        # Count currently running instances of this task type
        query = """
        SELECT COUNT(*) as running_count
        FROM tasks t
        JOIN task_execution_locks tel ON t.id = tel.task_id
        WHERE t.task_type = %s 
        AND t.status = 'in_progress'
        AND tel.expires_at > NOW()
        AND tel.lock_type = 'execution'
        """
        
        cursor = await self.db.execute(query, (task_type,))
        result = await cursor.fetchone()
        
        return result['running_count'] < max_instances
    
    def _calculate_task_priority(self, task_type: str) -> int:
        """Calculate task priority for execution ordering"""
        priority_map = {
            'idea_generation': 10,
            'technical_design': 9,
            'design_review': 8,
            'implementation_planning': 7,
            'literature_review': 6,
            'code_implementation': 6,
            'data_generation': 6,
            'paper_writing': 5,
            'paper_review': 4
        }
        return priority_map.get(task_type, 1)
    
    async def _get_cached_ready_tasks(self, project_id: str) -> Optional[List[Dict]]:
        """Get ready tasks from cache"""
        cache_key = f"ready_tasks:{project_id}"
        
        try:
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                import json
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
        
        return None
    
    async def _cache_ready_tasks(self, project_id: str, ready_tasks: List[Dict]) -> None:
        """Cache ready tasks"""
        cache_key = f"ready_tasks:{project_id}"
        
        try:
            import json
            await self.redis.setex(
                cache_key, 
                self.cache_ttl, 
                json.dumps(ready_tasks)
            )
        except Exception as e:
            logger.warning(f"Cache write error: {e}")
    
    async def _invalidate_project_cache(self, project_id: str) -> None:
        """Invalidate all cache entries for a project"""
        pattern = f"*:{project_id}"
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)
    
    def _validate_inputs(self, project_id: str, user_id: str) -> None:
        """Validate input parameters"""
        import re
        
        if not re.match(r'^[A-Za-z0-9\-_]+$', project_id):
            raise SecurityError("Invalid project ID format")
        
        if not re.match(r'^[A-Za-z0-9\-_@.]+$', user_id):
            raise SecurityError("Invalid user ID format")
        
        if len(project_id) > 255 or len(user_id) > 255:
            raise SecurityError("Input too long")
    
    async def _check_rate_limit(self, user_id: str) -> None:
        """Rate limiting per user"""
        rate_limit_key = f"rate_limit:{user_id}"
        
        # Sliding window rate limiting
        now = time.time()
        window = 60  # 1 minute window
        max_requests = 100  # 100 requests per minute
        
        # Remove old entries
        await self.redis.zremrangebyscore(rate_limit_key, 0, now - window)
        
        # Count current requests
        current_count = await self.redis.zcard(rate_limit_key)
        
        if current_count >= max_requests:
            raise SecurityError("Rate limit exceeded")
        
        # Add current request
        await self.redis.zadd(rate_limit_key, {str(now): now})
        await self.redis.expire(rate_limit_key, window)
    
    async def _log_dependency_check(self, project_id: str, user_id: str, task_count: int) -> None:
        """Audit logging for dependency checks"""
        log_entry = {
            'timestamp': time.time(),
            'action': 'dependency_check',
            'project_id': project_id,
            'user_id': user_id,
            'ready_task_count': task_count,
            'performance_metrics': self.performance_metrics.copy()
        }
        
        # Log to structured logging system
        logger.info("Dependency check completed", extra=log_entry)
    
    async def reserve_task(self, task_id: str, worker_id: str, timeout: int = 3600) -> bool:
        """Reserve a task for execution"""
        lock_key = f"task_execution:{task_id}"
        expires_at = time.time() + timeout
        
        # Try to acquire execution lock
        acquired = await self.redis.set(
            lock_key, 
            f"{worker_id}:{expires_at}", 
            nx=True, 
            ex=timeout
        )
        
        if acquired:
            # Update database with lock info
            await self.db.execute("""
                INSERT INTO task_execution_locks 
                (task_id, locked_by, expires_at, lock_type)
                VALUES (%s, %s, FROM_UNIXTIME(%s), 'execution')
                ON DUPLICATE KEY UPDATE
                locked_by = VALUES(locked_by),
                expires_at = VALUES(expires_at),
                locked_at = CURRENT_TIMESTAMP
            """, (task_id, worker_id, expires_at))
            
            # Invalidate cache
            project_id = await self._get_project_id_for_task(task_id)
            await self._invalidate_project_cache(project_id)
            
            return True
        
        return False
    
    async def release_task(self, task_id: str, worker_id: str) -> None:
        """Release task execution lock"""
        lock_key = f"task_execution:{task_id}"
        
        # Only release if we own the lock
        lua_script = """
        local lock_value = redis.call("get", KEYS[1])
        if lock_value and string.match(lock_value, ARGV[1] .. ":") then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        
        released = await self.redis.eval(lua_script, 1, lock_key, worker_id)
        
        if released:
            # Remove from database
            await self.db.execute("""
                DELETE FROM task_execution_locks 
                WHERE task_id = %s AND locked_by = %s AND lock_type = 'execution'
            """, (task_id, worker_id))
            
            # Invalidate cache
            project_id = await self._get_project_id_for_task(task_id)
            await self._invalidate_project_cache(project_id)
    
    async def update_task_status(self, task_id: str, new_status: TaskStatus, worker_id: str) -> None:
        """Update task status with proper locking"""
        async with self._task_update_lock(task_id, worker_id):
            # Update task status in database
            await self.db.execute("""
                UPDATE tasks 
                SET status = %s, updated_at = CURRENT_TIMESTAMP 
                WHERE id = %s
            """, (new_status.value, task_id))
            
            # Invalidate related caches
            project_id = await self._get_project_id_for_task(task_id)
            await self._invalidate_project_cache(project_id)
            
            # Propagate status changes to dependent tasks
            if new_status == TaskStatus.COMPLETED:
                await self._propagate_status_changes(task_id)
    
    @asynccontextmanager
    async def _task_update_lock(self, task_id: str, worker_id: str):
        """Lock for task status updates"""
        lock_key = f"task_update:{task_id}"
        
        acquired = await self.redis.set(lock_key, worker_id, nx=True, ex=10)
        if not acquired:
            raise ConcurrencyError(f"Could not acquire update lock for task {task_id}")
        
        try:
            yield
        finally:
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """
            await self.redis.eval(lua_script, 1, lock_key, worker_id)
    
    async def _propagate_status_changes(self, completed_task_id: str) -> None:
        """Propagate task completion to dependent tasks"""
        # Find tasks that depend on this completed task
        query = """
        SELECT DISTINCT td.task_id, t.status
        FROM task_dependencies td
        JOIN tasks t ON td.task_id = t.id
        WHERE td.depends_on_task_id = %s
        AND t.status IN ('pending', 'blocked')
        """
        
        cursor = await self.db.execute(query, (completed_task_id,))
        dependent_tasks = await cursor.fetchall()
        
        for task in dependent_tasks:
            # Check if this dependent task is now ready
            if await self._is_task_ready_detailed(task['task_id']):
                await self.db.execute("""
                    UPDATE tasks 
                    SET status = 'ready', updated_at = CURRENT_TIMESTAMP 
                    WHERE id = %s AND status != 'ready'
                """, (task['task_id'],))
    
    async def _is_task_ready_detailed(self, task_id: str) -> bool:
        """Detailed check if a specific task is ready"""
        # Check all required dependencies are satisfied
        query = """
        SELECT COUNT(*) as blocking_count
        FROM task_dependencies td
        JOIN tasks dt ON td.depends_on_task_id = dt.id
        LEFT JOIN (
            SELECT task_id, AVG(quality_score) as avg_quality
            FROM task_artifacts 
            WHERE quality_score IS NOT NULL
            GROUP BY task_id
        ) dt_artifacts ON dt.id = dt_artifacts.task_id
        WHERE td.task_id = %s
        AND td.dependency_type = 'required'
        AND (dt.status != 'completed' OR 
             (td.minimum_score IS NOT NULL AND 
              COALESCE(dt_artifacts.avg_quality, 0) < td.minimum_score))
        """
        
        cursor = await self.db.execute(query, (task_id,))
        result = await cursor.fetchone()
        
        return result['blocking_count'] == 0
    
    async def _get_project_id_for_task(self, task_id: str) -> str:
        """Get project ID for a task"""
        cursor = await self.db.execute(
            "SELECT project_id FROM tasks WHERE id = %s", 
            (task_id,)
        )
        result = await cursor.fetchone()
        return result['project_id'] if result else None
    
    async def get_performance_metrics(self) -> Dict:
        """Get performance metrics for monitoring"""
        return {
            **self.performance_metrics,
            'circuit_breaker_state': self.circuit_state.value,
            'failure_count': self.failure_count,
            'last_failure_time': self.last_failure_time
        }
    
    async def cleanup_expired_locks(self) -> int:
        """Cleanup expired locks (run periodically)"""
        # Remove expired Redis locks
        lua_script = """
        local keys = redis.call('keys', 'task_*:*')
        local expired = 0
        for i=1,#keys do
            local value = redis.call('get', keys[i])
            if value then
                local _, expires_str = string.match(value, '(.+):(.+)')
                if expires_str and tonumber(expires_str) < tonumber(ARGV[1]) then
                    redis.call('del', keys[i])
                    expired = expired + 1
                end
            end
        end
        return expired
        """
        
        redis_cleaned = await self.redis.eval(lua_script, 0, str(time.time()))
        
        # Remove expired database locks
        db_result = await self.db.execute("""
            DELETE FROM task_execution_locks 
            WHERE expires_at < NOW()
        """)
        
        db_cleaned = db_result.rowcount if hasattr(db_result, 'rowcount') else 0
        
        logger.info(f"Cleaned up {redis_cleaned} Redis locks and {db_cleaned} database locks")
        return redis_cleaned + db_cleaned
```

## Integration with Enhanced Orchestrator

```python
class ProductionOrchestrator:
    """Production-ready orchestrator with enhanced dependency management"""
    
    def __init__(self, config_path: str):
        self.config = ConfigManager(config_path)
        self.project_manager = ProjectManager(self.config)
        self.task_manager = TaskManager(self.config)
        self.model_manager = ModelManager(self.config)
        self.personality_manager = PersonalityManager(self.config)
        self.validation_engine = ValidationEngine(self.config)
        
        # Enhanced dependency resolver
        self.dependency_resolver = DistributedDependencyResolver(
            self.config.db_connection,
            self.config.redis_client,
            self.config.dependency_config
        )
        
        # Worker identification
        self.worker_id = f"orchestrator_{os.getpid()}_{int(time.time())}"
        
        # Monitoring and metrics
        self.metrics_collector = MetricsCollector(self.config)
        
    async def execute_project_cycle(self, project_id: str, user_id: str, max_parallel_tasks: int = 5) -> Dict[str, Any]:
        """Execute project cycle with enhanced dependency management"""
        start_time = time.time()
        
        try:
            # Get ready tasks with distributed dependency checking
            ready_tasks = await self.dependency_resolver.get_ready_tasks(project_id, user_id)
            
            if not ready_tasks:
                # Analyze blocking dependencies
                blocking_info = await self._analyze_blocking_dependencies(project_id)
                return {
                    'tasks_executed': 0,
                    'blocking_dependencies': blocking_info,
                    'next_action': 'resolve_dependencies',
                    'execution_time': time.time() - start_time
                }
            
            # Sort tasks by priority
            ready_tasks.sort(key=lambda x: x.get('priority', 0), reverse=True)
            
            # Limit concurrent execution
            tasks_to_execute = ready_tasks[:max_parallel_tasks]
            
            # Reserve tasks for execution
            reserved_tasks = []
            for task in tasks_to_execute:
                if await self.dependency_resolver.reserve_task(task['id'], self.worker_id):
                    reserved_tasks.append(task)
                    # Update task status to in_progress
                    await self.dependency_resolver.update_task_status(
                        task['id'], TaskStatus.IN_PROGRESS, self.worker_id
                    )
            
            if not reserved_tasks:
                return {
                    'tasks_executed': 0,
                    'message': 'All ready tasks are currently reserved by other workers',
                    'execution_time': time.time() - start_time
                }
            
            # Execute reserved tasks in parallel
            execution_tasks = []
            for task in reserved_tasks:
                execution_tasks.append(
                    self._execute_single_task(task, project_id)
                )
            
            # Wait for all tasks to complete
            results = await asyncio.gather(*execution_tasks, return_exceptions=True)
            
            # Process results and update statuses
            successful_executions = 0
            for i, result in enumerate(results):
                task = reserved_tasks[i]
                
                try:
                    if isinstance(result, Exception):
                        # Task failed
                        await self.dependency_resolver.update_task_status(
                            task['id'], TaskStatus.FAILED, self.worker_id
                        )
                        logger.error(f"Task {task['id']} failed: {result}")
                    else:
                        # Task completed successfully
                        await self.dependency_resolver.update_task_status(
                            task['id'], TaskStatus.COMPLETED, self.worker_id
                        )
                        successful_executions += 1
                        
                finally:
                    # Always release the task lock
                    await self.dependency_resolver.release_task(task['id'], self.worker_id)
            
            # Get next ready tasks after this execution
            next_ready_tasks = await self.dependency_resolver.get_ready_tasks(project_id, user_id)
            
            # Collect metrics
            execution_time = time.time() - start_time
            await self.metrics_collector.record_execution_cycle(
                project_id, len(reserved_tasks), successful_executions, execution_time
            )
            
            return {
                'tasks_executed': successful_executions,
                'tasks_failed': len(reserved_tasks) - successful_executions,
                'results': [r for r in results if not isinstance(r, Exception)],
                'errors': [str(r) for r in results if isinstance(r, Exception)],
                'next_ready_tasks': next_ready_tasks,
                'execution_time': execution_time
            }
            
        except Exception as e:
            logger.error(f"Error in project cycle execution: {e}")
            await self.metrics_collector.record_execution_error(project_id, str(e))
            raise
    
    async def _execute_single_task(self, task: Dict, project_id: str) -> Dict:
        """Execute a single task with comprehensive error handling"""
        task_start_time = time.time()
        
        try:
            # Select appropriate model and personality
            model = await self.model_manager.select_model(task)
            personality = await self.personality_manager.get_personality(task, model)
            
            # Execute the task
            result = await self.task_manager.execute_task(task, model, personality)
            
            # Validate the result
            validation_result = await self.validation_engine.validate_task_result(task, result)
            if not validation_result.is_valid:
                raise ValueError(f"Task result validation failed: {validation_result.errors}")
            
            # Record successful execution
            execution_time = time.time() - task_start_time
            await self.metrics_collector.record_task_execution(
                task['id'], task['task_type'], execution_time, True
            )
            
            return {
                'task_id': task['id'],
                'task_type': task['task_type'],
                'status': 'completed',
                'execution_time': execution_time,
                'artifacts': result.get('artifacts', []),
                'model_used': model.get('id'),
                'personality_used': personality.get('id')
            }
            
        except Exception as e:
            execution_time = time.time() - task_start_time
            await self.metrics_collector.record_task_execution(
                task['id'], task['task_type'], execution_time, False
            )
            
            logger.error(f"Task execution failed for {task['id']}: {e}")
            raise
    
    async def _analyze_blocking_dependencies(self, project_id: str) -> Dict:
        """Analyze what dependencies are blocking progress"""
        query = """
        SELECT 
            t.id,
            t.task_type,
            t.status,
            GROUP_CONCAT(
                CONCAT(dt.task_type, ':', dt.status, 
                       CASE WHEN td.minimum_score IS NOT NULL 
                            THEN CONCAT('(score:', COALESCE(dt_artifacts.avg_quality, 0), '/', td.minimum_score, ')')
                            ELSE '' END
                ) SEPARATOR '; '
            ) as blocking_dependencies
        FROM tasks t
        LEFT JOIN task_dependencies td ON t.id = td.task_id AND td.dependency_type = 'required'
        LEFT JOIN tasks dt ON td.depends_on_task_id = dt.id
        LEFT JOIN (
            SELECT task_id, AVG(quality_score) as avg_quality
            FROM task_artifacts 
            WHERE quality_score IS NOT NULL
            GROUP BY task_id
        ) dt_artifacts ON dt.id = dt_artifacts.task_id
        WHERE t.project_id = %s
        AND t.status IN ('pending', 'blocked')
        AND (dt.status IS NULL OR dt.status != 'completed' OR 
             (td.minimum_score IS NOT NULL AND COALESCE(dt_artifacts.avg_quality, 0) < td.minimum_score))
        GROUP BY t.id, t.task_type, t.status
        HAVING blocking_dependencies IS NOT NULL
        """
        
        cursor = await self.dependency_resolver.db.execute(query, (project_id,))
        blocked_tasks = await cursor.fetchall()
        
        blocking_analysis = {}
        for task in blocked_tasks:
            blocking_analysis[task['id']] = {
                'task_type': task['task_type'],
                'status': task['status'],
                'blocking_dependencies': task['blocking_dependencies'],
                'recommendations': await self._get_unblocking_recommendations(task['id'])
            }
        
        return blocking_analysis
    
    async def _get_unblocking_recommendations(self, task_id: str) -> List[str]:
        """Get recommendations for unblocking a task"""
        recommendations = []
        
        # Get specific blocking dependencies
        query = """
        SELECT dt.id, dt.task_type, dt.status, td.minimum_score,
               COALESCE(dt_artifacts.avg_quality, 0) as current_quality
        FROM task_dependencies td
        JOIN tasks dt ON td.depends_on_task_id = dt.id
        LEFT JOIN (
            SELECT task_id, AVG(quality_score) as avg_quality
            FROM task_artifacts 
            WHERE quality_score IS NOT NULL
            GROUP BY task_id
        ) dt_artifacts ON dt.id = dt_artifacts.task_id
        WHERE td.task_id = %s 
        AND td.dependency_type = 'required'
        AND (dt.status != 'completed' OR 
             (td.minimum_score IS NOT NULL AND COALESCE(dt_artifacts.avg_quality, 0) < td.minimum_score))
        """
        
        cursor = await self.dependency_resolver.db.execute(query, (task_id,))
        blocking_deps = await cursor.fetchall()
        
        for dep in blocking_deps:
            if dep['status'] != 'completed':
                recommendations.append(f"Complete {dep['task_type']} task (ID: {dep['id']})")
            elif dep['minimum_score'] and dep['current_quality'] < dep['minimum_score']:
                recommendations.append(
                    f"Improve quality of {dep['task_type']} task from {dep['current_quality']:.2f} to {dep['minimum_score']:.2f}"
                )
        
        return recommendations
    
    async def get_project_health_dashboard(self, project_id: str) -> Dict:
        """Get comprehensive project health information"""
        # Get dependency resolver metrics
        dep_metrics = await self.dependency_resolver.get_performance_metrics()
        
        # Get project progress statistics
        project_stats = await self._get_project_statistics(project_id)
        
        # Get current pipeline status
        pipeline_status = await self._get_pipeline_status(project_id)
        
        return {
            'project_id': project_id,
            'dependency_metrics': dep_metrics,
            'project_statistics': project_stats,
            'pipeline_status': pipeline_status,
            'health_score': await self._calculate_health_score(project_id),
            'generated_at': time.time()
        }
    
    async def _get_project_statistics(self, project_id: str) -> Dict:
        """Get project statistics"""
        query = """
        SELECT 
            COUNT(*) as total_tasks,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_tasks,
            SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress_tasks,
            SUM(CASE WHEN status = 'blocked' THEN 1 ELSE 0 END) as blocked_tasks,
            SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_tasks,
            AVG(CASE WHEN status = 'completed' THEN 
                TIMESTAMPDIFF(HOUR, created_at, updated_at) ELSE NULL END) as avg_completion_hours
        FROM tasks 
        WHERE project_id = %s
        """
        
        cursor = await self.dependency_resolver.db.execute(query, (project_id,))
        stats = await cursor.fetchone()
        
        return {
            'total_tasks': stats['total_tasks'],
            'completed_tasks': stats['completed_tasks'],
            'in_progress_tasks': stats['in_progress_tasks'],
            'blocked_tasks': stats['blocked_tasks'],
            'failed_tasks': stats['failed_tasks'],
            'completion_rate': stats['completed_tasks'] / max(stats['total_tasks'], 1),
            'avg_completion_hours': stats['avg_completion_hours'] or 0
        }
    
    async def _get_pipeline_status(self, project_id: str) -> Dict:
        """Get pipeline stage status"""
        query = """
        SELECT 
            stage_name,
            COUNT(*) as total_gates,
            SUM(CASE WHEN is_satisfied THEN 1 ELSE 0 END) as satisfied_gates,
            AVG(current_value / requirement_value) as completion_ratio
        FROM pipeline_gates 
        WHERE project_id = %s
        GROUP BY stage_name
        """
        
        cursor = await self.dependency_resolver.db.execute(query, (project_id,))
        pipeline_data = await cursor.fetchall()
        
        pipeline_status = {}
        for stage in pipeline_data:
            pipeline_status[stage['stage_name']] = {
                'total_gates': stage['total_gates'],
                'satisfied_gates': stage['satisfied_gates'],
                'completion_ratio': float(stage['completion_ratio'] or 0),
                'is_complete': stage['satisfied_gates'] == stage['total_gates']
            }
        
        return pipeline_status
    
    async def _calculate_health_score(self, project_id: str) -> float:
        """Calculate overall project health score (0-1)"""
        stats = await self._get_project_statistics(project_id)
        pipeline = await self._get_pipeline_status(project_id)
        
        # Base score from completion rate
        completion_score = stats['completion_rate'] * 0.4
        
        # Penalty for blocked/failed tasks
        block_penalty = (stats['blocked_tasks'] + stats['failed_tasks']) / max(stats['total_tasks'], 1) * 0.2
        
        # Pipeline progress bonus
        pipeline_scores = [stage['completion_ratio'] for stage in pipeline.values()]
        pipeline_score = (sum(pipeline_scores) / max(len(pipeline_scores), 1)) * 0.4
        
        health_score = max(0, completion_score + pipeline_score - block_penalty)
        return min(1.0, health_score)
```

## Monitoring and Maintenance

### Performance Monitoring

```python
class MetricsCollector:
    """Collect and export metrics for monitoring"""
    
    def __init__(self, config):
        self.config = config
        self.metrics_backend = config.get('metrics_backend', 'prometheus')
        
    async def record_execution_cycle(self, project_id: str, tasks_reserved: int, 
                                   tasks_completed: int, execution_time: float):
        """Record execution cycle metrics"""
        # Implementation would integrate with monitoring system
        pass
    
    async def record_task_execution(self, task_id: str, task_type: str, 
                                  execution_time: float, success: bool):
        """Record individual task execution metrics"""
        pass
    
    async def record_execution_error(self, project_id: str, error_message: str):
        """Record execution errors"""
        pass
```

### Maintenance Scripts

```python
async def cleanup_maintenance(dependency_resolver: DistributedDependencyResolver):
    """Regular maintenance tasks"""
    
    # Cleanup expired locks
    cleaned_locks = await dependency_resolver.cleanup_expired_locks()
    
    # Cleanup old cache entries
    await dependency_resolver.redis.eval("""
        local keys = redis.call('keys', '*:*')
        local cleaned = 0
        for i=1,#keys do
            local ttl = redis.call('ttl', keys[i])
            if ttl == -1 then  -- No expiry set
                redis.call('expire', keys[i], 3600)  -- Set 1 hour expiry
                cleaned = cleaned + 1
            end
        end
        return cleaned
    """, 0)
    
    # Reset circuit breaker if in half-open state for too long
    if dependency_resolver.circuit_state == CircuitBreakerState.HALF_OPEN:
        time_in_half_open = time.time() - dependency_resolver.last_failure_time
        if time_in_half_open > dependency_resolver.recovery_timeout * 2:
            dependency_resolver.circuit_state = CircuitBreakerState.CLOSED
            dependency_resolver.failure_count = 0
    
    logger.info(f"Maintenance completed: cleaned {cleaned_locks} locks")
```

## Security Enhancements

### Input Validation and Sanitization

```python
class SecurityValidator:
    """Comprehensive security validation"""
    
    @staticmethod
    def validate_project_id(project_id: str) -> bool:
        """Validate project ID format"""
        import re
        return bool(re.match(r'^[A-Za-z0-9\-_]{1,255}$', project_id))
    
    @staticmethod
    def validate_sql_injection_patterns(input_string: str) -> bool:
        """Check for SQL injection patterns"""
        dangerous_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)\b)",
            r"(\b(UNION|OR|AND)\b.*\b(SELECT|INSERT|UPDATE|DELETE)\b)",
            r"['\";]",
            r"--",
            r"/\*",
            r"\*/"
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, input_string.upper()):
                return False
        return True
    
    @staticmethod
    def sanitize_file_path(file_path: str) -> str:
        """Sanitize file paths to prevent traversal attacks"""
        import os
        # Remove dangerous path components
        safe_path = os.path.normpath(file_path)
        if safe_path.startswith('../') or safe_path.startswith('/'):
            raise SecurityError("Path traversal attempt detected")
        return safe_path
```

## Conclusion

This enhanced dependency management system provides:

1. **Production-Ready Architecture**: Distributed locking, circuit breaker patterns, and comprehensive error handling
2. **Scalability**: Optimized database queries, caching, and batch processing
3. **Security**: Input validation, rate limiting, and audit logging
4. **Monitoring**: Comprehensive metrics collection and health dashboards
5. **Reliability**: Failure recovery, graceful degradation, and maintenance procedures

The system is designed to handle hundreds of projects with thousands of tasks while maintaining data consistency and performance under high load.