# Global MCP Skill Registry Server

A Model Context Protocol (MCP) server that acts as an automated package manager for AI Agent Skills. It manages your agent's skill environment by automatically syncing remote Markdown (`.md`) skill definitions from designated Git repositories directly into your local execution environment upon startup.

## 🚀 Architecture Concept

Instead of forcing the agent to dynamically search for and install tools one by one during a conversation, this server operates on a declarative "Package Manager" manifest model.

On server startup, it reads your `remote_skills.yaml` manifest and launches background synchronization tasks using standard third-party CLI tools (like `gh skill install`). The MCP server strictly handles the discovery and local installation of these semantic markdown skills. Your agent's core framework then natively scans the local filesystem to pick up the tools and interact with them.

## 📦 Installation

Clone the repository and install dependencies:
```bash
pip install -r requirements.txt
```

Configure your environment variables:
*   `SKILL_REGISTRY_YAML` (default: `./remote_skills.yaml`): The path to the file listing your allowed remote skill repositories.
*   `LOCAL_SKILLS_DIR` (default: `.agents/skills`): The folder where downloaded `.md` skills will be saved for the agent to load.

Configure `remote_skills.yaml`:
```yaml
repositories:
  - my-org/core-skills-repo@v1.0.0
  - open-source/cool-agent-skills/skills/advanced_search.md@v1.2.3
```

## 🛠️ Usage

### Running the Server

Run the server using the `fastmcp` CLI (installed alongside the `mcp` SDK):
```bash
fastmcp run src/skill_registry/server.py
```
Note: FastMCP automatically handles stdio transport for agent connections.

### Integration with Claude Desktop / AI Agents

To add this to an MCP client like Claude Desktop, add the following to your `mcp_config.json`:
```json
{
  "mcpServers": {
    "skill-registry": {
      "command": "fastmcp",
      "args": ["run", "/absolute/path/to/src/skill_registry/server.py"],
      "env": {
        "SKILL_REGISTRY_YAML": "/absolute/path/to/remote_skills.yaml",
        "LOCAL_SKILLS_DIR": "/absolute/path/to/.agents/skills"
      }
    }
  }
}
```

## 🧪 Running Tests

This project includes an asynchronous test suite using `pytest`.
```bash
pytest tests/
```


## 📦 Skill Management Tools Integration

This project relies on standardized skill-management tools for robust bulk installation and updates from full repositories. The MCP server will automatically execute these CLI commands for you in the background based on your manifest.

You can also browse and install skills manually/interactively using the GitHub CLI or NPM:

```bash
# Using GitHub CLI (v2.90.0+)
# Browse skills in a repository and install them interactively
gh skill install github/awesome-copilot

# Or install a specific skill directly
gh skill install github/awesome-copilot documentation-writer

# Install a specific version using @tag
gh skill install github/awesome-copilot documentation-writer@v1.2.0

# Using NPX
npx skills add https://github.com/anthropics/skills --skill skill-creator
```

### Agent Skills Specification (Custom Repository Support)

For a repository to be compatible with tools like `gh skill install` or your agent's discovery mechanism, it must follow the **Agent Skills specification**:

1.  **SKILL.md File**: Each skill must contain a `SKILL.md` file in its own directory.
2.  **Frontmatter Metadata**: The `SKILL.md` file must include required YAML frontmatter fields:
    *   `name`: A unique identifier for the skill.
    *   `description`: Used by AI agents to determine when to trigger the skill.
3.  **Directory Naming**: The directory name must exactly match the skill name defined in the frontmatter.
4.  **Dependencies**: If the skill requires specific software, it typically uses the `uv` Python package manager to handle automated installation of dependencies.

**Prerequisites:**
*   The GitHub CLI v2.90.0+ is required for the `gh skill` commands.
*   A compatible AI agent is necessary (e.g., Claude Code, GitHub Copilot, or Gemini CLI).
*   If the skills include executable scripts, Python 3.11+ may be needed.
*   Use `gh skills list` to generate an index of your available tools.

## 📜 How it works (For the Agent)

Because the MCP server handles fetching and updating skills automatically in the background on startup, the local filesystem (`.agents/skills`) is the single source of truth for the active skill state.

When the agent connects to the MCP server, it is provided with a single tool:
*   `get_skill_sync_status`: Returns a message informing the agent that skills are synchronized in the background to the local `.agents/skills` directory, and that the agent should rely on its own native filesystem scanning capabilities to discover and utilize the available tools.