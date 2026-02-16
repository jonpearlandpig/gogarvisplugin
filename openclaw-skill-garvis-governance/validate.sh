#!/bin/bash
# Validate script for OpenClaw GARVIS skill
set -e
if [ -f "plugin.json" ] && [ -f "index.ts" ]; then
  echo "Manifest and entrypoint found."
else
  echo "Missing plugin.json or index.ts!"; exit 1
fi
echo "Validation passed."