#!/usr/bin/env bash
# Agent A shares FILE_ID with agent "agent-b"; agent B downloads using its own key.
set -euo pipefail
BASE=https://handoff-agent-file-sharing.replit.app
URL=$(curl -s -X POST "$BASE/v1/files/$FILE_ID/grants" -H "authorization: Bearer $AGENT_A_KEY" \
  -H 'content-type: application/json' -d '{"audience":"agent","audience_value":"agent-b","expires_in_hours":2}' \
  | python3 -c 'import json,sys;print(json.load(sys.stdin)["url"])')
curl -sfL -H "authorization: Bearer $AGENT_B_KEY" -o handed-off.bin "$URL" && echo "agent-b received handed-off.bin"
