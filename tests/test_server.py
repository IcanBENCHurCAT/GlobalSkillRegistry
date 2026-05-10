import os
import json
import pytest
from unittest.mock import patch, AsyncMock, mock_open
from src.skill_registry.server import parse_repo_string, discover_remote_skills, install_remote_skill

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

@patch("src.skill_registry.server.httpx.AsyncClient.get")
@patch("src.skill_registry.server.get_installed_skills")
@patch("builtins.open", new_callable=mock_open, read_data="repositories:\n  - org/repo@v1\n  - org/repo2/skills/stand.md@main")
@patch("os.path.exists")
@pytest.mark.asyncio
async def test_discover_remote_skills(mock_exists, mock_file, mock_installed, mock_get):
    mock_exists.return_value = True
    mock_installed.return_value = ["repo_known_skill.md"] # One skill is already installed

    result_str = await discover_remote_skills()
    result = json.loads(result_str)

    assert len(result) == 2 # 1 unsupported index, 1 standalone

    # Check unsupported message
    assert result[0]["repo_source"] == "org/repo@v1"
    assert result[0]["status"] == "UNSUPPORTED"
    assert "Bulk discovery via skill_index.json is no longer supported" in result[0]["message"]
    assert "gh skill search --owner org" in result[0]["message"]

    # Check standalone parsing
    assert result[1]["skill_name"] == "stand.md"
    assert result[1]["type"] == "standalone"

@patch("src.skill_registry.server.httpx.AsyncClient.get")
@patch("builtins.open", new_callable=mock_open)
@patch("pathlib.Path.mkdir")
@pytest.mark.asyncio
async def test_install_remote_skill(mock_mkdir, mock_file, mock_get):
    # Mock successful markdown download
    from unittest.mock import MagicMock
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "---\nname: test\n---\n# Test Skill"
    mock_get.return_value = mock_response

    result = await install_remote_skill(
        repo_source="org/repo@v1",
        file_path="skills/test.md",
        save_as="repo_test.md"
    )

    assert "Success" in result
    mock_file.assert_called_once()
    mock_get.assert_called_once_with("https://raw.githubusercontent.com/org/repo/v1/skills/test.md")

@pytest.mark.asyncio
async def test_install_remote_skill_bad_extension():
    result = await install_remote_skill("org/repo@v1", "skills/test.md", "repo_test.txt")
    assert "Error: save_as parameter must end with .md" in result
