#!/usr/bin/env node

/**
 * llmXive Structure Validation Script
 * Validates repository structure against schemas and requirements
 */

const fs = require('fs');
const path = require('path');
const Ajv = require('ajv');
const addFormats = require('ajv-formats');

const REPO_ROOT = path.join(__dirname, '..');
const SYSTEM_DIR = path.join(REPO_ROOT, '.llmxive-system');
const PROJECTS_DIR = path.join(REPO_ROOT, 'projects');
const SCHEMAS_DIR = path.join(SYSTEM_DIR, 'schemas');

class StructureValidator {
  constructor() {
    this.ajv = new Ajv({ allErrors: true });
    addFormats(this.ajv);
    this.schemas = {};
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
    } else {
      console.log(`${prefix} ${message}`);
    }
  }

  async loadSchemas() {
    this.log('Loading validation schemas...');
    
    if (!fs.existsSync(SCHEMAS_DIR)) {
      throw new Error('Schemas directory not found');
    }

    const schemaFiles = fs.readdirSync(SCHEMAS_DIR).filter(f => f.endsWith('.json'));
    
    for (const schemaFile of schemaFiles) {
      const schemaPath = path.join(SCHEMAS_DIR, schemaFile);
      const schemaContent = JSON.parse(fs.readFileSync(schemaPath, 'utf8'));
      const schemaName = path.basename(schemaFile, '.json');
      
      this.schemas[schemaName] = this.ajv.compile(schemaContent);
      this.log(`Loaded schema: ${schemaName}`);
    }
  }

  async validateSystemStructure() {
    this.log('Validating system structure...');
    
    const requiredDirectories = [
      '.llmxive-system',
      '.llmxive-system/registry',
      '.llmxive-system/config',
      '.llmxive-system/schemas',
      '.llmxive-system/templates',
      '.llmxive-system/logs',
      'projects',
      'web',
      'src',
      'scripts'
    ];

    for (const dir of requiredDirectories) {
      const dirPath = path.join(REPO_ROOT, dir);
      if (!fs.existsSync(dirPath)) {
        this.log(`Missing required directory: ${dir}`, 'error');
      }
    }

    const requiredFiles = [
      '.llmxive-system/config/system.json',
      '.llmxive-system/config/models.json',
      '.llmxive-system/schemas/project-config.schema.json',
      '.llmxive-system/schemas/review.schema.json'
    ];

    for (const file of requiredFiles) {
      const filePath = path.join(REPO_ROOT, file);
      if (!fs.existsSync(filePath)) {
        this.log(`Missing required file: ${file}`, 'error');
      }
    }
  }

  async validateProject(projectId) {
    const projectPath = path.join(PROJECTS_DIR, projectId);
    
    if (!fs.existsSync(projectPath)) {
      this.log(`Project directory not found: ${projectId}`, 'error');
      return;
    }

    // Check required directory structure
    const requiredDirs = [
      '.llmxive',
      'idea',
      'technical-design',
      'implementation-plan',
      'code',
      'data',
      'paper',
      'reviews',
      'reviews/design',
      'reviews/implementation',
      'reviews/paper',
      'reviews/code'
    ];

    for (const dir of requiredDirs) {
      const dirPath = path.join(projectPath, dir);
      if (!fs.existsSync(dirPath)) {
        this.log(`Project ${projectId} missing directory: ${dir}`, 'error');
      }
    }

    // Validate project configuration
    const configPath = path.join(projectPath, '.llmxive', 'config.json');
    if (fs.existsSync(configPath)) {
      try {
        const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
        
        if (this.schemas['project-config']) {
          const valid = this.schemas['project-config'](config);
          if (!valid) {
            this.log(`Project ${projectId} config validation failed:`, 'error');
            for (const error of this.schemas['project-config'].errors) {
              this.log(`  ${error.instancePath}: ${error.message}`, 'error');
            }
          } else {
            this.log(`Project ${projectId} config is valid`);
          }
        }
      } catch (error) {
        this.log(`Project ${projectId} config is invalid JSON: ${error.message}`, 'error');
      }
    } else {
      this.log(`Project ${projectId} missing config file`, 'error');
    }

    // Validate review files
    const reviewsPath = path.join(projectPath, 'reviews');
    if (fs.existsSync(reviewsPath)) {
      this.validateReviewFiles(projectId, reviewsPath);
    }
  }

  validateReviewFiles(projectId, reviewsPath) {
    const reviewTypes = ['design', 'implementation', 'paper', 'code'];
    
    for (const reviewType of reviewTypes) {
      const reviewTypePath = path.join(reviewsPath, reviewType);
      if (!fs.existsSync(reviewTypePath)) continue;

      const reviewFiles = fs.readdirSync(reviewTypePath).filter(f => f.endsWith('.md'));
      
      for (const reviewFile of reviewFiles) {
        const reviewPath = path.join(reviewTypePath, reviewFile);
        
        // Check filename format: author__MM-DD-YYYY__type.md
        const filenamePattern = /^(.+)__(\d{2}-\d{2}-\d{4})__([AM])\.md$/;
        if (!filenamePattern.test(reviewFile)) {
          this.log(`Project ${projectId} review file has invalid name format: ${reviewFile}`, 'warn');
        }

        // Check if review has proper frontmatter or metadata
        const content = fs.readFileSync(reviewPath, 'utf8');
        if (!content.includes('# Review') && !content.includes('## Review')) {
          this.log(`Project ${projectId} review file may be missing proper structure: ${reviewFile}`, 'warn');
        }
      }
    }
  }

  async validateAllProjects() {
    this.log('Validating all projects...');
    
    if (!fs.existsSync(PROJECTS_DIR)) {
      this.log('Projects directory not found', 'error');
      return;
    }

    const projects = fs.readdirSync(PROJECTS_DIR).filter(item => {
      const itemPath = path.join(PROJECTS_DIR, item);
      return fs.statSync(itemPath).isDirectory();
    });

    this.log(`Found ${projects.length} projects to validate`);

    for (const project of projects) {
      await this.validateProject(project);
    }
  }

  async validateDatabaseConsistency() {
    this.log('Validating database consistency...');
    
    const webDbPath = path.join(REPO_ROOT, 'web', 'database');
    if (!fs.existsSync(webDbPath)) {
      this.log('Web database directory not found', 'error');
      return;
    }

    // Check projects.json
    const projectsDbPath = path.join(webDbPath, 'projects.json');
    if (fs.existsSync(projectsDbPath)) {
      try {
        const projectsDb = JSON.parse(fs.readFileSync(projectsDbPath, 'utf8'));
        
        for (const project of projectsDb) {
          if (project.id) {
            const projectPath = path.join(PROJECTS_DIR, project.id);
            if (!fs.existsSync(projectPath)) {
              this.log(`Database references non-existent project: ${project.id}`, 'error');
            }
          }
        }
      } catch (error) {
        this.log(`Invalid projects database: ${error.message}`, 'error');
      }
    }
  }

  async validatePathConsistency() {
    this.log('Validating path consistency...');
    
    const filesToCheck = [
      'web/js/app.js',
      'web/src/data/ProjectDataManager.js',
      'scripts/llmxive-cli.py'
    ];

    for (const file of filesToCheck) {
      const filePath = path.join(REPO_ROOT, file);
      if (!fs.existsSync(filePath)) continue;

      const content = fs.readFileSync(filePath, 'utf8');
      
      // Check for old path references
      const oldPaths = [
        'technical_design_documents/',
        'implementation_plans/',
        'papers/',
        'reviews/',
        'web/src/core/',
        'web/src/managers/'
      ];

      for (const oldPath of oldPaths) {
        if (content.includes(oldPath)) {
          this.log(`File ${file} contains old path reference: ${oldPath}`, 'warn');
        }
      }
    }
  }

  async generateReport() {
    const reportPath = path.join(REPO_ROOT, 'validation-report.md');
    const report = [
      '# Structure Validation Report',
      '',
      `**Date**: ${new Date().toISOString()}`,
      '',
      `## Summary`,
      `- Errors: ${this.errors.length}`,
      `- Warnings: ${this.warnings.length}`,
      '',
      '## Errors',
      ...this.errors.map(e => `- ${e}`),
      '',
      '## Warnings',
      ...this.warnings.map(w => `- ${w}`),
      '',
      '## Validation Status',
      this.errors.length === 0 ? '✅ Repository structure is valid' : '❌ Repository structure has errors'
    ];

    fs.writeFileSync(reportPath, report.join('\\n'));
    console.log(report.join('\\n'));
  }

  async validate() {
    try {
      await this.loadSchemas();
      await this.validateSystemStructure();
      await this.validateAllProjects();
      await this.validateDatabaseConsistency();
      await this.validatePathConsistency();
      await this.generateReport();
      
      if (this.errors.length > 0) {
        process.exit(1);
      }
      
    } catch (error) {
      this.log(`Validation failed: ${error.message}`, 'error');
      process.exit(1);
    }
  }
}

// Main execution
if (require.main === module) {
  const validator = new StructureValidator();
  validator.validate();
}

module.exports = StructureValidator;