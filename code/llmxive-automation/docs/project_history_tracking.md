# Project History Tracking System

## Overview

A comprehensive history tracking system that records every action, decision, and contribution throughout a project's lifecycle. This provides both audit trails and valuable insights into the scientific discovery process.

## 1. History File Structure

### 1.1 Location and Naming
```
project_histories/
├── <project-id>/
│   ├── history.md          # Human-readable history
│   ├── history.json        # Machine-readable detailed history
│   └── history_summary.md  # Condensed summary for papers
```

### 1.2 History Entry Format

#### Markdown Format (history.md)
```markdown
# Project History: <project-title>
**Project ID**: <project-id>
**Started**: 2025-07-04 10:23:45 UTC
**Current Status**: In Progress
**Current Score**: 4.5

## Timeline

### 2025-07-04

**10:23:45** | `gpt2-small` | 🚀 Generated idea: "Analyzing Patterns in Synthetic Time Series Data"
- Issue: [#23](https://github.com/user/repo/issues/23)
- Initial brainstorming focused on anomaly detection in financial data

**10:25:12** | `gpt2-small` | 📝 Created [technical design document](../technical_design_documents/test-2025-001/design.md)
- Commit: [a1b2c3d](https://github.com/user/repo/commit/a1b2c3d)
- Proposed novel approach using wavelet transforms

**10:30:45** | `@human-user` | 👍 Upvoted idea (Stats: 1 👍, 0 👎, 12 views)

**10:35:22** | `tinyllama-1.1b` | 📋 [Reviewed](../reviews/test-2025-001/Design/tinyllama-1.1b__07-04-2025__A.md) technical design ([v1.0](https://github.com/user/repo/blob/a1b2c3d/technical_design_documents/test-2025-001/design.md))
- Score: +0.5 (Total: 0.5)
- Highlighted strong theoretical foundation

**10:40:18** | `phi-2` | 📋 [Critical Review](../reviews/test-2025-001/Design/phi-2__07-04-2025__A.md) - identified edge case issue
- Score: RESET TO 0 (Total: 0.0)
- Issue: Missing validation for empty time series
- Moved back to: Technical Design stage

**10:45:30** | `gpt2-small` | 🔧 Updated [technical design](../technical_design_documents/test-2025-001/design.md) addressing critical feedback
- Commit: [b2c3d4e](https://github.com/user/repo/commit/b2c3d4e)
- Added comprehensive edge case handling

### 2025-07-05

**09:15:00** | `mixtral-8x7b` | 📋 [Reviewed](../reviews/test-2025-001/Design/mixtral-8x7b__07-05-2025__A.md) revised design
- Score: +0.5 (Total: 0.5)
- Confirmed edge cases now properly addressed

[... continuing with all events ...]
```

#### JSON Format (history.json)
```json
{
  "project_id": "test-2025-001",
  "project_title": "Analyzing Patterns in Synthetic Time Series Data",
  "created_at": "2025-07-04T10:23:45Z",
  "events": [
    {
      "timestamp": "2025-07-04T10:23:45Z",
      "event_type": "idea_generated",
      "author": {
        "type": "model",
        "id": "gpt2-small",
        "version": "latest"
      },
      "action": "Generated project idea",
      "details": {
        "title": "Analyzing Patterns in Synthetic Time Series Data",
        "description": "Initial brainstorming focused on anomaly detection"
      },
      "artifacts": {
        "issue": {
          "type": "github_issue",
          "number": 23,
          "url": "https://github.com/user/repo/issues/23"
        }
      },
      "metadata": {
        "score_before": 0,
        "score_after": 0,
        "stage_before": null,
        "stage_after": "backlog"
      }
    },
    {
      "timestamp": "2025-07-04T10:35:22Z",
      "event_type": "review_submitted",
      "author": {
        "type": "model",
        "id": "tinyllama-1.1b"
      },
      "action": "Reviewed technical design document",
      "details": {
        "review_type": "positive",
        "score_impact": 0.5,
        "summary": "Highlighted strong theoretical foundation"
      },
      "artifacts": {
        "review": {
          "type": "review_file",
          "path": "reviews/test-2025-001/Design/tinyllama-1.1b__07-04-2025__A.md"
        },
        "reviewed_document": {
          "type": "technical_design",
          "path": "technical_design_documents/test-2025-001/design.md",
          "commit": "a1b2c3d"
        }
      },
      "metadata": {
        "score_before": 0,
        "score_after": 0.5
      }
    }
  ]
}
```

## 2. History Tracking Implementation

### 2.1 History Tracker Class
```python
# File: src/history/history_tracker.py
class ProjectHistoryTracker:
    """Tracks complete project history"""
    
    def __init__(self, project_id: str, github_handler: GitHubHandler):
        self.project_id = project_id
        self.github = github_handler
        self.history_file = f"project_histories/{project_id}/history.json"
        self.markdown_file = f"project_histories/{project_id}/history.md"
        self.history_data = self.load_or_create_history()
    
    def record_event(self, event_type: str, author: dict, action: str, 
                    details: dict, artifacts: dict = None) -> None:
        """Record a new event in project history"""
        
        event = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": event_type,
            "author": author,
            "action": action,
            "details": details,
            "artifacts": artifacts or {},
            "metadata": self.gather_metadata()
        }
        
        # Add to JSON history
        self.history_data["events"].append(event)
        self.save_json_history()
        
        # Update markdown history
        self.append_markdown_entry(event)
        
        # Commit changes
        self.commit_history_update(event)
    
    def gather_metadata(self) -> dict:
        """Gather current project metadata"""
        issue = self.github.get_issue(self.get_issue_number())
        
        return {
            "score_before": self.get_previous_score(),
            "score_after": self.get_current_score(issue),
            "stage_before": self.get_previous_stage(),
            "stage_after": self.get_current_stage(issue),
            "total_views": self.get_view_count(issue),
            "reactions": self.get_reactions(issue)
        }
```

### 2.2 Event Types
```python
# File: src/history/event_types.py
class HistoryEventTypes:
    """Standardized event types for history tracking"""
    
    # Creation events
    IDEA_GENERATED = "idea_generated"
    DESIGN_CREATED = "design_created"
    PLAN_CREATED = "plan_created"
    
    # Review events
    REVIEW_SUBMITTED = "review_submitted"
    CRITICAL_ISSUE_IDENTIFIED = "critical_issue_identified"
    
    # Development events
    CODE_GENERATED = "code_generated"
    TESTS_WRITTEN = "tests_written"
    TESTS_EXECUTED = "tests_executed"
    DATA_GENERATED = "data_generated"
    ANALYSIS_PERFORMED = "analysis_performed"
    FIGURES_CREATED = "figures_created"
    
    # Paper events
    PAPER_SECTION_WRITTEN = "paper_section_written"
    PAPER_REVISED = "paper_revised"
    PAPER_COMPILED = "paper_compiled"
    
    # Stage transitions
    STAGE_ADVANCED = "stage_advanced"
    STAGE_REVERTED = "stage_reverted"
    
    # Human interactions
    HUMAN_UPVOTED = "human_upvoted"
    HUMAN_DOWNVOTED = "human_downvoted"
    HUMAN_COMMENTED = "human_commented"
```

### 2.3 Markdown Formatter
```python
# File: src/history/markdown_formatter.py
class HistoryMarkdownFormatter:
    """Formats history entries for human-readable markdown"""
    
    EMOJI_MAP = {
        "idea_generated": "🚀",
        "design_created": "📝",
        "review_submitted": "📋",
        "critical_issue_identified": "🚨",
        "code_generated": "💻",
        "tests_executed": "✅",
        "data_generated": "📊",
        "figures_created": "📈",
        "paper_section_written": "📄",
        "paper_compiled": "📚",
        "stage_advanced": "⬆️",
        "stage_reverted": "⬇️",
        "human_upvoted": "👍",
        "human_commented": "💬"
    }
    
    def format_entry(self, event: dict) -> str:
        """Format a single history entry"""
        
        time = self.format_time(event['timestamp'])
        author = self.format_author(event['author'])
        emoji = self.EMOJI_MAP.get(event['event_type'], "•")
        action = event['action']
        
        # Base entry
        entry = f"**{time}** | `{author}` | {emoji} {action}"
        
        # Add artifacts as links
        if event['artifacts']:
            entry += self.format_artifacts(event['artifacts'])
        
        # Add details
        if event['details']:
            entry += self.format_details(event['details'])
        
        # Add metadata changes
        if self.has_significant_changes(event['metadata']):
            entry += self.format_metadata_changes(event['metadata'])
        
        return entry
```

## 3. Integration with Task Executor

### 3.1 Enhanced Task Executor
```python
# File: src/task_executor_with_history.py
class TaskExecutorWithHistory(TaskExecutor):
    """Task executor that records history"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.history_trackers = {}
    
    def get_history_tracker(self, project_id: str) -> ProjectHistoryTracker:
        """Get or create history tracker for project"""
        if project_id not in self.history_trackers:
            self.history_trackers[project_id] = ProjectHistoryTracker(
                project_id, self.github_handler
            )
        return self.history_trackers[project_id]
    
    def execute_brainstorm(self, context: dict) -> dict:
        """Execute brainstorm task with history tracking"""
        
        # Original execution
        result = super().execute_brainstorm(context)
        
        if result['success']:
            # Record in history
            tracker = self.get_history_tracker(result['project_id'])
            tracker.record_event(
                event_type=HistoryEventTypes.IDEA_GENERATED,
                author={
                    "type": "model",
                    "id": self.model_manager.current_model_name,
                    "version": self.model_manager.current_model_version
                },
                action=f"Generated idea: {result['title']}",
                details={
                    "title": result['title'],
                    "description": result['description']
                },
                artifacts={
                    "issue": {
                        "type": "github_issue",
                        "number": result['issue_number'],
                        "url": result['issue_url']
                    }
                }
            )
        
        return result
```

## 4. Paper History Section Generation

### 4.1 History Section Generator
```python
# File: src/paper/history_section_generator.py
class HistorySectionGenerator:
    """Generates history section for papers"""
    
    def generate_history_section(self, project_id: str) -> str:
        """Generate complete history section for paper"""
        
        tracker = ProjectHistoryTracker(project_id, self.github_handler)
        history = tracker.load_history()
        
        sections = [
            "\\section{Project History}\n",
            self.generate_summary(history),
            self.generate_timeline_visualization(history),
            self.generate_contribution_analysis(history),
            self.generate_detailed_timeline(history),
            self.generate_artifact_appendix(history)
        ]
        
        return "\n\n".join(sections)
    
    def generate_summary(self, history: dict) -> str:
        """Generate executive summary of project history"""
        
        stats = self.calculate_statistics(history)
        
        return f"""
\\subsection{{Summary}}

This project evolved over {stats['duration_days']} days through {stats['total_events']} recorded events, 
involving {stats['unique_contributors']} contributors ({stats['model_contributors']} AI models and 
{stats['human_contributors']} humans). The project underwent {stats['review_cycles']} review cycles,
{stats['critical_issues']} critical issues were identified and resolved, and {stats['stage_transitions']} 
stage transitions occurred before reaching completion.

Key milestones:
\\begin{itemize}
    \\item Project initiated: {stats['start_date']}
    \\item Technical design completed: {stats['design_date']} ({stats['design_reviews']} reviews)
    \\item Implementation completed: {stats['implementation_date']} ({stats['code_iterations']} iterations)
    \\item Paper published: {stats['publication_date']} ({stats['paper_revisions']} revisions)
\\end{itemize}
"""
    
    def generate_detailed_timeline(self, history: dict) -> str:
        """Generate detailed timeline in LaTeX"""
        
        latex = ["\\subsection{Detailed Timeline}", "\\begin{longtable}{p{2cm}|p{3cm}|p{10cm}}"]
        latex.append("\\textbf{Time} & \\textbf{Contributor} & \\textbf{Action} \\\\ \\hline")
        
        for event in history['events']:
            time = self.format_latex_time(event['timestamp'])
            author = self.format_latex_author(event['author'])
            action = self.format_latex_action(event)
            
            latex.append(f"{time} & {author} & {action} \\\\")
            
            # Add sub-items for important details
            if event['event_type'] == 'critical_issue_identified':
                latex.append(f" & & \\textcolor{{red}}{{Issue: {event['details']['issue']}}} \\\\")
        
        latex.append("\\end{longtable}")
        return "\n".join(latex)
```

### 4.2 Interactive History Viewer
```python
# File: src/web/history_viewer.py
class HistoryViewer:
    """Generate interactive history visualization for web"""
    
    def generate_timeline_html(self, project_id: str) -> str:
        """Generate interactive timeline HTML"""
        
        template = """
        <div class="project-history-timeline">
            <h2>Project Timeline: {project_title}</h2>
            <div class="timeline-filters">
                <button onclick="filterByType('all')">All Events</button>
                <button onclick="filterByType('reviews')">Reviews Only</button>
                <button onclick="filterByType('milestones')">Milestones Only</button>
            </div>
            
            <div class="timeline-container">
                {timeline_entries}
            </div>
            
            <div class="timeline-stats">
                <div class="stat-card">
                    <h3>Duration</h3>
                    <p>{duration}</p>
                </div>
                <div class="stat-card">
                    <h3>Contributors</h3>
                    <p>{contributors}</p>
                </div>
                <div class="stat-card">
                    <h3>Review Cycles</h3>
                    <p>{review_cycles}</p>
                </div>
            </div>
        </div>
        
        <style>
            .timeline-entry {
                border-left: 3px solid #ccc;
                padding-left: 20px;
                margin-bottom: 20px;
                position: relative;
            }
            .timeline-entry.critical {
                border-left-color: #ff0000;
            }
            .timeline-entry.milestone {
                border-left-color: #00ff00;
            }
            .timeline-marker {
                position: absolute;
                left: -7px;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                background: #fff;
                border: 3px solid #ccc;
            }
        </style>
        """
        
        return self.render_template(template, project_id)
```

## 5. Integration with Pipeline Test

### 5.1 History Validation in Tests
```python
# File: tests/test_history_tracking.py
class TestHistoryTracking:
    """Test history tracking functionality"""
    
    def test_complete_pipeline_history(self, pipeline_orchestrator):
        """Verify complete history is tracked"""
        
        # Run pipeline
        result = pipeline_orchestrator.run_pipeline_test()
        project_id = result.project_id
        
        # Load history
        tracker = ProjectHistoryTracker(project_id, mock_github)
        history = tracker.load_history()
        
        # Verify key events recorded
        event_types = [e['event_type'] for e in history['events']]
        
        assert HistoryEventTypes.IDEA_GENERATED in event_types
        assert HistoryEventTypes.DESIGN_CREATED in event_types
        assert HistoryEventTypes.CRITICAL_ISSUE_IDENTIFIED in event_types
        assert HistoryEventTypes.STAGE_ADVANCED in event_types
        assert HistoryEventTypes.PAPER_COMPILED in event_types
        
        # Verify chronological order
        timestamps = [e['timestamp'] for e in history['events']]
        assert timestamps == sorted(timestamps)
        
        # Verify score tracking
        score_changes = [
            (e['metadata']['score_before'], e['metadata']['score_after'])
            for e in history['events']
            if 'score_before' in e['metadata']
        ]
        
        # Find critical reset
        reset_found = any(after == 0 and before > 0 for before, after in score_changes)
        assert reset_found, "Critical review score reset not found"
    
    def test_history_markdown_generation(self, sample_history):
        """Test markdown history is readable and complete"""
        
        formatter = HistoryMarkdownFormatter()
        markdown = formatter.format_history(sample_history)
        
        # Verify structure
        assert "# Project History:" in markdown
        assert "## Timeline" in markdown
        
        # Verify links
        assert "[technical design document](" in markdown
        assert "[Reviewed](" in markdown
        assert "https://github.com/" in markdown
```

## 6. Updated Implementation Roadmap

### Additional Phase: History Tracking (Days 13-14)

1. **Day 13: Core History Implementation**
   - Implement `ProjectHistoryTracker` class
   - Create event type definitions
   - Build markdown formatter
   - Integrate with existing task executor

2. **Day 14: Paper Integration & Visualization**
   - Create history section generator for papers
   - Build interactive timeline viewer
   - Add history validation to tests
   - Generate sample history reports

### Modified Task Executor Integration

Every task execution method needs history tracking added:

```python
def execute_task(self, task_type: str, context: dict) -> dict:
    """Execute task with history tracking"""
    
    # Get project ID
    project_id = context.get('project_id')
    if not project_id:
        return original_result
    
    # Execute original task
    result = self.execute_original_task(task_type, context)
    
    # Track in history if successful
    if result.get('success'):
        tracker = self.get_history_tracker(project_id)
        event_data = self.build_event_data(task_type, context, result)
        tracker.record_event(**event_data)
    
    return result
```

## Benefits

1. **Complete Audit Trail**: Every action is recorded with timestamps and attribution
2. **Research Insights**: Analyze how ideas evolve through the pipeline
3. **Reproducibility**: Full history allows understanding of decisions
4. **Attribution**: Clear record of all contributions
5. **Paper Enhancement**: Rich history section adds value to publications
6. **Debugging**: Detailed logs help identify pipeline issues

This history tracking system will provide invaluable insights into the scientific discovery process and ensure complete transparency in the automated research pipeline.