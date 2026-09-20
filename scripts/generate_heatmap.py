"""
Fetches real GitHub contribution data via the GraphQL API and renders
an SVG heatmap where each cell fades in with a staggered delay
(a "reveal cell by cell" animation using native SVG <animate>, which
survives GitHub's sanitizer because it's served as a raw image file).

Env vars required:
  GH_USERNAME   - the GitHub username to fetch contributions for
  GH_TOKEN      - a token with at least `read:user` scope

Usage:
  GH_USERNAME=Lordshadow-afk GH_TOKEN=xxxx python scripts/generate_heatmap.py
"""

import os
import sys
import json
import urllib.request

USERNAME = os.environ["GH_USERNAME"]
TOKEN = os.environ["GH_TOKEN"]
OUT_PATH = "contrib-heatmap.svg"

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""


def fetch_contributions():
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USERNAME}}).encode(),
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    if "errors" in data:
        print(data["errors"], file=sys.stderr)
        sys.exit(1)
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]


def color_for(count):
    if count == 0:
        return "#161b22"
    if count < 3:
        return "#0e4429"
    if count < 6:
        return "#006d32"
    if count < 10:
        return "#26a641"
    return "#39d353"


def build_svg(weeks):
    cell = 11
    gap = 4
    step = cell + gap
    width = len(weeks) * step + 20
    height = 7 * step + 20

    cells = []
    delay = 0.0
    delay_step = 0.006  # controls how fast the reveal sweeps across

    for wi, week in enumerate(weeks):
        for di, day in enumerate(week["contributionDays"]):
            x = 10 + wi * step
            y = 10 + di * step
            fill = color_for(day["contributionCount"])
            cells.append(
                f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" '
                f'fill="{fill}" opacity="0">'
                f'<animate attributeName="opacity" from="0" to="1" '
                f'begin="{delay:.3f}s" dur="0.4s" fill="freeze"/>'
                f"</rect>"
            )
            delay += delay_step

    svg = (
        f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">'
        f'<rect width="{width}" height="{height}" fill="#0d1117"/>'
        + "".join(cells)
        + "</svg>"
    )
    return svg


def main():
    weeks = fetch_contributions()
    svg = build_svg(weeks)
    with open(OUT_PATH, "w") as f:
        f.write(svg)
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()