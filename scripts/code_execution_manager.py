#!/usr/bin/env python3
"""
Code Execution Manager for llmXive
Handles sandboxed execution of research code with environment management
"""

import os
import sys
import subprocess
import json
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import uuid

class CodeExecutionManager:
    """Manages sandboxed code execution with environment isolation"""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.execution_logs = []
        
    def detect_project_requirements(self, project_path: Path) -> Dict[str, any]:
        """Detect project requirements and execution environment needed"""
        requirements = {
            'language': 'python',
            'environment_type': 'venv',
            'dependencies': [],
            'requirements_files': [],
            'system_packages': [],
            'docker_required': False
        }
        
        # Check for Python requirements
        req_files = ['requirements.txt', 'setup.py', 'pyproject.toml', 'Pipfile']
        for req_file in req_files:
            req_path = project_path / req_file
            if req_path.exists():
                requirements['requirements_files'].append(str(req_path))
        
        # Check for specific language files
        code_files = list(project_path.glob('**/*.py'))
        if code_files:
            requirements['language'] = 'python'
        
        # Check for R files
        r_files = list(project_path.glob('**/*.R')) + list(project_path.glob('**/*.r'))
        if r_files:
            requirements['language'] = 'r'
            requirements['environment_type'] = 'conda'
        
        # Check for Julia files
        julia_files = list(project_path.glob('**/*.jl'))
        if julia_files:
            requirements['language'] = 'julia'
            requirements['environment_type'] = 'julia'
        
        # Check for JavaScript/Node.js
        if (project_path / 'package.json').exists():
            requirements['language'] = 'javascript'
            requirements['environment_type'] = 'npm'
        
        # Check for complex dependencies that might need Docker
        if any(dep in str(project_path) for dep in ['tensorflow', 'pytorch', 'cuda', 'gpu']):
            requirements['docker_required'] = True
        
        return requirements
    
    def create_execution_environment(self, project_path: Path, requirements: Dict) -> Path:
        """Create isolated execution environment"""
        env_id = f"llmxive-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{str(uuid.uuid4())[:8]}"
        env_path = project_path / '.execution' / env_id
        env_path.mkdir(parents=True, exist_ok=True)
        
        if requirements['docker_required']:
            return self._create_docker_environment(env_path, requirements)
        elif requirements['environment_type'] == 'conda':
            return self._create_conda_environment(env_path, requirements)
        elif requirements['environment_type'] == 'venv':
            return self._create_venv_environment(env_path, requirements)
        else:
            return env_path
    
    def _create_venv_environment(self, env_path: Path, requirements: Dict) -> Path:
        """Create Python virtual environment"""
        venv_path = env_path / 'venv'
        
        # Create virtual environment
        result = subprocess.run([
            sys.executable, '-m', 'venv', str(venv_path)
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to create virtual environment: {result.stderr}")
        
        # Install dependencies
        pip_path = venv_path / 'bin' / 'pip'
        if not pip_path.exists():
            pip_path = venv_path / 'Scripts' / 'pip.exe'  # Windows
        
        # Install basic scientific packages
        basic_packages = [
            'numpy', 'pandas', 'matplotlib', 'scipy', 'jupyter', 
            'scikit-learn', 'seaborn', 'plotly', 'requests'
        ]
        
        for package in basic_packages:
            subprocess.run([str(pip_path), 'install', package], 
                         capture_output=True, text=True)
        
        # Install from requirements files
        for req_file in requirements['requirements_files']:
            if Path(req_file).exists():
                subprocess.run([str(pip_path), 'install', '-r', req_file], 
                             capture_output=True, text=True)
        
        return venv_path
    
    def _create_conda_environment(self, env_path: Path, requirements: Dict) -> Path:
        """Create Conda environment"""
        conda_env_name = f"llmxive-{env_path.name}"
        
        # Create conda environment
        result = subprocess.run([
            'conda', 'create', '-n', conda_env_name, 'python=3.9', '-y'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"Failed to create conda environment: {result.stderr}")
        
        # Install packages
        packages = ['numpy', 'pandas', 'matplotlib', 'scipy', 'jupyter', 'r-base']
        subprocess.run([
            'conda', 'install', '-n', conda_env_name, '-c', 'conda-forge', '-y'
        ] + packages, capture_output=True, text=True)
        
        return env_path
    
    def _create_docker_environment(self, env_path: Path, requirements: Dict) -> Path:
        """Create Docker environment"""
        dockerfile_content = f'''
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    make \\
    git \\
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY . .

# Create non-root user
RUN useradd -m -s /bin/bash researcher
USER researcher

CMD ["python", "main.py"]
'''
        
        dockerfile_path = env_path / 'Dockerfile'
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content)
        
        return env_path
    
    def execute_code(self, project_path: Path, code_file: Path, timeout: int = 300) -> Dict:
        """Execute code in sandboxed environment"""
        execution_id = str(uuid.uuid4())[:8]
        start_time = datetime.now()
        
        # Detect requirements
        requirements = self.detect_project_requirements(project_path)
        
        # Create execution environment
        env_path = self.create_execution_environment(project_path, requirements)
        
        # Prepare execution
        exec_result = {
            'execution_id': execution_id,
            'start_time': start_time.isoformat(),
            'code_file': str(code_file),
            'requirements': requirements,
            'environment_path': str(env_path),
            'success': False,
            'output': '',
            'error': '',
            'runtime_seconds': 0,
            'files_created': [],
            'exit_code': -1
        }
        
        try:
            # Execute code based on environment type
            if requirements['docker_required']:
                result = self._execute_in_docker(project_path, code_file, env_path, timeout)
            elif requirements['environment_type'] == 'conda':
                result = self._execute_in_conda(project_path, code_file, env_path, timeout)
            else:
                result = self._execute_in_venv(project_path, code_file, env_path, timeout)
            
            exec_result.update(result)
            exec_result['success'] = result['exit_code'] == 0
            
        except Exception as e:
            exec_result['error'] = str(e)
            exec_result['success'] = False
        
        finally:
            end_time = datetime.now()
            exec_result['end_time'] = end_time.isoformat()
            exec_result['runtime_seconds'] = (end_time - start_time).total_seconds()
            
            # Log execution
            self.execution_logs.append(exec_result)
            
            # Save execution report
            self._save_execution_report(project_path, exec_result)
            
            # Cleanup environment if needed
            if not exec_result['success']:
                self._cleanup_environment(env_path, requirements)
        
        return exec_result
    
    def _execute_in_venv(self, project_path: Path, code_file: Path, env_path: Path, timeout: int) -> Dict:
        """Execute code in Python virtual environment"""
        python_path = env_path / 'bin' / 'python'
        if not python_path.exists():
            python_path = env_path / 'Scripts' / 'python.exe'  # Windows
        
        result = subprocess.run([
            str(python_path), str(code_file)
        ], cwd=str(project_path), capture_output=True, text=True, timeout=timeout)
        
        # Check for created files
        files_created = []
        for pattern in ['*.png', '*.jpg', '*.pdf', '*.csv', '*.json', '*.html']:
            files_created.extend(project_path.glob(pattern))
        
        return {
            'output': result.stdout,
            'error': result.stderr,
            'exit_code': result.returncode,
            'files_created': [str(f) for f in files_created]
        }
    
    def _execute_in_conda(self, project_path: Path, code_file: Path, env_path: Path, timeout: int) -> Dict:
        """Execute code in Conda environment"""
        conda_env_name = f"llmxive-{env_path.name}"
        
        result = subprocess.run([
            'conda', 'run', '-n', conda_env_name, 'python', str(code_file)
        ], cwd=str(project_path), capture_output=True, text=True, timeout=timeout)
        
        return {
            'output': result.stdout,
            'error': result.stderr,
            'exit_code': result.returncode,
            'files_created': []
        }
    
    def _execute_in_docker(self, project_path: Path, code_file: Path, env_path: Path, timeout: int) -> Dict:
        """Execute code in Docker container"""
        container_name = f"llmxive-{env_path.name}"
        
        # Build Docker image
        build_result = subprocess.run([
            'docker', 'build', '-t', container_name, str(env_path)
        ], capture_output=True, text=True)
        
        if build_result.returncode != 0:
            return {
                'output': '',
                'error': f"Docker build failed: {build_result.stderr}",
                'exit_code': build_result.returncode,
                'files_created': []
            }
        
        # Run Docker container
        result = subprocess.run([
            'docker', 'run', '--rm', '--name', container_name,
            '-v', f"{project_path}:/app", container_name, 
            'python', str(code_file.name)
        ], capture_output=True, text=True, timeout=timeout)
        
        return {
            'output': result.stdout,
            'error': result.stderr,
            'exit_code': result.returncode,
            'files_created': []
        }
    
    def _save_execution_report(self, project_path: Path, exec_result: Dict):
        """Save execution report to project directory"""
        report_path = project_path / 'code' / 'execution_report.json'
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(exec_result, f, indent=2)
        
        # Also save human-readable report
        readable_report = self._format_execution_report(exec_result)
        readable_path = project_path / 'code' / 'execution_report.md'
        with open(readable_path, 'w') as f:
            f.write(readable_report)
    
    def _format_execution_report(self, exec_result: Dict) -> str:
        """Format execution report as markdown"""
        status = "✅ SUCCESS" if exec_result['success'] else "❌ FAILED"
        
        report = f"""# Code Execution Report

**Status**: {status}
**Execution ID**: {exec_result['execution_id']}
**Started**: {exec_result['start_time']}
**Runtime**: {exec_result['runtime_seconds']:.2f} seconds
**Exit Code**: {exec_result['exit_code']}

## Environment Details
- **Language**: {exec_result['requirements']['language']}
- **Environment Type**: {exec_result['requirements']['environment_type']}
- **Docker Required**: {exec_result['requirements']['docker_required']}

## Code File
```
{exec_result['code_file']}
```

## Output
```
{exec_result['output']}
```

## Errors
```
{exec_result['error']}
```

## Files Created
{chr(10).join(f"- {f}" for f in exec_result['files_created'])}

## Next Steps
{'Code executed successfully! Review the output and generated files.' if exec_result['success'] else 'Code execution failed. Please review the errors above and fix the issues before running again.'}
"""
        return report
    
    def _cleanup_environment(self, env_path: Path, requirements: Dict):
        """Clean up execution environment"""
        if requirements['environment_type'] == 'conda':
            conda_env_name = f"llmxive-{env_path.name}"
            subprocess.run(['conda', 'env', 'remove', '-n', conda_env_name, '-y'], 
                         capture_output=True, text=True)
        
        # Remove environment directory
        if env_path.exists():
            shutil.rmtree(env_path, ignore_errors=True)
    
    def get_execution_history(self, project_path: Path) -> List[Dict]:
        """Get execution history for a project"""
        history = []
        reports_dir = project_path / 'code'
        
        if reports_dir.exists():
            for report_file in reports_dir.glob('execution_report_*.json'):
                try:
                    with open(report_file, 'r') as f:
                        history.append(json.load(f))
                except:
                    continue
        
        return sorted(history, key=lambda x: x['start_time'], reverse=True)