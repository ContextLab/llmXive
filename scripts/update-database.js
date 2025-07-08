#!/usr/bin/env node

/**
 * Database Update Script
 * Updates web database files to match new project structure
 */

const fs = require('fs');
const path = require('path');

const REPO_ROOT = path.join(__dirname, '..');
const WEB_DB_PATH = path.join(REPO_ROOT, 'web', 'database');
const PROJECTS_DIR = path.join(REPO_ROOT, 'projects');

class DatabaseUpdater {
  constructor() {
    this.projects = new Map();
    this.contributors = new Map();
    this.updatedProjects = [];
  }

  log(message, level = 'info') {
    const timestamp = new Date().toISOString();
    const prefix = `[${timestamp}] [${level.toUpperCase()}]`;
    console.log(`${prefix} ${message}`);
  }

  async loadExistingProjects() {
    this.log('Loading existing projects from filesystem...');
    
    if (!fs.existsSync(PROJECTS_DIR)) {
      throw new Error('Projects directory not found');
    }

    const projectDirs = fs.readdirSync(PROJECTS_DIR).filter(item => {
      const itemPath = path.join(PROJECTS_DIR, item);
      return fs.statSync(itemPath).isDirectory();
    });

    for (const projectDir of projectDirs) {
      const projectPath = path.join(PROJECTS_DIR, projectDir);
      const configPath = path.join(projectPath, '.llmxive', 'config.json');
      
      if (fs.existsSync(configPath)) {
        try {
          const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
          this.projects.set(projectDir, config);
          this.log(`Loaded project: ${projectDir}`);
        } catch (error) {
          this.log(`Failed to load project config: ${projectDir}`, 'warn');
        }
      }
    }

    this.log(`Loaded ${this.projects.size} projects`);
  }

  mapOldIdToNewId(oldId) {
    // Map old project IDs to new project IDs
    const mapping = {
      'llmxive-auto-001': 'PROJ-001-llmxive-automation',
      'llmxive-automation-testing': 'PROJ-001-llmxive-automation-testing',
      'llmxive-v2-final': 'PROJ-001-automated-pipeline-scheduler',
      'biology-20250704-001': 'PROJ-20250704-biology-20250704-001',
      'chemistry-20250704-001': 'PROJ-20250704-chemistry-20250704-001',
      'materials-science-20250705-001': 'PROJ-20250705-materials-science-20250705-001',
      'energy-20250704-001': 'PROJ-20250704-energy-20250704-001',
      'computer-science-20250705-001': 'PROJ-20250705-computer-science-20250705-001',
      'robotics-20250705-001': 'PROJ-20250705-robotics-20250705-001',
      'agriculture-20250704-001': 'PROJ-20250704-agriculture-20250704-001',
      'environmental-science-20250704-001': 'PROJ-20250704-environmental-science-20250704-001',
      'psychology-20250704-001': 'PROJ-20250704-psychology-20250704-001'
    };
    return mapping[oldId] || oldId;
  }

  async updateProjectsDatabase() {
    this.log('Updating projects database...');
    
    const oldDbPath = path.join(WEB_DB_PATH, 'projects.json');
    let oldDb = { projects: {} };
    
    if (fs.existsSync(oldDbPath)) {
      oldDb = JSON.parse(fs.readFileSync(oldDbPath, 'utf8'));
    }

    const newProjects = [];
    let validProjects = 0;
    let removedProjects = 0;

    // Process existing projects
    for (const [oldId, oldProject] of Object.entries(oldDb.projects || {})) {
      const newId = this.mapOldIdToNewId(oldId);
      
      if (this.projects.has(newId)) {
        const config = this.projects.get(newId);
        
        // Check if project is well-formed
        if (this.isProjectWellFormed(newId, config)) {
          const updatedProject = {
            id: newId,
            title: config.title || oldProject.title,
            description: config.description || oldProject.description,
            field: config.field || oldProject.field,
            status: config.status || oldProject.status,
            phase: this.inferPhase(config),
            githubIssue: oldProject.githubIssue,
            dateCreated: config.created_date || oldProject.dateCreated,
            dateModified: config.updated_date || oldProject.dateModified,
            contributors: config.contributors || oldProject.contributors,
            completeness: this.calculateCompleteness(newId),
            keywords: oldProject.keywords || [],
            dependencies: oldProject.dependencies || [],
            location: `projects/${newId}/`,
            estimatedTimeline: oldProject.estimatedTimeline,
            reviews: this.gatherReviews(newId) || oldProject.reviews || []
          };
          
          newProjects.push(updatedProject);
          validProjects++;
          this.log(`Updated project: ${oldId} -> ${newId}`);
        } else {
          this.log(`Removed poorly formed project: ${oldId}`, 'warn');
          removedProjects++;
        }
      } else {
        this.log(`Project not found in filesystem: ${oldId}`, 'warn');
        removedProjects++;
      }
    }

    // Add any new projects not in old database
    for (const [projectId, config] of this.projects.entries()) {
      if (!newProjects.find(p => p.id === projectId)) {
        if (this.isProjectWellFormed(projectId, config)) {
          const newProject = {
            id: projectId,
            title: config.title,
            description: config.description || 'Migrated project',
            field: config.field,
            status: config.status,
            phase: this.inferPhase(config),
            githubIssue: null,
            dateCreated: config.created_date,
            dateModified: config.updated_date,
            contributors: config.contributors || [],
            completeness: this.calculateCompleteness(projectId),
            keywords: this.extractKeywords(config),
            dependencies: [],
            location: `projects/${projectId}/`,
            estimatedTimeline: null,
            reviews: this.gatherReviews(projectId) || []
          };
          
          newProjects.push(newProject);
          validProjects++;
          this.log(`Added new project: ${projectId}`);
        } else {
          this.log(`Skipped poorly formed project: ${projectId}`, 'warn');
          removedProjects++;
        }
      }
    }

    const newDb = {
      metadata: {
        version: "2.0.0",
        created: new Date().toISOString().split('T')[0],
        description: "llmXive Projects Database - Updated for v2.0 structure",
        totalProjects: validProjects,
        dateRange: this.getDateRange(newProjects),
        lastUpdated: new Date().toISOString()
      },
      projects: newProjects
    };

    // Write updated database
    fs.writeFileSync(oldDbPath, JSON.stringify(newDb, null, 2));
    this.log(`Database updated: ${validProjects} projects, ${removedProjects} removed`);
    
    return { validProjects, removedProjects };
  }

  isProjectWellFormed(projectId, config) {
    const projectPath = path.join(PROJECTS_DIR, projectId);
    
    // Check required fields
    if (!config.title || !config.field || !config.status) {
      return false;
    }
    
    // Check required directories exist
    const requiredDirs = [
      '.llmxive',
      'technical-design',
      'reviews'
    ];
    
    for (const dir of requiredDirs) {
      const dirPath = path.join(projectPath, dir);
      if (!fs.existsSync(dirPath)) {
        return false;
      }
    }
    
    // Check if project has any content
    const techDesignPath = path.join(projectPath, 'technical-design');
    const hasContent = fs.existsSync(techDesignPath) && 
                      fs.readdirSync(techDesignPath).length > 0;
    
    return hasContent;
  }

  inferPhase(config) {
    if (config.phases) {
      if (config.phases.paper && config.phases.paper.completed) return 'paper';
      if (config.phases.code && config.phases.code.completed) return 'code';
      if (config.phases.implementation_plan && config.phases.implementation_plan.completed) return 'implementation_plan';
      if (config.phases.technical_design && config.phases.technical_design.completed) return 'technical_design';
      if (config.phases.idea && config.phases.idea.completed) return 'idea';
    }
    return 'design';
  }

  calculateCompleteness(projectId) {
    const projectPath = path.join(PROJECTS_DIR, projectId);
    let completeness = 0;
    
    // Check each phase directory for content
    const phases = ['idea', 'technical-design', 'implementation-plan', 'code', 'data', 'paper'];
    
    for (const phase of phases) {
      const phasePath = path.join(projectPath, phase);
      if (fs.existsSync(phasePath)) {
        const files = fs.readdirSync(phasePath).filter(f => !f.startsWith('.'));
        if (files.length > 0) {
          completeness += Math.floor(100 / phases.length);
        }
      }
    }
    
    return Math.min(completeness, 100);
  }

  extractKeywords(config) {
    const keywords = [];
    if (config.title) {
      keywords.push(...config.title.toLowerCase().split(/\s+/).filter(w => w.length > 3));
    }
    if (config.field) {
      keywords.push(config.field.toLowerCase().replace(/\s+/g, '-'));
    }
    return [...new Set(keywords)];
  }

  gatherReviews(projectId) {
    const reviewsPath = path.join(PROJECTS_DIR, projectId, 'reviews');
    const reviews = [];
    
    if (!fs.existsSync(reviewsPath)) return reviews;
    
    const reviewTypes = ['design', 'implementation', 'paper', 'code'];
    
    for (const reviewType of reviewTypes) {
      const reviewTypePath = path.join(reviewsPath, reviewType);
      if (!fs.existsSync(reviewTypePath)) continue;
      
      const reviewFiles = fs.readdirSync(reviewTypePath).filter(f => f.endsWith('.md'));
      
      for (const reviewFile of reviewFiles) {
        const match = reviewFile.match(/^(.+)__(\d{2}-\d{2}-\d{4})__([AM])\.md$/);
        if (match) {
          const [, reviewer, date, type] = match;
          reviews.push({
            date: date,
            type: reviewType,
            reviewer: reviewer,
            reviewType: type === 'A' ? 'automated' : 'manual',
            location: `projects/${projectId}/reviews/${reviewType}/${reviewFile}`
          });
        }
      }
    }
    
    return reviews;
  }

  getDateRange(projects) {
    const dates = projects.map(p => new Date(p.dateCreated)).filter(d => !isNaN(d));
    if (dates.length === 0) return 'Unknown';
    
    const earliest = new Date(Math.min(...dates)).toISOString().split('T')[0];
    const latest = new Date(Math.max(...dates)).toISOString().split('T')[0];
    
    return `${earliest} to ${latest}`;
  }

  async updateContributorsDatabase() {
    this.log('Updating contributors database...');
    
    const contributorsPath = path.join(WEB_DB_PATH, 'contributors.json');
    const contributors = new Map();
    
    // Gather contributors from all projects
    for (const [projectId, config] of this.projects.entries()) {
      if (config.contributors) {
        for (const contributor of config.contributors) {
          if (!contributors.has(contributor.username)) {
            contributors.set(contributor.username, {
              username: contributor.username,
              name: contributor.username,
              type: contributor.type,
              model: contributor.model,
              projects: [],
              totalContributions: 0,
              firstContribution: contributor.dateContributed || config.created_date,
              lastContribution: contributor.dateContributed || config.updated_date
            });
          }
          
          const contrib = contributors.get(contributor.username);
          contrib.projects.push(projectId);
          contrib.totalContributions++;
        }
      }
    }
    
    const contributorsDb = {
      metadata: {
        version: "2.0.0",
        created: new Date().toISOString().split('T')[0],
        totalContributors: contributors.size,
        lastUpdated: new Date().toISOString()
      },
      contributors: Array.from(contributors.values())
    };
    
    fs.writeFileSync(contributorsPath, JSON.stringify(contributorsDb, null, 2));
    this.log(`Contributors database updated: ${contributors.size} contributors`);
  }

  async updateAnalyticsDatabase() {
    this.log('Updating analytics database...');
    
    const analyticsPath = path.join(WEB_DB_PATH, 'analytics.json');
    const projects = Array.from(this.projects.values());
    
    const analytics = {
      metadata: {
        version: "2.0.0",
        generated: new Date().toISOString(),
        totalProjects: projects.length
      },
      stats: {
        by_field: this.getFieldStats(projects),
        by_status: this.getStatusStats(projects),
        by_phase: this.getPhaseStats(projects),
        completeness: this.getCompletenessStats(projects),
        timeline: this.getTimelineStats(projects)
      }
    };
    
    fs.writeFileSync(analyticsPath, JSON.stringify(analytics, null, 2));
    this.log('Analytics database updated');
  }

  getFieldStats(projects) {
    const stats = {};
    for (const project of projects) {
      stats[project.field] = (stats[project.field] || 0) + 1;
    }
    return stats;
  }

  getStatusStats(projects) {
    const stats = {};
    for (const project of projects) {
      stats[project.status] = (stats[project.status] || 0) + 1;
    }
    return stats;
  }

  getPhaseStats(projects) {
    const stats = {};
    for (const project of projects) {
      const phase = this.inferPhase(project);
      stats[phase] = (stats[phase] || 0) + 1;
    }
    return stats;
  }

  getCompletenessStats(projects) {
    const completeness = projects.map(p => this.calculateCompleteness(p.id));
    return {
      average: completeness.reduce((a, b) => a + b, 0) / completeness.length,
      median: completeness.sort()[Math.floor(completeness.length / 2)],
      distribution: {
        '0-25%': completeness.filter(c => c < 25).length,
        '25-50%': completeness.filter(c => c >= 25 && c < 50).length,
        '50-75%': completeness.filter(c => c >= 50 && c < 75).length,
        '75-100%': completeness.filter(c => c >= 75).length
      }
    };
  }

  getTimelineStats(projects) {
    const now = new Date();
    const monthsAgo = new Date(now.getFullYear(), now.getMonth() - 6, 1);
    
    return {
      recent_projects: projects.filter(p => 
        new Date(p.created_date) >= monthsAgo
      ).length,
      active_projects: projects.filter(p => 
        ['in-progress', 'ready'].includes(p.status)
      ).length,
      completed_projects: projects.filter(p => 
        p.status === 'done'
      ).length
    };
  }

  async update() {
    try {
      await this.loadExistingProjects();
      
      const results = await this.updateProjectsDatabase();
      await this.updateContributorsDatabase();
      await this.updateAnalyticsDatabase();
      
      this.log(`Database update completed: ${results.validProjects} projects, ${results.removedProjects} removed`);
      
      return results;
    } catch (error) {
      this.log(`Database update failed: ${error.message}`, 'error');
      process.exit(1);
    }
  }
}

// Main execution
if (require.main === module) {
  const updater = new DatabaseUpdater();
  updater.update();
}

module.exports = DatabaseUpdater;