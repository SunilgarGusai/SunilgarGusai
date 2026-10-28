from __future__ import annotations

import json
from datetime import date
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
MEM_START = "<!-- ACADEMIC_SYNC:PROFILE_MEMBERSHIPS:START -->"
MEM_END = "<!-- ACADEMIC_SYNC:PROFILE_MEMBERSHIPS:END -->"


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
    """Write normal scholarly citations rather than machine-like status labels."""
    items = [x for x in data["scholarship"] if x["visibility"]["github_profile"]]
    lines = ["## Publications", ""]
    for item in items:
        title = item["title"]
        if item.get("doi") and item.get("show_doi", {}).get("github_profile", True):
            url = "https://doi.org/" + item["doi"]
        elif item.get("publication_url") and item.get("show_publication_url", {}).get("github_profile", True):
            url = item["publication_url"]
        else:
            url = None
        link = f"[{title}]({url})" if url else title
        detail = item.get("citation_detail", str(item["year"]))
        if item["status"] == "accepted":
            lines.append(f"- **{link}.** *{item['venue']}*. Accepted for publication.")
        else:
            scopus_link = (
                f" [Scopus record](https://www.scopus.com/record/display.uri?eid={item['scopus_eid']})."
                if item.get("scopus_eid")
                else ""
            )
            lines.append(f"- {link}. *{item['venue']}*, {detail}.{scopus_link}")
    lines += ["", "For additional publication details, please see my [academic CV](https://sunilgargusai.github.io/sunilgar-portfolio/assets/CV_DR_Sunilgar_L_Gusai.pdf)."]
    return "\n".join(lines).rstrip()


def render_teaching_role(data: dict) -> str:
    """Keep institutional responsibilities concise and first person."""
    ident = data["public_identity"]
    role_map = {x["id"]: x for x in data["roles"]}
    active = [role_map[role_id]["title"]
              for role_id in ident.get("profile_leadership_role_ids", [])
              if role_id in role_map and role_map[role_id].get("visibility", {}).get("github_profile")]
    if active:
        return ("At Marwadi University, I also serve as " +
                " and ".join(active) +
                ". These responsibilities complement my work in teaching, mentoring and research.")
    return "I contribute to teaching, student mentoring and academic research at Marwadi University."


def render_memberships(data: dict) -> str:
    """Publish only the professional organization and actual membership designation."""
    members = [m for m in data.get("professional_memberships", [])
               if m.get("visibility", {}).get("github_profile")]
    lines = ["## Professional memberships", ""]
    for m in members:
        if m.get("since"):
            since_date = date.fromisoformat(m["since"]).strftime("%d %B %Y").lstrip("0")
            period = f"since {since_date}"
        else:
            period = m["period"].replace(" -- ", "–").lower()
        lines.append(
            f'- **{m["organization"]} ({m["acronym"]})** — {m["designation"]} ({period}).'
        )
    return "\n".join(lines)


def main() -> None:
    data = fetch_master()
    text = README.read_text(encoding="utf-8")
    validate(data, text)

    updated = replace_marked(text, ROLE_START, ROLE_END, render_role(data))
    updated = replace_marked(updated, PUB_START, PUB_END, render_publications(data))
    updated = replace_marked(updated, TEACH_START, TEACH_END, render_teaching_role(data))
    updated = replace_marked(updated, MEM_START, MEM_END, render_memberships(data))

    if updated != text:
        README.write_text(updated, encoding="utf-8")
        print(f'Profile synchronized to academic identity version {data["identity_version"]}.')
    else:
        print(f'Profile already matches academic identity version {data["identity_version"]}.')


if __name__ == "__main__":
    main()
