# E-mail to the people who downloaded a tool, when its new stable version is published
# (run by .github/workflows/on-release.yml on "release published", not for pre-releases).
#
# Newsletter: MailerLite (API key in the repository secret MAILERLITE_TOKEN). Every tool has a group named like its
# tag prefix, e.g. "ve-measure": the download form on vizemotion.com puts the subscriber there (with consent).
# No key, no group or an empty group = nothing is sent (the release itself is never blocked).
# The FIRST stable release of a tool also goes to the group "lab-nowosci" (people who asked for Lab news):
# a new tool is the most important news for them (owner, 2026-10-31).

import json
import os
import re
import sys
import urllib.request

TOKEN = os.environ.get("MAILERLITE_TOKEN", "")
FROM = os.environ.get("MAIL_FROM", "lab@vizemotion.com")
FROM_NAME = "vizemotion Lab"
API = "https://connect.mailerlite.com/api"
LAB_GROUP = "lab-nowosci"


def call(method, path, body=None):
    req = urllib.request.Request(API + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json",
                                          "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        txt = r.read().decode("utf-8")
        return json.loads(txt) if txt else {}


def group_by_name(name):
    groups = call("GET", f"/groups?filter[name]={name}").get("data", [])
    return next((g for g in groups if g.get("name") == name), None)


def send(group, subject, html, label):
    camp = call("POST", "/campaigns", {"name": label, "type": "regular", "groups": [group["id"]],
                                        "emails": [{"subject": subject, "from_name": FROM_NAME, "from": FROM, "content": html}]})
    cid = camp["data"]["id"]
    call("POST", f"/campaigns/{cid}/schedule", {"delivery": "instant"})
    print(f"sent to {group['name']}: campaign {cid}")


def first_stable(prefix, tag):
    """True when `tag` is the only published stable release of this tool (GitHub API, token from the workflow)."""
    repo, gh = os.environ.get("GITHUB_REPOSITORY", ""), os.environ.get("GITHUB_TOKEN", "")
    if not repo or not gh:
        return False
    req = urllib.request.Request(f"https://api.github.com/repos/{repo}/releases?per_page=100",
                                 headers={"Authorization": f"Bearer {gh}", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        rels = json.loads(r.read().decode("utf-8"))
    stable = [x["tag_name"] for x in rels if not x.get("prerelease") and not x.get("draft")
              and re.match(rf"^{re.escape(prefix)}-\d", x.get("tag_name", ""))]
    return stable == [tag]


def main():
    event = json.load(open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8"))
    rel = event.get("release") or {}
    m = re.match(r"^(ve-[a-z-]+?)-(\d+(?:\.\d+)+)$", rel.get("tag_name", ""))
    if not TOKEN or not m or rel.get("prerelease"):
        print("nothing to send (no key, not a tool tag, or a pre-release)")
        return 0
    group_name, ver = m.group(1), m.group(2)
    name = rel.get("name") or f"{group_name} {ver}"
    page = f"https://vizemotion.com/lab/{group_name}/"

    # New tool → Lab news (independent of the tool's own group, which is still empty for a brand-new tool)
    try:
        if first_stable(group_name, rel.get("tag_name", "")):
            lab = group_by_name(LAB_GROUP)
            if lab and lab.get("active_count"):
                send(lab, f"New in the Lab: {name} / Nowość w Labie: {name}",
                     f"<h2>{name}</h2><p>A new free tool in vizemotion Lab. / Nowe, darmowe narzędzie w vizemotion Lab.</p>"
                     f"<p>{rel.get('body', '').splitlines()[0] if rel.get('body') else ''}</p>"
                     f"<p><a href=\"{page}\">vizemotion.com — see it / zobacz</a></p>"
                     "<p style=\"color:#888\">You get this because you asked for news from vizemotion Lab. "
                     "Dostajesz to, bo zapisałeś się na nowości z vizemotion Lab. {$unsubscribe}</p>",
                     f"{name} new tool")
            else:
                print(f"no subscribers in group {LAB_GROUP}")
    except Exception as e:                     # Lab news must never block the tool's own e-mail
        print(f"lab news skipped: {e}")

    group = group_by_name(group_name)
    if not group or not group.get("active_count"):
        print(f"no subscribers in group {group_name}")
        return 0
    notes = "".join(f"<li>{line.lstrip('-* ').strip()}</li>" for line in (rel.get("body") or "").splitlines()
                    if line.strip().startswith(("-", "*")))
    html = (f"<h2>{name}</h2><p>A new version is out. / Jest nowa wersja.</p>"
            f"{'<ul>' + notes + '</ul>' if notes else ''}"
            f"<p><a href=\"{page}\">vizemotion.com — download / pobierz</a></p>"
            "<p style=\"color:#888\">You get this because you downloaded the tool and asked for updates. "
            "Dostajesz to, bo pobrałeś skrypt i zgodziłeś się na powiadomienia. {$unsubscribe}</p>")
    send(group, f"{name} — new version / nowa wersja", html, f"{name} release")
    return 0


if __name__ == "__main__":
    sys.exit(main())
