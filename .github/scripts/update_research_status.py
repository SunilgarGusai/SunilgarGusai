from __future__ import annotations

import datetime as dt
import json
import os
import re
import urllib.request
from pathlib import Path

USER = "SunilgarGusai"
EXCLUDED = {"SunilgarGusai", "sunilgar-portfolio"}
API = f"https://api.github.com/users/{USER}/repos?per_page=100&sort=pushed"
README = Path("README.md")
MASTER_URL = "https://raw.githubusercontent.com/SunilgarGusai/sunilgar-portfolio/main/data/academic-profile.json"
START = "<!-- OBSERVATORY:START -->"
END = "<!-- OBSERVATORY:END -->"


def get_repos():
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": f"{USER}-research-observatory",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(API, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def get_catalog() -> dict[str, dict]:
    request = urllib.request.Request(
        MASTER_URL,
        headers={"User-Agent": f"{USER}-research-observatory-master"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    return {item["repository"]: item for item in payload.get("research_programmes", [])}


def names(repo_name: str, catalog: dict[str, dict]) -> tuple[str, str, str]:
    item = catalog.get(repo_name)
    if item:
        return item.get("icon", "🔬"), item["title"], item.get("short_title", item["title"])
    clean = repo_name.replace("-Reproducibility", "").replace("-", " ")
    return "🔬", clean, clean


def date_for(repo: dict) -> dt.datetime:
    return dt.datetime.fromisoformat(repo["pushed_at"].replace("Z", "+00:00"))


def build_block(research: list[dict], catalog: dict[str, dict]) -> str:
    count = len(research)
    if not research:
        return f"""{START}
## ◉ Current research signal

> **0 public research programmes** · **4 connected research directions** · **Open reproducibility**

No public research repository is currently available.
{END}"""

    latest = research[0]
    icon, title, _ = names(latest["name"], catalog)
    latest_date = date_for(latest).strftime("%d %b %Y")

    trail_parts = []
    for repo in research[:4]:
        _, _, short = names(repo["name"], catalog)
        date_text = date_for(repo).strftime("%d %b")
        trail_parts.append(f"`{date_text}` **{short}**")
    trail = " → ".join(trail_parts)

    return f"""{START}
## ◉ Current research signal

> **{count} public research programmes** · **4 connected research directions** · **Open reproducibility**

### {icon} [{title}]({latest['html_url']})
**Most recently active public research project** · latest push **{latest_date}**

**Recent research trail**  
{trail}
{END}"""


def main():
    repos = get_repos()
    catalog = get_catalog()
    research = [
        repo
        for repo in repos
        if not repo.get("fork")
        and not repo.get("archived")
        and repo.get("name") not in EXCLUDED
    ]
    research.sort(key=lambda repo: repo.get("pushed_at") or "", reverse=True)

    text = README.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    if not pattern.search(text):
        raise RuntimeError("Research Observatory markers were not found in README.md")

    updated = pattern.sub(build_block(research, catalog), text, count=1)
    if updated != text:
        README.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    main()
