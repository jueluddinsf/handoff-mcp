<p align="center"><img src="assets/logo.svg" width="96" height="96" alt="Handoff logo"></p>

# Handoff: File Sharing for AI Agents

**Private file storage and controlled share links for AI agents, with no human signup.**

Handoff gives an agent somewhere to put a file and a safe way to hand it to someone else. That someone can be a human or another agent. The agent saves the file privately, then creates a share link with the rules it needs: an expiry, a maximum number of opens, an optional human approval step, and a specific recipient agent. It can check status, revoke, and read the access log at any time.

- **Remote MCP server:** `https://hand-off.space/mcp` (Streamable HTTP)
- **REST API:** `https://hand-off.space/v1` ([OpenAPI](https://hand-off.space/openapi.json), [llms.txt](https://hand-off.space/llms.txt))
- **Auth:** `Authorization: Bearer <api_key>`. An agent gets a key by calling `POST /v1/signup`, with no email, card or human account.
- **Registry name:** `io.github.jueluddinsf/handoff`

This repository holds docs and listing metadata. The service is hosted, so you have nothing to install.

## Use it when an agent needs to…

- **Deliver a report to a human.** The agent saves `report.pdf`, then sends a link that expires in 24 hours and opens at most 3 times.
- **Hand a file to another agent.** The link works only when the named recipient agent presents its own key.
- **Wait for a human before releasing a file.** The link stays locked (`pending_approval`) until the owner approves it.
- **Take something back.** Revoke a link, and see every successful and refused open.

## Quickstart: REST (3 calls)

```bash
BASE=https://hand-off.space

# 1. Sign up. The key is shown once, so store it.
curl -s -X POST $BASE/v1/signup -H 'content-type: application/json' -d '{"agent_id":"my-agent"}'
# → {"account_id":"…","api_key":"hf_…","agent_id":"my-agent","caps":{…}}
export HANDOFF_API_KEY=hf_...

# 2. Save a file privately (base64 bytes)
curl -s -X POST $BASE/v1/files -H "authorization: Bearer $HANDOFF_API_KEY" -H 'content-type: application/json' \
  -d "{\"name\":\"report.md\",\"mime\":\"text/markdown\",\"content_base64\":\"$(printf '# Q3 report' | base64)\"}"
# → {"id":"FILE_ID","name":"report.md",…}

# 3. Create a share link
curl -s -X POST $BASE/v1/files/FILE_ID/grants -H "authorization: Bearer $HANDOFF_API_KEY" -H 'content-type: application/json' \
  -d '{"audience":"anyone_with_link","expires_in_hours":24,"max_opens":3}'
# → {"grant_id":"…","url":"https://hand-off.space/g/…"}
```

Give the `url` to the recipient. It downloads with a plain `GET`.

## Quickstart: MCP (3 tool calls)

1. Connect your client to `https://hand-off.space/mcp` (configs below).
2. Get a key. Call the `signup` MCP tool, or `POST /v1/signup` as shown above. Put the key in your client's `Authorization: Bearer …` header and reconnect.
   > The keyless `signup` tool is rolling out. If your client shows only the six tools below, use `POST /v1/signup`.
3. Call `save_file` → `create_share_link`, then hand over the returned `url`.

### Tools

| Tool | What it does |
|---|---|
| `save_file` | Save a file privately: `name`, `mime`, `content_base64`. Returns the file id. No link is created. |
| `list_files` | List your files, newest first. |
| `create_share_link` | `file_id`, `audience` (`anyone_with_link` or `agent`), optional `audience_value` (the recipient's `agent_id`), `expires_in_hours`, `max_opens`, `requires_approval`. Returns `grant_id` and `url`. |
| `get_share_status` | Approval, expiry, revocation and `open_count` for a link, without using up an open. |
| `revoke_share` | Permanently revoke a link. |
| `get_access_log` | Up to the latest 1,000 opens and refusals for a link. |

## Client configuration

In each config below, replace `YOUR_HANDOFF_API_KEY` with your key, or use the environment-variable form shown.

### Claude Code

```bash
claude mcp add --transport http handoff https://hand-off.space/mcp \
  --header "Authorization: Bearer YOUR_HANDOFF_API_KEY"
```

You can also commit a project-scoped `.mcp.json`, which is the file in this repo. Claude Code expands `${HANDOFF_API_KEY}` from your environment:

```json
{ "mcpServers": { "handoff": { "type": "http", "url": "https://hand-off.space/mcp",
  "headers": { "Authorization": "Bearer ${HANDOFF_API_KEY}" } } } }
```

### Claude Desktop

Claude Desktop custom connectors don't take a static header, so bridge with [`mcp-remote`](https://www.npmjs.com/package/mcp-remote) in `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "handoff": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://hand-off.space/mcp",
               "--header", "Authorization:${HANDOFF_AUTH}"],
      "env": { "HANDOFF_AUTH": "Bearer YOUR_HANDOFF_API_KEY" }
    }
  }
}
```

### Cursor (`~/.cursor/mcp.json` or `.cursor/mcp.json`)

```json
{
  "mcpServers": {
    "handoff": {
      "url": "https://hand-off.space/mcp",
      "headers": { "Authorization": "Bearer ${env:HANDOFF_API_KEY}" }
    }
  }
}
```

### VS Code / GitHub Copilot (`.vscode/mcp.json`)

```json
{
  "inputs": [
    { "type": "promptString", "id": "handoff_api_key", "description": "Handoff API key", "password": true }
  ],
  "servers": {
    "handoff": {
      "type": "http",
      "url": "https://hand-off.space/mcp",
      "headers": { "Authorization": "Bearer ${input:handoff_api_key}" }
    }
  }
}
```

### Cline (`cline_mcp_settings.json`)

Set `"type": "streamableHttp"` explicitly. If you leave it out, Cline falls back to legacy SSE.

```json
{
  "mcpServers": {
    "handoff": {
      "type": "streamableHttp",
      "url": "https://hand-off.space/mcp",
      "headers": { "Authorization": "Bearer YOUR_HANDOFF_API_KEY" },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

### Windsurf (`~/.codeium/windsurf/mcp_config.json`)

```json
{
  "mcpServers": {
    "handoff": {
      "serverUrl": "https://hand-off.space/mcp",
      "headers": { "Authorization": "Bearer ${env:HANDOFF_API_KEY}" }
    }
  }
}
```

### OpenAI Agents SDK (Python)

```python
import asyncio, os
from agents import Agent, Runner
from agents.mcp import MCPServerStreamableHttp

async def main():
    async with MCPServerStreamableHttp(
        name="handoff",
        params={
            "url": "https://hand-off.space/mcp",
            "headers": {"Authorization": f"Bearer {os.environ['HANDOFF_API_KEY']}"},
        },
        cache_tools_list=True,
    ) as handoff:
        agent = Agent(
            name="Reporter",
            instructions="Write the report, save it with Handoff, and reply with a share link that expires in 24h.",
            mcp_servers=[handoff],
        )
        print((await Runner.run(agent, "Summarize Q3 sales into report.md and share it.")).final_output)

asyncio.run(main())
```

### LangChain / LangGraph (`langchain-mcp-adapters`)

```python
import os
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent

client = MultiServerMCPClient({
    "handoff": {
        "transport": "streamable_http",
        "url": "https://hand-off.space/mcp",
        "headers": {"Authorization": f"Bearer {os.environ['HANDOFF_API_KEY']}"},
    }
})
tools = await client.get_tools()
agent = create_agent("openai:gpt-4.1", tools)  # or langgraph.prebuilt.create_react_agent
```

### Hermes Agent (`~/.hermes/config.yaml`)

```yaml
mcp_servers:
  handoff:
    url: "https://hand-off.space/mcp"
    headers:
      Authorization: "Bearer YOUR_HANDOFF_API_KEY"
```

### Any other MCP client

| Setting | Value |
|---|---|
| URL | `https://hand-off.space/mcp` |
| Transport | Streamable HTTP (stateless, `POST` only) |
| Header | `Authorization: Bearer <api_key>` |

More step-by-step setup for agents is in [`llms-install.md`](llms-install.md).

### Agent Skill (no MCP needed)

This repo also ships an [Agent Skill](skills/handoff/SKILL.md) that teaches any skills-capable agent (Claude Code, Codex, Copilot, Cursor and others) to use the REST API:

```bash
npx skills add jueluddinsf/handoff-mcp
```

## Recipes

### Agent → human report, with an expiry
`save_file(report.pdf)` → `create_share_link(audience="anyone_with_link", expires_in_hours=24, max_opens=3)` → send the `url`. Use `get_access_log` to confirm it was opened.

### Agent → agent handoff
Agent A calls `create_share_link(audience="agent", audience_value="agent-b")`. Agent B downloads with its own key:

```bash
curl -L -H "authorization: Bearer $AGENT_B_KEY" -o out.bin "$URL"
```

Any other caller gets `401 {"error":"unauthorized"}`.

### Human-approval gate
`create_share_link(..., requires_approval=true)`. Until the owner approves, opens return `403 {"error":"pending_approval"}`. To approve or deny:

```bash
curl -X POST -H "authorization: Bearer $HANDOFF_API_KEY" $BASE/v1/grants/GRANT_ID/approve   # or /deny
```

## Limits (free, unclaimed accounts)

- 100 MB total, 50 files, 10 MB per file, 200 successful opens per day.
- Allowed file types: txt, md, csv, json, pdf, png, jpg, gif, webp, svg, xml, yaml, log, docx, xlsx, pptx.
- Executables, scripts, HTML and archives are refused.
- Signup is rate-limited per IP.

### Download responses

| Status | Error | Meaning |
|---|---|---|
| `410` | `expired` | The link is past its expiry. |
| `429` | `limit` | The link hit its max opens or the daily cap. |
| `403` | `revoked` / `denied` / `pending_approval` | Revoked, denied, or still waiting for approval. |
| `401` | `unauthorized` | The link is for a different agent. |

## Security model

- Files are private by default. Every share is an explicit grant with its own token.
- Downloads are served as `application/octet-stream` attachments with `Content-Security-Policy: sandbox` and `nosniff`.
- Every attempt, successful or refused, is logged.
- API keys are stored hashed and shown once.

Report security issues privately (see [CONTRIBUTING.md](CONTRIBUTING.md)).

## License

[MIT](LICENSE). This applies to the docs and examples in this repository. The hosted service is operated by Juel Uddin.
