// Auto-generated GitHub-aligned document mapping
// Generated on 2025-07-07T17:51:57.392Z

export const GITHUB_ALIGNED_PATHS = {
  "llmxive-auto-001": {
    "design": "technical_design_documents/llmXive_automation/design.md"
  },
  "llmxive-automation-testing": {
    "design": "technical_design_documents/llmXive_automation/design.md"
  },
  "llmxive-v2-final": {
    "design": "technical_design_documents/llmxive-v2-final/design.md"
  },
  "biology-20250704-001": {
    "design": "technical_design_documents/biology-20250704-001/design-completed.md"
  },
  "chemistry-20250704-001": {
    "design": "technical_design_documents/chemistry-20250704-001/design-completed.md"
  },
  "materials-science-20250705-001": {
    "design": "technical_design_documents/materials-science-20250705-001/design-completed.md"
  },
  "energy-20250704-001": {
    "design": "technical_design_documents/energy-20250704-001/design.md"
  },
  "computer-science-20250705-001": {
    "design": "technical_design_documents/computer-science-20250705-001/design.md"
  },
  "robotics-20250705-001": {
    "design": "technical_design_documents/robotics-20250705-001/design.md"
  },
  "agriculture-20250704-001": {
    "design": "technical_design_documents/agriculture-20250704-001/design.md"
  },
  "environmental-science-20250704-001": {
    "design": "technical_design_documents/environmental-science-20250704-001/design.md"
  },
  "psychology-20250704-001": {
    "design": "technical_design_documents/psychology-20250704-001/design.md"
  }
};

// GitHub base URLs
export const GITHUB_RAW_BASE = 'https://raw.githubusercontent.com/ContextLab/llmXive/main';
export const GITHUB_BLOB_BASE = 'https://github.com/ContextLab/llmXive/blob/main';

// Get document path for a project
export function getDocumentPath(projectId, documentType = 'design') {
    const project = GITHUB_ALIGNED_PATHS[projectId];
    return project ? project[documentType] : null;
}

// Get GitHub raw URL for direct content fetching
export function getGitHubRawUrl(filePath) {
    return `${GITHUB_RAW_BASE}/${filePath}`;
}

// Get GitHub blob URL for viewing
export function getGitHubBlobUrl(filePath) {
    return `${GITHUB_BLOB_BASE}/${filePath}`;
}
