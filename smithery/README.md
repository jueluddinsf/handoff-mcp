# Smithery

No `smithery.yaml` is needed. That file configures Smithery builds/deploys, and Handoff is already hosted, so it is published to Smithery **by URL**.

- Form (logged in): https://smithery.ai/new
  - Namespace: `jueluddinsf`
  - Server ID: `handoff`
  - MCP Server URL: `https://hand-off.space/mcp`
- CLI alternative, after `smithery login`:

  ```bash
  smithery mcp publish "https://hand-off.space/mcp" \
    -n @jueluddinsf/handoff --config-schema "$(cat smithery/config-schema.json)"
  ```

## Why the config schema looks this way

Smithery reserves the `authorization` header for its own OAuth, so `x-from` cannot be `authorization` (per Smithery's Session Configuration docs). The schema reads the key from the `x-handoff-api-key` header and forwards it as `Authorization` (`x-to`).

Smithery forwards the **raw value** with no `Bearer ` prefix. Handoff must therefore accept `Authorization: hf_…` as well as `Authorization: Bearer hf_…`, or accept an `X-Handoff-Api-Key` header directly.
