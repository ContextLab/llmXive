# llmXive v2.0: Additional Systems Design

**Project ID**: LLMX-2024-001-ADDON  
**Date**: 2025-07-06  
**Status**: Design Phase  
**Contributors**: Claude (Sonnet 4), Jeremy Manning, Gemini (via Claude Code)  
**Parent Document**: llmXive_v2_redesign_refined.md

## Overview

This document specifies the design for six additional systems that extend the core llmXive v2.0 architecture to provide comprehensive task management, quality control, and model management capabilities.

## System 1: Task Type Management System

### Architecture Overview

```
orchestrator/
├── tasks/
│   ├── definitions/           # Task definition .md files
│   │   ├── idea_generation.md
│   │   ├── technical_design.md
│   │   ├── code_implementation.md
│   │   ├── data_analysis.md
│   │   ├── paper_writing.md
│   │   └── review_tasks.md
│   ├── loader/               # Task loading and parsing
│   │   ├── __init__.py
│   │   ├── task_loader.py
│   │   ├── prompt_parser.py
│   │   └── validation.py
│   └── registry/             # Task registry and cache
│       ├── task_registry.py
│       └── task_cache.py
```

### Task Definition Format

```markdown
# Technical Design Task

## Metadata
```yaml
task_id: "technical_design"
name: "Technical Design Document Creation"
category: "design"
version: "1.2.0"
created_date: "2024-01-15"
last_updated: "2024-07-06"
```

## Description
Create comprehensive technical design documents that specify the architecture, implementation approach, and technical requirements for a research project.

## System Prompt
<system>
You are a senior technical architect with extensive experience in system design and implementation. You approach problems systematically, considering scalability, maintainability, and technical feasibility.

Your task is to create a comprehensive technical design document for the project: {project_title}.

Key requirements:
- Analyze technical requirements and constraints thoroughly
- Propose detailed implementation architecture
- Identify potential challenges and mitigation strategies
- Provide clear specifications for development teams
- Consider long-term maintenance and extensibility

Project Context:
{project_context}

Technical Constraints:
{technical_constraints}
</system>

## Task Instructions
1. **Requirements Analysis**
   - Review project objectives and success criteria
   - Identify functional and non-functional requirements
   - Analyze existing constraints and dependencies

2. **Architecture Design**
   - Propose high-level system architecture
   - Define component interactions and data flows
   - Consider scalability and performance requirements

3. **Implementation Specifications**
   - Provide detailed component specifications
   - Define APIs and interfaces
   - Specify data models and schemas

4. **Risk Assessment**
   - Identify technical risks and challenges
   - Propose mitigation strategies
   - Define fallback approaches

## Model Eligibility
```yaml
minimum_requirements:
  context_length: 32000
  reasoning_capability: "advanced"
  technical_writing: "proficient"
  domain_knowledge: "intermediate"

preferred_models:
  - "claude-3.5-sonnet"
  - "gpt-4-turbo"
  - "claude-3-opus"
  - "gemini-1.5-pro"

capability_weights:
  technical_reasoning: 0.4
  documentation_quality: 0.3
  domain_expertise: 0.2
  creativity: 0.1
```

## Quality Criteria
- Technical accuracy and feasibility: > 0.90
- Comprehensive coverage: > 0.85
- Clear documentation: > 0.88
- Implementation readiness: > 0.80

## Expected Outputs
- `technical_design/main.md` - Primary design document
- `technical_design/diagrams/` - Architecture diagrams
- `technical_design/specifications/` - Detailed specs
- Updated project metadata with design completion status
```

### Task Loader Implementation

```python
import re
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

@dataclass
class TaskDefinition:
    task_id: str
    name: str
    category: str
    version: str
    metadata: Dict[str, Any]
    description: str
    system_prompt: Optional[str]
    instructions: str
    model_eligibility: Dict[str, Any]
    quality_criteria: Dict[str, float]
    expected_outputs: List[str]
    file_path: Path

class TaskLoader:
    def __init__(self, tasks_dir: Path):
        self.tasks_dir = tasks_dir
        self.task_cache: Dict[str, TaskDefinition] = {}
        self.last_scan: Optional[float] = None
    
    def load_all_tasks(self, force_reload: bool = False) -> Dict[str, TaskDefinition]:
        """Load all task definitions from the tasks directory"""
        current_time = time.time()
        
        # Check if we need to reload (cache invalidation)
        if not force_reload and self.last_scan and (current_time - self.last_scan) < 300:  # 5 min cache
            return self.task_cache
        
        self.task_cache.clear()
        
        for task_file in self.tasks_dir.glob("*.md"):
            try:
                task_def = self.load_task_definition(task_file)
                self.task_cache[task_def.task_id] = task_def
            except Exception as e:
                logger.error(f"Failed to load task definition {task_file}: {e}")
        
        self.last_scan = current_time
        return self.task_cache
    
    def load_task_definition(self, file_path: Path) -> TaskDefinition:
        """Load and parse a single task definition file"""
        content = file_path.read_text(encoding='utf-8')
        
        # Parse metadata YAML block
        metadata_match = re.search(r'```yaml\n(.*?)\n```', content, re.DOTALL)
        if not metadata_match:
            raise ValueError(f"No metadata block found in {file_path}")
        
        metadata = yaml.safe_load(metadata_match.group(1))
        
        # Extract system prompt if present
        system_prompt = None
        system_match = re.search(r'<system>(.*?)</system>', content, re.DOTALL)
        if system_match:
            system_prompt = system_match.group(1).strip()
        
        # Parse other sections
        sections = self.parse_markdown_sections(content)
        
        return TaskDefinition(
            task_id=metadata['task_id'],
            name=metadata['name'],
            category=metadata['category'],
            version=metadata['version'],
            metadata=metadata,
            description=sections.get('Description', ''),
            system_prompt=system_prompt,
            instructions=sections.get('Task Instructions', ''),
            model_eligibility=self.parse_yaml_section(sections.get('Model Eligibility', '{}')),
            quality_criteria=self.parse_yaml_section(sections.get('Quality Criteria', '{}')),
            expected_outputs=self.parse_list_section(sections.get('Expected Outputs', '')),
            file_path=file_path
        )
    
    def parse_markdown_sections(self, content: str) -> Dict[str, str]:
        """Parse markdown content into sections"""
        sections = {}
        current_section = None
        current_content = []
        
        for line in content.split('\n'):
            if line.startswith('## '):
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = line[3:].strip()
                current_content = []
            elif current_section:
                current_content.append(line)
        
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def get_task_definition(self, task_id: str) -> Optional[TaskDefinition]:
        """Get a specific task definition by ID"""
        tasks = self.load_all_tasks()
        return tasks.get(task_id)
```

## System 2: Personality Management System

### Architecture Overview

```
orchestrator/
├── personalities/
│   ├── definitions/          # Personality definition .md files
│   │   ├── critical_thinker.md
│   │   ├── creative_brainstormer.md
│   │   ├── technical_architect.md
│   │   ├── domain_expert.md
│   │   └── quality_reviewer.md
│   ├── loader/              # Personality loading system
│   │   ├── __init__.py
│   │   ├── personality_loader.py
│   │   └── combiner.py
│   └── engine/              # Personality application engine
│       ├── personality_engine.py
│       └── prompt_builder.py
```

### Personality Definition Format

```markdown
# Critical Thinker Personality

## Metadata
```yaml
personality_id: "critical_thinker"
name: "Critical Thinker"
category: "analytical"
version: "1.0.0"
compatibility: ["technical_architect", "quality_reviewer"]
conflicts: ["rapid_prototyper", "creative_brainstormer"]
```

## Description
A systematic, evidence-based thinker who prioritizes logical rigor and thorough analysis. This personality emphasizes careful validation of assumptions and comprehensive evaluation of alternatives.

## Personality Prompt
You are an expert researcher with a deep commitment to intellectual rigor and logical correctness. Your main concern is statistical validity, methodological soundness, and evidence-based reasoning. 

While you appreciate exciting and innovative ideas, you are naturally skeptical and methodical. You carefully examine every assumption, validate claims against evidence, and question conclusions rather than accepting them at face value.

Key traits:
- Systematic and methodical in your approach
- Evidence-based decision making
- Thorough validation of assumptions and claims
- Constructive skepticism of new ideas
- Focus on logical consistency and statistical rigor
- Preference for established methodologies over untested approaches

When reviewing work or making recommendations:
1. Always ask for supporting evidence
2. Question underlying assumptions
3. Look for potential confounding factors
4. Suggest robust validation methods
5. Recommend conservative, well-tested approaches when high reliability is required

## Behavioral Modifiers
```yaml
communication_style:
  tone: "professional_analytical"
  detail_level: "comprehensive"
  question_frequency: "high"
  evidence_requirements: "strict"

decision_making:
  risk_tolerance: "low"
  validation_requirements: "extensive"
  methodology_preference: "established"
  innovation_approach: "cautious"

task_approach:
  planning_depth: "thorough"
  assumption_checking: "rigorous"
  alternative_evaluation: "comprehensive"
  documentation_level: "detailed"
```

## Task-Specific Applications
```yaml
technical_design:
  focus_areas:
    - requirement_validation
    - risk_assessment
    - methodology_evaluation
    - assumption_documentation

code_implementation:
  focus_areas:
    - error_handling
    - edge_case_coverage
    - testing_comprehensiveness
    - documentation_quality

research_tasks:
  focus_areas:
    - methodology_rigor
    - statistical_validity
    - evidence_quality
    - reproducibility
```
```

### Personality Engine Implementation

```python
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum

class PersonalityCompatibility(Enum):
    COMPATIBLE = "compatible"
    NEUTRAL = "neutral"
    CONFLICTING = "conflicting"

@dataclass
class PersonalityDefinition:
    personality_id: str
    name: str
    category: str
    description: str
    personality_prompt: str
    behavioral_modifiers: Dict[str, Any]
    task_applications: Dict[str, Any]
    compatibility: List[str]
    conflicts: List[str]

class PersonalityEngine:
    def __init__(self, personalities_dir: Path):
        self.personalities_dir = personalities_dir
        self.loader = PersonalityLoader(personalities_dir)
        self.personality_cache: Dict[str, PersonalityDefinition] = {}
    
    def build_system_prompt(self, base_prompt: str, personalities: List[str], 
                          task_context: Dict[str, Any]) -> str:
        """Build a complete system prompt with personality integration"""
        
        # Validate personality compatibility
        compatibility_result = self.check_personality_compatibility(personalities)
        if not compatibility_result.is_compatible:
            raise PersonalityError(f"Incompatible personalities: {compatibility_result.conflicts}")
        
        # Load personality definitions
        personality_defs = []
        for personality_id in personalities:
            personality_def = self.loader.get_personality(personality_id)
            if personality_def:
                personality_defs.append(personality_def)
        
        # Build integrated prompt
        prompt_parts = [base_prompt]
        
        # Add personality prompts
        for personality_def in personality_defs:
            prompt_parts.append(personality_def.personality_prompt)
        
        # Add task-specific behavioral modifiers
        task_type = task_context.get('task_type')
        if task_type:
            behavioral_instructions = self.build_behavioral_instructions(
                personality_defs, task_type
            )
            if behavioral_instructions:
                prompt_parts.append(behavioral_instructions)
        
        return '\n\n'.join(prompt_parts)
    
    def check_personality_compatibility(self, personalities: List[str]) -> CompatibilityResult:
        """Check if a set of personalities can work together"""
        conflicts = []
        
        for i, p1 in enumerate(personalities):
            for p2 in personalities[i+1:]:
                p1_def = self.loader.get_personality(p1)
                p2_def = self.loader.get_personality(p2)
                
                if p1_def and p2_def:
                    if p2 in p1_def.conflicts or p1 in p2_def.conflicts:
                        conflicts.append((p1, p2))
        
        return CompatibilityResult(
            is_compatible=len(conflicts) == 0,
            conflicts=conflicts
        )
    
    def build_behavioral_instructions(self, personalities: List[PersonalityDefinition], 
                                    task_type: str) -> Optional[str]:
        """Build task-specific behavioral instructions based on personalities"""
        instructions = []
        
        for personality in personalities:
            task_application = personality.task_applications.get(task_type)
            if task_application:
                focus_areas = task_application.get('focus_areas', [])
                if focus_areas:
                    instruction = f"As a {personality.name}, pay special attention to: " + \
                                ", ".join(focus_areas)
                    instructions.append(instruction)
        
        return '\n'.join(instructions) if instructions else None

@dataclass
class CompatibilityResult:
    is_compatible: bool
    conflicts: List[tuple]
```

## System 3: Voting System

### Database Schema Extension

```sql
-- Votes table
CREATE TABLE votes (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    project_id VARCHAR(255) NOT NULL,
    artifact_type ENUM('idea', 'design', 'plan', 'code', 'paper', 'review') NOT NULL,
    artifact_id VARCHAR(500) NOT NULL,  -- Could be file path or specific identifier
    user_id VARCHAR(255),  -- NULL for anonymous votes
    user_session VARCHAR(255),  -- For anonymous user tracking
    vote_type ENUM('upvote', 'downvote', 'neutral') NOT NULL,
    vote_value INTEGER DEFAULT 1,  -- Allow weighted votes
    comment TEXT,  -- Optional comment with vote
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),  -- For spam detection
    user_agent TEXT,  -- For spam detection
    INDEX idx_project_artifact (project_id, artifact_type, artifact_id),
    INDEX idx_user_votes (user_id, created_at),
    INDEX idx_session_votes (user_session, created_at),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- Vote aggregations (materialized view for performance)
CREATE TABLE vote_aggregations (
    project_id VARCHAR(255) NOT NULL,
    artifact_type ENUM('idea', 'design', 'plan', 'code', 'paper', 'review') NOT NULL,
    artifact_id VARCHAR(500) NOT NULL,
    upvotes INTEGER DEFAULT 0,
    downvotes INTEGER DEFAULT 0,
    total_votes INTEGER DEFAULT 0,
    average_score DECIMAL(4,3) DEFAULT 0.000,
    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (project_id, artifact_type, artifact_id),
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

-- Vote abuse detection
CREATE TABLE vote_abuse_patterns (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    pattern_type ENUM('rapid_voting', 'vote_bombing', 'sock_puppet', 'coordinated') NOT NULL,
    identifier VARCHAR(255) NOT NULL,  -- IP, user_id, or pattern signature
    detection_count INTEGER DEFAULT 1,
    first_detected TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_detected TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_blocked BOOLEAN DEFAULT FALSE,
    INDEX idx_pattern_lookup (pattern_type, identifier)
);
```

### Voting Service Implementation

```python
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import hashlib
import ipaddress

class VoteType(Enum):
    UPVOTE = "upvote"
    DOWNVOTE = "downvote"
    NEUTRAL = "neutral"

class ArtifactType(Enum):
    IDEA = "idea"
    DESIGN = "design"
    PLAN = "plan"
    CODE = "code"
    PAPER = "paper"
    REVIEW = "review"

class VotingService:
    def __init__(self, db_connection, spam_detector: SpamDetector):
        self.db = db_connection
        self.spam_detector = spam_detector
    
    async def submit_vote(self, vote_request: VoteRequest) -> VoteResult:
        """Submit a vote with spam detection and validation"""
        
        # Validate vote request
        validation_result = await self.validate_vote_request(vote_request)
        if not validation_result.is_valid:
            return VoteResult(success=False, errors=validation_result.errors)
        
        # Check for spam patterns
        spam_check = await self.spam_detector.check_vote_spam(vote_request)
        if spam_check.is_spam:
            await self.record_abuse_pattern(vote_request, spam_check.pattern_type)
            return VoteResult(success=False, errors=["Vote blocked due to suspicious activity"])
        
        # Check for duplicate votes
        existing_vote = await self.get_existing_vote(vote_request)
        
        async with self.db.transaction():
            if existing_vote:
                # Update existing vote
                await self.update_vote(existing_vote.id, vote_request)
            else:
                # Create new vote
                await self.create_vote(vote_request)
            
            # Update aggregations
            await self.update_vote_aggregations(
                vote_request.project_id,
                vote_request.artifact_type,
                vote_request.artifact_id
            )
        
        return VoteResult(success=True)
    
    async def get_vote_aggregations(self, project_id: str, 
                                  artifact_type: Optional[ArtifactType] = None) -> Dict[str, VoteAggregation]:
        """Get vote aggregations for a project or specific artifacts"""
        query = """
        SELECT artifact_type, artifact_id, upvotes, downvotes, total_votes, average_score
        FROM vote_aggregations
        WHERE project_id = %s
        """
        params = [project_id]
        
        if artifact_type:
            query += " AND artifact_type = %s"
            params.append(artifact_type.value)
        
        rows = await self.db.fetch_all(query, params)
        
        aggregations = {}
        for row in rows:
            key = f"{row['artifact_type']}:{row['artifact_id']}"
            aggregations[key] = VoteAggregation(
                upvotes=row['upvotes'],
                downvotes=row['downvotes'],
                total_votes=row['total_votes'],
                average_score=row['average_score']
            )
        
        return aggregations

class SpamDetector:
    def __init__(self, db_connection):
        self.db = db_connection
        self.rate_limits = {
            'votes_per_minute': 10,
            'votes_per_hour': 100,
            'votes_per_day': 500
        }
    
    async def check_vote_spam(self, vote_request: VoteRequest) -> SpamCheckResult:
        """Comprehensive spam detection for votes"""
        patterns = []
        
        # Check rate limiting
        rate_check = await self.check_rate_limits(vote_request)
        if rate_check.exceeded:
            patterns.append(AbusivePattern.RAPID_VOTING)
        
        # Check for vote bombing (many votes on same artifact quickly)
        bombing_check = await self.check_vote_bombing(vote_request)
        if bombing_check.detected:
            patterns.append(AbusivePattern.VOTE_BOMBING)
        
        # Check for coordinated voting (similar IPs voting similarly)
        coordination_check = await self.check_coordinated_voting(vote_request)
        if coordination_check.detected:
            patterns.append(AbusivePattern.COORDINATED)
        
        return SpamCheckResult(
            is_spam=len(patterns) > 0,
            pattern_type=patterns[0] if patterns else None,
            confidence=self.calculate_spam_confidence(patterns)
        )
    
    async def check_rate_limits(self, vote_request: VoteRequest) -> RateLimitResult:
        """Check if user/session has exceeded voting rate limits"""
        identifier = vote_request.user_id or vote_request.user_session
        
        time_windows = {
            'minute': datetime.now() - timedelta(minutes=1),
            'hour': datetime.now() - timedelta(hours=1),
            'day': datetime.now() - timedelta(days=1)
        }
        
        for window, since_time in time_windows.items():
            count = await self.count_votes_since(identifier, since_time)
            limit = self.rate_limits[f'votes_per_{window}']
            
            if count >= limit:
                return RateLimitResult(exceeded=True, window=window, count=count, limit=limit)
        
        return RateLimitResult(exceeded=False)
```

## System 4: Task Contribution System

### Database Schema

```sql
-- Task contributions table
CREATE TABLE task_contributions (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    contribution_type ENUM('new_task', 'task_improvement', 'personality', 'model_profile') NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    contributor_id VARCHAR(255),  -- user_id or model_id
    contributor_type ENUM('human', 'ai') NOT NULL,
    content_md TEXT NOT NULL,  -- The actual markdown content
    metadata_json JSON,  -- Additional structured metadata
    status ENUM('submitted', 'under_review', 'approved', 'rejected', 'needs_revision') DEFAULT 'submitted',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    reviewed_by VARCHAR(255),
    review_notes TEXT,
    approved_at TIMESTAMP NULL,
    INDEX idx_status_type (status, contribution_type),
    INDEX idx_contributor (contributor_id, contributor_type)
);

-- Contribution reviews
CREATE TABLE contribution_reviews (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    contribution_id INTEGER NOT NULL,
    reviewer_id VARCHAR(255) NOT NULL,
    reviewer_type ENUM('human', 'ai') NOT NULL,
    review_type ENUM('technical', 'content', 'quality', 'security') NOT NULL,
    score DECIMAL(3,2),  -- 0.00 to 1.00
    feedback TEXT,
    recommendation ENUM('approve', 'reject', 'needs_revision') NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contribution_id) REFERENCES task_contributions(id) ON DELETE CASCADE,
    INDEX idx_contribution_reviews (contribution_id, review_type)
);
```

### Contribution Service Implementation

```python
class ContributionType(Enum):
    NEW_TASK = "new_task"
    TASK_IMPROVEMENT = "task_improvement"
    PERSONALITY = "personality"
    MODEL_PROFILE = "model_profile"

class ContributionService:
    def __init__(self, db_connection, validation_service: ValidationService):
        self.db = db_connection
        self.validator = validation_service
        self.auto_reviewers = AutoReviewerPool()
    
    async def submit_contribution(self, contribution: ContributionRequest) -> ContributionResult:
        """Submit a new task contribution for review"""
        
        # Validate contribution format
        validation_result = await self.validator.validate_contribution(contribution)
        if not validation_result.is_valid:
            return ContributionResult(success=False, errors=validation_result.errors)
        
        # Store contribution
        contribution_id = await self.store_contribution(contribution)
        
        # Trigger automatic reviews
        await self.trigger_automatic_reviews(contribution_id, contribution.contribution_type)
        
        # Notify human reviewers if needed
        if contribution.contributor_type == ContributorType.HUMAN:
            await self.notify_human_reviewers(contribution_id)
        
        return ContributionResult(
            success=True,
            contribution_id=contribution_id,
            status=ContributionStatus.SUBMITTED
        )
    
    async def trigger_automatic_reviews(self, contribution_id: int, 
                                      contribution_type: ContributionType):
        """Trigger automated reviews for a contribution"""
        
        # Get contribution content
        contribution = await self.get_contribution(contribution_id)
        
        # Define review types based on contribution type
        review_types = self.get_required_review_types(contribution_type)
        
        for review_type in review_types:
            # Select appropriate AI reviewer
            reviewer = await self.auto_reviewers.select_reviewer(review_type, contribution_type)
            
            if reviewer:
                # Submit for AI review
                review_task = ReviewTask(
                    contribution_id=contribution_id,
                    reviewer_id=reviewer.model_id,
                    review_type=review_type,
                    content=contribution.content_md,
                    metadata=contribution.metadata_json
                )
                
                await self.queue_ai_review(review_task)
    
    def get_required_review_types(self, contribution_type: ContributionType) -> List[ReviewType]:
        """Determine what types of reviews are needed for a contribution"""
        review_mapping = {
            ContributionType.NEW_TASK: [
                ReviewType.TECHNICAL, ReviewType.CONTENT, ReviewType.SECURITY
            ],
            ContributionType.TASK_IMPROVEMENT: [
                ReviewType.TECHNICAL, ReviewType.CONTENT
            ],
            ContributionType.PERSONALITY: [
                ReviewType.CONTENT, ReviewType.QUALITY
            ],
            ContributionType.MODEL_PROFILE: [
                ReviewType.TECHNICAL, ReviewType.SECURITY
            ]
        }
        
        return review_mapping.get(contribution_type, [ReviewType.CONTENT])

class AutoReviewerPool:
    def __init__(self):
        self.technical_reviewers = [
            "claude-3.5-sonnet", "gpt-4-turbo", "gemini-1.5-pro"
        ]
        self.content_reviewers = [
            "claude-3.5-sonnet", "gpt-4-turbo"
        ]
        self.security_reviewers = [
            "claude-3.5-sonnet"  # Models specifically good at security analysis
        ]
    
    async def select_reviewer(self, review_type: ReviewType, 
                            contribution_type: ContributionType) -> Optional[ModelInfo]:
        """Select the best available model for a specific review type"""
        
        reviewer_pool = {
            ReviewType.TECHNICAL: self.technical_reviewers,
            ReviewType.CONTENT: self.content_reviewers,
            ReviewType.SECURITY: self.security_reviewers,
            ReviewType.QUALITY: self.content_reviewers
        }.get(review_type, self.content_reviewers)
        
        # Select based on availability and capability
        for model_id in reviewer_pool:
            model_info = await self.get_model_info(model_id)
            if model_info and model_info.is_available:
                return model_info
        
        return None
```

## System 5: Automated Curation System

### Curation Job Architecture

```python
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio
from datetime import datetime, timedelta

class CurationIssueType(Enum):
    INCOMPLETE_ENTRY = "incomplete_entry"
    INCORRECT_FORMAT = "incorrect_format"
    MISSING_INFORMATION = "missing_information"
    CORRECTNESS_CONCERN = "correctness_concern"
    OPTIMIZATION_OPPORTUNITY = "optimization_opportunity"

@dataclass
class CurationIssue:
    issue_type: CurationIssueType
    severity: str  # "low", "medium", "high", "critical"
    project_id: str
    artifact_path: str
    description: str
    suggested_fix: Optional[str]
    requires_human_review: bool
    detected_at: datetime
    auto_fixable: bool

class CurationScheduler:
    def __init__(self, db_connection, issue_detector: IssueDetector):
        self.db = db_connection
        self.detector = issue_detector
        self.curation_jobs = {
            'daily': self.run_daily_curation,
            'weekly': self.run_weekly_curation,
            'monthly': self.run_monthly_curation
        }
    
    async def run_daily_curation(self):
        """Daily curation tasks - lightweight checks"""
        projects = await self.get_recently_updated_projects(days=1)
        
        for project in projects:
            issues = []
            
            # Check for incomplete entries
            incomplete_issues = await self.detector.check_incomplete_entries(project)
            issues.extend(incomplete_issues)
            
            # Check formatting
            format_issues = await self.detector.check_formatting(project)
            issues.extend(format_issues)
            
            # Process and store issues
            await self.process_detected_issues(issues)
    
    async def run_weekly_curation(self):
        """Weekly curation tasks - more comprehensive"""
        projects = await self.get_recently_updated_projects(days=7)
        
        for project in projects:
            issues = []
            
            # All daily checks
            issues.extend(await self.detector.check_incomplete_entries(project))
            issues.extend(await self.detector.check_formatting(project))
            
            # Missing information checks
            missing_info_issues = await self.detector.check_missing_information(project)
            issues.extend(missing_info_issues)
            
            # Basic correctness checks
            correctness_issues = await self.detector.check_basic_correctness(project)
            issues.extend(correctness_issues)
            
            await self.process_detected_issues(issues)
    
    async def run_monthly_curation(self):
        """Monthly curation tasks - comprehensive quality review"""
        all_projects = await self.get_all_active_projects()
        
        for project in all_projects:
            issues = []
            
            # Comprehensive correctness review
            correctness_issues = await self.detector.comprehensive_correctness_check(project)
            issues.extend(correctness_issues)
            
            # Optimization opportunities (high-capability models only)
            optimization_issues = await self.detector.check_optimization_opportunities(project)
            issues.extend(optimization_issues)
            
            await self.process_detected_issues(issues)

class IssueDetector:
    def __init__(self, model_pool: ModelPool):
        self.model_pool = model_pool
        
    async def check_incomplete_entries(self, project: Project) -> List[CurationIssue]:
        """Detect incomplete or stub entries that should be removed"""
        issues = []
        
        # Check for files with minimal content
        for artifact in project.get_all_artifacts():
            if artifact.file_type in ['.md', '.py', '.tex']:
                content = await artifact.read_content()
                
                # Check for various incompleteness indicators
                if self.is_incomplete_content(content):
                    issues.append(CurationIssue(
                        issue_type=CurationIssueType.INCOMPLETE_ENTRY,
                        severity="medium",
                        project_id=project.id,
                        artifact_path=artifact.path,
                        description=f"File appears incomplete: {len(content)} chars, lacks substantial content",
                        suggested_fix="Remove file or complete implementation",
                        requires_human_review=True,
                        detected_at=datetime.now(),
                        auto_fixable=False
                    ))
        
        return issues
    
    def is_incomplete_content(self, content: str) -> bool:
        """Determine if content appears incomplete"""
        content = content.strip()
        
        # Too short
        if len(content) < 100:
            return True
        
        # Common placeholder patterns
        placeholder_patterns = [
            "TODO", "FIXME", "placeholder", "stub", "not implemented",
            "coming soon", "work in progress", "TBD"
        ]
        
        content_lower = content.lower()
        placeholder_count = sum(1 for pattern in placeholder_patterns if pattern in content_lower)
        
        # High ratio of placeholder content
        if placeholder_count > 3 or (placeholder_count > 0 and len(content) < 500):
            return True
        
        return False
    
    async def check_formatting(self, project: Project) -> List[CurationIssue]:
        """Check for formatting issues that can be auto-corrected"""
        issues = []
        
        for artifact in project.get_markdown_artifacts():
            content = await artifact.read_content()
            formatting_issues = self.detect_formatting_issues(content)
            
            for issue_desc, fix in formatting_issues:
                issues.append(CurationIssue(
                    issue_type=CurationIssueType.INCORRECT_FORMAT,
                    severity="low",
                    project_id=project.id,
                    artifact_path=artifact.path,
                    description=issue_desc,
                    suggested_fix=fix,
                    requires_human_review=False,
                    detected_at=datetime.now(),
                    auto_fixable=True
                ))
        
        return issues
    
    def detect_formatting_issues(self, content: str) -> List[Tuple[str, str]]:
        """Detect common markdown formatting issues"""
        issues = []
        
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            # Missing space after hash in headers
            if re.match(r'^#+[^#\s]', line):
                issues.append((
                    f"Line {i+1}: Missing space after # in header",
                    "Add space after # symbols"
                ))
            
            # Inconsistent list formatting
            if re.match(r'^\s*[-*+]\S', line):
                issues.append((
                    f"Line {i+1}: Missing space after list marker",
                    "Add space after list marker"
                ))
            
            # Trailing whitespace
            if line.endswith(' ') or line.endswith('\t'):
                issues.append((
                    f"Line {i+1}: Trailing whitespace",
                    "Remove trailing whitespace"
                ))
        
        return issues
    
    async def comprehensive_correctness_check(self, project: Project) -> List[CurationIssue]:
        """Use high-capability models to check correctness"""
        issues = []
        
        # Select high-capability model for correctness checking
        model = await self.model_pool.get_high_capability_model([
            "claude-3.5-sonnet", "claude-3-opus", "gpt-4-turbo", "gemini-1.5-pro"
        ])
        
        if not model:
            return issues
        
        # Check different types of artifacts
        for artifact in project.get_code_artifacts():
            correctness_result = await self.check_code_correctness(artifact, model)
            if correctness_result.has_issues:
                issues.extend(correctness_result.issues)
        
        for artifact in project.get_paper_artifacts():
            correctness_result = await self.check_paper_correctness(artifact, model)
            if correctness_result.has_issues:
                issues.extend(correctness_result.issues)
        
        return issues
    
    async def check_code_correctness(self, artifact: Artifact, model: Model) -> CorrectnessResult:
        """Use AI to check code correctness"""
        content = await artifact.read_content()
        
        prompt = f"""
        Please review this code for correctness, identifying any:
        1. Logical errors or bugs
        2. Incorrect assumptions
        3. Security vulnerabilities
        4. Performance issues
        5. Best practice violations
        
        Code file: {artifact.path}
        ```{artifact.language}
        {content}
        ```
        
        For each issue found, provide:
        - Issue type and severity
        - Line number(s) affected
        - Description of the problem
        - Suggested fix
        
        Respond in JSON format with an array of issues.
        """
        
        response = await model.generate(prompt)
        issues = self.parse_correctness_response(response, artifact)
        
        return CorrectnessResult(has_issues=len(issues) > 0, issues=issues)
```

## System 6: Model Pool Management

### Model Database Schema

```sql
-- Models registry
CREATE TABLE models_registry (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    model_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(500) NOT NULL,
    provider ENUM('anthropic', 'openai', 'google', 'huggingface', 'ollama', 'local') NOT NULL,
    model_type ENUM('completion', 'chat', 'embedding', 'multimodal') NOT NULL,
    version VARCHAR(100),
    source_url TEXT,
    documentation_url TEXT,
    status ENUM('active', 'deprecated', 'experimental', 'unavailable') DEFAULT 'experimental',
    vetting_status ENUM('unvetted', 'in_review', 'vetted', 'rejected') DEFAULT 'unvetted',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_provider_status (provider, status),
    INDEX idx_vetting_status (vetting_status)
);

-- Model capabilities
CREATE TABLE model_capabilities (
    model_id VARCHAR(255) NOT NULL,
    capability_type VARCHAR(100) NOT NULL,
    capability_level ENUM('none', 'basic', 'intermediate', 'advanced', 'expert') NOT NULL,
    confidence_score DECIMAL(3,2),  -- 0.00 to 1.00
    benchmark_score DECIMAL(5,4),   -- Raw benchmark score
    notes TEXT,
    assessed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    assessed_by VARCHAR(255),  -- assessor ID
    FOREIGN KEY (model_id) REFERENCES models_registry(model_id) ON DELETE CASCADE,
    PRIMARY KEY (model_id, capability_type)
);

-- Model configurations
CREATE TABLE model_configurations (
    model_id VARCHAR(255) NOT NULL,
    config_key VARCHAR(255) NOT NULL,
    config_value JSON NOT NULL,
    config_type ENUM('parameter', 'security', 'access', 'deployment') NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (model_id) REFERENCES models_registry(model_id) ON DELETE CASCADE,
    PRIMARY KEY (model_id, config_key)
);

-- Model performance metrics
CREATE TABLE model_performance (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    model_id VARCHAR(255) NOT NULL,
    task_type VARCHAR(100) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(8,4) NOT NULL,
    measurement_date DATE NOT NULL,
    project_id VARCHAR(255),  -- Optional: performance on specific project
    notes TEXT,
    FOREIGN KEY (model_id) REFERENCES models_registry(model_id) ON DELETE CASCADE,
    INDEX idx_model_task_performance (model_id, task_type, measurement_date)
);
```

### Model Discovery and Management

```python
import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

class ModelDiscoveryService:
    def __init__(self, db_connection):
        self.db = db_connection
        self.discovery_sources = {
            'huggingface': HuggingFaceDiscovery(),
            'anthropic': AnthropicDiscovery(),
            'openai': OpenAIDiscovery()
        }
        self.vetting_service = ModelVettingService(db_connection)
    
    async def discover_new_models(self, source: Optional[str] = None) -> List[ModelCandidate]:
        """Discover new models from various sources"""
        candidates = []
        
        sources = [source] if source else self.discovery_sources.keys()
        
        for source_name in sources:
            discovery_service = self.discovery_sources[source_name]
            try:
                source_candidates = await discovery_service.discover_models()
                candidates.extend(source_candidates)
            except Exception as e:
                logger.error(f"Failed to discover models from {source_name}: {e}")
        
        # Filter out already known models
        new_candidates = await self.filter_new_models(candidates)
        
        return new_candidates
    
    async def filter_new_models(self, candidates: List[ModelCandidate]) -> List[ModelCandidate]:
        """Filter out models already in our registry"""
        existing_models = await self.get_existing_model_ids()
        
        new_candidates = []
        for candidate in candidates:
            if candidate.model_id not in existing_models:
                new_candidates.append(candidate)
        
        return new_candidates
    
    async def queue_model_for_vetting(self, candidate: ModelCandidate) -> bool:
        """Add a discovered model to the vetting queue"""
        try:
            # Store in registry with 'unvetted' status
            await self.store_model_candidate(candidate)
            
            # Queue for automated vetting
            await self.vetting_service.queue_for_vetting(candidate.model_id)
            
            return True
        except Exception as e:
            logger.error(f"Failed to queue model {candidate.model_id} for vetting: {e}")
            return False

class HuggingFaceDiscovery:
    def __init__(self):
        self.api_url = "https://huggingface.co/api"
        self.interesting_tags = [
            "text-generation", "conversational", "question-answering",
            "code-generation", "scientific", "reasoning"
        ]
    
    async def discover_models(self) -> List[ModelCandidate]:
        """Discover promising models from HuggingFace"""
        candidates = []
        
        async with aiohttp.ClientSession() as session:
            for tag in self.interesting_tags:
                models = await self.search_models_by_tag(session, tag)
                for model_info in models:
                    if self.is_promising_model(model_info):
                        candidate = self.create_model_candidate(model_info)
                        candidates.append(candidate)
        
        return candidates
    
    async def search_models_by_tag(self, session: aiohttp.ClientSession, 
                                 tag: str) -> List[Dict[str, Any]]:
        """Search HuggingFace for models with specific tags"""
        url = f"{self.api_url}/models"
        params = {
            'filter': tag,
            'sort': 'downloads',
            'direction': -1,
            'limit': 50
        }
        
        async with session.get(url, params=params) as response:
            if response.status == 200:
                return await response.json()
            else:
                return []
    
    def is_promising_model(self, model_info: Dict[str, Any]) -> bool:
        """Determine if a model is worth vetting"""
        # Check download count
        downloads = model_info.get('downloads', 0)
        if downloads < 1000:  # Minimum threshold
            return False
        
        # Check model size (prefer larger models for reasoning tasks)
        model_size = self.estimate_model_size(model_info)
        if model_size and model_size < 7_000_000_000:  # Less than 7B parameters
            return False
        
        # Check for promising keywords in description
        description = model_info.get('description', '').lower()
        positive_keywords = [
            'reasoning', 'coding', 'scientific', 'research', 'instruction',
            'chat', 'assistant', 'helpful', 'accurate'
        ]
        
        keyword_score = sum(1 for keyword in positive_keywords if keyword in description)
        
        return keyword_score >= 2
    
    def estimate_model_size(self, model_info: Dict[str, Any]) -> Optional[int]:
        """Estimate model parameter count from available information"""
        # Try to extract from model name or description
        name = model_info.get('modelId', '').lower()
        description = model_info.get('description', '').lower()
        
        text = f"{name} {description}"
        
        # Look for parameter count indicators
        import re
        size_patterns = [
            r'(\d+)b\b',  # e.g., "7b", "13b"
            r'(\d+)\s*billion',
            r'(\d+\.?\d*)\s*b\s*param',
        ]
        
        for pattern in size_patterns:
            match = re.search(pattern, text)
            if match:
                size_str = match.group(1)
                try:
                    size_b = float(size_str)
                    return int(size_b * 1_000_000_000)  # Convert to actual parameter count
                except ValueError:
                    continue
        
        return None

class ModelVettingService:
    def __init__(self, db_connection):
        self.db = db_connection
        self.vetting_tasks = [
            'basic_reasoning',
            'code_generation',
            'technical_writing',
            'instruction_following',
            'safety_compliance'
        ]
    
    async def queue_for_vetting(self, model_id: str):
        """Queue a model for automated vetting"""
        await self.update_vetting_status(model_id, 'in_review')
        
        # Run vetting tasks
        vetting_results = {}
        for task in self.vetting_tasks:
            result = await self.run_vetting_task(model_id, task)
            vetting_results[task] = result
        
        # Evaluate overall vetting score
        overall_score = self.calculate_vetting_score(vetting_results)
        
        # Decide on vetting outcome
        if overall_score >= 0.7:
            await self.approve_model(model_id, vetting_results)
        elif overall_score >= 0.5:
            await self.flag_for_human_review(model_id, vetting_results)
        else:
            await self.reject_model(model_id, vetting_results)
    
    async def run_vetting_task(self, model_id: str, task_type: str) -> VettingTaskResult:
        """Run a specific vetting task for a model"""
        task_config = self.get_vetting_task_config(task_type)
        
        try:
            # Load the model
            model = await self.load_model_for_testing(model_id)
            
            # Run the vetting task
            response = await model.generate(
                prompt=task_config['prompt'],
                max_tokens=task_config['max_tokens'],
                temperature=task_config['temperature']
            )
            
            # Evaluate the response
            score = await self.evaluate_vetting_response(
                task_type, task_config['expected_criteria'], response
            )
            
            return VettingTaskResult(
                task_type=task_type,
                score=score,
                response=response,
                success=True
            )
            
        except Exception as e:
            return VettingTaskResult(
                task_type=task_type,
                score=0.0,
                response="",
                success=False,
                error=str(e)
            )
    
    def get_vetting_task_config(self, task_type: str) -> Dict[str, Any]:
        """Get configuration for a specific vetting task"""
        configs = {
            'basic_reasoning': {
                'prompt': """Solve this step by step:
                A farmer has 17 sheep. All but 9 die. How many sheep are left?
                
                Show your reasoning clearly.""",
                'max_tokens': 200,
                'temperature': 0.1,
                'expected_criteria': ['correct_answer', 'clear_reasoning', 'step_by_step']
            },
            'code_generation': {
                'prompt': """Write a Python function that takes a list of integers and returns the list sorted in ascending order, but with all even numbers appearing before odd numbers.
                
                Example: [3, 1, 4, 2, 5] → [2, 4, 1, 3, 5]""",
                'max_tokens': 300,
                'temperature': 0.2,
                'expected_criteria': ['syntactically_correct', 'functionally_correct', 'good_style']
            },
            'technical_writing': {
                'prompt': """Explain the concept of "Big O notation" in computer science in a way that would be accessible to someone with basic programming knowledge but no formal computer science background.""",
                'max_tokens': 400,
                'temperature': 0.3,
                'expected_criteria': ['clear_explanation', 'appropriate_examples', 'correct_information']
            }
        }
        
        return configs.get(task_type, {})
```

## Integration with Core Architecture

### Updated Orchestrator Integration

```python
class OrchestratorV2Enhanced:
    def __init__(self, config_path: str):
        # Core components (from original design)
        self.config = ConfigManager(config_path)
        self.project_manager = ProjectManager(self.config)
        self.validation_engine = ValidationEngine(self.config)
        
        # Enhanced components
        self.task_manager = TaskManagerV2(self.config)
        self.model_manager = ModelManagerV2(self.config)
        self.personality_manager = PersonalityManagerV2(self.config)
        
        # New systems
        self.voting_service = VotingService(self.config.db_connection)
        self.contribution_service = ContributionService(self.config.db_connection)
        self.curation_scheduler = CurationScheduler(self.config.db_connection)
        self.model_discovery = ModelDiscoveryService(self.config.db_connection)
        
    async def execute_project_cycle(self, project_id: str) -> Dict[str, Any]:
        """Enhanced project cycle execution with new systems"""
        project = await self.project_manager.load_project(project_id)
        
        # Validate project state
        validation_result = await self.validation_engine.validate_project(project)
        if not validation_result.is_valid:
            raise ValidationError(validation_result.errors)
        
        # Get human feedback from voting system
        vote_aggregations = await self.voting_service.get_vote_aggregations(project_id)
        
        # Determine next tasks using enhanced task management
        next_tasks = await self.task_manager.get_next_tasks(project, vote_aggregations)
        
        # Execute tasks with personality-enhanced models
        results = []
        for task in next_tasks:
            # Select model and personality
            model = await self.model_manager.select_model(task)
            personalities = await self.personality_manager.select_personalities(task, model)
            
            # Build enhanced prompt
            enhanced_prompt = await self.personality_manager.build_system_prompt(
                task.base_prompt, personalities, task.context
            )
            
            # Execute task
            result = await self.task_manager.execute_task(task, model, enhanced_prompt)
            results.append(result)
            
            # Update project state
            await self.project_manager.update_project(project, task, result)
        
        return results
    
    async def run_curation_cycle(self):
        """Run automated curation and quality control"""
        await self.curation_scheduler.run_daily_curation()
        
        # Also discover new models periodically
        new_models = await self.model_discovery.discover_new_models()
        for model in new_models:
            await self.model_discovery.queue_model_for_vetting(model)
```

## Implementation Priority and Timeline

### Phase 1: Foundation Systems (4-6 weeks)
1. **Task Type Management** (Week 1-2)
   - File-based task definitions
   - Task loader and parser
   - Integration with orchestrator

2. **Personality Management** (Week 2-3)
   - Personality definition system
   - Prompt building engine
   - Basic compatibility checking

3. **Voting System** (Week 3-4)
   - Database schema and API
   - Basic web interface
   - Spam detection

### Phase 2: Contribution and Quality Control (4-6 weeks)
4. **Task Contribution System** (Week 5-6)
   - Submission workflow
   - Automated review system
   - Approval process

5. **Automated Curation** (Week 7-8)
   - Basic issue detection
   - Automated fixes
   - Human review integration

### Phase 3: Advanced Model Management (3-4 weeks)
6. **Model Pool Management** (Week 9-10)
   - Discovery system
   - Vetting framework
   - Performance tracking

## Security Considerations

### Task and Personality Security
- **Prompt Injection Prevention**: Validate all task definitions and personality prompts
- **Content Sanitization**: Strip potentially malicious content from contributions
- **Access Controls**: Limit who can modify core task/personality definitions

### Voting System Security
- **Rate Limiting**: Prevent vote bombing and spam
- **Identity Verification**: Track anonymous users via sessions
- **Abuse Detection**: Machine learning-based spam detection

### Model Security
- **Sandboxed Vetting**: Run model tests in isolated environments
- **Capability Restrictions**: Limit model access during vetting
- **Security Scanning**: Check models for potential security issues

## Conclusion

These six additional systems provide comprehensive coverage of task management, quality control, and community engagement needs for llmXive v2.0. The designs integrate seamlessly with the existing architecture while maintaining security, scalability, and maintainability principles.

The phased implementation approach ensures that foundational systems are solid before building more complex features, while the security-first design protects against common vulnerabilities in AI-driven systems.

---

*This document extends the core llmXive v2.0 design with essential systems for community engagement, quality control, and model management.*