## Plugin Installation (OpenClaw)

To use the GARVIS Governance skill as an OpenClaw plugin:

1. Download the latest release artifact (garvis-openclaw-skill.zip) from the GitHub Releases page, or build manually:
    ```bash
    cd openclaw-skill-garvis-governance
    zip -r ../garvis-openclaw-skill.zip .
    ```
2. Unzip or copy the skill folder to your OpenClaw workspace:
    ```bash
    unzip garvis-openclaw-skill.zip -d ~/.openclaw/workspace/skills/garvis-governance/
    # or use the provided install script
    cd openclaw-skill-garvis-governance
    bash install.sh
    ```
3. Validate the install (optional):
    ```bash
    cd ~/.openclaw/workspace/skills/garvis-governance/
    bash validate.sh
    ```
4. Restart your OpenClaw agent/gateway and verify the skill is loaded.

See openclaw-skill-garvis-governance/README.md for more details.
# GARVIS Full Stack - Sovereign Intelligence Framework

> **Build your own sovereign intelligence and enforcement system.**

GARVIS Full Stack is an open-source starter kit for building sovereign intelligence platforms with role-based content management, audit logging, and AI-powered assistance.

![GARVIS Dashboard](docs/images/dashboard-preview.png)

## What is GARVIS?

GARVIS (Governance, Authority, Routing, Verification, Intelligence, Sovereignty) is an architectural framework for building systems with:

- **Authority Hierarchy** - Clear chain of command from sovereign to execution
- **Content Governance** - Version-controlled documents, glossaries, and registries
- **Audit Trail** - Immutable logging of all system changes
- **AI Integration** - Built-in LLM assistant for system queries
- **Role-Based Access** - Admin, Editor, Viewer permission levels

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.10+
- MongoDB 6+
- Git

### 1. Clone & Setup

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/gogarvis.git
cd gogarvis

# Setup backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env

# Setup frontend
cd ../frontend
yarn install
cp .env.example .env
```

### 2. Configure Environment

Edit `backend/.env`:
```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=your_database_name
CORS_ORIGINS=http://localhost:3000
EMERGENT_LLM_KEY=your_key_here  # Get from emergentagent.com
```

Edit `frontend/.env`:
```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

### 3. Seed Database

```bash
cd backend
python seed.py
```

### 4. Run Development Servers

```bash
# Terminal 1 - Backend
cd backend
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Terminal 2 - Frontend
cd frontend
yarn start
```


## Admin Setup

Set the `ADMIN_EMAILS` environment variable (comma-separated) with trusted emails.
Example: `ADMIN_EMAILS=you@domain.com,team@domain.com`
Only these emails get Admin role on first login. Others default to Viewer.

Visit `http://localhost:3000` and log in. Only users whose email is in `ADMIN_EMAILS` will be assigned Admin role; all others will be Viewer by default.

---

## Docker Quick Start

```bash
# Build and run with Docker Compose
docker-compose up -d

# Seed the database
docker-compose exec backend python seed.py
```

---

## Project Structure

```
gogarvis/
├── backend/
│   ├── server.py          # FastAPI application
│   ├── seed.py            # Database seeder
│   ├── config.py          # System configuration
│   ├── requirements.txt   # Python dependencies
│   └── .env.example       # Environment template
├── frontend/
│   ├── src/
│   │   ├── App.js         # Main React app
│   │   ├── pages/         # Page components
│   │   └── components/    # UI components
│   ├── package.json       # Node dependencies
│   └── .env.example       # Environment template
├── docs/
│   ├── CUSTOMIZATION.md   # How to customize
│   ├── ARCHITECTURE.md    # System architecture
│   └── API.md             # API reference
├── docker-compose.yml     # Docker configuration
└── README.md              # This file
```

---

## Customization

GARVIS is designed to be forked and customized. See [CUSTOMIZATION.md](docs/CUSTOMIZATION.md) for:

- **Rebranding** - Change system name, colors, logo
- **Adding Operators** - Define your own AI operator registry
- **Custom Content Types** - Extend the schema for your needs
- **Authentication** - Configure your own OAuth provider

### Quick Rebrand

Edit `backend/config.py`:
```python
SYSTEM_CONFIG = {
    "name": "YOUR_SYSTEM_NAME",
    "tagline": "Your tagline here",
    "version": "1.0.0",
    "owner": "Your Organization",
    "primary_color": "#FF4500",
}
```

---

## Core Concepts

### Authority Hierarchy

```
SOVEREIGN AUTHORITY (You)
    ↓
TELAUTHORIUM (Rights Registry)
    ↓
GARVIS (Intelligence Layer)
    ↓
FLIGHTPATH COS (Phase Control)
    ↓
MOSE (Operator Routing)
    ↓
PIG PEN (AI Operators)
    ↓
TELA (Execution)
    ↓
AUDIT LEDGER (Immutable Log)
```

### Content Types

| Type | Description | Editable By |
|------|-------------|-------------|
| Documents | PDF specs, guides, references | Editor+ |
| Glossary | Canonical terminology | Editor+ |
| Components | System architecture layers | Editor+ |
| Pig Pen Operators | AI operator registry (TAI-D) | Editor+ |
| Brand Profiles | Design system configs | Editor+ |

### User Roles

| Role | Permissions |
|------|-------------|
| Admin | Full access + user management |
| Editor | Create, edit, delete content |
| Viewer | Read-only access |

---

## API Reference

See [API.md](docs/API.md) for full documentation.

### Key Endpoints

```
# Authentication
POST /api/auth/session    # Exchange OAuth token
GET  /api/auth/me         # Get current user
POST /api/auth/logout     # End session

# Content (requires auth for write)
GET/POST   /api/documents
GET/PUT    /api/glossary
GET/POST   /api/pigpen
GET/POST   /api/brands

# Admin (requires admin role)
GET /api/admin/users
PUT /api/admin/users/{id}/role

# System
GET /api/dashboard/stats
GET /api/audit-log
GET /api/versions/{type}/{id}
POST /api/versions/{type}/{id}/rollback/{version_id}
```

---

## Tech Stack

- **Frontend**: React 19, Tailwind CSS, Shadcn UI, Lucide Icons
- **Backend**: FastAPI, Python 3.10+, Motor (async MongoDB)
- **Database**: MongoDB
- **Auth**: Emergent Google OAuth (or bring your own)
- **AI**: OpenAI GPT via Emergent LLM Key

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing`)
5. Open a Pull Request

---

## License

MIT License - See [LICENSE](LICENSE) for details.

Built with the GARVIS architecture by [Pearl & Pig](https://pearlandpig.com).

---

## Support

- 📖 [Documentation](docs/)
- 🐛 [Issues](https://github.com/YOUR_USERNAME/gogarvis/issues)
- 💬 [Discussions](https://github.com/YOUR_USERNAME/gogarvis/discussions)
