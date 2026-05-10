# Global MCP Skill Registry Server

A Model Context Protocol (MCP) server that acts as a package manager for AI Agent Skills. It allows your agent to dynamically discover, fetch, and install remote Markdown (`.md`) skill definitions from designated Git repositories directly into its local execution environment.

## 🚀 Architecture Concept

Instead of loading hundreds of tools dynamically, this server follows a Package Manager model. The agent uses this MCP server to browse a catalog (`discover_remote_skills`). When it needs a skill, it installs it locally (`install_remote_skill`). Your agent's core framework then naturally picks up the `.md` file from the local directory.

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

While this MCP server allows on-demand fetching of specific `.md` files, we highly recommend integrating with standardized skill-management tools for bulk installation and updates from full repositories.

You can browse and install skills interactively using the GitHub CLI or NPM:

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

When the agent connects, it gets two tools:
*   `discover_remote_skills`: Returns a JSON catalog of available remote Markdown skills. It checks `LOCAL_SKILLS_DIR` to report if a skill is `AVAILABLE` or already `INSTALLED`.
    *Note: Bulk repository discovery using `skill_index.json` is deprecated. Please use dedicated package managers like `gh skill` or `npx skills` for full-repository discovery.*
*   `install_remote_skill`: Downloads the target markdown file and writes it to the local skills directory using a namespaced filename to avoid collisions.
