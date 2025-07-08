// Auto-generated document path mapping
// Generated on 2025-07-07T17:44:17.293Z

export const DOCUMENT_PATHS = {
  "biology-20250704-001": {
    "design": "technical_design_documents/biology-20250704-001/design-completed.md"
  },
  "chemistry-20250704-001": {
    "design": "technical_design_documents/chemistry-20250704-001/design-completed.md"
  },
  "materials-science-20250705-001": {
    "design": "technical_design_documents/materials-science-20250705-001/design-completed.md"
  }
};

// GitHub base URL for fallback links
export const GITHUB_BASE = 'https://github.com/ContextLab/llmXive/blob/main';

// Get document URL for a project
export function getDocumentUrl(projectId, documentType) {
    const mapping = DOCUMENT_PATHS[projectId];
    if (!mapping || !mapping[documentType]) {
        return null;
    }
    return mapping[documentType];
}

// Get GitHub URL for a document
export function getGitHubUrl(filePath) {
    return `${GITHUB_BASE}/${filePath}`;
}
