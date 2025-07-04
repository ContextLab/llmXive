"""Response parsing for various LLM output formats"""

import re
import json
import logging
from datetime import datetime
from typing import Optional, Dict, List, Any, Union

logger = logging.getLogger(__name__)


class ResponseParser:
    """Comprehensive parser for all LLM response formats"""
    
    def __init__(self):
        """Initialize response parser"""
        self.parsers = {
            "review_score": self.parse_review_score,
            "code_block": self.parse_code_block,
            "table_row": self.parse_table_row,
            "status_report": self.parse_status_report,
            "markdown": self.parse_markdown,
            "structured_data": self.parse_structured_data,
            "list_items": self.parse_list_items,
            "key_value": self.parse_key_value,
            "brainstorm": self.parse_brainstorm_response,
            "review": self.parse_review_response,
            "figure_plan": self.parse_figure_plan
        }
        
    def parse_response(self, response: str, expected_format: str) -> Any:
        """
        Main parsing method that routes to specific parsers
        
        Args:
            response: Raw LLM response
            expected_format: Expected format type
            
        Returns:
            Parsed response in appropriate format
        """
        if not response:
            return None
            
        if expected_format not in self.parsers:
            logger.warning(f"Unknown format {expected_format}, using generic parser")
            return self.parse_generic(response)
            
        try:
            return self.parsers[expected_format](response)
        except Exception as e:
            logger.error(f"Error parsing {expected_format}: {e}")
            return self.parse_generic(response)
            
    def parse_review_score(self, text: str) -> Optional[float]:
        """Extract review scores in various formats"""
        # Score patterns
        score_patterns = [
            (r'Score:\s*([0-9.]+)', lambda m: float(m.group(1))),
            (r'Strong Accept\s*[\(\[]?1\.0[\)\]]?', lambda m: 1.0),
            (r'Accept\s*[\(\[]?0\.7[\)\]]?', lambda m: 0.7),
            (r'Weak Accept\s*[\(\[]?0\.3[\)\]]?', lambda m: 0.3),
            (r'Reject\s*[\(\[]?0(?:\.0)?[\)\]]?', lambda m: 0.0),
            (r'rating[:\s]+([0-9.]+)\s*/\s*1(?:\.0)?', lambda m: float(m.group(1))),
            (r'(?:score|rating).*?([0-9.]+)', lambda m: float(m.group(1)))
        ]
        
        for pattern, extractor in score_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    score = extractor(match)
                    # Allow scores up to 10 and normalize to 0-1
                    if 0 <= score <= 10:
                        if score > 1.0:
                            score = score / 10.0  # Normalize to 0-1 range
                        return score
                except ValueError:
                    continue
                    
        return None
        
    def parse_code_block(self, text: str) -> Optional[str]:
        """Extract code blocks in various formats"""
        # Multiple code block formats
        code_patterns = [
            # Markdown fenced blocks
            r'```(?:python|py)?\s*\n(.*?)\n```',
            r'~~~(?:python|py)?\s*\n(.*?)\n~~~',
            # Indented code after prompt
            r'(?:code:|output:|result:)\s*\n((?:[ \t]+.+\n)+)',
            # XML-style tags
            r'<code>\s*\n?(.*?)\n?</code>',
            # Direct code with def/class
            r'((?:def|class|import|from)\s+\S+.*?)(?=\n\n|\n[A-Z]|\Z)'
        ]
        
        for pattern in code_patterns:
            matches = re.findall(pattern, text, re.DOTALL | re.MULTILINE)
            if matches:
                # Return the longest match (likely most complete)
                return max(matches, key=len).strip()
                
        # Check if the entire response looks like code
        if any(text.strip().startswith(x) for x in ['def ', 'class ', 'import ', 'from ']):
            return text.strip()
            
        return None
        
    def parse_table_row(self, text: str) -> Optional[str]:
        """Parse table row in markdown format"""
        # Look for pipe-separated values
        row_pattern = r'\|([^|\n]+\|)+'
        match = re.search(row_pattern, text)
        
        if match:
            # Clean and format the row
            row = match.group(0).strip()
            
            # Ensure proper spacing
            cells = [cell.strip() for cell in row.split('|') if cell.strip()]
            return '| ' + ' | '.join(cells) + ' |'
            
        # Try to construct from structured data
        if ':' in text:
            parts = []
            for line in text.split('\n'):
                if ':' in line and not line.strip().startswith('#'):
                    _, value = line.split(':', 1)
                    parts.append(value.strip())
                    
            if parts:
                return '| ' + ' | '.join(parts) + ' |'
                
        return None
        
    def parse_brainstorm_response(self, text: str) -> Optional[Dict[str, str]]:
        """Parse brainstorming response"""
        result = {}
        
        # Check for Title/Idea format (used in FORK_IDEA)
        title_match = re.search(r'Title:\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
        if title_match:
            # Parse Title/Idea format
            idea_match = re.search(r'Idea:\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
            if idea_match:
                result['idea'] = idea_match.group(1).strip()
            else:
                result['idea'] = title_match.group(1).strip()
                
            # Extract other fields
            field_match = re.search(r'Field:\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
            if field_match:
                result['field'] = field_match.group(1).strip()
                
            # Generate ID from field
            if 'field' in result:
                field_short = result['field'].lower().replace(' ', '-')[:20]
                date_str = datetime.now().strftime('%Y%m%d')
                result['id'] = f"{field_short}-{date_str}-001"
                
            # Extract keywords
            keywords_match = re.search(r'Keywords?:\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
            if keywords_match:
                result['keywords'] = keywords_match.group(1).strip()
            else:
                # Generate keywords from idea
                words = result.get('idea', '').lower().split()[:5]
                result['keywords'] = ', '.join(words)
                
            if 'field' in result and 'idea' in result:
                return result
        
        # Try standard format
        # Required fields
        fields = ['field', 'idea', 'id', 'keywords']
        
        for field in fields:
            # Try different patterns
            patterns = [
                rf"{field}:\s*(.+?)(?:\n|$)",
                rf"\*\*{field}\*\*:\s*(.+?)(?:\n|$)",
                rf"{field.title()}:\s*(.+?)(?:\n|$)",
                rf"{field.upper()}:\s*(.+?)(?:\n|$)"
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                if match:
                    value = match.group(1).strip()
                    # Clean up the value
                    if field == 'idea':
                        # Allow multi-line ideas
                        value = re.sub(r'\n(?=\w+:)', '', value)
                    result[field.lower()] = value
                    break
                    
        # Check if we got all required fields
        if len(result) == len(fields):
            return result
            
        logger.warning(f"Missing fields in brainstorm response. Got: {list(result.keys())}")
        return None
        
    def parse_review_response(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse review response"""
        result = {}
        
        # Extract strengths
        strengths_match = re.search(r'Strengths?:?\s*\n((?:[-*•]\s*.+\n?)+)', text, re.MULTILINE | re.IGNORECASE)
        if strengths_match:
            result['strengths'] = strengths_match.group(1).strip()
            
        # Extract concerns
        concerns_match = re.search(r'Concerns?:?\s*\n((?:[-*•]\s*.+\n?)+)', text, re.MULTILINE | re.IGNORECASE)
        if concerns_match:
            result['concerns'] = concerns_match.group(1).strip()
            
        # Extract recommendation
        rec_match = re.search(r'Recommendation:\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
        if rec_match:
            result['recommendation'] = rec_match.group(1).strip()
            
        # Extract score
        score = self.parse_review_score(text)
        if score is not None:
            result['score'] = score
            
        # Extract summary
        summary_match = re.search(r'Summary:\s*(.+?)(?:\n\n|\Z)', text, re.IGNORECASE | re.DOTALL)
        if summary_match:
            result['summary'] = summary_match.group(1).strip()
            
        # Validate we have minimum required fields
        if 'score' in result and ('strengths' in result or 'concerns' in result):
            return result
            
        return None
        
    def parse_markdown(self, text: str) -> Dict[str, List]:
        """Parse markdown elements"""
        elements = {
            'headers': [],
            'lists': [],
            'code_blocks': [],
            'tables': [],
            'links': [],
            'emphasis': []
        }
        
        # Headers
        header_pattern = r'^(#{1,6})\s+(.+)$'
        for match in re.finditer(header_pattern, text, re.MULTILINE):
            elements['headers'].append({
                'level': len(match.group(1)),
                'text': match.group(2).strip()
            })
            
        # Lists (bullet and numbered)
        list_pattern = r'^[\s]*[-*+\d.]+\s+(.+)$'
        for match in re.finditer(list_pattern, text, re.MULTILINE):
            elements['lists'].append(match.group(1).strip())
            
        # Code blocks
        code_pattern = r'```(\w*)\n(.*?)\n```'
        for match in re.finditer(code_pattern, text, re.DOTALL):
            elements['code_blocks'].append({
                'language': match.group(1) or 'text',
                'code': match.group(2)
            })
            
        # Tables
        table_pattern = r'(\|.+\|(?:\n\|[-:\s|]+\|)?(?:\n\|.+\|)*)'
        for match in re.finditer(table_pattern, text, re.MULTILINE):
            elements['tables'].append(match.group(1))
            
        # Links  
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        for match in re.finditer(link_pattern, text):
            elements['links'].append({
                'text': match.group(1),
                'url': match.group(2)
            })
            
        return elements
        
    def parse_structured_data(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse structured data in various formats"""
        # Try JSON first
        json_pattern = r'\{[^{}]*\}'
        json_matches = re.findall(json_pattern, text)
        
        for match in json_matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
                
        # Try key-value pairs
        data = {}
        kv_pattern = r'^([A-Za-z_]\w*):\s*(.+)$'
        
        for match in re.finditer(kv_pattern, text, re.MULTILINE):
            key = match.group(1).lower()
            value = match.group(2).strip()
            
            # Try to parse value as appropriate type
            if value.lower() in ['true', 'false']:
                data[key] = value.lower() == 'true'
            elif value.replace('.', '').replace('-', '').isdigit():
                try:
                    data[key] = float(value) if '.' in value else int(value)
                except ValueError:
                    data[key] = value
            else:
                data[key] = value
                
        return data if data else None
        
    def parse_list_items(self, text: str) -> List[str]:
        """Extract list items in various formats"""
        items = []
        
        # Different list formats
        list_patterns = [
            r'^\s*[-*+]\s+(.+)$',         # Bullet lists
            r'^\s*\d+[.)]\s+(.+)$',       # Numbered lists
            r'^\s*\[[ x]\]\s+(.+)$',      # Checkbox lists
            r'^(?:[A-Z]|[a-z])[.)]\s+(.+)$',  # Letter lists
        ]
        
        for pattern in list_patterns:
            for match in re.finditer(pattern, text, re.MULTILINE):
                item = match.group(1).strip()
                if item and item not in items:
                    items.append(item)
                    
        # If no formal list found, try newline-separated items
        if not items:
            lines = text.strip().split('\n')
            items = [line.strip() for line in lines 
                    if line.strip() and not line.strip().endswith(':') and len(line.strip()) > 5]
                    
        return items
        
    def parse_key_value(self, text: str) -> Dict[str, str]:
        """Parse key-value pairs"""
        result = {}
        
        # Multiple key-value patterns
        patterns = [
            r'^([A-Za-z_]\w*):\s*(.+?)(?=\n[A-Za-z_]|\Z)',
            r'\*\*([A-Za-z_]\w*)\*\*:\s*(.+?)(?=\n|\Z)',
            r'^-\s*([A-Za-z_]\w*):\s*(.+?)(?=\n|\Z)'
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.MULTILINE | re.DOTALL):
                key = match.group(1).lower().replace(' ', '_')
                value = match.group(2).strip()
                result[key] = value
                
        return result
        
    def parse_status_report(self, text: str) -> Dict[str, Any]:
        """Parse project status report"""
        result = {}
        
        # Status
        status_match = re.search(r'Status:\s*(READY_TO_ADVANCE|NOT_READY|READY|BLOCKED)', 
                                text, re.IGNORECASE)
        if status_match:
            result['status'] = status_match.group(1).upper()
            
        # Missing score
        score_match = re.search(r'Missing Score:\s*([0-9.]+)', text, re.IGNORECASE)
        if score_match:
            result['missing_score'] = float(score_match.group(1))
            
        # Missing requirements (list)
        req_match = re.search(r'Missing Requirements?:?\s*\n((?:[-*]\s*.+\n?)+)', 
                             text, re.MULTILINE)
        if req_match:
            result['missing_requirements'] = self.parse_list_items(req_match.group(1))
            
        # Recommended actions
        actions_match = re.search(r'Recommended Actions?:?\s*\n((?:[-*]\s*.+\n?)+)', 
                                 text, re.MULTILINE)
        if actions_match:
            result['recommended_actions'] = self.parse_list_items(actions_match.group(1))
            
        return result
        
    def parse_figure_plan(self, text: str) -> List[Dict[str, str]]:
        """Parse figure planning response"""
        figures = []
        
        # Look for figure specifications
        figure_pattern = r'(?:Figure|Fig\.?)\s*(\d+)[:.]\s*(.+?)\n((?:[-*]\s*.+\n?)+)'
        
        for match in re.finditer(figure_pattern, text, re.MULTILINE):
            figure = {
                'number': match.group(1),
                'title': match.group(2).strip(),
                'details': match.group(3).strip()
            }
            
            # Extract specific details
            details_text = figure['details']
            
            # Type
            type_match = re.search(r'Type:\s*(.+?)(?:\n|$)', details_text, re.IGNORECASE)
            if type_match:
                figure['type'] = type_match.group(1).strip()
                
            # Data source
            data_match = re.search(r'Data (?:source|from):\s*(.+?)(?:\n|$)', 
                                  details_text, re.IGNORECASE)
            if data_match:
                figure['data_source'] = data_match.group(1).strip()
                
            figures.append(figure)
            
        return figures
        
    def parse_generic(self, text: str) -> str:
        """Generic parsing for unexpected formats"""
        # Clean up common formatting issues
        text = text.strip()
        
        # Remove any instruction echoing
        lines = text.split('\n')
        if lines and any(keyword in lines[0].lower() 
                        for keyword in ['task:', 'instructions:', 'output:']):
            lines = lines[1:]
            text = '\n'.join(lines)
            
        return text