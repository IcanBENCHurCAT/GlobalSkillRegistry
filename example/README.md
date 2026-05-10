# Skill Registry Example Sandbox

This directory is designed as a playground for you to experiment with discovering, installing, updating, and removing skills using the Global MCP Skill Registry.

## Files Provided
*   **`remote_skills.yaml`**: A sample configuration file containing a dummy repository reference.
*   **`sample-repo/`**: A mock repository directory that follows the Agent Skills specification. It contains a `hello-world` skill with the required `SKILL.md` file and frontmatter.

## Things to Try

1.  **Test Local Directory Detection:**
    Try copying the `hello-world` skill to your `.agents/skills` directory and see if the MCP server detects it as "INSTALLED":
    ```bash
    mkdir -p ../.agents/skills/hello-world
    cp sample-repo/hello-world/SKILL.md ../.agents/skills/hello-world/
    ```

2.  **Manifest Updates:**
    Edit the `remote_skills.yaml` file to add new repository strings or specific Markdown URLs, and observe how the output of `discover_remote_skills` changes (note: the dummy repos will show as UNSUPPORTED or throw HTTP errors unless you use real GitHub paths).

3.  **Simulate Third-Party Tools:**
    Since the MCP server now delegates bulk fetching to tools like `gh skill install`, you can simulate an installation by creating a matching directory and `SKILL.md` file in `.agents/skills`.

Enjoy testing your agent capabilities!
