import os
import json
import yaml
import httpx
from pathlib import Path
from typing import List, Dict, Any
from mcp.server.fastmcp import FastMCP

# Initialize the FastMCP Server
mcp = FastMCP("GlobalSkillRegistry")

# Environment Variables Configuration
CONFIG_PATH = os.getenv("SKILL_REGISTRY_YAML", "remote_skills.yaml")
LOCAL_SKILLS_DIR = os.getenv("LOCAL_SKILLS_DIR", "./local_skills")

def ensure_local_dir():
    """Ensure local skills directory exists."""
    Path(LOCAL_SKILLS_DIR).mkdir(parents=True, exist_ok=True)

def parse_repo_string(repo_str: str) -> dict:
    """
    Parses strings like 'org/repo/path/to/skill.md@v1.0' into components.
    """
    parts = repo_str.split('@')
    path_part = parts[0]
    version = parts[1] if len(parts) > 1 else 'main'

    path_segments = path_part.split('/')
    org = path_segments[0]
    repo = path_segments[1]
    subpath = '/'.join(path_segments[2:]) if len(path_segments) > 2 else None

    return {
        "org": org,
        "repo": repo,
        "subpath": subpath,
        "version": version,
        "raw_base_url": f"https://raw.githubusercontent.com/{org}/{repo}/{version}"
    }

def get_installed_skills() -> List[str]:
    """Returns a list of markdown filenames currently in the local skills directory."""
    ensure_local_dir()
    return [f.name for f in Path(LOCAL_SKILLS_DIR).iterdir() if f.is_file() and f.suffix == '.md']

@mcp.tool()
async def discover_remote_skills() -> str:
    """
    Retrieves the catalog of available remote Markdown skills from the global repository list.
    Use this tool to see what skills can be installed on-demand.
    It returns the skill names, descriptions, and whether they are already installed locally.
    """
    if not os.path.exists(CONFIG_PATH):
        return json.dumps({"error": f"Skill registry configuration YAML not found at {CONFIG_PATH}."})

    with open(CONFIG_PATH, 'r') as file:
        try:
            config = yaml.safe_load(file) or {}
        except yaml.YAMLError as e:
            return json.dumps({"error": f"Failed to parse YAML: {e}"})

    repos = config.get('repositories', [])
    installed = get_installed_skills()
    catalog = []

    async with httpx.AsyncClient() as client:
        for repo_str in repos:
            parsed = parse_repo_string(repo_str)

            # If it points to a specific .md file, it's a standalone skill
            if parsed["subpath"] and parsed["subpath"].endswith('.md'):
                skill_name = parsed["subpath"].split('/')[-1]
                status = "INSTALLED" if skill_name in installed else "AVAILABLE"
                catalog.append({
                    "skill_name": skill_name,
                    "repo_source": repo_str,
                    "type": "standalone",
                    "status": status
                })
                continue

            # Otherwise, fetch the skill_index.json at the repo root
            index_url = f"{parsed['raw_base_url']}/skill_index.json"
            try:
                response = await client.get(index_url)
                if response.status_code == 200:
                    index_data = response.json()
                    for skill in index_data.get('skills', []):
                        # Prefix skill name to prevent naming collisions
                        namespaced_skill = f"{parsed['repo']}_{skill['name']}"
                        status = "INSTALLED" if f"{namespaced_skill}.md" in installed else "AVAILABLE"

                        catalog.append({
                            "skill_name": namespaced_skill,
                            "original_name": skill['name'],
                            "description": skill.get('description', 'No description'),
                            "repo_source": repo_str,
                            "file_path": skill['path'],
                            "status": status
                        })
            except Exception as e:
                catalog.append({"error": f"Failed to fetch index for {repo_str}: {str(e)}"})

    return json.dumps(catalog, indent=2)

@mcp.tool()
async def install_remote_skill(repo_source: str, file_path: str, save_as: str) -> str:
    """
    Downloads and installs a specific Markdown skill from the remote catalog to the local skills directory.
    Once installed, it will be automatically loaded as a local tool in subsequent agent loops.

    Args:
        repo_source: The original string from the catalog (e.g., 'org/repo@v1.0').
        file_path: The path to the .md file in the remote repo (e.g., 'skills/search.md').
        save_as: The namespaced filename to save it as locally (MUST end in .md, e.g., 'global_repo_search.md').
    """
    if not save_as.endswith('.md'):
        return "Error: save_as parameter must end with .md"

    ensure_local_dir()
    parsed = parse_repo_string(repo_source)

    # If subpath is provided in repo_source, it overrides the file_path argument
    target_path = parsed["subpath"] if parsed["subpath"] else file_path
    download_url = f"{parsed['raw_base_url']}/{target_path}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(download_url)
            if response.status_code == 200:
                local_file = Path(LOCAL_SKILLS_DIR) / save_as
                with open(local_file, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                return f"Success: Skill downloaded and installed to {local_file}. It is now available as a local skill."
            else:
                return f"Error: Failed to download skill. HTTP Status {response.status_code}"
        except Exception as e:
            return f"Error: Could not complete installation. {str(e)}"

if __name__ == "__main__":
    # Start the server via stdio transport
    mcp.run()
