---
name: "GARVIS Governance"
description: "Enforces Governance, Authority, Routing, Verification, Intelligence, and Sovereignty (GARVIS) principles for OpenClaw agents. Provides authority checks, immutable audit logging, and prompt routing/verification before sensitive actions."
version: "0.1.0"
author: "Your Name <your@email.com>"
license: "MIT"
tags: ["governance", "rbac", "audit", "openai", "security"]
---

# GARVIS Governance Skill

This skill enforces GARVIS principles for all agent actions:

- **Governance**: All sensitive actions (e.g., LLM calls, file operations) are checked against user authority and governance rules.
- **Authority**: Role-based access control (RBAC) is enforced before any tool or LLM call.
- **Routing/Verification**: Prompts and actions are routed and verified according to governance policies.
- **Intelligence**: LLM or OpenAI calls are only allowed if approved by governance.
- **Sovereignty**: All actions are logged immutably for traceability and compliance.

## Usage

- Before any sensitive action, call the `garvis_authority_check` tool:
  - Example: `garvis_authority_check(user_id="alice", action="delete_file", context="projectX")`
- The tool returns `{ approved: boolean, reason: string, required_role?: string }`.
- If not approved, the agent must halt the action and report the reason.

## Examples

- "Check authority for deleting files"
- "Log all LLM calls with user and outcome"
- "Route prompt through governance before OpenAI access"

## Enforcement

- This skill auto-applies governance checks via a pre-LLM hook.
- All actions (approved or denied) are logged to MongoDB for audit.

---
