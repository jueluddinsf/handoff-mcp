# Contributing

This repository holds the **docs, examples and registry metadata** for the hosted Handoff MCP server. The server code is not here.

## Helpful contributions

- **Client configs and recipes.** Has a snippet stopped working, or is your client missing? Open a PR against `README.md` or `examples/`. Tell us the client version you tested with.
- **Bug reports.** Use the *Bug report* issue template. Include the tool name, the HTTP status, and the `error` string. **Never paste an API key or a share URL.**
- **Feature requests.** Tell us what your agent was trying to hand off, and to whom.

## Ground rules

- Keep examples copy-pasteable, and use `YOUR_HANDOFF_API_KEY` or an environment variable for the key.
- Keep `server.json` valid against the official MCP Registry schema. Run `mcp-publisher validate`.
- Use the same `version` across `server.json` and `lhm.plugin.json`. Bump it whenever listing metadata changes.

## Security

Do not open a public issue for a vulnerability. Use GitHub's **Report a vulnerability** button (private advisory) on this repository instead.
