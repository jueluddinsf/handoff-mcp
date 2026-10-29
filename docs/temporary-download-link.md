# Temporary download link for AI agents (expiring, open-limited, revocable)

**Answer:** to give someone a temporary download link from an agent, call Handoff's `share_file` (or `POST /v1/share`) with the file plus `expires_in_hours` and/or `max_opens`. It is one call, with no API key needed, and links expire in 7 days by default. After the time runs out, the link returns `410 {"error":"expired",…}`. After the last allowed open, it returns `429 {"error":"limit",…}`. You can also revoke it at any moment.

Handoff is a hosted MCP server and REST API at `https://hand-off.space`. There is no human signup.

## One call

**MCP:** `share_file` with `{"name":"export.csv","content_text":"id,total\n1,42\n","expires_in_hours":1,"max_opens":1}` returns `url`, `expires_at` and `grant_id`, plus `api_key` once if you sent no key.

**REST:**

```bash
curl -s --data-binary @export.csv "https://hand-off.space/v1/share?name=export.csv&format=url&expires_in_hours=1&max_opens=1"
# https://hand-off.space/g/…
# api_key: hf_…        (only when no key was sent; save it to revoke the link)
```

That gives a one-hour, single-use link. The first GET returns 200 with the file. The second returns `410 {"error":"limit",…}`. Link previews from Slack, X, Discord and similar don't count as opens.

## The options

| Field on `share_file` / `create_share_link` | Effect | Response when it trips |
|---|---|---|
| `expires_in_hours` | Stop serving after N hours (fractions allowed, max 87600) | `410 {"error":"expired",…}` |
| `max_opens` | Allow at most N successful downloads | `410 {"error":"limit",…}` |
| `requires_approval` | Lock the link until the owner approves ([details](approval-before-release.md)) | `403 {"error":"pending_approval",…}` |
| `audience: "agent"` + `audience_value` | Only one named agent's key can open it ([details](agent-to-agent-file-transfer.md)) | `401 {"error":"unauthorized",…}` |
| `revoke_share` (after creation) | Kill the link permanently | `403 {"error":"revoked",…}` |

Every attempt, including refused ones, appears in `get_access_log`.

## More control over MCP

Save once, then create several links with different limits:

1. `signup` (once) returns `api_key`. Send it as `Authorization: Bearer <api_key>`.
2. `save_file` with `{"name":"export.csv","mime":"text/csv","content_base64":"<base64>"}` returns `id`.
3. `create_share_link` with `{"file_id":"<id>","audience":"anyone_with_link","expires_in_hours":1,"max_opens":1}` returns `url` (shown once).

That gives a one-hour, single-use link. Hand over the `url`.

## More control over REST

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

# First GET → 200 with the file. Second GET → 410 {"error":"limit",…}.
# After an hour → 410 {"error":"expired",…}.
# Revoke early:
curl -s -X POST $BASE/v1/grants/GRANT_ID/revoke -H "authorization: Bearer $HANDOFF_API_KEY"
```

## Connect Handoff to your agent

The server is hosted at `https://hand-off.space/mcp` (Streamable HTTP), so there is nothing to install. You can connect **with no header** and call `share_file` right away. It returns an `api_key` once, the first time. Save it with `export HANDOFF_API_KEY=hf_...` and add the header below, so that later calls (status, revoke, logs, more files) use the same account. You can also get a key on its own with `curl -s -X POST https://hand-off.space/v1/signup -H 'content-type: application/json' -d '{}'`, or with the `signup` tool.

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

**What's the default expiry?** `share_file` and `POST /v1/share` links expire after 7 days (168 hours). `create_share_link` links also default to 7 days when `expires_in_hours` is omitted.

**Can I extend a link?** Yes. Call `update_share` with the `grant_id` and a new `expires_in_hours`, measured from now.

**Does checking status use up an open?** No. `get_share_status` and `get_access_log` never count as opens. A successful `fetch_shared_file` or `GET` does. Link previews from Slack, X, Discord and similar unfurlers don't.

**How is this different from a paste bin or a public file host?** The file stays private. Each link is a separate, logged grant with its own limits, and a refused open is recorded too.

**Is the download safe to open?** Files are served as `application/octet-stream` attachments with `Content-Security-Policy: sandbox` and `nosniff`. HTML, markdown, code and zip files can be uploaded; executables can't.

---

More: [README](../README.md) · [Send a file to a user](send-file-to-user.md) · [Temporary download link](temporary-download-link.md) · [Agent-to-agent file transfer](agent-to-agent-file-transfer.md) · [Approval before release](approval-before-release.md) · [llms.txt](https://hand-off.space/llms.txt) · [OpenAPI](https://hand-off.space/openapi.json)
