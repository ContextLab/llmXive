import os
import re
import time
import json
from typing import Any, Dict, List, Optional, Tuple
from agents.base import BaseAgent

class AugmentedAgent(BaseAgent):
    """Augmented agent with failure signature retrieval."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.signature_index_path = config.get('signature_index_path')
        self.signature_index = self._load_signature_index()
        self.model_name = config.get('model_name', 'meta-llama/Meta-Llama-3-8B')
        self.max_tokens = config.get('max_tokens', 512)
        self.temperature = config.get('temperature', 0.7)
        self.model = None
        self.tokenizer = None
        self._load_model()
    
    def _load_signature_index(self) -> Dict[str, str]:
        """Load the failure signature index."""
        if not self.signature_index_path or not os.path.exists(self.signature_index_path):
            return {}
        
        with open(self.signature_index_path, 'r') as f:
            data = json.load(f)
            # Convert list to dict for easier lookup
            return {entry['tool_id']: entry['pattern_string'] for entry in data}
    
    def _load_model(self) -> None:
        """Load the LLM model."""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
            import torch
            
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16
            )
            
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                quantization_config=quantization_config,
                device_map="auto",
                torch_dtype=torch.float16
            )
        except Exception as e:
            raise RuntimeError(f"Failed to load model: {e}")
    
    def _check_failure_signature(self, tool_output: str) -> Optional[str]:
        """Check if tool output matches any failure signature."""
        for tool_id, pattern in self.signature_index.items():
            if '*' in pattern:
                # Wildcard match
                regex_pattern = pattern.replace('*', '.*')
                if re.search(regex_pattern, tool_output):
                    return tool_id
            else:
                # Exact match
                if pattern in tool_output:
                    return tool_id
        return None
    
    def _replan(self, task: Dict[str, Any], failure_context: str) -> Dict[str, Any]:
        """Re-plan the task after detecting a failure."""
        prompt = f"Task: {task.get('instruction', '')}\n"
        prompt += f"Context: {task.get('context', '')}\n"
        prompt += f"Previous failure: {failure_context}\n"
        prompt += "Please re-plan and execute the task, avoiding the previous failure."
        
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=self.max_tokens,
            temperature=self.temperature,
            do_sample=True
        )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        return {
            'status': 'replanned',
            'response': response,
            'recovery_strategy': 'replan'
        }
    
    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the augmented agent on a task."""
        start_time = time.time()
        
        # Initial execution attempt
        prompt = f"Task: {task.get('instruction', '')}\n"
        if task.get('context'):
            prompt += f"Context: {task['context']}\n"
        
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=self.max_tokens,
            temperature=self.temperature,
            do_sample=True
        )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Check for failure signatures in the response
        failure_tool = self._check_failure_signature(response)
        
        if failure_tool:
            # Trigger recovery
            recovery_result = self._replan(task, f"Detected failure in tool: {failure_tool}")
            response = recovery_result['response']
            status = recovery_result['status']
            recovery_strategy = recovery_result['recovery_strategy']
        else:
            status = 'success'
            recovery_strategy = None
        
        elapsed_time = time.time() - start_time
        
        return {
            'task_id': task.get('id', 'unknown'),
            'response': response,
            'status': status,
            'execution_time': elapsed_time,
            'agent_type': 'augmented',
            'failure_detected': failure_tool is not None,
            'recovery_strategy': recovery_strategy
        }
    
    def reset(self) -> None:
        """Reset the agent state."""
        pass
