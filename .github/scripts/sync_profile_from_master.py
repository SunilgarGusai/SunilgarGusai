from __future__ import annotations

import json
import os
import re
import urllib.request
from pathlib import Path

README = Path("README.md")
MASTER_URL = os.environ.get(
    "ACADEMIC_PROFILE_URL",
    "https://raw.githubusercontent.com/SunilgarGusai/sunilgar-portfolio/main/data/academic-profile.json",
)

ROLE_START = "<!-- ACADEMIC_SYNC:PROFILE_ROLE:START -->"
ROLE_END = "<!-- ACADEMIC_SYNC:PROFILE_ROLE:END -->"
PUB_START = "<!-- ACADEMIC_SYNC:PROFILE_PUBLICATIONS:START -->"
PUB_END = "<!-- ACADEMIC_SYNC:PROFILE_PUBLICATIONS:END -->"
TEACH_START = "<!-- ACADEMIC_SYNC:PROFILE_TEACHING_ROLE:START -->"
TEACH_END = "<!-- ACADEMIC_SYNC:PROFILE_TEACHING_ROLE:END -->"


def fetch_master() -> dict:
    request = urllib.request.Request(
        MASTER_URL,
        headers={"User-Agent": "SunilgarGusai-academic-identity-sync"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def replace_marked(text: str, start: str, end: str, body: str) -> str:
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    if not pattern.search(text):
        raise RuntimeError(f"Missing sync markers: {start} / {end}")
    return pattern.sub(f"{start}\n{body.rstrip()}\n{end}", text, count=1)


def validate(data: dict, readme: str) -> None:
    if data.get("schema_version") != 1:
        raise RuntimeError("Unsupported academic-profile schema")

    for item in data.get("scholarship", []):
        if item.get("visibility", {}).get("github_profile") and item.get("status") not in {"published", "accepted"}:
            raise RuntimeError(
                f"Unsafe public profile status for {item.get('id')}: {item.get('status')}"
            )

    for project in data.get("research_programmes", []):
        if project.get("showcase", {}).get("github_profile"):
            repo = project["repository"]
            if f"github.com/SunilgarGusai/{repo}" not in readme:
                raise RuntimeError(
                    f"{repo}: master requests GitHub-profile showcase but no curated visual card is present"
                )


def render_role(data: dict) -> str:
    ident = data["public_identity"]
    return (
        '<p align="center">\n'
        f'  <b>{ident["primary_title"]} · {ident["secondary_title"]} · {ident["profile_suffix"]}</b>\n'
        '</p>'
    )


def render_publications(data: dict) -> str:
    items = [x for x in data["scholarship"] if x["visibility"]["github_profile"]]
    lines = ["## Published & accepted scholarship", ""]
    tick = chr(96)

    for item in items:
        lines.append(f'### {item["title"]}')
        lines.append(item["profile_summary_line"] + "  ")

        if item.get("doi") and item.get("show_doi", {}).get("github_profile", True):
            doi = item["doi"]
            badge = doi.replace("/", "%2F").replace("-", "--")
            lines.append(
                f'[![DOI](https://img.shields.io/badge/DOI-{badge}-3B82F6?style=flat-square)]'
                f'(https://doi.org/{doi})  '
            )

        tags = item.get("tags", [])
        if tags:
            lines.append(" · ".join(f"{tick}{tag.lower()}{tick}" for tag in tags))
        lines.append("")

    return "\n".join(lines).rstrip()


def render_teaching_role(data: dict) -> str:
    ident = data["public_identity"]
    roles = {x["id"]: x for x in data["roles"]}
    labels = []

    for role_id in ident.get("profile_leadership_role_ids", []):
        role = roles.get(role_id)
        if role and role.get("visibility", {}).get("github_profile"):
            labels.append(role.get("profile_sentence_title", role["title"]))

    if not labels:
        return "I contribute to teaching, curriculum work, student mentoring, research collaboration and institutional service."

    lead = labels[0] if len(labels) == 1 else ", ".join(labels[:-1]) + " and " + labels[-1]
    return f'I serve as {lead}, {ident["profile_teaching_tail"]}'


def main() -> None:
    data = fetch_master()
    text = README.read_text(encoding="utf-8")
    validate(data, text)

    updated = replace_marked(text, ROLE_START, ROLE_END, render_role(data))
    updated = replace_marked(updated, PUB_START, PUB_END, render_publications(data))
    updated = replace_marked(updated, TEACH_START, TEACH_END, render_teaching_role(data))

    if updated != text:
        README.write_text(updated, encoding="utf-8")
        print(f'Profile synchronized to academic identity version {data["identity_version"]}.')
    else:
        print(f'Profile already matches academic identity version {data["identity_version"]}.')


if __name__ == "__main__":
    main()
