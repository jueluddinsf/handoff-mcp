---
name: handoff
description: Send a file you produced (report, PDF, CSV, image, dataset) to a user or another agent as an expiring, revocable, logged share link, with optional max opens, human approval and agent-only audience. Use when you need to deliver a file to someone outside this session, get a temporary download link, hand a file to another agent, or release a file only after a human approves.
---

# Handoff: deliver files with controlled share links

Handoff is a hosted service at `https://hand-off.space`. Use the MCP server at `/mcp` if it is connected. Otherwise use the REST API with curl.

## 1. Get a key (once)

```bash
curl -s -X POST https://hand-off.space/v1/signup -H 'content-type: application/json' -d '{}'
```

Store `api_key`, because it is shown only once. Send it as `Authorization: Bearer <api_key>`.

## 2. Save the file

`POST /v1/files` with `{"name":"report.pdf","mime":"application/pdf","content_base64":"<base64>"}`. The MCP equivalent is `save_file`. Keep the returned `id`.

## 3. Create the link that fits the situation

Use `POST /v1/files/{id}/grants`, or the MCP tool `create_share_link`.

| Situation | Body |
|---|---|
| A human needs it today | `{"audience":"anyone_with_link","expires_in_hours":24,"max_opens":3}` |
| Another agent needs it | `{"audience":"agent","audience_value":"<their agent_id>","expires_in_hours":2}` |
| A human must approve first | add `"requires_approval":true`, then the owner calls `POST /v1/grants/{grant_id}/approve` |

Return the `url` to the recipient.

## 4. Follow up

- `get_share_status` (`GET /v1/grants/{id}`) shows the open count.
- `get_access_log` (`GET /v1/grants/{id}/logs`) shows who opened it and when.
- `revoke_share` (`POST /v1/grants/{id}/revoke`) shuts the link at once.

## Rules

- Never paste the API key into a file, a link or a chat message.
- Prefer short expiries and a small `max_opens`.
- Free accounts: 10 MB per file, 50 files, 100 MB total, 200 opens per day.
- Executables, HTML, scripts and archives are refused.
