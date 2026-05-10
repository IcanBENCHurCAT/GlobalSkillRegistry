import os
import json
import pytest
from unittest.mock import patch, AsyncMock, mock_open
from src.skill_registry.server import parse_repo_string, get_skill_sync_status, sync_remote_skills

# --- Fixtures and Mocks ---
@pytest.fixture(autouse=True)
def setup_env():
    """Mock environment variables before each test."""
    os.environ["SKILL_REGISTRY_YAML"] = "dummy_skills.yaml"
    os.environ["LOCAL_SKILLS_DIR"] = "./test_local_skills"
    yield
    # Cleanup env
    del os.environ["SKILL_REGISTRY_YAML"]
    del os.environ["LOCAL_SKILLS_DIR"]

# --- Tests ---
def test_parse_repo_string():
    # Test standard root index mapping
    parsed = parse_repo_string("my-org/my-repo@v1.0.0")
    assert parsed["org"] == "my-org"
    assert parsed["repo"] == "my-repo"
    assert parsed["subpath"] is None
    assert parsed["version"] == "v1.0.0"
    assert parsed["raw_base_url"] == "https://raw.githubusercontent.com/my-org/my-repo/v1.0.0"

    # Test standalone file mapping
    parsed2 = parse_repo_string("open-source/cool-skills/skills/search.md@main")
    assert parsed2["subpath"] == "skills/search.md"
    assert parsed2["version"] == "main"

@patch("src.skill_registry.server.asyncio.create_subprocess_shell")
@patch("src.skill_registry.server.httpx.AsyncClient.get")
@patch("builtins.open", new_callable=mock_open, read_data="repositories:\n  - org/repo@v1\n  - org/repo2/skills/stand.md@main")
@patch("os.path.exists")
@pytest.mark.asyncio
async def test_sync_remote_skills(mock_exists, mock_file, mock_get, mock_subprocess):
    mock_exists.return_value = True

    # Mock subprocess
    mock_process = AsyncMock()
    mock_subprocess.return_value = mock_process

    # Mock HTTP response
    from unittest.mock import MagicMock
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "---\nname: stand\n---\n"
    mock_get.return_value = mock_response

    await sync_remote_skills()

    # The actual call arguments check:
    args, kwargs = mock_subprocess.call_args
    from src.skill_registry.server import LOCAL_SKILLS_DIR
    assert f"gh skill install -d '{LOCAL_SKILLS_DIR}' org/repo@v1" in args[0]

    # Check HTTP was called for standalone
    mock_get.assert_called_once_with("https://raw.githubusercontent.com/org/repo2/main/skills/stand.md")

@pytest.mark.asyncio
async def test_get_skill_sync_status():
    result = await get_skill_sync_status()
    assert "the mcp server has added a bunch of skills" in result
