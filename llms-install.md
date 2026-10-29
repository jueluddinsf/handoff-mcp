# Installing Handoff (instructions for AI agents)

Handoff is a **hosted remote MCP server**. There is nothing to clone, build, or run locally.

- MCP endpoint: `https://hand-off.space/mcp`
- Transport: Streamable HTTP. It is stateless and accepts `POST` only. Send `Accept: application/json, text/event-stream`.
- Auth: **none needed to connect** or to call `share_file`. Later calls use `Authorization: Bearer <api_key>`.

## Step 1: Add the server with no auth

**Cline** (`cline_mcp_settings.json`). Keep `"type": "streamableHttp"`, because Cline otherwise falls back to SSE:

```json
{
  "mcpServers": {
    "handoff": {
      "type": "streamableHttp",
      "url": "https://hand-off.space/mcp",
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

**Claude Code:** `claude mcp add --transport http handoff https://hand-off.space/mcp`

For other clients (Claude Desktop, Cursor, VS Code, Windsurf, Hermes, OpenClaw, OpenAI Agents SDK, LangChain), use the matching snippet in README.md and leave the header out.

## Step 2: First use, in one call

Call `share_file` with:

```json
{"name": "hello.md", "content_text": "# hello"}
```

The result includes `url` (the download link, which expires in 7 days by default), `grant_id`, `file_id` and `api_key`, which is **shown once** because this call created your account. Fetch the `url` with a plain GET, and it downloads `hello.md`.

Without MCP, the same call over REST is `curl -s --data-binary @hello.md "https://hand-off.space/v1/share?name=hello.md&format=url"`. The first line is the URL. The second line is `api_key: hf_…`.

## Step 3: Save the key

Store `api_key` right away. It cannot be recovered. Then do one of these:

- add `"headers": { "Authorization": "Bearer hf_REPLACE_WITH_KEY" }` to the config above and restart the server, or
- if your client cannot set headers, pass `"api_key": "hf_…"` as an argument on each tool call.

You need the key to revoke a link, check status, read the access log, or keep later files in the same account. A later `share_file` without a key creates a new, separate account.

If you want a key before sharing anything, call the `signup` tool, or `POST https://hand-off.space/v1/signup` with `{}`. You can pass `{"agent_id":"your-name"}` (it must match `^[a-zA-Z0-9_-]{1,80}$`) if other agents will share files with you by name.

## Step 4: Verify

With the key set, call `list_files`. It lists the file from Step 2.

If you get `API key required`, check these:

- the header is missing or misspelled
- `Bearer ` (with the space) is missing before the key
- the server was not restarted after you edited the config

## More control

The server has 14 tools: share_file, signup, save_file, list_files, create_share_link, get_share_status, approve_share, deny_share, revoke_share, get_access_log, fetch_shared_file, delete_file, list_shares, update_share.

- `share_file` options: `expires_in_hours`, `max_opens`, `audience` (`anyone_with_link` or `agent`), `audience_value`, `requires_approval`, `mime`, `ref`.
- To share one stored file several times with different rules, call `save_file` (`name`, `content_text` or `content_base64`) and then `create_share_link` for each link. `create_share_link` links expire in 7 days unless you set `expires_in_hours`; change it later with `update_share`.

## Notes

- Free accounts: 100 MB total, 50 files, 10 MB per file, 200 opens per day.
- HTML, markdown, code and zip files are allowed. Executables are refused.
- Link previews (Slack, X, Discord…) don't consume opens. A link that used up its `max_opens` returns `410`.
- Store the key like a password. Never put it in a share link, a file name, or a public repository.
