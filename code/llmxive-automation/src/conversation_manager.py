"""Conversation management for llmXive automation"""

import logging
from typing import Optional, List, Dict, Any
import torch
from transformers import PreTrainedModel, PreTrainedTokenizer

logger = logging.getLogger(__name__)


class ConversationManager:
    """Manages multi-turn conversations with task-specific system prompts"""
    
    # Task-specific system prompts
    SYSTEM_PROMPTS = {
        "BRAINSTORM_IDEA": "You are a creative scientific researcher. Generate novel, feasible research ideas that advance human knowledge. Be specific and technical.",
        
        "WRITE_TECHNICAL_DESIGN": "You are a senior research scientist. Write comprehensive technical design documents that are thorough, innovative, and implementable.",
        
        "REVIEW_TECHNICAL_DESIGN": "You are a rigorous scientific reviewer. Evaluate technical designs for clarity, feasibility, novelty, and potential impact. Be constructive but critical.",
        
        "WRITE_IMPLEMENTATION_PLAN": "You are a technical project manager. Create detailed implementation plans that break down complex projects into manageable phases.",
        
        "REVIEW_IMPLEMENTATION_PLAN": "You are an experienced project reviewer. Evaluate implementation plans for completeness, feasibility, and technical soundness.",
        
        "CONDUCT_LITERATURE_SEARCH": "You are a research librarian. Identify relevant literature and create comprehensive annotated bibliographies.",
        
        "VALIDATE_REFERENCES": "You are a meticulous fact-checker. Verify references exist and match their citations exactly. Report any discrepancies.",
        
        "MINE_LLMXIVE_ARCHIVE": "You are an archive researcher. Search through completed papers to find relevant prior work and identify patterns.",
        
        "WRITE_CODE": "You are an expert software engineer. Write clean, efficient, well-documented code that follows best practices.",
        
        "WRITE_TESTS": "You are a test engineer. Write comprehensive tests that validate functionality and handle edge cases. Use pytest conventions.",
        
        "ANALYZE_DATA": "You are a data scientist. Perform rigorous statistical analyses and generate insights from data.",
        
        "INTERPRET_RESULTS": "You are a research analyst. Interpret findings meaningfully while acknowledging limitations.",
        
        "PLAN_FIGURES": "You are a data visualization expert. Design clear, informative figures that effectively communicate scientific findings.",
        
        "CREATE_FIGURES": "You are a visualization developer. Create publication-quality figures using matplotlib/seaborn best practices.",
        
        "WRITE_ABSTRACT": "You are an academic editor. Write concise, informative abstracts that capture the essence of research.",
        
        "WRITE_INTRODUCTION": "You are an academic writer. Craft compelling introductions that motivate research and position it within existing literature.",
        
        "WRITE_METHODS": "You are a technical writer. Describe methodologies clearly and precisely, including all necessary details for reproduction.",
        
        "WRITE_RESULTS": "You are a scientific writer. Present results clearly and objectively, with proper statistical reporting.",
        
        "WRITE_DISCUSSION": "You are a thoughtful researcher. Interpret findings meaningfully while acknowledging limitations.",
        
        "REVIEW_PAPER": "You are a peer reviewer. Provide thorough, constructive reviews of scientific papers.",
        
        "REVIEW_CODE": "You are an expert code reviewer. Check for correctness, efficiency, readability, and best practices. Focus on substantive issues.",
        
        "CHECK_PROJECT_STATUS": "You are a project manager. Analyze project state objectively and recommend next steps based on defined criteria.",
        
        "CREATE_ISSUE_COMMENT": "You are a helpful collaborator. Provide constructive, specific feedback that advances the discussion. Be concise.",
        
        "UPDATE_README_TABLE": "You are a precise documentation maintainer. Update tables with exact formatting, maintaining consistency with existing entries.",
        
        "GENERATE_HELPER_FUNCTION": "You are a software architect. Create clean, reusable functions with clear interfaces and comprehensive documentation.",
        
        "IDENTIFY_IMPROVEMENTS": "You are a critical reviewer. Identify weaknesses and suggest constructive improvements.",
        
        "ADD_TASK_TYPE": "You are a system architect. Design and implement new task capabilities for the automation system.",
        
        "EDIT_TASK_TYPE": "You are a code refactoring expert. Improve existing implementations based on identified issues."
    }
    
    def __init__(self, model: PreTrainedModel, tokenizer: PreTrainedTokenizer, 
                 max_context: int = 2048):
        """
        Initialize conversation manager
        
        Args:
            model: The loaded language model
            tokenizer: The model's tokenizer
            max_context: Maximum context window size
        """
        self.model = model
        self.tokenizer = tokenizer
        self.max_context = max_context
        self.conversation_history: List[Dict[str, str]] = []
        self.model_name = model.name_or_path if hasattr(model, 'name_or_path') else ""
        
    def query_model(self, prompt: str, task_type: Optional[str] = None,
                   max_retries: int = 3, temperature: float = 0.7,
                   max_new_tokens: int = 512) -> Optional[str]:
        """
        Send prompt to model with task-specific formatting
        
        Args:
            prompt: The user prompt
            task_type: The task type for system prompt selection
            max_retries: Maximum number of retry attempts
            temperature: Sampling temperature
            max_new_tokens: Maximum tokens to generate
            
        Returns:
            Model response or None if failed
        """
        # Get system prompt for task
        system_prompt = self.SYSTEM_PROMPTS.get(
            task_type, 
            "You are a helpful AI assistant working on scientific research automation."
        )
        
        for attempt in range(max_retries):
            try:
                # Format prompt for the specific model
                formatted_prompt = self._format_for_model(system_prompt, prompt)
                
                # Manage context window
                formatted_prompt = self._manage_context(formatted_prompt)
                
                # Tokenize
                inputs = self.tokenizer(
                    formatted_prompt,
                    return_tensors="pt",
                    truncation=True,
                    max_length=self.max_context
                )
                
                # Move to same device as model
                if hasattr(self.model, 'device'):
                    inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
                
                # Generate
                with torch.no_grad():
                    # Prepare generation kwargs
                    gen_kwargs = {
                        "max_new_tokens": max_new_tokens,
                        "temperature": temperature,
                        "do_sample": True,
                        "top_p": 0.95,
                        "top_k": 50,
                        "repetition_penalty": 1.1,
                        "pad_token_id": self.tokenizer.pad_token_id,
                        "eos_token_id": self.tokenizer.eos_token_id
                    }
                    
                    # Disable cache for models with known issues
                    if "phi" in self.model_name.lower():
                        gen_kwargs["use_cache"] = False
                        
                    outputs = self.model.generate(
                        **inputs,
                        **gen_kwargs
                    )
                
                # Decode response
                response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
                
                # Extract only the assistant's response
                response = self._extract_response(response, formatted_prompt)
                
                # Validate response format for the task
                if self._validate_response(response, task_type):
                    # Store in conversation history
                    self.conversation_history.append({
                        "role": "user",
                        "content": prompt
                    })
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": response  
                    })
                    
                    logger.debug(f"Successful response on attempt {attempt + 1}")
                    return response
                else:
                    logger.warning(f"Invalid response format on attempt {attempt + 1}, retrying...")
                    temperature = min(1.0, temperature + 0.1)
                    
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise
                    
        return None
        
    def _format_for_model(self, system_prompt: str, user_prompt: str) -> str:
        """Format prompt based on model's expected format"""
        model_name = self.model.name_or_path.lower()
        
        # Common model formats
        if "phi" in model_name:
            return f"<|system|>{system_prompt}<|end|>\n<|user|>{user_prompt}<|end|>\n<|assistant|>"
            
        elif "qwen" in model_name:
            return f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{user_prompt}<|im_end|>\n<|im_start|>assistant\n"
            
        elif "gemma" in model_name:
            return f"<start_of_turn>user\n{system_prompt}\n\n{user_prompt}<end_of_turn>\n<start_of_turn>model\n"
            
        elif "tinyllama" in model_name or "llama" in model_name:
            return f"<|system|>\n{system_prompt}</s>\n<|user|>\n{user_prompt}</s>\n<|assistant|>\n"
            
        elif "mistral" in model_name or "mixtral" in model_name:
            return f"[INST] {system_prompt}\n\n{user_prompt} [/INST]"
            
        elif "stablelm" in model_name:
            return f"<|system|>\n{system_prompt}\n<|endoftext|>\n<|user|>\n{user_prompt}\n<|endoftext|>\n<|assistant|>\n"
            
        else:
            # Generic format
            return f"System: {system_prompt}\n\nHuman: {user_prompt}\n\nAssistant:"
            
    def _manage_context(self, prompt: str) -> str:
        """Manage context window by truncating if needed"""
        # Simple truncation for now - could be improved with summarization
        tokens = self.tokenizer.encode(prompt)
        if len(tokens) > self.max_context - 512:  # Leave room for response
            # Keep the most recent context
            tokens = tokens[-(self.max_context - 512):]
            prompt = self.tokenizer.decode(tokens, skip_special_tokens=True)
        return prompt
        
    def _extract_response(self, full_response: str, prompt: str) -> str:
        """Extract only the assistant's response from the full output"""
        # For models that include the full conversation, extract just the assistant's part
        response = full_response
        
        # Try to find assistant marker and extract content after it
        assistant_markers = ["<|assistant|>", "Assistant:", "assistant\n", "model\n"]
        for marker in assistant_markers:
            if marker in response:
                parts = response.split(marker)
                if len(parts) > 1:
                    response = parts[-1].strip()
                    break
        
        # If the original prompt format is still in the response, try to remove it
        if prompt in response:
            response = response.split(prompt)[-1].strip()
            
        # Remove system/user prompt artifacts
        if "<|system|>" in response:
            # Extract only the part after all the template stuff
            parts = response.split('\n')
            clean_parts = []
            skip_until_idea = True
            
            for part in parts:
                # Skip lines until we find actual content
                if skip_until_idea:
                    if any(keyword in part.lower() for keyword in ['title:', 'idea:', 'abstract:', 'approach:']):
                        skip_until_idea = False
                        clean_parts.append(part)
                else:
                    clean_parts.append(part)
                    
            response = '\n'.join(clean_parts).strip()
            
        # Clean up any remaining format tokens
        cleanup_patterns = [
            "<|assistant|>", "<|endoftext|>", "<|im_end|>", "<|system|>", "<|user|>",
            "</s>", "<end_of_turn>", "[/INST]", "<|end|>"
        ]
        
        for pattern in cleanup_patterns:
            response = response.replace(pattern, "").strip()
            
        return response
        
    def _validate_response(self, response: str, task_type: Optional[str]) -> bool:
        """Validate response meets task requirements"""
        if not response or len(response.strip()) < 10:
            return False
            
        # Task-specific validation
        validators = {
            "BRAINSTORM_IDEA": lambda r: len(r.strip()) > 20,  # Just need some content
            "WRITE_TECHNICAL_DESIGN": lambda r: len(r) > 500,  # Should be substantial
            "REVIEW_TECHNICAL_DESIGN": lambda r: "score:" in r.lower() or any(x in r.lower() for x in ["accept", "reject"]),
            "WRITE_CODE": lambda r: "def " in r or "class " in r or "import " in r,
            "WRITE_TESTS": lambda r: "def test" in r,
            "VALIDATE_REFERENCES": lambda r: any(x in r.lower() for x in ["valid", "invalid"]),
            "WRITE_METHODS": lambda r: len(r) > 200,
            "UPDATE_README_TABLE": lambda r: "|" in r,
            "GENERATE_HELPER_FUNCTION": lambda r: "def " in r,
            "CHECK_PROJECT_STATUS": lambda r: any(x in r.lower() for x in ["status", "recommend", "threshold"]),
            "PLAN_FIGURES": lambda r: any(x in r.lower() for x in ["figure", "plot", "visualization"]),
            "CREATE_FIGURES": lambda r: any(x in r for x in ["plt.", "fig", "ax", "matplotlib", "seaborn"])
        }
        
        validator = validators.get(task_type, lambda r: True)
        return validator(response)
        
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        
    def get_history(self) -> List[Dict[str, str]]:
        """Get conversation history"""
        return self.conversation_history.copy()