# How an AI agent can send a file to a user

**Answer:** save the file to Handoff, create a share link, and reply with the URL. The user opens it in any browser, with no account. Over MCP that is three tool calls: `signup` (once), `save_file`, then `create_share_link`. You can make the link expire, cap how many times it opens, and revoke it later.

This works for anything the agent produced, such as a PDF report, a CSV export, a chart image or a DOCX. Use it when the chat can't carry the attachment, or when the file has to leave the session.

## MCP: three tool calls

1. `signup` with `{}`. It returns `api_key` once. Put it in your client's `Authorization: Bearer …` header, or pass `api_key` on each call.
2. `save_file` with `{"name": "report.pdf", "mime": "application/pdf", "content_base64": "<base64 bytes>"}`. It returns `id`, which is the `file_id`.
3. `create_share_link` with `{"file_id": "<id>", "audience": "anyone_with_link", "expires_in_hours": 24, "max_opens": 3}`. It returns `grant_id` and `url`.

Reply to the user with the `url`. **It is shown only once**, so keep it. `get_share_status` returns the open count but never the URL again.

A real `create_share_link` result looks like this:

```json
{"grant_id":"7cb4ea92-…","url":"https://hand-off.space/g/51e507a5…","token":"51e507a5…","token_prefix":"51e507a5"}
```

## REST: the same three calls with curl

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
# 3. Create the link and give the url to the user.
curl -s -X POST $BASE/v1/files/$FILE_ID/grants -H "authorization: Bearer $HANDOFF_API_KEY" \
  -H 'content-type: application/json' \
  -d '{"audience":"anyone_with_link","expires_in_hours":24,"max_opens":3}'
# → {"grant_id":"…","url":"https://hand-off.space/g/…","token":"…","token_prefix":"…"}
```

The user downloads with a plain `GET` (or a click). The file arrives as an attachment.

## Confirm they got it, or take it back

- `get_access_log` (REST `GET /v1/grants/{grant_id}/logs`) lists every open, with `result` set to `ok`, `limit`, `expired` and so on.
- `get_share_status` (REST `GET /v1/grants/{grant_id}`) shows `open_count`, expiry and revocation.
- `revoke_share` (REST `POST /v1/grants/{grant_id}/revoke`) makes the link return `403 {"error":"revoked"}`. The file is kept.

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

## Prompt to try

> Write the Q3 summary as report.pdf, save it to Handoff, and send me a link that expires in 24 hours and opens at most 3 times.

## FAQ

**Does the user need an account or an app?** No. A link with `audience: "anyone_with_link"` opens with a plain browser GET.

**What file types and sizes work?** Free accounts accept txt, md, csv, json, pdf, png, jpg, gif, webp, svg, xml, yaml, log, docx, xlsx and pptx, up to 10 MB per file and 100 MB in total. Executables, scripts, HTML and archives are refused.

**Is the file public?** No. Files are private until you create a link, and each link is a separate grant with its own token, limits and log.

**I lost the URL.** It can't be shown again. Create a new link with `create_share_link` (use `list_files` to find the `file_id`), and revoke the old one if needed.

**Can I send it only to a specific agent instead?** Yes. See [agent-to-agent file transfer](agent-to-agent-file-transfer.md).

---

More: [README](../README.md) · [Send a file to a user](send-file-to-user.md) · [Temporary download link](temporary-download-link.md) · [Agent-to-agent file transfer](agent-to-agent-file-transfer.md) · [Approval before release](approval-before-release.md) · [llms.txt](https://hand-off.space/llms.txt) · [OpenAPI](https://hand-off.space/openapi.json)
