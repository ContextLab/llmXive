#!/usr/bin/env node

/**
 * Project Population Script for llmXive
 * 
 * Populates the local llmXive system with all projects from the repository
 * with correct author attributions
 */

// Project data with corrected attributions
const PROJECTS_DATA = {
    // Meta-system projects
    "llmxive-auto-001": {
        id: "llmxive-auto-001",
        title: "llmXive Automation System",
        description: "Fully automated research pipeline using GitHub Actions and HuggingFace models",
        field: "Infrastructure/Meta-project",
        status: "backlog",
        phase: "design",
        githubIssue: 21,
        dateCreated: "2025-07-04",
        contributors: [
            {
                type: "AI",
                name: "Claude",
                model: "Claude 4 Sonnet",
                role: "primary_author"
            }
        ],
        completeness: 85,
        keywords: ["automation", "github-actions", "huggingface", "pipeline"],
        dependencies: ["GitHub Actions", "HuggingFace API", "Docker"],
        location: "technical_design_documents/llmXive_automation/design.md"
    },

    "llmxive-automation-testing": {
        id: "llmxive-automation-testing",
        title: "Full Pipeline Testing System",
        description: "Comprehensive testing framework for the automation pipeline",
        field: "Testing Infrastructure",
        status: "planning",
        phase: "implementation_plan",
        githubIssue: 31,
        dateCreated: "2025-07-04",
        contributors: [
            {
                type: "AI",
                name: "Claude Code",
                model: "Claude 4 Sonnet (Anthropic)",
                role: "primary_author"
            }
        ],
        completeness: 75,
        keywords: ["testing", "automation", "pipeline", "validation"],
        dependencies: ["Docker", "PyTest", "GitHub API"],
        location: "implementation_plans/llmxive-automation-testing/plan.md"
    },

    "llmxive-v2-final": {
        id: "llmxive-v2-final",
        title: "llmXive v2.0 System Architecture",
        description: "Next-generation llmXive system with LaTeX template integration",
        field: "Architecture/Meta-project",
        status: "design",
        phase: "design",
        githubIssue: null,
        dateCreated: "2025-07-04",
        contributors: [
            {
                type: "AI",
                name: "Claude",
                model: "Claude 4 Sonnet",
                role: "primary_author"
            },
            {
                type: "human",
                name: "Jeremy Manning",
                role: "contributor"
            },
            {
                type: "AI",
                name: "Gemini",
                model: "Google Gemini",
                role: "contributor"
            }
        ],
        completeness: 95,
        keywords: ["architecture", "latex", "github-native", "v2.0"],
        dependencies: ["GitHub Pages", "Docker", "LaTeX"],
        location: "technical_design_documents/llmXive_v2_final_consolidated.md"
    },

    // Research domain projects
    "biology-20250704-001": {
        id: "biology-20250704-001",
        title: "Exploring the Mechanisms of Gene Regulation in Different Cell Types",
        description: "Multi-scale approach to understanding gene regulation mechanisms across different cell types",
        field: "Biology",
        status: "backlog",
        phase: "design",
        githubIssue: 30,
        dateCreated: "2025-07-04",
        contributors: [
            {
                type: "AI",
                name: "TinyLlama",
                model: "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
                role: "primary_author"
            },
            {
                type: "AI",
                name: "Google Gemini",
                model: "Google Gemini",
                role: "methodology_enhancement"
            }
        ],
        completeness: 90,
        keywords: ["gene-regulation", "cell-types", "genomics", "bioinformatics", "single-cell", "multi-omics"],
        dependencies: ["Bioinformatics tools", "Laboratory equipment", "Single-cell platforms", "CRISPR systems"],
        location: "technical_design_documents/biology-20250704-001/design-completed.md",
        issues: []
    },

    "chemistry-20250704-001": {
        id: "chemistry-20250704-001",
        title: "Renewable Energy in Mining Operations: A Comprehensive Review",
        description: "Comprehensive technical design document reviewing renewable energy integration in mining operations worldwide",
        field: "Chemistry/Energy",
        status: "backlog",
        phase: "design",
        githubIssue: 33,
        dateCreated: "2025-07-04",
        contributors: [
            {
                type: "AI",
                name: "TinyLlama",
                model: "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
                role: "primary_author"
            },
            {
                type: "AI",
                name: "Google Gemini",
                model: "Google Gemini",
                role: "content_repair_enhancement"
            }
        ],
        completeness: 95,
        keywords: ["renewable-energy", "mining", "solar", "wind", "geothermal", "sustainability", "meta-analysis"],
        dependencies: ["Mining industry data", "Renewable energy systems", "Literature databases"],
        location: "technical_design_documents/chemistry-20250704-001/design-completed.md",
        issues: [],
        reviews: [
            {
                date: "2025-07-05",
                type: "automated",
                score: 1.0,
                reviewer: "LLM",
                location: "reviews/chemistry-20250704-001/Design/llm__07-05-2025__A.md"
            }
        ]
    },

    "materials-science-20250705-001": {
        id: "materials-science-20250705-001",
        title: "Development of a Multi-Purpose Fuel Cell Energy Storage Device",
        description: "Comprehensive technical design for hybrid fuel cell-battery energy storage system with advanced materials",
        field: "Materials Science/Energy Storage",
        status: "backlog",
        phase: "design",
        githubIssue: 37,
        dateCreated: "2025-07-05",
        contributors: [
            {
                type: "AI",
                name: "TinyLlama",
                model: "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
                role: "primary_author"
            },
            {
                type: "AI",
                name: "Google Gemini",
                model: "Google Gemini",
                role: "content_development"
            }
        ],
        completeness: 95,
        keywords: ["fuel-cell", "energy-storage", "materials-science", "hybrid-systems", "graphene", "PEM"],
        dependencies: ["Energy storage technology", "Materials science expertise", "Electrochemical testing", "Thermal management"],
        location: "technical_design_documents/materials-science-20250705-001/design-completed.md",
        issues: [],
        reviews: [
            {
                date: "2025-07-05",
                type: "automated",
                score: 0.15,
                result: "rejected",
                reviewer: "LLM",
                location: "reviews/materials-science-20250705-001/Design/llm__07-05-2025__A.md"
            }
        ]
    },

    "energy-20250704-001": {
        id: "energy-20250704-001",
        title: "Addressing Energy Inequity in Low-Income Communities",
        description: "Solutions for energy inequity using renewable energy systems and education programs",
        field: "Energy/Social Policy",
        status: "backlog",
        phase: "design",
        githubIssue: 29,
        dateCreated: "2025-07-04",
        contributors: [
            {
                type: "AI",
                name: "TinyLlama",
                model: "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
                role: "primary_author"
            }
        ],
        completeness: 60,
        keywords: ["energy-equity", "renewable-energy", "social-policy", "community"],
        dependencies: ["Community partnerships", "Renewable energy infrastructure"],
        location: "technical_design_documents/energy-20250704-001/design.md",
        issues: ["Missing detailed budget analysis", "Needs specific community partnerships"]
    },

    "computer-science-20250705-001": {
        id: "computer-science-20250705-001",
        title: "Improving Accessibility and Usability of Complex Computer Systems",
        description: "Machine learning approaches to accessibility feedback and adaptive input/output systems",
        field: "Computer Science/Accessibility",
        status: "backlog",
        phase: "design",
        githubIssue: 35,
        dateCreated: "2025-07-05",
        contributors: [
            {
                type: "AI",
                name: "TinyLlama",
                model: "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
                role: "primary_author"
            }
        ],
        completeness: 55,
        keywords: ["accessibility", "machine-learning", "usability", "WCAG"],
        dependencies: ["Machine learning frameworks", "Accessibility testing tools"],
        location: "technical_design_documents/computer-science-20250705-001/design.md",
        issues: ["Missing detailed implementation specifications", "Needs user testing protocols"]
    },

    "robotics-20250705-001": {
        id: "robotics-20250705-001",
        title: "Robotic Artificial Intelligence for Autonomous Vehicles",
        description: "Open-loop control systems with sensor fusion and reinforcement learning for autonomous vehicles",
        field: "Robotics/AI",
        status: "backlog",
        phase: "design",
        githubIssue: 36,
        dateCreated: "2025-07-05",
        contributors: [
            {
                type: "AI",
                name: "TinyLlama",
                model: "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
                role: "primary_author"
            }
        ],
        completeness: 70,
        keywords: ["robotics", "autonomous-vehicles", "SLAM", "reinforcement-learning"],
        dependencies: ["Robotics hardware", "ROS framework", "Machine learning libraries"],
        location: "technical_design_documents/robotics-20250705-001/design.md",
        issues: ["Timeline dates from 2021-2022", "Missing current cost analysis"]
    },

    "agriculture-20250704-001": {
        id: "agriculture-20250704-001",
        title: "Agricultural Research Project",
        description: "Agriculture-focused research project (content not yet analyzed)",
        field: "Agriculture",
        status: "backlog",
        phase: "design",
        githubIssue: 27,
        dateCreated: "2025-07-04",
        contributors: [
            {
                type: "AI",
                name: "TinyLlama",
                model: "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
                role: "primary_author"
            }
        ],
        completeness: null, // Not yet analyzed
        keywords: ["agriculture"],
        dependencies: [],
        location: "technical_design_documents/agriculture-20250704-001/design.md",
        issues: ["Content not yet analyzed"]
    },

    "environmental-science-20250704-001": {
        id: "environmental-science-20250704-001",
        title: "Environmental Science Research Project",
        description: "Environmental science research project (content not yet analyzed)",
        field: "Environmental Science",
        status: "backlog",
        phase: "design",
        githubIssue: 28,
        dateCreated: "2025-07-04",
        contributors: [
            {
                type: "AI",
                name: "TinyLlama",
                model: "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
                role: "primary_author"
            }
        ],
        completeness: null, // Not yet analyzed
        keywords: ["environmental-science"],
        dependencies: [],
        location: "technical_design_documents/environmental-science-20250704-001/design.md",
        issues: ["Content not yet analyzed"]
    },

    "psychology-20250704-001": {
        id: "psychology-20250704-001",
        title: "Psychology Research Project",
        description: "Psychology research project (content not yet analyzed)",
        field: "Psychology",
        status: "backlog",
        phase: "design",
        githubIssue: 26,
        dateCreated: "2025-07-04",
        contributors: [
            {
                type: "AI",
                name: "TinyLlama",
                model: "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
                role: "primary_author"
            }
        ],
        completeness: null, // Not yet analyzed
        keywords: ["psychology"],
        dependencies: [],
        location: "technical_design_documents/psychology-20250704-001/design.md",
        issues: ["Content not yet analyzed"]
    }
};

// Repository state information
const REPOSITORY_STATE = {
    totalProjects: Object.keys(PROJECTS_DATA).length,
    completedPapers: 0,
    activeReviews: 2,
    automationStatus: "In development",
    webInterfaceStatus: "Functional with recent fixes",
    lastUpdated: "2025-07-07"
};

// Export project data
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        PROJECTS_DATA,
        REPOSITORY_STATE
    };
}

// Function to populate projects into llmXive system
async function populateProjects() {
    console.log('🚀 Starting llmXive Project Population');
    console.log('=====================================');
    console.log(`📊 Total Projects: ${REPOSITORY_STATE.totalProjects}`);
    console.log('');

    for (const [projectId, project] of Object.entries(PROJECTS_DATA)) {
        console.log(`📋 Processing: ${project.title}`);
        console.log(`   ID: ${projectId}`);
        console.log(`   Field: ${project.field}`);
        console.log(`   Status: ${project.status}`);
        console.log(`   Contributors: ${project.contributors.map(c => `${c.name} (${c.model || c.role})`).join(', ')}`);
        console.log(`   Completeness: ${project.completeness || 'Not analyzed'}%`);
        
        if (project.issues && project.issues.length > 0) {
            console.log(`   ⚠️  Issues: ${project.issues.join(', ')}`);
        }
        
        if (project.reviews && project.reviews.length > 0) {
            console.log(`   📝 Reviews: ${project.reviews.length}`);
        }
        
        console.log('');
    }

    console.log('✅ Project catalog complete!');
    console.log('');
    console.log('📋 Summary:');
    console.log(`   • Meta-system projects: 3`);
    console.log(`   • Research projects: ${REPOSITORY_STATE.totalProjects - 3}`);
    console.log(`   • Projects by TinyLlama: ${Object.values(PROJECTS_DATA).filter(p => 
        p.contributors.some(c => c.model === 'TinyLlama/TinyLlama-1.1B-Chat-v1.0')).length}`);
    console.log(`   • Projects by Claude: ${Object.values(PROJECTS_DATA).filter(p => 
        p.contributors.some(c => c.model && c.model.includes('Claude'))).length}`);
    console.log(`   • Projects needing completion: ${Object.values(PROJECTS_DATA).filter(p => 
        p.completeness && p.completeness < 80).length}`);
    console.log('');
    console.log('🔧 Next steps:');
    console.log('   1. Complete partial/missing content with Gemini');
    console.log('   2. Add Gemini to contributor lists for completed sections');
    console.log('   3. Populate llmXive database with corrected data');
    console.log('   4. Verify local version displays all content correctly');
}

// Run if called directly
if (typeof require !== 'undefined' && require.main === module) {
    populateProjects().catch(console.error);
}

console.log('📚 Project data loaded successfully');
console.log('💾 Available:', Object.keys(PROJECTS_DATA).length, 'projects');