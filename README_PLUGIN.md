# GARVIS Pluginization & OpenClaw Adapter

This document describes how to use, build, and install the GARVIS plugin and OpenClaw adapter from this monorepo.

## Monorepo Structure

- `packages/gogarvis-core/` — Core governance, RBAC, and audit logic (framework-agnostic)
- `packages/gogarvis-adapter-openclaw/` — OpenClaw skill adapter (TypeScript)
- `openclaw-skill-garvis-governance/` — Plugin skill folder for OpenClaw

## Building

Use `pnpm install` and `pnpm build` to build all packages.

## Releasing

On tag, GitHub Actions will package the OpenClaw skill and upload as a release artifact.

## Installing as OpenClaw Plugin

See the main README for install instructions, or use the install.sh script in the skill folder.
