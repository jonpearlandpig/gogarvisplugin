# GARVIS Governance Skill for OpenClaw

This skill enforces governance, authority, and audit logging for OpenClaw agents using MongoDB and RBAC.

## Setup

1. Set your MongoDB URI:
   - On Linux/macOS: `export MONGODB_URI="mongodb://localhost:27017"`
   - On Windows: `set MONGODB_URI=mongodb://localhost:27017`
2. Place this folder in `~/.openclaw/workspace/skills/garvis-governance/`.
3. Restart OpenClaw gateway:
   - `openclaw gateway restart`
4. Test with:
   - `openclaw agent --message "test garvis authority for deleting files"`
5. Check MongoDB for audit logs in the `audit_log` collection.

## Publishing
- Push to GitHub or submit to ClawHub per OpenClaw documentation.

## Extending
- Add more tools, hooks, or governance logic in `index.ts`.
- Update `SKILL.md` for new features or usage notes.
