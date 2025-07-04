# Self-Improvement Task Types

These tasks allow the automation system to modify and improve itself.

## Meta-Automation Tasks

### ADD_TASK_TYPE
- **Purpose**: Add a new task type to the automation system
- **Input**: Task description, requirements, implementation approach
- **Output**: Updated task executor with new capability
- **Process**:
  1. Analyze what the new task needs to do
  2. Write the task implementation
  3. Add to task_handlers mapping
  4. Update system prompts
  5. Create tests for the new task

### EDIT_TASK_TYPE
- **Purpose**: Modify existing task implementation
- **Input**: Task type name, improvement suggestions
- **Output**: Updated task implementation
- **Process**:
  1. Review current implementation
  2. Identify specific improvements
  3. Modify the code
  4. Update documentation
  5. Test the changes

### IMPROVE_PROMPT_ENGINEERING
- **Purpose**: Enhance system prompts for better results
- **Input**: Task type, example failures
- **Output**: Improved prompts
- **Process**:
  1. Analyze failed outputs
  2. Identify prompt weaknesses
  3. Revise prompts
  4. Test improvements

### OPTIMIZE_TASK_SELECTION
- **Purpose**: Improve task prioritization algorithm
- **Input**: Execution history, outcomes
- **Output**: Updated prioritization logic
- **Process**:
  1. Analyze task success patterns
  2. Identify prioritization improvements
  3. Update scoring algorithm
  4. Validate changes

### ADD_RESPONSE_PARSER
- **Purpose**: Add new response parsing capability
- **Input**: Response format type, examples
- **Output**: New parser implementation
- **Process**:
  1. Analyze response patterns
  2. Write parsing logic
  3. Add error handling
  4. Test with examples

### IMPROVE_ERROR_HANDLING
- **Purpose**: Enhance error recovery mechanisms
- **Input**: Error logs, failure patterns
- **Output**: Better error handling
- **Process**:
  1. Analyze common failures
  2. Design recovery strategies
  3. Implement handlers
  4. Test edge cases

## Implementation Example

```python
def execute_add_task_type(self, context):
    """Add a new task type to the automation system"""
    
    task_name = context.get('task_name')
    task_description = context.get('description')
    implementation_hints = context.get('hints', '')
    
    if not task_name or not task_description:
        return {"error": "Missing task_name or description"}
        
    prompt = f"""Task: Generate implementation for a new automation task type.

Task Name: {task_name}
Description: {task_description}
Implementation Hints: {implementation_hints}

Generate a complete implementation that:
1. Follows the pattern of existing task handlers
2. Includes proper error handling
3. Parses LLM responses appropriately
4. Updates GitHub as needed
5. Returns standardized success/error format

Output the complete method implementation:"""

    response = self.conv_mgr.query_model(prompt, task_type="ADD_TASK_TYPE")
    
    # Extract code
    implementation = self.parse_code_block(response)
    
    if not implementation:
        return {"error": "Failed to generate implementation"}
        
    # Add to task implementations file
    impl_path = "code/llmxive-automation/src/task_implementations.py"
    
    # Read current file
    current_code = self.github.get_file_content(impl_path)
    
    # Insert new implementation
    insertion_point = "# === END OF TASK IMPLEMENTATIONS ==="
    updated_code = current_code.replace(
        insertion_point,
        f"{implementation}\n\n    {insertion_point}"
    )
    
    # Update task handler mapping
    handler_line = f'            "{task_name}": self.execute_{task_name.lower()},'
    updated_code = updated_code.replace(
        "# === TASK_HANDLERS_END ===",
        f"{handler_line}\n            # === TASK_HANDLERS_END ==="
    )
    
    # Save updated file
    self.github.update_file(impl_path, updated_code,
        f"Add {task_name} task type to automation system")
        
    # Generate system prompt
    prompt_gen = f"""Generate a system prompt for this task type:
{task_description}

The prompt should be 1-2 sentences describing the AI's role."""

    system_prompt = self.conv_mgr.query_model(prompt_gen, temperature=0.7)
    
    # Update prompts file
    self.update_system_prompts(task_name, system_prompt.strip())
    
    return {
        "success": True,
        "task_type_added": task_name,
        "implementation_path": impl_path
    }


def execute_edit_task_type(self, context):
    """Edit existing task implementation"""
    
    task_name = context.get('task_name')
    issues = context.get('issues', [])
    improvements = context.get('improvements', [])
    
    if not task_name:
        return {"error": "No task_name provided"}
        
    # Get current implementation
    impl_path = "code/llmxive-automation/src/task_implementations.py"
    current_code = self.github.get_file_content(impl_path)
    
    # Extract the specific method
    method_name = f"execute_{task_name.lower()}"
    method_code = self.extract_method(current_code, method_name)
    
    if not method_code:
        return {"error": f"Method {method_name} not found"}
        
    prompt = f"""Task: Improve this task implementation.

Current Implementation:
```python
{method_code}
```

Issues Found:
{chr(10).join(f"- {issue}" for issue in issues)}

Suggested Improvements:
{chr(10).join(f"- {imp}" for imp in improvements)}

Generate the improved implementation that addresses these issues:"""

    response = self.conv_mgr.query_model(prompt, task_type="EDIT_TASK_TYPE")
    
    # Extract improved code
    improved_code = self.parse_code_block(response)
    
    # Replace in file
    updated_file = current_code.replace(method_code, improved_code)
    
    # Save changes
    self.github.update_file(impl_path, updated_file,
        f"Improve {task_name} implementation")
        
    return {
        "success": True,
        "task_type_edited": task_name,
        "improvements_applied": len(improvements)
    }
```

## Self-Improvement Workflow

1. **Monitor Performance**
   - Track task success rates
   - Identify failure patterns
   - Collect user feedback

2. **Identify Improvements**
   - Missing task types
   - Inefficient implementations
   - Poor prompt engineering
   - Error handling gaps

3. **Implement Changes**
   - Add new capabilities
   - Refine existing ones
   - Improve prompts
   - Enhance parsing

4. **Validate Improvements**
   - Test changes
   - Monitor outcomes
   - Iterate as needed

## Benefits

- **Adaptability**: System evolves based on needs
- **Continuous Improvement**: Gets better over time
- **Customization**: Adds domain-specific capabilities
- **Resilience**: Fixes its own issues
- **Learning**: Improves from experience