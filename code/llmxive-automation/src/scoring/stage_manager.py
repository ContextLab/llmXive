"""Stage transition management for llmXive projects."""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from enum import Enum

from .score_tracker import ScoreTracker

logger = logging.getLogger(__name__)


class ProjectStage(Enum):
    """Project stages in the llmXive pipeline."""
    BACKLOG = "backlog"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    DONE = "done"


class StageTransition:
    """Represents a stage transition."""
    
    def __init__(self, from_stage: ProjectStage, to_stage: ProjectStage,
                 requirements: Dict[str, any], timestamp: Optional[datetime] = None):
        """Initialize a stage transition.
        
        Args:
            from_stage: Starting stage
            to_stage: Target stage
            requirements: Requirements that must be met
            timestamp: When the transition occurred
        """
        self.from_stage = from_stage
        self.to_stage = to_stage
        self.requirements = requirements
        self.timestamp = timestamp or datetime.now(timezone.utc)
        self.validation_results = {}
    
    def is_valid(self) -> bool:
        """Check if all requirements were met."""
        return all(self.validation_results.values())


class StageManager:
    """Manages project stage transitions."""
    
    # Define valid transitions and their requirements
    TRANSITIONS = {
        ProjectStage.BACKLOG: {
            'next': ProjectStage.READY,
            'requirements': {
                'has_technical_design': True,
                'score_threshold': 5.0,
                'required_artifacts': ['technical_design_document']
            }
        },
        ProjectStage.READY: {
            'next': ProjectStage.IN_PROGRESS,
            'requirements': {
                'has_implementation_plan': True,
                'score_threshold': 5.0,
                'required_artifacts': ['implementation_plan']
            }
        },
        ProjectStage.IN_PROGRESS: {
            'next': ProjectStage.IN_REVIEW,
            'requirements': {
                'has_paper_draft': True,
                'has_complete_code': True,
                'score_threshold': 1.0,  # Only 1 model needed to signal completion
                'required_artifacts': ['paper_draft', 'code_repository']
            }
        },
        ProjectStage.IN_REVIEW: {
            'next': ProjectStage.DONE,
            'requirements': {
                'has_paper_pdf': True,
                'score_threshold': 5.0,  # Need 5 points after comprehensive reviews
                'required_artifacts': ['paper_pdf', 'code_repository']
            }
        },
        ProjectStage.DONE: {
            'next': None,  # Terminal stage
            'requirements': {}
        }
    }
    
    def __init__(self, score_tracker: ScoreTracker, github_handler=None):
        """Initialize stage manager.
        
        Args:
            score_tracker: ScoreTracker instance
            github_handler: Optional GitHub handler for label management
        """
        self.score_tracker = score_tracker
        self.github = github_handler
        self.project_stages = {}  # project_id -> current stage
        self.transition_history = {}  # project_id -> list of transitions
    
    def get_current_stage(self, project_id: str) -> ProjectStage:
        """Get the current stage of a project.
        
        Args:
            project_id: Project identifier
            
        Returns:
            Current stage (defaults to BACKLOG)
        """
        return self.project_stages.get(project_id, ProjectStage.BACKLOG)
    
    def can_advance(self, project_id: str, project_state: Dict[str, any]) -> Tuple[bool, Dict[str, bool]]:
        """Check if a project can advance to the next stage.
        
        Args:
            project_id: Project identifier
            project_state: Current project state with artifacts, score, etc.
            
        Returns:
            Tuple of (can_advance, requirement_results)
        """
        current_stage = self.get_current_stage(project_id)
        
        # Check if there's a next stage
        transition_config = self.TRANSITIONS.get(current_stage)
        if not transition_config or transition_config['next'] is None:
            return False, {'no_next_stage': False}
        
        requirements = transition_config['requirements']
        results = {}
        
        # Check score threshold
        if 'score_threshold' in requirements:
            current_score = self.score_tracker.get_current_score(project_id)
            results['score_threshold_met'] = current_score >= requirements['score_threshold']
        
        # Check required artifacts
        if 'required_artifacts' in requirements:
            artifacts = project_state.get('artifacts', {})
            for artifact in requirements['required_artifacts']:
                results[f'has_{artifact}'] = artifact in artifacts and artifacts[artifact] is not None
        
        # Check specific boolean requirements
        for key, expected_value in requirements.items():
            if key not in ['score_threshold', 'required_artifacts'] and isinstance(expected_value, bool):
                results[key] = project_state.get(key, False) == expected_value
        
        # All requirements must be met
        can_advance = all(results.values())
        
        return can_advance, results
    
    def advance_stage(self, project_id: str, project_state: Dict[str, any],
                     force: bool = False) -> Tuple[bool, Optional[StageTransition]]:
        """Advance a project to the next stage.
        
        Args:
            project_id: Project identifier
            project_state: Current project state
            force: Force transition even if requirements not met
            
        Returns:
            Tuple of (success, transition_record)
        """
        current_stage = self.get_current_stage(project_id)
        
        # Check if advancement is possible
        can_advance, validation_results = self.can_advance(project_id, project_state)
        
        if not can_advance and not force:
            logger.warning(f"Cannot advance {project_id} from {current_stage.value}: "
                          f"Requirements not met: {validation_results}")
            return False, None
        
        # Get next stage
        transition_config = self.TRANSITIONS.get(current_stage)
        if not transition_config or transition_config['next'] is None:
            logger.error(f"No next stage defined for {current_stage.value}")
            return False, None
        
        next_stage = transition_config['next']
        
        # Create transition record
        transition = StageTransition(
            from_stage=current_stage,
            to_stage=next_stage,
            requirements=transition_config['requirements']
        )
        transition.validation_results = validation_results
        
        # Update current stage
        old_stage = current_stage
        self.project_stages[project_id] = next_stage
        
        # Record transition
        if project_id not in self.transition_history:
            self.transition_history[project_id] = []
        self.transition_history[project_id].append(transition)
        
        # Reset score for new stage
        self.score_tracker.reset_score(project_id, reason=f"advanced_to_{next_stage.value}")
        
        # Update GitHub labels if available
        if self.github and 'issue_number' in project_state:
            self._update_stage_labels(project_state['issue_number'], old_stage, next_stage)
        
        logger.info(f"Advanced {project_id} from {old_stage.value} to {next_stage.value}")
        
        return True, transition
    
    def set_stage(self, project_id: str, stage: ProjectStage, 
                  reason: str = "manual_set") -> None:
        """Manually set a project's stage.
        
        Args:
            project_id: Project identifier
            stage: New stage
            reason: Reason for manual setting
        """
        old_stage = self.get_current_stage(project_id)
        self.project_stages[project_id] = stage
        
        # Record as special transition
        transition = StageTransition(
            from_stage=old_stage,
            to_stage=stage,
            requirements={'manual': True, 'reason': reason}
        )
        
        if project_id not in self.transition_history:
            self.transition_history[project_id] = []
        self.transition_history[project_id].append(transition)
        
        logger.info(f"Manually set {project_id} stage to {stage.value} (reason: {reason})")
    
    def move_to_previous_stage(self, project_id: str, project_state: Dict[str, any],
                               reason: str = "critical_review") -> Tuple[bool, Optional[StageTransition]]:
        """Move a project back to the previous stage.
        
        Args:
            project_id: Project identifier
            project_state: Current project state
            reason: Reason for moving back
            
        Returns:
            Tuple of (success, transition_record)
        """
        current_stage = self.get_current_stage(project_id)
        
        # Define previous stages
        previous_stages = {
            ProjectStage.READY: ProjectStage.BACKLOG,
            ProjectStage.IN_PROGRESS: ProjectStage.READY,
            ProjectStage.IN_REVIEW: ProjectStage.IN_PROGRESS,
            ProjectStage.DONE: ProjectStage.IN_REVIEW
        }
        
        if current_stage not in previous_stages:
            logger.error(f"Cannot move back from {current_stage.value}")
            return False, None
        
        previous_stage = previous_stages[current_stage]
        
        # Create transition record
        transition = StageTransition(
            from_stage=current_stage,
            to_stage=previous_stage,
            requirements={'moved_back': True, 'reason': reason}
        )
        
        # Update current stage
        self.project_stages[project_id] = previous_stage
        
        # Record transition
        if project_id not in self.transition_history:
            self.transition_history[project_id] = []
        self.transition_history[project_id].append(transition)
        
        # Reset score
        self.score_tracker.reset_score(project_id, reason=f"moved_back_to_{previous_stage.value}")
        
        # Update GitHub labels if available
        if self.github and 'issue_number' in project_state:
            self._update_stage_labels(project_state['issue_number'], current_stage, previous_stage)
        
        logger.info(f"Moved {project_id} back from {current_stage.value} to {previous_stage.value} (reason: {reason})")
        
        return True, transition
    
    def get_transition_history(self, project_id: str) -> List[StageTransition]:
        """Get the transition history for a project.
        
        Args:
            project_id: Project identifier
            
        Returns:
            List of transitions
        """
        return self.transition_history.get(project_id, [])
    
    def get_stage_summary(self, project_id: str, project_state: Dict[str, any]) -> Dict[str, any]:
        """Get a summary of the project's stage status.
        
        Args:
            project_id: Project identifier
            project_state: Current project state
            
        Returns:
            Summary dictionary
        """
        current_stage = self.get_current_stage(project_id)
        can_advance, requirements = self.can_advance(project_id, project_state)
        current_score = self.score_tracker.get_current_score(project_id)
        
        # Get next stage info
        transition_config = self.TRANSITIONS.get(current_stage, {})
        next_stage = transition_config.get('next')
        
        summary = {
            'current_stage': current_stage.value,
            'next_stage': next_stage.value if next_stage else None,
            'can_advance': can_advance,
            'current_score': current_score,
            'requirements_met': requirements,
            'transition_count': len(self.get_transition_history(project_id))
        }
        
        # Add missing requirements
        if not can_advance and requirements:
            summary['missing_requirements'] = [
                req for req, met in requirements.items() if not met
            ]
        
        return summary
    
    def _update_stage_labels(self, issue_number: int, 
                           old_stage: ProjectStage, new_stage: ProjectStage) -> None:
        """Update stage labels on GitHub issue.
        
        Args:
            issue_number: GitHub issue number
            old_stage: Previous stage
            new_stage: New stage
        """
        try:
            # Remove old stage label
            old_label = f"stage: {old_stage.value}"
            self.github.remove_label(issue_number, old_label)
            
            # Add new stage label
            new_label = f"stage: {new_stage.value}"
            self.github.add_label(issue_number, new_label)
            
            # Update project board if applicable
            if hasattr(self.github, 'move_to_column'):
                column_mapping = {
                    ProjectStage.BACKLOG: "Backlog",
                    ProjectStage.READY: "Ready",
                    ProjectStage.IN_PROGRESS: "In Progress",
                    ProjectStage.IN_REVIEW: "In Review",
                    ProjectStage.DONE: "Done"
                }
                if new_stage in column_mapping:
                    self.github.move_to_column(issue_number, column_mapping[new_stage])
            
            logger.info(f"Updated labels for issue #{issue_number}: "
                       f"{old_stage.value} -> {new_stage.value}")
            
        except Exception as e:
            logger.error(f"Failed to update stage labels: {e}")
    
    def validate_stage_transitions(self, project_id: str) -> List[str]:
        """Validate that all stage transitions were valid.
        
        Args:
            project_id: Project identifier
            
        Returns:
            List of validation messages
        """
        messages = []
        transitions = self.get_transition_history(project_id)
        
        for i, transition in enumerate(transitions):
            # Check if it was a valid progression
            expected_next = self.TRANSITIONS.get(transition.from_stage, {}).get('next')
            
            if transition.requirements.get('manual'):
                messages.append(f"Transition {i+1}: Manual set to {transition.to_stage.value} "
                              f"(reason: {transition.requirements.get('reason')})")
            elif transition.to_stage != expected_next:
                messages.append(f"❌ Transition {i+1}: Invalid transition from "
                              f"{transition.from_stage.value} to {transition.to_stage.value}")
            elif not transition.is_valid():
                messages.append(f"⚠️  Transition {i+1}: Requirements not fully met for "
                              f"{transition.from_stage.value} -> {transition.to_stage.value}")
            else:
                messages.append(f"✅ Transition {i+1}: Valid transition to {transition.to_stage.value}")
        
        return messages