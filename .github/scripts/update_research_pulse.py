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
START = "<!-- RESEARCH-NOW:START -->"
END = "<!-- RESEARCH-NOW:END -->"

DISPLAY = {
    "VELE-PowerGrid-Reproducibility": ("⚡", "VELE Power-Grid Vulnerability Screening"),
    "EGFR-Graph-QSAR-Reproducibility": ("🧬", "EGFR Graph QSAR — Representation Limits"),
    "applicability-gated-molecular-ai": ("🧠", "Applicability-Gated Molecular AI"),
    "PAPER-JCMM-reproducibility": ("📐", "Calibration Transfer of Conformal Prediction"),
}


def get_repos():
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": f"{USER}-profile-status",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(API, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def display_name(repo_name: str) -> tuple[str, str]:
    if repo_name in DISPLAY:
        return DISPLAY[repo_name]
    name = repo_name.replace("-Reproducibility", "").replace("-", " ")
    return "🔬", name


def build_block(research: list[dict]) -> str:
    count = len(research)
    if research:
        latest = research[0]
        pushed = dt.datetime.fromisoformat(latest["pushed_at"].replace("Z", "+00:00"))
        date_text = pushed.strftime("%d %b %Y")
        icon, title = display_name(latest["name"])
        url = latest["html_url"]
        recent = (
            "### Recently active\n"
            f"{icon} **[{title}]({url})**  \n"
            f"Latest public push · **{date_text}**"
        )
    else:
        recent = "### Recently active\nNo public research repository is currently available."

    return f"""{START}
## ◉ Research now

> **{count} public research projects** · **4 research tracks** · **Open reproducibility**

{recent}

**Research arc**  
**λ Spectral Graph Theory** → **⌘ Network Resilience** → **⬡ Molecular Graphs & QSPR/QSAR** → **◎ Reliable Scientific AI**
{END}"""


def main():
    repos = get_repos()
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
        raise RuntimeError("Research Now markers were not found in README.md")

    updated = pattern.sub(build_block(research), text, count=1)
    if updated != text:
        README.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    main()
