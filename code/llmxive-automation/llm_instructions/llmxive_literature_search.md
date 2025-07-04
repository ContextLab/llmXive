# llmXive Literature Search Implementation

This implementation searches the actual llmXive archive of completed papers.

## Updated Literature Search Implementation

```python
class LLMXiveLiteratureSearcher:
    """Searches the llmXive archive of completed papers"""
    
    def __init__(self, github_handler):
        self.github = github_handler
        
    def search_llmxive_papers(self, topic, keywords=[]):
        """Search completed papers in llmXive archive"""
        
        # Read the completed papers table
        papers_readme = self.github.get_file_content("papers/README.md")
        if not papers_readme:
            return []
            
        # Parse completed papers table
        completed_papers = self.parse_completed_papers_table(papers_readme)
        
        # Search through papers
        relevant_papers = []
        
        for paper in completed_papers:
            # Read paper content
            paper_content = self.read_paper_content(paper['id'])
            
            if paper_content:
                # Check relevance
                relevance_score = self.calculate_relevance(
                    paper_content, topic, keywords)
                    
                if relevance_score > 0.3:  # Threshold
                    paper['relevance_score'] = relevance_score
                    paper['content_preview'] = self.extract_abstract(paper_content)
                    relevant_papers.append(paper)
                    
        # Sort by relevance
        relevant_papers.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return relevant_papers
        
    def parse_completed_papers_table(self, readme_content):
        """Extract paper information from README table"""
        import re
        
        papers = []
        
        # Find the completed work table
        table_match = re.search(
            r'## Completed work\s*\n\s*\|.*?\|.*?\n\|[-:\s|]+\|.*?\n((?:\|.*?\|.*?\n)+)',
            readme_content, re.MULTILINE | re.DOTALL
        )
        
        if not table_match:
            return papers
            
        table_rows = table_match.group(1).strip().split('\n')
        
        for row in table_rows:
            if not row.strip() or not '|' in row:
                continue
                
            # Parse table row
            cells = [cell.strip() for cell in row.split('|')[1:-1]]
            
            if len(cells) >= 6:  # Expected columns
                paper = {
                    'id': cells[0],
                    'title': cells[1],
                    'status': cells[2],
                    'issue_link': cells[3],
                    'paper_link': cells[4],
                    'contributors': cells[5]
                }
                papers.append(paper)
                
        return papers
        
    def read_paper_content(self, paper_id):
        """Read the actual paper content"""
        
        # Try different possible paths
        paths_to_try = [
            f"papers/{paper_id}/paper.tex",
            f"papers/{paper_id}/paper.md", 
            f"papers/{paper_id}/main.tex",
            f"papers/{paper_id}/manuscript.tex"
        ]
        
        for path in paths_to_try:
            content = self.github.get_file_content(path)
            if content:
                return content
                
        return None
        
    def calculate_relevance(self, paper_content, topic, keywords):
        """Calculate relevance score for a paper"""
        
        content_lower = paper_content.lower()
        topic_lower = topic.lower()
        
        # Base relevance from topic
        relevance = 0.0
        
        # Topic in title/abstract
        if topic_lower in content_lower[:1000]:  # First 1000 chars
            relevance += 0.5
            
        # Topic frequency in full text
        topic_count = content_lower.count(topic_lower)
        relevance += min(topic_count * 0.05, 0.3)
        
        # Keyword matching
        for keyword in keywords:
            if keyword.lower() in content_lower:
                relevance += 0.1
                
        # Cap at 1.0
        return min(relevance, 1.0)
        
    def extract_abstract(self, paper_content):
        """Extract abstract from paper content"""
        import re
        
        # Try LaTeX abstract
        abstract_match = re.search(
            r'\\begin\{abstract\}(.*?)\\end\{abstract\}',
            paper_content, re.DOTALL
        )
        
        if abstract_match:
            return abstract_match.group(1).strip()
            
        # Try markdown abstract
        abstract_match = re.search(
            r'## Abstract\s*\n(.*?)(?=\n##|\Z)',
            paper_content, re.DOTALL
        )
        
        if abstract_match:
            return abstract_match.group(1).strip()
            
        # Return first paragraph as fallback
        lines = paper_content.split('\n')
        for i, line in enumerate(lines):
            if line.strip() and not line.startswith('#') and not line.startswith('\\'):
                return ' '.join(lines[i:i+5])  # First 5 lines
                
        return "Abstract not found"
        
    def create_llmxive_bibliography(self, papers, topic):
        """Create bibliography from llmXive papers"""
        
        bibliography = f"""# llmXive Literature Review: {topic}

**Generated**: {datetime.now().strftime('%Y-%m-%d')}
**Papers Found**: {len(papers)}
**Source**: llmXive Completed Papers Archive

## Relevant Papers

"""
        
        for i, paper in enumerate(papers, 1):
            bibliography += f"""### {i}. {paper['title']}

**Project ID**: {paper['id']}
**Contributors**: {paper['contributors']}
**Relevance Score**: {paper['relevance_score']:.2f}
**Paper Link**: {paper['paper_link']}
**Issue**: {paper['issue_link']}

**Abstract/Preview**:
{paper.get('content_preview', 'Not available')}

**Relevance to {topic}**:
This paper is relevant because it addresses aspects of {topic} through...

---

"""
        
        if not papers:
            bibliography += """*No relevant papers found in the llmXive archive for this topic.*

Consider:
1. Broadening search terms
2. Checking papers currently in progress
3. This may be a novel area for llmXive research
"""
        
        return bibliography


# Updated task implementation for literature search
def execute_literature_search(self, context):
    """Conduct literature search within llmXive archive"""
    
    topic = context.get('topic')
    keywords = context.get('keywords', [])
    project_id = context.get('project_id')
    
    if not topic:
        return {"error": "No topic provided"}
        
    # Initialize llmXive searcher
    searcher = LLMXiveLiteratureSearcher(self.github)
    
    # Search the archive
    relevant_papers = searcher.search_llmxive_papers(topic, keywords)
    
    # Have LLM analyze the papers for deeper insights
    if relevant_papers:
        papers_summary = "\n".join([
            f"- {p['title']} (ID: {p['id']}, Relevance: {p['relevance_score']:.2f})"
            for p in relevant_papers[:10]
        ])
        
        prompt = f"""Task: Analyze these llmXive papers for insights related to {topic}.

Papers found:
{papers_summary}

Provide:
1. How these papers relate to {topic}
2. Key methods or findings that could be relevant
3. Gaps in the current llmXive literature
4. Suggestions for building on this work

Be specific about connections and opportunities."""

        analysis = self.conv_mgr.query_model(prompt, task_type="CONDUCT_LITERATURE_SEARCH")
    else:
        analysis = f"No papers directly related to {topic} found in llmXive archive. This represents an opportunity for novel research."
        
    # Create bibliography
    bibliography = searcher.create_llmxive_bibliography(relevant_papers, topic)
    
    # Add LLM analysis
    bibliography += f"\n\n## Analysis\n\n{analysis}"
    
    # Save bibliography
    bib_path = f"literature/{project_id or 'general'}/llmxive_bibliography.md"
    self.github.create_file(bib_path, bibliography,
        f"Add llmXive literature review for {topic}")
        
    # Also create a note about external literature
    external_note = f"""# Note on External Literature

This search was conducted within the llmXive archive only. 

For a comprehensive literature review including external human-authored papers, we would need:
1. Access to academic databases (arXiv, PubMed, etc.)
2. Web browsing capabilities
3. PDF parsing abilities

A GitHub issue has been created to track this enhancement: #[TODO]

For now, please supplement this llmXive-internal review with manual searches of relevant external literature."""

    note_path = f"literature/{project_id or 'general'}/external_literature_note.md"
    self.github.create_file(note_path, external_note,
        f"Add note about external literature for {topic}")
        
    return {
        "success": True,
        "bibliography_path": bib_path,
        "papers_found": len(relevant_papers),
        "note_path": note_path
    }
```

## Usage Example

When the automation system needs to do a literature search:

```python
# Execute literature search task
result = executor.execute_task(
    task_type="CONDUCT_LITERATURE_SEARCH",
    context={
        "topic": "neural network optimization",
        "keywords": ["gradient", "convergence", "learning rate"],
        "project_id": "ml-optimization-001"
    }
)

# Result includes:
# - bibliography_path: Path to generated bibliography
# - papers_found: Number of relevant llmXive papers
# - note_path: Path to note about external literature
```

## Benefits of llmXive-Internal Search

1. **Self-Referential**: Papers can build on previous llmXive work
2. **Quality Assured**: All papers have been reviewed
3. **Accessible**: No external API dependencies
4. **Reproducible**: All referenced work is in the repository
5. **Growing**: Archive expands with each completed project

## Future Enhancement

Create GitHub issue for web-based literature search:

```markdown
**Title**: Add Web-Based Literature Search Capability

**Description**: 
Currently, literature searches are limited to the llmXive archive. To conduct comprehensive literature reviews, we need:

1. Web browsing capabilities for models that support it
2. Academic database API integration (arXiv, Semantic Scholar, PubMed)
3. PDF download and parsing
4. Reference validation through DOI/URL checking
5. Citation graph analysis

This would enable truly comprehensive literature reviews combining both llmXive and external human research.

**Labels**: enhancement, automation, literature-search
```