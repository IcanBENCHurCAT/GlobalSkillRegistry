import os
import json
import yaml
import httpx
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Dict, Any
from mcp.server.fastmcp import FastMCP

# Environment Variables Configuration
CONFIG_PATH = os.getenv("SKILL_REGISTRY_YAML", "remote_skills.yaml")
LOCAL_SKILLS_DIR = os.getenv("LOCAL_SKILLS_DIR", ".agents/skills")

async def sync_remote_skills():
    if not os.path.exists(CONFIG_PATH):
        print(f"No config found at {CONFIG_PATH}, skipping background sync.")
        return
    with open(CONFIG_PATH, 'r') as file:
        try:
            config = yaml.safe_load(file) or {}
        except yaml.YAMLError as e:
            print(f"Failed to parse {CONFIG_PATH}: {e}")
            return

    repos = config.get('repositories', [])
    for repo_str in repos:
        parsed = parse_repo_string(repo_str)
        # Handle full repos vs standalone skills differently
        if parsed["subpath"] and parsed["subpath"].endswith('.md'):
            # Standalone skill download
            download_url = f"{parsed['raw_base_url']}/{parsed['subpath']}"
            skill_name = parsed["subpath"].split('/')[-1]
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(download_url)
                    if response.status_code == 200:
                        local_file = Path(LOCAL_SKILLS_DIR) / skill_name
                        with open(local_file, 'w', encoding='utf-8') as f:
                            f.write(response.text)
            except Exception as e:
                print(f"Failed to sync {repo_str}: {e}")
        else:
            # Full repo using gh skill install
            # Note: gh skill install currently takes github/repo format
            target = f"{parsed['org']}/{parsed['repo']}"
            if parsed['version'] != 'main':
                target += f"@{parsed['version']}"
            cmd = f"gh skill install -d '{LOCAL_SKILLS_DIR}' {target}"
            print(f"Executing background sync: {cmd}")
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()

@asynccontextmanager
async def lifespan(server: FastMCP):
    ensure_local_dir()
    # Start background sync task
    asyncio.create_task(sync_remote_skills())
    yield

# Initialize the FastMCP Server
mcp = FastMCP("GlobalSkillRegistry", lifespan=lifespan)

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

@mcp.tool()
async def get_skill_sync_status() -> str:
    """
    Retrieves the status of the background skill sync.
    """
    return "the mcp server has added a bunch of skills to your environment and you need to either look through them yourself or ask me about them"

if __name__ == "__main__":
    # Start the server via stdio transport
    mcp.run()
