# GoGarvis Portal - Product Requirements Document

## Original Problem Statement
Build a web application based on PDF documentation for the "GoGarvis" system. The application serves as a web portal and CMS with the following core requirements:
- Browse documentation and system architecture
- CMS with Google authentication and role-based access
- Manage Documents, Glossary Terms, Brand Profiles, and Pig Pen Operators
- Canonical/frozen list of exactly 33 Pig Pen operators

## What's Been Implemented

### MVP Portal (Completed)
- Dashboard with system statistics
- Documentation browser
- Architecture visualization
- Glossary management

### CMS System (Completed)
- Full CRUD for Documents, Glossary, Brands, Pig Pen Operators
- Version history and audit logging
- Content versioning stored in `content_versions` collection

### Authentication & Authorization (Completed)
- Emergent-managed Google Auth integration
- Role-Based Access Control (Admin, Editor, Viewer)
- First registered user becomes Admin
- Sovereign user (jonpearlandpig@gmail.com) has special permissions

### Pig Pen Operators (Completed - Feb 14, 2026)
- ✅ Canonical list of exactly 33 operators (FIXED)
- Operators are frozen/locked from editing
- Categories: Creative Engine, Data & Integrity, Executive & Architecture, Governance & IP, Growth & Commercial, Legacy & Integrity, Quality & Trust, Systems & Ops, Writers Room

### Open-Source Starter Kit (Completed)
- Docker configuration (docker-compose.yml, Dockerfiles)
- Documentation in /app/docs
- README.md with setup instructions
- CUSTOMIZATION.md guide

### Garvis AI Chat with File Upload (Completed - Feb 14, 2026)
- ✅ Bulk file upload support (drag & drop + button)
- Supported formats: PNG, JPG, WEBP, PDF, TXT, MD
- 50MB file size limit per file
- Vision analysis for images via GPT-5.2
- Text extraction for documents (PDF, TXT, MD)
- Files stored persistently and can be referenced in chat
- Context injection: document text added to AI prompts

## Technical Architecture
```
/app/
├── backend/
│   ├── server.py       # FastAPI main app
│   ├── seed.py         # DB seeding (33 operators)
│   ├── tests/          # Pytest test files
│   └── requirements.txt
├── frontend/
│   ├── src/pages/      # React components
│   └── package.json
├── uploads/            # Uploaded chat files
├── docs/               # Starter kit docs
├── gogarvis_docs/      # Original PDFs
└── docker-compose.yml
```

## Database Schema
- `users`: {email, name, picture, role}
- `operators`: {operator_id, tai_d, name, capabilities, category, decision_weight, canonical}
- `documents`: {doc_id, filename, title, category, content}
- `content_versions`: {collection_name, document_id, data, version, created_at, created_by}
- `chat_files`: {file_id, filename, file_type, size, path, is_image, extracted_text, uploaded_at}
- `chat_history`: {session_id, role, content, file_ids, timestamp}
- `glossary`, `components`, `brands`

## API Endpoints (File Upload)
- `POST /api/chat/upload` - Upload multiple files
- `GET /api/chat/files/{file_id}` - Get file metadata
- `DELETE /api/chat/files/{file_id}` - Delete file
- `POST /api/chat` - Chat with optional file_ids array

## Backlog / Future Tasks
- (P2) MOSE visualization tool - Interactive display of operator decision weights

## Changelog
- **Feb 14, 2026**: Added bulk file upload to Garvis AI chat (images + documents, drag & drop, vision analysis, text extraction)
- **Feb 14, 2026**: Fixed Pig Pen operator count from 54 to correct 33 canonical operators
