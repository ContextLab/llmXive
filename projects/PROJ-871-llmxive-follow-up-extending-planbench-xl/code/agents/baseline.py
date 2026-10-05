import os
import time
import torch
from typing import Any, Dict, List, Optional
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from agents.base import BaseAgent

class BaselineAgent(BaseAgent):
    """Baseline agent using internal LLM reasoning only."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.model_name = config.get('model_name', 'meta-llama/Meta-Llama-3-8B')
        self.max_tokens = config.get('max_tokens', 512)
        self.temperature = config.get('temperature', 0.7)
        self.model = None
        self.tokenizer = None
        self._load_model()
    
    def _load_model(self) -> None:
        """Load the LLM model."""
        try:
            # Quantization config for CPU feasibility
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
    
    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the baseline agent on a task."""
        start_time = time.time()
        
        # Construct prompt from task
        prompt = f"Task: {task.get('instruction', '')}\n"
        if task.get('context'):
            prompt += f"Context: {task['context']}\n"
        
        # Generate response
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=self.max_tokens,
            temperature=self.temperature,
            do_sample=True
        )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        elapsed_time = time.time() - start_time
        
        return {
            'task_id': task.get('id', 'unknown'),
            'response': response,
            'status': 'success',
            'execution_time': elapsed_time,
            'agent_type': 'baseline'
        }
    
    def reset(self) -> None:
        """Reset the agent state."""
        pass
