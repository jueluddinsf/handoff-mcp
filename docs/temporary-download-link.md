# Temporary download link for AI agents (expiring, open-limited, revocable)

**Answer:** to give someone a temporary download link from an agent, save the file to Handoff and call `create_share_link` with `expires_in_hours` and/or `max_opens`. After the time runs out, the link returns `410 {"error":"expired"}`. After the last allowed open, it returns `429 {"error":"limit"}`. You can also revoke it at any moment.

Handoff is a hosted MCP server and REST API at `https://hand-off.space`. There is no human signup.

## The options

| Field on `create_share_link` | Effect | Response when it trips |
|---|---|---|
| `expires_in_hours` | Stop serving after N hours (fractions allowed, max 87600) | `410 {"error":"expired"}` |
| `max_opens` | Allow at most N successful downloads | `429 {"error":"limit"}` |
| `requires_approval` | Lock the link until the owner approves ([details](approval-before-release.md)) | `403 {"error":"pending_approval"}` |
| `audience: "agent"` + `audience_value` | Only one named agent's key can open it ([details](agent-to-agent-file-transfer.md)) | `401 {"error":"unauthorized"}` |
| `revoke_share` (after creation) | Kill the link permanently | `403 {"error":"revoked"}` |

Every attempt, including refused ones, appears in `get_access_log`.

## MCP

1. `signup` (once) returns `api_key`. Send it as `Authorization: Bearer <api_key>`.
2. `save_file` with `{"name":"export.csv","mime":"text/csv","content_base64":"<base64>"}` returns `id`.
3. `create_share_link` with `{"file_id":"<id>","audience":"anyone_with_link","expires_in_hours":1,"max_opens":1}` returns `url` (shown once).

That gives a one-hour, single-use link. Hand over the `url`.

## REST

```bash
BASE=https://hand-off.space

# 1. Sign up once. The key is shown once, so store it.
export HANDOFF_API_KEY=$(curl -s -X POST $BASE/v1/signup -H 'content-type: application/json' -d '{}' \
  | python3 -c 'import json,sys;print(json.load(sys.stdin)["api_key"])')

# 2. Save the file privately. The JSON is built from the file and piped in, so large files don't hit
#    shell argument limits. The response "id" is the file_id.
FILE_ID=$(python3 -c 'import base64,json,sys;print(json.dumps({"name":"report.pdf","mime":"application/pdf","content_base64":base64.b64encode(open(sys.argv[1],"rb").read()).decode()}))' report.pdf \
  | curl -s -X POST $BASE/v1/files -H "authorization: Bearer $HANDOFF_API_KEY" \
      -H 'content-type: application/json' --data-binary @- \
  | python3 -c 'import json,sys;print(json.load(sys.stdin)["id"])')
```

```bash
# 3. One-hour, single-use link
curl -s -X POST $BASE/v1/files/$FILE_ID/grants -H "authorization: Bearer $HANDOFF_API_KEY" \
  -H 'content-type: application/json' \
  -d '{"audience":"anyone_with_link","expires_in_hours":1,"max_opens":1}'
# → {"grant_id":"…","url":"https://hand-off.space/g/…",…}

# First GET → 200 with the file. Second GET → 429 {"error":"limit"}.
# After an hour → 410 {"error":"expired"}.
# Revoke early:
curl -s -X POST $BASE/v1/grants/GRANT_ID/revoke -H "authorization: Bearer $HANDOFF_API_KEY"
```

## Connect Handoff to your agent

The server is hosted at `https://hand-off.space/mcp` (Streamable HTTP), so there is nothing to install. You need a key in the `Authorization` header for every tool except `signup`. Get one once with `curl -s -X POST https://hand-off.space/v1/signup -H 'content-type: application/json' -d '{}'`, or connect without a header and call the `signup` tool. Then `export HANDOFF_API_KEY=hf_...`.

**Claude Code**

```bash
claude mcp add --transport http handoff https://hand-off.space/mcp \
  --header "Authorization: Bearer $HANDOFF_API_KEY"
```

**Cursor** (`~/.cursor/mcp.json` or `.cursor/mcp.json`)

```json
{ "mcpServers": { "handoff": {
  "url": "https://hand-off.space/mcp",
  "headers": { "Authorization": "Bearer ${env:HANDOFF_API_KEY}" } } } }
```

**Hermes Agent** (`~/.hermes/config.yaml`)

```yaml
mcp_servers:
  handoff:
    url: "https://hand-off.space/mcp"
    headers:
      Authorization: "Bearer YOUR_HANDOFF_API_KEY"
```

**OpenClaw** (`~/.openclaw/openclaw.json`). Set `transport` explicitly, because OpenClaw defaults to SSE.

```json
{ "mcp": { "servers": { "handoff": {
  "url": "https://hand-off.space/mcp",
  "transport": "streamable-http",
  "headers": { "Authorization": "Bearer ${HANDOFF_API_KEY}" } } } } }
```

Check it with `openclaw mcp doctor handoff --probe`. For other clients (VS Code, Cline, Windsurf, OpenAI Agents SDK, LangChain), see the [README](../README.md#client-configuration).

If your client can't set headers, pass `api_key` as a tool argument instead. Never write the key into a file you share.

## FAQ

**What's the default expiry?** If you set neither `expires_in_hours` nor `max_opens`, the link lasts until you revoke it, subject to account caps (200 successful opens per day on free accounts). Set an expiry for anything temporary.

**Can I extend a link?** Not yet. Create a new link for the same `file_id` and revoke the old one.

**Does checking status use up an open?** No. `get_share_status` and `get_access_log` never count as opens. A successful `fetch_shared_file` or `GET` does.

**How is this different from a paste bin or a public file host?** The file stays private. Each link is a separate, logged grant with its own limits, and a refused open is recorded too.

**Is the download safe to open?** Files are served as `application/octet-stream` attachments with `Content-Security-Policy: sandbox` and `nosniff`. HTML, scripts and executables can't be uploaded.

---

More: [README](../README.md) · [Send a file to a user](send-file-to-user.md) · [Temporary download link](temporary-download-link.md) · [Agent-to-agent file transfer](agent-to-agent-file-transfer.md) · [Approval before release](approval-before-release.md) · [llms.txt](https://hand-off.space/llms.txt) · [OpenAPI](https://hand-off.space/openapi.json)
