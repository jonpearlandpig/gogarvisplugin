# GoGarvis - Sovereign Intelligence Framework

## Product Requirements Document v2.1

### Overview
GoGarvis is an **open-source starter kit** for building sovereign intelligence platforms. Fork it, customize it, build your own "OS".

### Vision
Enable anyone to create their own governance/intelligence system with:
- Clear authority hierarchy
- Content management with version control
- Audit trail for all changes
- AI-powered assistance
- Role-based access control

---

## For Users Who Clone This Repo

### Quick Start
```bash
git clone https://github.com/jonpearlandpig/gogarvis.git
cd gogarvis
# Follow README.md for setup
```

### What You Get
- Full CMS with documents, glossary, operators, brands
- Version history with rollback
- Audit logging
- AI chat assistant
- Google OAuth authentication
- Role-based access (Admin, Editor, Viewer)

### What You Customize
1. **System Name** - `backend/config.py`
2. **Visual Identity** - Colors, fonts, logo
3. **Content** - Your own operators, documents, terms
4. **Authority Layers** - Define your hierarchy
5. **AI Prompt** - Train it on your domain

---

## Tech Stack
- **Frontend**: React 19, Tailwind CSS, Shadcn UI
- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **AI**: OpenAI GPT via Emergent LLM Key
- **Auth**: Emergent Google OAuth

---

## Project Structure
```
gogarvis/
├── README.md              # Setup guide
├── LICENSE                # MIT License
├── docker-compose.yml     # Docker setup
├── backend/
│   ├── server.py          # API application
│   ├── seed.py            # Database seeder
│   ├── config.py          # System configuration
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.js
│   │   └── pages/
│   ├── Dockerfile
│   └── .env.example
└── docs/
    ├── CUSTOMIZATION.md   # How to rebrand
    ├── ARCHITECTURE.md    # System design
    ├── API.md             # API reference
    └── specs/             # Original PDF specs
```

---

## Features Implemented

### Authentication
- [x] Emergent Google OAuth
- [x] Session management
- [x] Role-based access (Admin/Editor/Viewer)
- [x] First user = Admin

### Content Management
- [x] Documents CRUD + versioning
- [x] Glossary CRUD + versioning
- [x] System Components + versioning
- [x] Pig Pen Operators CRUD + versioning
- [x] Brand Profiles CRUD + versioning

### Version Control
- [x] Snapshot on every change
- [x] Full history per item
- [x] Rollback to any version

### Audit
- [x] Log all mutations
- [x] Who, what, when, details
- [x] Filter by type

### AI Assistant
- [x] GPT-5.2 powered chat
- [x] System-aware responses
- [x] Session persistence

---

## Seeded Content (Default)
- 18 Documents (from original PDFs)
- 30 Glossary Terms
- 8 System Components (authority hierarchy)
- 18 Pig Pen Operators (TAI-D registry)
- 1 Brand Profile

---

## Future Enhancements (Community)
- Document upload (PDF ingestion)
- Version diff viewer
- Bulk operations
- Content templates
- Workflow approvals
- Webhook integrations
- Multi-tenant support

---

## Credits
- Architecture by **Pearl & Pig**
- Built with **Emergent Agent**
- Open source under **MIT License**

---

*Last updated: Feb 13, 2026*
