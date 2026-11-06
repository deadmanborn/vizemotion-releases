# Builds versions.json from the GitHub releases of this repository (run by .github/workflows/on-release.yml).
#
# A release is one tool version: tag ve-<tool>-<version> (e.g. ve-measure-0.8), the package as its asset,
# "pre-release" = test channel. versions.json is what the tools, VE Manager and vizemotion.com read:
#   {"measure": {"name": "VE Measure", "stable": "0.8", "test": "0.9", "page": "...", "notes": "...",
#                "date": "2026-10-29", "download": "<asset url of the stable>", "download_test": "..."}}
# A release carries the tool's own installer <tag>.mzp (drag onto a 3ds Max viewport) next to the <tag>.zip
# VE Manager installs from: "download" points at the .mzp when there is one, "download_zip" at the zip.
# Nothing is typed twice: publish a release, this file and the site follow.
#
# It also builds ve-tools.json, the catalog of the public VE Manager: only the tools listed in public.json, their
# newest stable release with a zip, with the full download address ("url") of that zip. Test versions never go there.

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


def write(path, data):
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    old = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
    if text != old:
        open(path, "w", encoding="utf-8").write(text)
        print(f"{path} updated")
    else:
        print(f"{path} unchanged")


def catalog(releases, public):
    """ve-tools.json for the public VE Manager: {"schema": 1, "tools": {id: {name, about, entry, page, channels:
    {"stable": {version, tag, zip, url, date, notes}}}}} - the published tools only, stable only."""
    tools = {}
    for r in releases:
        m = TAG.match(r.get("tag_name", ""))
        if not m or r.get("draft") or r.get("prerelease"):
            continue
        slug, ver = m.group(1), m.group(2)
        tid = slug.replace("-", "_")
        if tid not in public:
            continue
        zp = next((a for a in (r.get("assets") or []) if a.get("name", "").lower().endswith(".zip")), None)
        if not zp:
            continue                                      # VE Manager installs zips only
        have = tools.get(tid, {}).get("channels", {}).get("stable")
        if have and vkey(have["version"]) >= vkey(ver):
            continue
        body = (r.get("body") or "").strip()
        tools[tid] = {
            "name": NAMES.get(slug, f"VE {slug.title()}"),
            "about": public[tid].get("about", ""),
            "entry": public[tid].get("entry", f"ve_{tid}.ms"),
            "page": SITE.format(slug=f"ve-{slug}"),
            "channels": {"stable": {
                "version": ver, "tag": r["tag_name"], "zip": zp["name"], "url": zp.get("browser_download_url", ""),
                "date": (r.get("published_at") or "")[:10], "notes": body.splitlines()[0][:200] if body else ""}}}
    return {"schema": 1, "tools": dict(sorted(tools.items()))}


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
        urls = [a.get("browser_download_url", "") for a in (r.get("assets") or [])]
        mzp = next((u for u in urls if u.lower().endswith(".mzp")), "")
        zp = next((u for u in urls if u.lower().endswith(".zip")), "")
        e[chan] = ver
        e["download" if chan == "stable" else "download_test"] = mzp or zp or (urls[0] if urls else "")
        e["download_zip" if chan == "stable" else "download_zip_test"] = zp
        if chan == "stable":
            e["notes"] = (r.get("body") or "").strip().splitlines()[0][:200] if r.get("body") else ""
            e["date"] = (r.get("published_at") or "")[:10]
    for e in out.values():                                # a test older than the stable is not offered
        if "test" in e and "stable" in e and vkey(e["test"]) <= vkey(e["stable"]):
            e.pop("test"), e.pop("download_test", None), e.pop("download_zip_test", None)
    write("versions.json", dict(sorted(out.items())))
    with open("public.json", encoding="utf-8") as f:
        public = json.load(f).get("tools", {})
    write("ve-tools.json", catalog(releases, public))


if __name__ == "__main__":
    main()
