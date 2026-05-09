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
*   `LOCAL_SKILLS_DIR` (default: `./local_skills`): The folder where downloaded `.md` skills will be saved for the agent to load.

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
        "LOCAL_SKILLS_DIR": "/absolute/path/to/local_skills"
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

## 📜 How it works (For the Agent)

When the agent connects, it gets two tools:
*   `discover_remote_skills`: Returns a JSON catalog of available skills, parsing `skill_index.json` from the root of defined repositories. It checks `LOCAL_SKILLS_DIR` to report if a skill is `AVAILABLE` or already `INSTALLED`.
*   `install_remote_skill`: Downloads the target markdown file and writes it to the local skills directory using a namespaced filename to avoid collisions.
