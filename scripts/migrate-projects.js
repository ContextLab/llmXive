#!/usr/bin/env node

/**
 * llmXive Project Migration Script
 * Migrates projects from scattered directories to unified structure
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// Configuration
const DRY_RUN = process.argv.includes('--dry-run');
const VERBOSE = process.argv.includes('--verbose');
const FORCE = process.argv.includes('--force');

const REPO_ROOT = path.join(__dirname, '..');
const PROJECTS_DIR = path.join(REPO_ROOT, 'projects');
const SYSTEM_DIR = path.join(REPO_ROOT, '.llmxive-system');

// Migration mapping
const MIGRATION_SOURCES = {
  papers: path.join(REPO_ROOT, 'papers'),
  technical_design_documents: path.join(REPO_ROOT, 'technical_design_documents'),
  implementation_plans: path.join(REPO_ROOT, 'implementation_plans'),
  reviews: path.join(REPO_ROOT, 'reviews'),
  code: path.join(REPO_ROOT, 'code'),
  data: path.join(REPO_ROOT, 'data')
};

class ProjectMigrator {
  constructor() {
    this.migrations = [];
    this.errors = [];
    this.warnings = [];
  }

  log(message, level = 'info') {
    const timestamp = new Date().toISOString();
    const prefix = `[${timestamp}] [${level.toUpperCase()}]`;
    
    if (level === 'error') {
      console.error(`${prefix} ${message}`);
      this.errors.push(message);
    } else if (level === 'warn') {
      console.warn(`${prefix} ${message}`);
      this.warnings.push(message);
    } else if (VERBOSE || level === 'info') {
      console.log(`${prefix} ${message}`);
    }
  }

  async validateEnvironment() {
    this.log('Validating environment...');
    
    // Check if we're in a git repository
    try {
      execSync('git status', { cwd: REPO_ROOT, stdio: 'ignore' });
    } catch (error) {
      throw new Error('Not in a git repository');
    }

    // Check if system directory exists
    if (!fs.existsSync(SYSTEM_DIR)) {
      throw new Error('.llmxive-system directory not found. Run setup-system.js first.');
    }

    // Check if projects directory exists
    if (!fs.existsSync(PROJECTS_DIR)) {
      if (!DRY_RUN) {
        fs.mkdirSync(PROJECTS_DIR, { recursive: true });
      }
      this.log('Created projects directory');
    }

    // Check for uncommitted changes
    try {
      const status = execSync('git status --porcelain', { cwd: REPO_ROOT, encoding: 'utf8' });
      if (status.trim() && !FORCE) {
        throw new Error('Repository has uncommitted changes. Use --force to proceed or commit changes first.');
      }
    } catch (error) {
      if (!FORCE) {
        throw error;
      }
    }

    this.log('Environment validation passed');
  }

  generateProjectId(originalName, field = 'unknown') {
    // Extract number from name if present
    const numberMatch = originalName.match(/(\d+)/);
    const number = numberMatch ? numberMatch[1].padStart(3, '0') : '001';
    
    // Clean name for project ID
    const cleanName = originalName
      .replace(/[^a-zA-Z0-9-]/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-|-$/g, '')
      .toLowerCase();
    
    return `PROJ-${number}-${cleanName}`;
  }

  async discoverExistingProjects() {
    this.log('Discovering existing projects...');
    const projects = new Map();

    // Scan papers directory
    if (fs.existsSync(MIGRATION_SOURCES.papers)) {
      const entries = fs.readdirSync(MIGRATION_SOURCES.papers);
      for (const entry of entries) {
        const fullPath = path.join(MIGRATION_SOURCES.papers, entry);
        if (fs.statSync(fullPath).isDirectory() && entry !== 'README.md') {
          const projectId = this.generateProjectId(entry, 'unknown');
          projects.set(projectId, {
            id: projectId,
            originalName: entry,
            sources: {
              paper: fullPath
            },
            field: this.inferField(entry),
            status: 'in-progress'
          });
        }
      }
    }

    // Scan technical design documents
    if (fs.existsSync(MIGRATION_SOURCES.technical_design_documents)) {
      const entries = fs.readdirSync(MIGRATION_SOURCES.technical_design_documents);
      for (const entry of entries) {
        const fullPath = path.join(MIGRATION_SOURCES.technical_design_documents, entry);
        if (fs.statSync(fullPath).isDirectory()) {
          const projectId = this.generateProjectId(entry);
          if (projects.has(projectId)) {
            projects.get(projectId).sources.technical_design = fullPath;
          } else {
            projects.set(projectId, {
              id: projectId,
              originalName: entry,
              sources: {
                technical_design: fullPath
              },
              field: this.inferField(entry),
              status: 'ready'
            });
          }
        }
      }
    }

    // Scan implementation plans
    if (fs.existsSync(MIGRATION_SOURCES.implementation_plans)) {
      const entries = fs.readdirSync(MIGRATION_SOURCES.implementation_plans);
      for (const entry of entries) {
        const fullPath = path.join(MIGRATION_SOURCES.implementation_plans, entry);
        if (fs.statSync(fullPath).isDirectory()) {
          const projectId = this.generateProjectId(entry);
          if (projects.has(projectId)) {
            projects.get(projectId).sources.implementation_plan = fullPath;
          } else {
            projects.set(projectId, {
              id: projectId,
              originalName: entry,
              sources: {
                implementation_plan: fullPath
              },
              field: this.inferField(entry),
              status: 'ready'
            });
          }
        }
      }
    }

    this.log(`Discovered ${projects.size} projects`);
    return projects;
  }

  inferField(projectName) {
    const fieldMappings = {
      'biology': ['biology', 'bio', 'gene', 'neural', 'neuroscience', 'brain'],
      'chemistry': ['chemistry', 'chem', 'chemical', 'molecular'],
      'computer-science': ['computer', 'cs', 'software', 'algorithm', 'programming'],
      'materials-science': ['materials', 'material', 'physics', 'physical'],
      'energy': ['energy', 'power', 'solar', 'battery'],
      'environmental-science': ['environmental', 'environment', 'climate', 'ecology'],
      'psychology': ['psychology', 'psych', 'behavioral', 'cognitive'],
      'robotics': ['robotics', 'robot', 'automation'],
      'agriculture': ['agriculture', 'agri', 'farming', 'crop']
    };

    const lowerName = projectName.toLowerCase();
    for (const [field, keywords] of Object.entries(fieldMappings)) {
      if (keywords.some(keyword => lowerName.includes(keyword))) {
        return field;
      }
    }
    return 'meta';
  }

  async createProjectStructure(project) {
    const projectPath = path.join(PROJECTS_DIR, project.id);
    
    if (DRY_RUN) {
      this.log(`Would create project structure: ${projectPath}`, 'debug');
      return;
    }

    // Create main directory
    if (!fs.existsSync(projectPath)) {
      fs.mkdirSync(projectPath, { recursive: true });
    }

    // Create .llmxive subdirectory
    const llmxivePath = path.join(projectPath, '.llmxive');
    if (!fs.existsSync(llmxivePath)) {
      fs.mkdirSync(llmxivePath);
    }

    // Create phase directories
    const phases = ['idea', 'technical-design', 'implementation-plan', 'code', 'data', 'paper', 'reviews'];
    for (const phase of phases) {
      const phasePath = path.join(projectPath, phase);
      if (!fs.existsSync(phasePath)) {
        fs.mkdirSync(phasePath);
      }
    }

    // Create review subdirectories
    const reviewPath = path.join(projectPath, 'reviews');
    const reviewTypes = ['design', 'implementation', 'paper', 'code'];
    for (const reviewType of reviewTypes) {
      const reviewTypePath = path.join(reviewPath, reviewType);
      if (!fs.existsSync(reviewTypePath)) {
        fs.mkdirSync(reviewTypePath);
      }
    }

    // Create project configuration
    const config = {
      id: project.id,
      title: project.originalName.replace(/-/g, ' ').replace(/\\b\\w/g, l => l.toUpperCase()),
      description: `Migrated project: ${project.originalName}`,
      field: project.field,
      status: project.status,
      created_date: new Date().toISOString(),
      updated_date: new Date().toISOString(),
      contributors: [],
      github_issues: [],
      phases: {
        idea: { completed: false, points: 0 },
        technical_design: { completed: false, points: 0 },
        implementation_plan: { completed: false, points: 0 },
        code: { completed: false, points: 0 },
        paper: { completed: false, points: 0 }
      }
    };

    const configPath = path.join(llmxivePath, 'config.json');
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2));

    this.log(`Created project structure: ${project.id}`);
  }

  async migrateProjectContent(project) {
    const projectPath = path.join(PROJECTS_DIR, project.id);
    
    for (const [sourceType, sourcePath] of Object.entries(project.sources)) {
      if (!fs.existsSync(sourcePath)) {
        this.log(`Source not found: ${sourcePath}`, 'warn');
        continue;
      }

      const targetPath = path.join(projectPath, this.getTargetDirectory(sourceType));
      
      if (DRY_RUN) {
        this.log(`Would migrate: ${sourcePath} -> ${targetPath}`, 'debug');
        continue;
      }

      // Copy files
      try {
        execSync(`cp -r "${sourcePath}/"* "${targetPath}/"`, { stdio: 'ignore' });
        this.log(`Migrated ${sourceType}: ${sourcePath} -> ${targetPath}`);
      } catch (error) {
        this.log(`Failed to migrate ${sourceType}: ${error.message}`, 'error');
      }
    }
  }

  getTargetDirectory(sourceType) {
    const mapping = {
      'paper': 'paper',
      'technical_design': 'technical-design',
      'implementation_plan': 'implementation-plan',
      'code': 'code',
      'data': 'data',
      'reviews': 'reviews'
    };
    return mapping[sourceType] || sourceType;
  }

  async generateMigrationReport() {
    const reportPath = path.join(REPO_ROOT, 'migration-report.md');
    const report = [
      '# Project Migration Report',
      '',
      `**Date**: ${new Date().toISOString()}`,
      `**Mode**: ${DRY_RUN ? 'DRY RUN' : 'LIVE'}`,
      '',
      `## Summary`,
      `- Projects migrated: ${this.migrations.length}`,
      `- Errors: ${this.errors.length}`,
      `- Warnings: ${this.warnings.length}`,
      '',
      '## Migrated Projects',
      ...this.migrations.map(m => `- ${m.id}: ${m.originalName} (${m.field})`),
      '',
      '## Errors',
      ...this.errors.map(e => `- ${e}`),
      '',
      '## Warnings',
      ...this.warnings.map(w => `- ${w}`)
    ];

    if (!DRY_RUN) {
      fs.writeFileSync(reportPath, report.join('\\n'));
    }
    
    console.log(report.join('\\n'));
  }

  async migrate() {
    try {
      await this.validateEnvironment();
      
      const projects = await this.discoverExistingProjects();
      
      this.log(`Starting migration of ${projects.size} projects...`);
      
      for (const project of projects.values()) {
        try {
          await this.createProjectStructure(project);
          await this.migrateProjectContent(project);
          this.migrations.push(project);
        } catch (error) {
          this.log(`Failed to migrate project ${project.id}: ${error.message}`, 'error');
        }
      }
      
      await this.generateMigrationReport();
      
      this.log('Migration completed');
      
      if (this.errors.length > 0) {
        process.exit(1);
      }
      
    } catch (error) {
      this.log(`Migration failed: ${error.message}`, 'error');
      process.exit(1);
    }
  }
}

// Main execution
if (require.main === module) {
  const migrator = new ProjectMigrator();
  migrator.migrate();
}

module.exports = ProjectMigrator;