# Changelog

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-21

### Added
- Initial project skeleton with FastAPI backend and React + TypeScript + Vite frontend
- Docker Compose configuration with backend, frontend, Keycloak, and PostgreSQL
- CI workflow for backend tests, frontend build/test, and Docker builds
- Portfolio configuration and project metadata
- Project structure per owned-app contract
- **Backend (16 modules)**: FastAPI app, config, database, security, API routes (health, plugins, audit, context, GTM), SQLAlchemy models (Plugin, AuditRun, AuditFinding, ContextPack, ContextSection, GTMOfferStack, GTMOfferLine, GTMProofAsset, GTMProofClaim), services (audit, context, GTM scorers)
- **Frontend (6 modules)**: React app with typed API client, Layout, PluginCard, Dashboard, Vite config
- Plugin marketplace API with pagination, filtering, search
- Skill audit engine with static analysis of SKILL.md frontmatter/body
- Company context pack generator with interview questions
- GTM scorers for offer stack (pain-point validation) and proof assets (source/permission validation)
- MCP tool picker stub for GTM Directory integration
- Role-based access control (viewer/operator/admin)
- Demo mode with explicit opt-in

### Security
- OIDC PKCE authentication flow designed with Keycloak realm export
- SQLite persistent storage with parameterized queries
- Non-root Docker users configured
- CORS restricted to configured frontend URL
- No hardcoded secrets; all via environment variables

## [Unreleased]

### Planned
- OIDC authentication with Keycloak (SPA PKCE flow)
- Plugin marketplace CRUD and search (UI integration)
- Skill audit engine for static analysis (UI integration)
- Company context pack generator (UI integration)
- GTM scorers (offer stack, proof assets) (UI integration)
- Pick GTM tools with MCP integration (UI integration)