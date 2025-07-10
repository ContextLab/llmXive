#!/usr/bin/env python3
"""
Pipeline Configuration API
Provides REST endpoints for pipeline configuration management
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import yaml
import json
from pathlib import Path
import logging
from typing import Dict, Any, Tuple
import os
import sys

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from pipeline_config_manager import PipelineConfigManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
CONFIG_PATH = Path(__file__).parent.parent / "pipeline_config.yaml"
SCHEMA_PATH = Path(__file__).parent.parent / "pipeline_schema.json"

# Initialize pipeline manager
pipeline_manager = PipelineConfigManager(CONFIG_PATH, SCHEMA_PATH)


@app.route('/api/pipeline/config', methods=['GET'])
def get_pipeline_config():
    """Get current pipeline configuration"""
    try:
        if not CONFIG_PATH.exists():
            return jsonify({"error": "Configuration file not found"}), 404
        
        with open(CONFIG_PATH, 'r') as f:
            config_content = f.read()
        
        return config_content, 200, {'Content-Type': 'application/x-yaml'}
        
    except Exception as e:
        logger.error(f"Error getting configuration: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/pipeline/config', methods=['POST'])
def save_pipeline_config():
    """Save pipeline configuration"""
    try:
        # Check authentication (simplified for demo)
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Authentication required"}), 401
        
        # Get YAML content from request
        yaml_content = request.get_data(as_text=True)
        
        if not yaml_content:
            return jsonify({"error": "No configuration provided"}), 400
        
        # Validate the configuration
        try:
            config = yaml.safe_load(yaml_content)
            pipeline_manager.config = config
            is_valid, errors = pipeline_manager.validate_config(config)
            
            if not is_valid:
                return jsonify({
                    "error": "Configuration validation failed",
                    "errors": errors
                }), 400
                
        except yaml.YAMLError as e:
            return jsonify({
                "error": "Invalid YAML format",
                "details": str(e)
            }), 400
        
        # Save the configuration
        with open(CONFIG_PATH, 'w') as f:
            f.write(yaml_content)
        
        logger.info("Pipeline configuration saved successfully")
        
        return jsonify({
            "message": "Configuration saved successfully",
            "timestamp": pipeline_manager.state.variables.get('timestamp', 'now')
        }), 200
        
    except Exception as e:
        logger.error(f"Error saving configuration: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/pipeline/validate', methods=['POST'])
def validate_pipeline_config():
    """Validate pipeline configuration"""
    try:
        yaml_content = request.get_data(as_text=True)
        
        if not yaml_content:
            return jsonify({"error": "No configuration provided"}), 400
        
        # Parse YAML
        try:
            config = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            return jsonify({
                "valid": False,
                "errors": [f"YAML parsing error: {str(e)}"]
            }), 200
        
        # Validate with pipeline manager
        pipeline_manager.config = config
        is_valid, errors = pipeline_manager.validate_config(config)
        
        return jsonify({
            "valid": is_valid,
            "errors": errors,
            "warnings": []  # Could add warnings for best practices
        }), 200
        
    except Exception as e:
        logger.error(f"Error validating configuration: {e}")
        return jsonify({
            "valid": False,
            "errors": [f"Validation error: {str(e)}"]
        }), 500


@app.route('/api/pipeline/mermaid', methods=['POST'])
def generate_mermaid_diagram():
    """Generate Mermaid diagram from pipeline configuration"""
    try:
        yaml_content = request.get_data(as_text=True)
        
        if not yaml_content:
            return jsonify({"error": "No configuration provided"}), 400
        
        # Parse YAML
        try:
            config = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            return jsonify({"error": f"YAML parsing error: {str(e)}"}), 400
        
        # Generate Mermaid diagram
        mermaid_code = generate_mermaid_from_config(config)
        
        return jsonify({
            "mermaid": mermaid_code,
            "format": "mermaid"
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating Mermaid diagram: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/pipeline/execution-order', methods=['GET'])
def get_execution_order():
    """Get pipeline execution order"""
    try:
        pipeline_manager.load_config()
        execution_order = pipeline_manager.get_execution_order()
        
        return jsonify({
            "execution_order": execution_order,
            "total_steps": len(execution_order)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting execution order: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/pipeline/step/<step_name>/dependencies', methods=['GET'])
def get_step_dependencies(step_name):
    """Get dependencies for a specific step"""
    try:
        pipeline_manager.load_config()
        
        if not pipeline_manager.config:
            return jsonify({"error": "Configuration not loaded"}), 500
        
        steps = pipeline_manager.config.get('steps', {})
        step = steps.get(step_name)
        
        if not step:
            return jsonify({"error": f"Step '{step_name}' not found"}), 404
        
        can_execute, reason = pipeline_manager.can_execute_step(step_name)
        
        return jsonify({
            "step_name": step_name,
            "dependencies": step.get('depends_on', []),
            "conditions": step.get('conditions', []),
            "can_execute": can_execute,
            "reason": reason
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting step dependencies: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/pipeline/statistics', methods=['GET'])
def get_pipeline_statistics():
    """Get pipeline statistics"""
    try:
        pipeline_manager.load_config()
        
        if not pipeline_manager.config:
            return jsonify({"error": "Configuration not loaded"}), 500
        
        steps = pipeline_manager.config.get('steps', {})
        
        # Calculate statistics
        total_steps = len(steps)
        
        parallel_steps = sum(1 for step in steps.values() 
                           if not step.get('depends_on', []))
        
        review_steps = sum(1 for step_name in steps.keys() 
                         if 'review' in step_name.lower())
        
        total_timeout = sum(step.get('timeout', 300) for step in steps.values())
        estimated_duration_minutes = total_timeout // 60
        
        model_requirements = {}
        for step_name, step in steps.items():
            model_sel = step.get('model_selection', {})
            provider = model_sel.get('provider', 'any')
            model_requirements[provider] = model_requirements.get(provider, 0) + 1
        
        return jsonify({
            "total_steps": total_steps,
            "parallel_capable": parallel_steps,
            "review_steps": review_steps,
            "estimated_duration_minutes": estimated_duration_minutes,
            "total_timeout_seconds": total_timeout,
            "model_requirements": model_requirements,
            "complexity_score": calculate_complexity_score(steps)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting pipeline statistics: {e}")
        return jsonify({"error": str(e)}), 500


def generate_mermaid_from_config(config: Dict[str, Any]) -> str:
    """Generate Mermaid flowchart code from pipeline configuration"""
    steps = config.get('steps', {})
    branches = config.get('branches', {})
    
    mermaid = ['graph TD']
    
    # Step categories for styling
    step_categories = {
        'idea': ['idea_generation', 'idea_review', 'idea_revision'],
        'design': ['technical_design', 'design_review', 'implementation_plan'],
        'execution': ['code_generation', 'code_execution'],
        'analysis': ['data_analysis', 'paper_writing', 'paper_review'],
        'publication': ['latex_compilation']
    }
    
    # Add nodes
    for step_name, step in steps.items():
        description = step.get('description', step_name)
        timeout = step.get('timeout', 300)
        
        # Truncate description for display
        if len(description) > 30:
            description = description[:27] + '...'
        
        # Clean description for Mermaid
        clean_desc = description.replace('"', '\\"').replace('\n', ' ')
        
        mermaid.append(f'    {step_name}["{clean_desc}<br/><small>{timeout}s</small>"]')
        
        # Add styling class
        category = get_step_category(step_name, step_categories)
        mermaid.append(f'    class {step_name} {category}')
    
    # Add edges for dependencies
    for step_name, step in steps.items():
        dependencies = step.get('depends_on', [])
        for dep in dependencies:
            if dep in steps:
                mermaid.append(f'    {dep} --> {step_name}')
    
    # Add conditional branches
    for branch_name, branch in branches.items():
        condition = branch.get('condition', '')
        if len(condition) > 25:
            condition = condition[:22] + '...'
        
        clean_condition = condition.replace('"', '\\"')
        mermaid.append(f'    {branch_name}{{{{"❓ {clean_condition}"}}}}')
        mermaid.append(f'    class {branch_name} branch')
        
        # Connect branches based on action
        action = branch.get('action', '')
        if action == 'terminate':
            mermaid.append(f'    {branch_name} --> END[🛑 Stop]')
        elif action == 'branch':
            target_steps = branch.get('steps', [])
            for target in target_steps:
                if target in steps:
                    mermaid.append(f'    {branch_name} --> {target}')
    
    # Add styling
    mermaid.extend([
        '',
        'classDef idea fill:#e3f2fd,stroke:#1976d2,stroke-width:2px',
        'classDef design fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px',
        'classDef execution fill:#e8f5e8,stroke:#388e3c,stroke-width:2px',
        'classDef analysis fill:#fff3e0,stroke:#f57c00,stroke-width:2px',
        'classDef publication fill:#fce4ec,stroke:#c2185b,stroke-width:2px',
        'classDef branch fill:#fff9c4,stroke:#f9a825,stroke-width:2px,stroke-dasharray: 5 5',
        'classDef default fill:#f5f5f5,stroke:#757575,stroke-width:2px'
    ])
    
    return '\n'.join(mermaid)


def get_step_category(step_name: str, categories: Dict[str, list]) -> str:
    """Get the category CSS class for a step"""
    for category, step_list in categories.items():
        if step_name in step_list:
            return category
    return 'default'


def calculate_complexity_score(steps: Dict[str, Any]) -> float:
    """Calculate a complexity score for the pipeline"""
    if not steps:
        return 0.0
    
    # Base complexity
    complexity = len(steps) * 1.0
    
    # Add complexity for dependencies
    for step in steps.values():
        dependencies = step.get('depends_on', [])
        complexity += len(dependencies) * 0.5
        
        # Add complexity for conditions
        conditions = step.get('conditions', [])
        complexity += len(conditions) * 0.3
        
        # Add complexity for model requirements
        model_sel = step.get('model_selection', {})
        if model_sel.get('min_parameters', 0) > 10:
            complexity += 0.2
        
        # Add complexity for timeouts
        timeout = step.get('timeout', 300)
        if timeout > 600:  # More than 10 minutes
            complexity += 0.1
    
    # Normalize to 0-10 scale
    normalized = min(complexity / 10.0, 10.0)
    return round(normalized, 2)


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "pipeline-api",
        "config_exists": CONFIG_PATH.exists(),
        "schema_exists": SCHEMA_PATH.exists()
    }), 200


if __name__ == '__main__':
    # Development server
    port = int(os.environ.get('PORT', 5002))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print(f"🚀 Starting Pipeline API server on port {port}")
    print(f"📁 Config path: {CONFIG_PATH}")
    print(f"📋 Schema path: {SCHEMA_PATH}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)