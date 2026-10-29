# E-mail to the people who downloaded a tool, when its new stable version is published
# (run by .github/workflows/on-release.yml on "release published", not for pre-releases).
#
# Newsletter: MailerLite (API key in the repository secret MAILERLITE_TOKEN). Every tool has a group named like its
# tag prefix, e.g. "ve-measure": the download form on vizemotion.com puts the subscriber there (with consent).
# No key, no group or an empty group = nothing is sent (the release itself is never blocked).

import json
import os
import re
import sys
import urllib.request

TOKEN = os.environ.get("MAILERLITE_TOKEN", "")
FROM = os.environ.get("MAIL_FROM", "lab@vizemotion.com")
FROM_NAME = "vizemotion Lab"
API = "https://connect.mailerlite.com/api"


def call(method, path, body=None):
    req = urllib.request.Request(API + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json",
                                          "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        txt = r.read().decode("utf-8")
        return json.loads(txt) if txt else {}


def main():
    event = json.load(open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8"))
    rel = event.get("release") or {}
    m = re.match(r"^(ve-[a-z-]+?)-(\d+(?:\.\d+)+)$", rel.get("tag_name", ""))
    if not TOKEN or not m or rel.get("prerelease"):
        print("nothing to send (no key, not a tool tag, or a pre-release)")
        return 0
    group_name, ver = m.group(1), m.group(2)
    groups = call("GET", f"/groups?filter[name]={group_name}").get("data", [])
    group = next((g for g in groups if g.get("name") == group_name), None)
    if not group or not group.get("active_count"):
        print(f"no subscribers in group {group_name}")
        return 0
    name = rel.get("name") or f"{group_name} {ver}"
    page = f"https://vizemotion.com/lab/{group_name}/"
    notes = "".join(f"<li>{line.lstrip('-* ').strip()}</li>" for line in (rel.get("body") or "").splitlines()
                    if line.strip().startswith(("-", "*")))
    html = (f"<h2>{name}</h2><p>A new version is out. / Jest nowa wersja.</p>"
            f"{'<ul>' + notes + '</ul>' if notes else ''}"
            f"<p><a href=\"{page}\">vizemotion.com — download / pobierz</a></p>"
            "<p style=\"color:#888\">You get this because you downloaded the tool and asked for updates. "
            "Dostajesz to, bo pobrałeś skrypt i zgodziłeś się na powiadomienia. {$unsubscribe}</p>")
    camp = call("POST", "/campaigns", {"name": f"{name} release", "type": "regular", "groups": [group["id"]],
                                        "emails": [{"subject": f"{name} — new version / nowa wersja", "from_name": FROM_NAME,
                                                    "from": FROM, "content": html}]})
    cid = camp["data"]["id"]
    call("POST", f"/campaigns/{cid}/schedule", {"delivery": "instant"})
    print(f"sent to {group_name}: campaign {cid}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
