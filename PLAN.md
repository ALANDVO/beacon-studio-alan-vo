# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

auth-oidc

## Roadmap

### project-skeleton — Project Skeleton with FastAPI + React + Vite

Status: done

Acceptance:
- Backend FastAPI app runs and serves health endpoint
- Frontend React + TypeScript + Vite builds successfully
- Docker Compose brings up backend, frontend, Keycloak, PostgreSQL
- CI workflow runs backend tests and frontend build/test

Implementation: `backend/app/main.py`, `backend/requirements.txt`, `backend/Dockerfile`, `frontend/package.json`, `frontend/Dockerfile`, `compose.yaml`, `.github/workflows/ci.yml`, `.gitignore`, `.env.example`, `portfolio.json`, `pyproject.toml`, `README.md`, `LICENSE`, `CHANGELOG.md`

Tests: `backend/tests/test_health.py`, `frontend/src/__tests__/App.test.tsx`

### auth-oidc — OIDC Authentication with Keycloak (SPA PKCE)

Status: in_progress

Acceptance:
- Login redirects to Keycloak with PKCE
- Callback exchanges code for tokens
- Access token used for authorized API calls
- Logout clears session

Implementation: `backend/app/services/auth.py`, `backend/app/api/v1/auth.py`, `backend/app/api/deps.py`, `backend/app/api/v1/router.py`, `backend/app/core/security.py`

Tests: `backend/tests/test_auth.py`

### marketplace-core — Plugin Marketplace Core Domain Engine

Status: planned

Acceptance:
- CRUD for plugins (harness, category, install command)
- Search/filter by harness, category, tags
- Plugin detail view with install instructions
- Export/import plugin collections

### skill-audit-engine — Skill Audit Engine (Static Analysis)

Status: planned

Acceptance:
- Parses SKILL.md frontmatter and body
- Detects overlapping/vague descriptions
- Reports context cost estimates
- Flags missing files referenced in skill

### company-context-pack — Company Context Pack Generator

Status: planned

Acceptance:
- Interactive interview flow
- Generates context/ folder with agent-readable files
- Marks unknowns and unsourced results explicitly

### gtm-scorers — GTM Scorers: Offer Stack & Proof Assets

Status: planned

Acceptance:
- Offer stack scorer rejects lines with no pain point
- Proof assets scorer rejects claims without source/permission
- Deterministic scoring algorithms

### pick-gtm-tools — Pick GTM Tools with MCP Integration

Status: planned

Acceptance:
- Searches GTM Directory MCP server
- Returns cited tool shortlists
- No API key required

