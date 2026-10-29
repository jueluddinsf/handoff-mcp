# Human approval before an agent releases a file

**Answer:** to make an agent wait for a human before a file goes out, share it with Handoff's `share_file` (or `POST /v1/share`) and `requires_approval: true`. The link exists right away, so the agent can send it, but every open returns `403 {"error":"pending_approval",…}` until the owner calls `approve_share`. If the owner calls `deny_share`, it stays blocked with `403 {"error":"denied",…}`. Every attempt is logged.

Use this for anything sensitive, such as a contract draft, customer data, an invoice or a model-generated report a person should check first.

## One call

**MCP:** `share_file` with `{"name":"contract.md","content_text":"# Draft contract","requires_approval":true,"expires_in_hours":48}` returns `url`, `grant_id` and, if you sent no key, `api_key`. **Keep the `api_key` with the approver**, because approving needs it.

**REST:**

```bash
curl -s -X POST https://hand-off.space/v1/share -H 'content-type: application/json' \
  -d '{"name":"contract.md","content_text":"# Draft contract","requires_approval":true,"expires_in_hours":48}'
# → {"url":"…","grant_id":"GRANT_ID","requires_approval":true,…,"api_key":"hf_…"}

# Until approved, GET url → 403 {"error":"pending_approval",…}. The approver runs:
curl -s -X POST https://hand-off.space/v1/grants/GRANT_ID/approve -H "authorization: Bearer hf_…"
# → {…,"approval_status":"approved",…}. The same url now returns 200.
```

## More control over MCP

1. `signup` (once) and `save_file` as usual. `save_file` returns `id`.
2. `create_share_link` with `{"file_id":"<id>","audience":"anyone_with_link","requires_approval":true,"expires_in_hours":48}` returns `grant_id` and `url`. Save both.
3. Send the `url` to the recipient, and tell the human approver what is waiting.
4. The approver (or the agent, on the human's explicit instruction) calls `approve_share` with `{"grant_id":"<grant_id>"}`, or `deny_share`.
5. Check with `get_share_status`. `approval_status` is `pending`, `approved` or `denied`.

You can combine this with `audience: "agent"` for an approval-gated agent-to-agent handoff, and with `max_opens` and `expires_in_hours`.

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
# 3. Create a locked link
curl -s -X POST $BASE/v1/files/$FILE_ID/grants -H "authorization: Bearer $HANDOFF_API_KEY" \
  -H 'content-type: application/json' \
  -d '{"audience":"anyone_with_link","requires_approval":true,"expires_in_hours":48}'
# → {"grant_id":"GRANT_ID","url":"https://hand-off.space/g/…",…}

curl -s "$URL"                       # → 403 {"error":"pending_approval",…}

# 4. The owner approves (or POST …/deny)
curl -s -X POST $BASE/v1/grants/GRANT_ID/approve -H "authorization: Bearer $HANDOFF_API_KEY"
# → {…,"approval_status":"approved",…}

curl -s "$URL"                       # → 200, the file
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

## Prompt to try

> Save contract-draft.docx to Handoff and give me a link for the client that only works after I approve it. Tell me the grant_id.

## FAQ

**Who can approve?** The account that owns the link, using its API key, through `approve_share` or `POST /v1/grants/{id}/approve`. Keep the key with the human or the orchestrator, not with the recipient.

**Does the agent have to resend the link after approval?** No. The same URL starts working as soon as it's approved.

**Can I see who tried to open it while it was locked?** Yes. `get_access_log` records refused opens with `result: "pending_approval"`.

**Can a denied link be approved later?** No. `approve_share` on a denied link returns `409 {"error":"Denied grants stay blocked"}`. Create a new link if you change your mind.

**Can I still revoke after approving?** Yes. `revoke_share` stops it permanently.

---

More: [README](../README.md) · [Send a file to a user](send-file-to-user.md) · [Temporary download link](temporary-download-link.md) · [Agent-to-agent file transfer](agent-to-agent-file-transfer.md) · [Approval before release](approval-before-release.md) · [llms.txt](https://hand-off.space/llms.txt) · [OpenAPI](https://hand-off.space/openapi.json)
