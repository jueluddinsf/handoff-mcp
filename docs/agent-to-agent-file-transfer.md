# Agent-to-agent file transfer over MCP

**Answer:** to hand a file from one AI agent to another, agent A saves it to Handoff and creates a link with `audience: "agent"` and `audience_value` set to agent B's `agent_id`. Only agent B's API key can open that link. Agent B calls `fetch_shared_file` with the URL, or sends a `GET` with its own `Authorization` header. Anyone else, including agent A, gets `401 {"error":"unauthorized"}`.

The two agents can run in different clients (Claude Code, Cursor, Hermes, OpenClaw, a LangGraph worker) and on different machines. They only need the URL and their own keys, with no shared disk and no pairing step.

## 1. Each agent signs up once

Agent B picks a stable `agent_id`, so that others can address it by name:

```bash
curl -s -X POST https://hand-off.space/v1/signup -H 'content-type: application/json' \
  -d '{"agent_id":"report-reviewer"}'
# → {"account_id":"…","api_key":"hf_…","agent_id":"report-reviewer","caps":{…}}
```

An `agent_id` is unique across Handoff and may contain letters, numbers, `_` and `-` (up to 80 characters). Over MCP, call `signup` with `{"agent_id":"report-reviewer"}`. Agent A can sign up with `{}`.

## 2. Agent A sends

**MCP**

1. `save_file` with `{"name":"dataset.csv","mime":"text/csv","content_base64":"<base64>"}` returns `id`.
2. `create_share_link` with `{"file_id":"<id>","audience":"agent","audience_value":"report-reviewer","expires_in_hours":2}` returns `url`.
3. Pass the `url` to agent B through your orchestrator, a message, a ticket or a shared prompt.

**REST**

```bash
curl -s -X POST https://hand-off.space/v1/files/$FILE_ID/grants \
  -H "authorization: Bearer $AGENT_A_KEY" -H 'content-type: application/json' \
  -d '{"audience":"agent","audience_value":"report-reviewer","expires_in_hours":2}'
# → {"grant_id":"…","url":"https://hand-off.space/g/…",…}
```

(`FILE_ID` comes from `POST /v1/files`. See [send a file to a user](send-file-to-user.md#rest-the-same-three-calls-with-curl).)

## 3. Agent B receives

**MCP:** call `fetch_shared_file` with `{"url_or_token":"<url>"}`, using agent B's key in the header. Files up to 1 MB come back inline as `content_base64`, plus `content_text` for text files:

```json
{"name":"report.md","mime":"text/markdown","size":11,"sha256":"30f7…","content_base64":"IyBRMyByZXBvcnQ=","content_text":"# Q3 report"}
```

For larger files, the tool returns an error with the byte size. Download those with `GET` instead.

**REST:**

```bash
curl -sfL -H "authorization: Bearer $AGENT_B_KEY" -o dataset.csv "$URL"
```

A request without agent B's key, or with any other key, gets `401 {"error":"unauthorized"}`. Agent B can check the `sha256` against the value agent A saw from `save_file`.

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

**Does the file pass through the model's context?** Only if you use `fetch_shared_file`, which returns bytes inline up to 1 MB. A `GET` with curl writes straight to disk.

**Can agent A see whether B picked it up?** Yes. `get_access_log` shows each attempt with its `result` (`ok`, `unauthorized`, `expired`, `limit`…), and `get_share_status` shows `open_count`.

**Can I require a human to approve the handoff?** Yes. Add `"requires_approval": true`. See [approval before release](approval-before-release.md).

**Can B pass it on to C?** Not through the same link. B would save its own copy and create a new link addressed to C. That keeps each hop logged and revocable.

---

More: [README](../README.md) · [Send a file to a user](send-file-to-user.md) · [Temporary download link](temporary-download-link.md) · [Agent-to-agent file transfer](agent-to-agent-file-transfer.md) · [Approval before release](approval-before-release.md) · [llms.txt](https://hand-off.space/llms.txt) · [OpenAPI](https://hand-off.space/openapi.json)
