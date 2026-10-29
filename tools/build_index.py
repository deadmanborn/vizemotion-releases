# Builds versions.json from the GitHub releases of this repository (run by .github/workflows/on-release.yml).
#
# A release is one tool version: tag ve-<tool>-<version> (e.g. ve-measure-0.8), the package as its asset,
# "pre-release" = test channel. versions.json is what the tools, VE Manager and vizemotion.com read:
#   {"measure": {"name": "VE Measure", "stable": "0.8", "test": "0.9", "page": "...", "notes": "...",
#                "date": "2026-10-29", "download": "<asset url of the stable>", "download_test": "..."}}
# Nothing is typed twice: publish a release, this file and the site follow.

import json
import os
import re
import urllib.request

REPO = os.environ.get("GITHUB_REPOSITORY", "deadmanborn/vizemotion-releases")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
SITE = "https://vizemotion.com/lab/{slug}/"
NAMES = {"measure": "VE Measure", "pivot": "VE Pivot Placer", "clean": "VE Clean", "gutter": "VE Gutter",
         "scene-doctor": "VE Scene Doctor", "max-agent": "VE Max Agent", "panels": "VE Panels", "roof": "VE Roof",
         "manager": "VE Manager"}
TAG = re.compile(r"^ve-([a-z-]+?)-(\d+(?:\.\d+)+)$")


def api(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "vizemotion-index"})
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def vkey(v):
    return [int(x) for x in v.split(".")]


def main():
    releases, page = [], 1
    while True:
        batch = api(f"https://api.github.com/repos/{REPO}/releases?per_page=100&page={page}")
        releases += batch
        if len(batch) < 100:
            break
        page += 1
    out = {}
    for r in releases:
        m = TAG.match(r.get("tag_name", ""))
        if not m or r.get("draft"):
            continue
        slug, ver = m.group(1), m.group(2)
        tid = slug.replace("-", "_")                      # ids used by the tools: scene_doctor, max_agent
        e = out.setdefault(tid, {"name": NAMES.get(slug, f"VE {slug.title()}"), "page": SITE.format(slug=f"ve-{slug}")})
        chan = "test" if r.get("prerelease") else "stable"
        if chan in e and vkey(e[chan]) >= vkey(ver):
            continue
        asset = (r.get("assets") or [{}])[0].get("browser_download_url", "")
        e[chan] = ver
        e["download" if chan == "stable" else "download_test"] = asset
        if chan == "stable":
            e["notes"] = (r.get("body") or "").strip().splitlines()[0][:200] if r.get("body") else ""
            e["date"] = (r.get("published_at") or "")[:10]
    for e in out.values():                                # a test older than the stable is not offered
        if "test" in e and "stable" in e and vkey(e["test"]) <= vkey(e["stable"]):
            e.pop("test"), e.pop("download_test", None)
    text = json.dumps(dict(sorted(out.items())), indent=2, ensure_ascii=False) + "\n"
    old = open("versions.json", encoding="utf-8").read() if os.path.exists("versions.json") else ""
    if text != old:
        open("versions.json", "w", encoding="utf-8").write(text)
        print("versions.json updated")
    else:
        print("versions.json unchanged")


if __name__ == "__main__":
    main()
