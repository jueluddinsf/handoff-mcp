---
name: handoff
description: Send a file you produced (report, PDF, CSV, image, dataset) to a user or another agent as an expiring, revocable, logged share link, with optional max opens, human approval and agent-only audience. Use when you need to deliver a file to someone outside this session, get a temporary download link, hand a file to another agent, or release a file only after a human approves.
---

# Handoff: deliver files with controlled share links

Handoff is a hosted service at `https://hand-off.space`. Use the MCP server at `/mcp` if it is connected. Otherwise use the REST API with curl.

## 1. Share in one call (default)

No key is needed. Send the bytes and get a link back:

```bash
curl -s --data-binary @report.pdf "https://hand-off.space/v1/share?name=report.pdf&format=url"
```

The first line is the download URL. If this call created an account, the second line is `api_key: hf_…`. **Save that key** somewhere private (not in a shared file), because it is shown only once and you need it to revoke the link or read the access log. On later calls, send `Authorization: Bearer <api_key>` so new files stay in the same account.

JSON works too: `POST /v1/share` with `{"name":"notes.md","content_text":"# Notes"}`, or `content_base64` for binary. Over MCP, call `share_file` with the same fields.

The default link opens for anyone who has it and expires in 7 days. Add rules as JSON fields, or as query parameters with raw bytes:

| Situation | Add |
|---|---|
| A human needs it today | `"expires_in_hours":24,"max_opens":3` |
| Another agent needs it | `"audience":"agent","audience_value":"<their agent_id>","expires_in_hours":2` |
| A human must approve first | `"requires_approval":true`, then the owner calls `POST /v1/grants/{grant_id}/approve` (MCP `approve_share`) |

Return the `url` to the recipient.

## 2. More control: save once, share many times

1. Get a key once: `POST /v1/signup` with `{}`, or the MCP tool `signup`.
2. `POST /v1/files` with `{"name":"report.pdf","content_base64":"<base64>"}` (or `content_text`). The MCP equivalent is `save_file`. Keep the returned `id`.
3. `POST /v1/files/{id}/grants` (MCP `create_share_link`) with the same rule fields as above, plus `"audience":"anyone_with_link"` or `"agent"`. Each call makes a separate link with its own limits and log.

## 4. Follow up

- `get_share_status` (`GET /v1/grants/{id}`) shows the open count.
- `get_access_log` (`GET /v1/grants/{id}/logs`) shows who opened it and when.
- `revoke_share` (`POST /v1/grants/{id}/revoke`) shuts the link at once.

## Rules

- Never paste the API key into a file, a link or a chat message.
- Prefer short expiries and a small `max_opens`.
- Free accounts: 10 MB per file, 50 files, 100 MB total, 200 opens per day.
- HTML, markdown, code and zip files are allowed; executables are refused.
- Link previews from Slack, X, Discord and similar don't consume opens. An exhausted link returns `410`.
