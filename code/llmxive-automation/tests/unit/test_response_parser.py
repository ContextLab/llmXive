"""Unit tests for ResponseParser"""

import pytest
from src.response_parser import ResponseParser


class TestResponseParser:
    """Test suite for ResponseParser"""
    
    @pytest.fixture
    def parser(self):
        """Create ResponseParser instance"""
        return ResponseParser()
    
    def test_parse_review_score_formats(self, parser):
        """Test parsing various score formats"""
        test_cases = [
            ("Score: 0.7", 0.7),
            ("Strong Accept (1.0)", 1.0),
            ("Accept (0.7)", 0.7),
            ("Weak Accept (0.3)", 0.3),
            ("Reject (0.0)", 0.0),
            ("rating: 0.8/1.0", 0.8),
            ("The score is 0.5", 0.5),
            ("No score here", None),
        ]
        
        for text, expected in test_cases:
            result = parser.parse_review_score(text)
            assert result == expected
    
    def test_parse_code_block_formats(self, parser):
        """Test parsing different code block formats"""
        # Markdown fenced block
        text1 = """Here's the code:
```python
def hello():
    return "world"
```"""
        result1 = parser.parse_code_block(text1)
        assert "def hello():" in result1
        assert "return \"world\"" in result1
        
        # Alternative fence
        text2 = """~~~python
import numpy as np
x = np.array([1, 2, 3])
~~~"""
        result2 = parser.parse_code_block(text2)
        assert "import numpy" in result2
        
        # Direct code
        text3 = """def calculate(x):
    return x * 2
    
print(calculate(5))"""
        result3 = parser.parse_code_block(text3)
        assert result3 is not None
        
        # No code
        text4 = "Just some regular text without code"
        result4 = parser.parse_code_block(text4)
        assert result4 is None
    
    def test_parse_table_row(self, parser):
        """Test parsing table rows"""
        # Well-formed row
        text1 = "| Project-1 | Test Project | Active |"
        result1 = parser.parse_table_row(text1)
        assert result1 == "| Project-1 | Test Project | Active |"
        
        # Row with extra spaces
        text2 = "|  Cell 1  |   Cell 2   |"
        result2 = parser.parse_table_row(text2)
        assert "Cell 1" in result2
        assert "Cell 2" in result2
        
        # Key-value format
        text3 = """Project: Test
Status: Active
Type: Research"""
        result3 = parser.parse_table_row(text3)
        assert result3 is not None
        assert "|" in result3
    
    def test_parse_brainstorm_response(self, parser):
        """Test parsing brainstorm responses"""
        # Well-formed response
        text1 = """Field: Computer Science
Idea: Develop a new algorithm for distributed computing that reduces latency
ID: cs-distributed-001
Keywords: distributed systems, algorithms, latency"""
        
        result1 = parser.parse_brainstorm_response(text1)
        assert result1 is not None
        assert result1['field'] == "Computer Science"
        assert "algorithm" in result1['idea']
        assert result1['id'] == "cs-distributed-001"
        assert "distributed systems" in result1['keywords']
        
        # Alternative formatting
        text2 = """**Field**: Biology
**Idea**: Create CRISPR variant for plant disease resistance
**ID**: bio-crispr-001
**Keywords**: CRISPR, plants, disease"""
        
        result2 = parser.parse_brainstorm_response(text2)
        assert result2 is not None
        assert result2['field'] == "Biology"
        
        # Missing fields
        text3 = """Field: Physics
Idea: Something about quantum"""
        result3 = parser.parse_brainstorm_response(text3)
        assert result3 is None  # Missing required fields
    
    def test_parse_review_response(self, parser):
        """Test parsing review responses"""
        text = """Strengths:
- Clear methodology
- Well-written introduction
- Good evaluation metrics

Concerns:
- Limited dataset size
- Missing baseline comparisons
- Timeline too optimistic

Recommendation: Accept
Score: 0.7
Summary: A solid proposal with minor issues that can be addressed."""
        
        result = parser.parse_review_response(text)
        assert result is not None
        assert "Clear methodology" in result['strengths']
        assert "Limited dataset" in result['concerns']
        assert result['recommendation'] == "Accept"
        assert result['score'] == 0.7
        assert "solid proposal" in result['summary']
    
    def test_parse_markdown_elements(self, parser):
        """Test parsing markdown elements"""
        text = """# Main Header
## Subheader

- List item 1
- List item 2

```python
code_block()
```

| Col1 | Col2 |
|------|------|
| A    | B    |

[Link text](http://example.com)"""
        
        result = parser.parse_markdown(text)
        
        # Check headers
        assert len(result['headers']) == 2
        assert result['headers'][0]['level'] == 1
        assert result['headers'][0]['text'] == "Main Header"
        
        # Check lists
        assert len(result['lists']) == 2
        assert "List item 1" in result['lists']
        
        # Check code blocks
        assert len(result['code_blocks']) == 1
        assert result['code_blocks'][0]['language'] == 'python'
        
        # Check tables
        assert len(result['tables']) == 1
        
        # Check links
        assert len(result['links']) == 1
        assert result['links'][0]['url'] == "http://example.com"
    
    def test_parse_structured_data(self, parser):
        """Test parsing structured data"""
        # JSON format
        text1 = 'Some text {"key": "value", "number": 42} more text'
        result1 = parser.parse_structured_data(text1)
        assert result1 == {"key": "value", "number": 42}
        
        # Key-value pairs
        text2 = """status: active
count: 10
enabled: true
score: 0.95"""
        result2 = parser.parse_structured_data(text2)
        assert result2['status'] == 'active'
        assert result2['count'] == 10
        assert result2['enabled'] is True
        assert result2['score'] == 0.95
    
    def test_parse_list_items(self, parser):
        """Test parsing various list formats"""
        # Bullet lists
        text1 = """- Item 1
- Item 2
- Item 3"""
        result1 = parser.parse_list_items(text1)
        assert len(result1) == 3
        assert "Item 1" in result1
        
        # Numbered lists
        text2 = """1. First item
2. Second item
3. Third item"""
        result2 = parser.parse_list_items(text2)
        assert len(result2) == 3
        assert "First item" in result2
        
        # Checkbox lists
        text3 = """[x] Completed task
[ ] Pending task
[x] Another done task"""
        result3 = parser.parse_list_items(text3)
        assert len(result3) == 3
        assert "Completed task" in result3
        
        # Mixed content
        text4 = """Some intro text:
- Mixed item 1
Regular paragraph
* Mixed item 2"""
        result4 = parser.parse_list_items(text4)
        assert "Mixed item 1" in result4
        assert "Mixed item 2" in result4
        assert "Regular paragraph" not in result4  # Should skip non-list items
    
    def test_parse_status_report(self, parser):
        """Test parsing status reports"""
        text = """Status: READY_TO_ADVANCE
Missing Score: 2.5
Missing Requirements:
- Need more reviews
- Update documentation
- Add tests

Recommended Actions:
- Request additional reviews
- Complete test suite"""
        
        result = parser.parse_status_report(text)
        assert result['status'] == "READY_TO_ADVANCE"
        assert result['missing_score'] == 2.5
        assert len(result['missing_requirements']) == 3
        assert "Need more reviews" in result['missing_requirements']
        assert len(result['recommended_actions']) == 2
    
    def test_parse_figure_plan(self, parser):
        """Test parsing figure plans"""
        text = """Figure 1: Distribution of Results
- Type: Histogram
- Data source: experiment_results.csv
- Shows frequency distribution

Figure 2. Correlation Analysis
- Type: Scatter plot
- Data from: correlation_data.csv
- Demonstrates relationship between variables"""
        
        result = parser.parse_figure_plan(text)
        assert len(result) == 2
        assert result[0]['number'] == '1'
        assert result[0]['title'] == "Distribution of Results"
        assert 'histogram' in result[0].get('type', '').lower()
        assert result[1]['number'] == '2'
    
    def test_parse_key_value(self, parser):
        """Test key-value parsing"""
        text = """Project: TestProject
Status: Active
Priority: High
**Owner**: John Doe
- Type: Research"""
        
        result = parser.parse_key_value(text)
        assert result['project'] == 'TestProject'
        assert result['status'] == 'Active'
        assert result['priority'] == 'High'
        assert result['owner'] == 'John Doe'
        assert result['type'] == 'Research'
    
    def test_parse_generic_fallback(self, parser):
        """Test generic parsing fallback"""
        text = """Task: Do something
Instructions: Follow these steps

Here is the actual content we want."""
        
        result = parser.parse_generic(text)
        assert "Task:" not in result  # Should remove instruction echoing
        assert "actual content" in result
    
    def test_empty_and_none_inputs(self, parser):
        """Test handling of empty and None inputs"""
        assert parser.parse_response("", "any_format") is None
        assert parser.parse_response(None, "any_format") is None
        
        # Individual parsers should handle empty strings gracefully
        assert parser.parse_review_score("") is None
        assert parser.parse_code_block("") is None
        assert parser.parse_brainstorm_response("") is None