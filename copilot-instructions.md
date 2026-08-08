# Global MCP Skill Registry: Context & Guardrails

This document provides context on the design, architectural goals, and explicit guardrails for developing and modifying the Global MCP Skill Registry server.

## Architectural Purpose

The project architecture follows a **'Package Manager'** pattern for an MCP Skill Registry. It explicitly avoids acting as a monolithic, dynamic tool registry that intercepts every agent action.

Instead, the MCP server acts purely as a background discovery and installation mechanism for semantic markdown (`.md`) skills. It reads a declarative manifest (`remote_skills.yaml`) and ensures that the local execution environment has the specified tools downloaded and available.

## Strict Guardrails & Core Rules

When contributing to this project, adhere to the following rules:

1.  **Single Source of Truth:** The local filesystem (specifically the `.agents/skills` directory) is the single source of truth for tracking installed skills. Implementations of complex databases, Redis caches, or TTLs for tracking skill state are explicitly forbidden.
2.  **Separation of Concerns:** Maintain a strict boundary between fetching and executing. The MCP server *only* handles discovery, fetching, and background installation of skills. The core Agent Framework exclusively handles reading, parsing, and acting on the installed `.md` files. The MCP Server should never read the contents of a skill to execute its logic.
3.  **No Remote Execution:** The MCP server must never execute remote scripts. It strictly adheres to a 'fetch-and-save' paradigm for remote `.md` definitions.
4.  **No Custom Indexing:** Parsing of custom `skill_index.json` files for bulk repository discovery is deprecated. For repository-wide remote skill discovery and management, the project relies on native integration with third-party CLI tools (e.g., `gh skill install`, `npx skills add`).

## Startup Synchronization Pattern

The core mechanism for updating skills is the **Background Startup Sync**:
*   The MCP server utilizes a local `remote_skills.yaml` configuration file to determine which global skill repositories to track.
*   On startup, an asynchronous lifespan hook (`FastMCP` lifespan) parses the manifest.
*   For full repository entries, it launches a background subprocess using `gh skill install -d .agents/skills <repo>@<version>`. This ensures the local file system is always synced to the requested versions before the agent begins complex tasks.
*   Because standard package management CLI tools handle version resolution and overwriting, checking `.agents/skills` into git does not prevent the MCP server from updating skills to new versions defined in the YAML file on the next run.

## Agent Tooling Philosophy

Instead of providing dynamic tools to search the internet or install items interactively during a conversation, the MCP server provides minimal tooling designed to inform the agent of the background architecture.

The primary tool is `get_skill_sync_status`, which tells the agent that the MCP server has populated its environment and instructs the agent to rely on native directory scanning to find available capabilities.

## Standards Compliance

The project complies with the **Agent Skills specification**. Compatible skills must:
*   Exist within a directory matching the skill's name.
*   Contain a `SKILL.md` file in that directory.
*   Include required YAML frontmatter fields (`name`, `description`).
*   Utilize standard tooling for dependencies (e.g., `uv` for python dependencies).
