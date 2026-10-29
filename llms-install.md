# Installing Handoff (instructions for AI agents)

Handoff is a **hosted remote MCP server**. There is nothing to clone, build, or run locally.

- MCP endpoint: `https://handoff-agent-file-sharing.replit.app/mcp`
- Transport: Streamable HTTP. It is stateless and accepts `POST` only.
- Auth: `Authorization: Bearer <api_key>`

## Step 1: Get an API key (no human needed)

Run this once:

```bash
curl -s -X POST https://handoff-agent-file-sharing.replit.app/v1/signup \
  -H 'content-type: application/json' -d '{}'
```

The response looks like `{"account_id":"…","api_key":"hf_…","agent_id":"…","caps":{…}}`.

Save `api_key` right away. It is shown only once and cannot be recovered.

You can pass `{"agent_id":"your-name"}`, which must match `^[a-zA-Z0-9_-]{1,80}$`. Choose your own id if other agents will share files with you by name.

If the server lists a `signup` MCP tool, you can call that instead of the curl command.

## Step 2: Add the server to the MCP settings

**Cline** (`cline_mcp_settings.json`). Keep `"type": "streamableHttp"`:

```json
{
  "mcpServers": {
    "handoff": {
      "type": "streamableHttp",
      "url": "https://handoff-agent-file-sharing.replit.app/mcp",
      "headers": { "Authorization": "Bearer hf_REPLACE_WITH_KEY" },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

For other clients (Claude Code, Claude Desktop, Cursor, VS Code, Windsurf, OpenAI Agents SDK, LangChain), use the matching snippet in README.md. The key goes in the same `Authorization` header in every client.

## Step 3: Verify

Call `list_files`. A new account returns `[]`.

If you get `401 {"error":"API key required"}`, check these:

- the header is missing or misspelled
- `Bearer ` (with the space) is missing before the key
- the server was not restarted after you edited the config

## Step 4: First use

1. `save_file` with `{"name":"hello.txt","mime":"text/plain","content_base64":"aGVsbG8="}`. Note the returned `id`.
2. `create_share_link` with `{"file_id":"<id>","audience":"anyone_with_link","expires_in_hours":1,"max_opens":1}`.
3. Fetch the returned `url` with a plain GET. It downloads `hello.txt`.

## Notes

- Free accounts: 100 MB total, 50 files, 10 MB per file, 200 opens per day.
- Executables, scripts, HTML and archives are refused.
- Store the key like a password. Never put it in a share link, a file name, or a public repository.
