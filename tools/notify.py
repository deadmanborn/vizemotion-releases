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
SIGNATURE = "Adam Iwanowicz, vizemotion Lab"
LOGO = "https://vizemotion.com/wp-content/themes/vizemotion/assets/mail/ve-znak.png"  # red V + light E, on the dark footer
API = "https://connect.mailerlite.com/api"
LAB_GROUP = "lab-nowosci"


def call(method, path, body=None):
    req = urllib.request.Request(API + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json",
                                          "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        txt = r.read().decode("utf-8")
        return json.loads(txt) if txt else {}


def esc(t):
    return (t or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def changes(body):
    """Release notes lines starting with - or * (the markdown list of the GitHub release)."""
    return [re.sub(r"^[-*]\s*", "", ln.strip()) for ln in (body or "").splitlines() if ln.strip().startswith(("-", "*"))]


def mail_html(title, intro_pl, intro_en, items, button, url, why_pl, why_en):
    """Branded e-mail (tables + inline styles, as mail programs need): yellow header, PL, then EN, dark footer with logo."""
    lst = "".join(f'<li style="margin:0 0 6px">{esc(i)}</li>' for i in items)
    lst = f'<ul style="margin:0 0 18px;padding-left:20px">{lst}</ul>' if lst else ""
    btn = (f'<a href="{url}" style="display:inline-block;padding:13px 22px;border-radius:8px;background:#111214;'
           f'color:#ffffff;text-decoration:none;font-weight:600">{esc(button)}</a>')
    font = "font-family:Helvetica,Arial,sans-serif;font-size:16px;line-height:1.55;color:#111214"
    return f"""<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f2f2ee">
<tr><td align="center" style="padding:24px 12px">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#ffffff;border-radius:12px;overflow:hidden;{font}">
<tr><td style="background:#ffd400;padding:22px 28px;font-size:13px;font-weight:700;letter-spacing:.08em;text-transform:uppercase">vizemotion Lab</td></tr>
<tr><td style="padding:28px 28px 8px">
<h1 style="margin:0 0 14px;font-size:26px;line-height:1.2">{esc(title)}</h1>
<p style="margin:0 0 16px">{intro_pl}</p>{lst}<p style="margin:0 0 26px">{btn}</p>
<p style="margin:0 0 6px;color:#5f6268;font-size:14px;border-top:1px solid #e4e4df;padding-top:18px">{intro_en}</p>
</td></tr>
<tr><td style="padding:8px 28px 26px;font-size:14px;color:#5f6268">{SIGNATURE}</td></tr>
<tr><td style="background:#111214;padding:22px 28px;color:#a9adb4;font-size:12px;line-height:1.5">
<a href="https://vizemotion.com/lab/" style="text-decoration:none"><img src="{LOGO}" width="44" height="22" alt="VE" style="vertical-align:middle;border:0"></a>
<a href="https://vizemotion.com/" style="color:#ffffff;text-decoration:none;font-weight:700;font-size:15px;vertical-align:middle;margin-left:8px">vizemotion</a>
<p style="margin:14px 0 0">{why_pl}<br>{why_en}</p>
<p style="margin:10px 0 0"><a href="https://vizemotion.com/lab/" style="color:#ffffff">vizemotion.com/lab</a> · {{$unsubscribe}}</p>
</td></tr></table></td></tr></table>"""


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
                send(lab, f"Nowość w Labie: {name} / New in the Lab",
                     mail_html(f"Nowość w Labie: {name}",
                               "Nowe, darmowe narzędzie w vizemotion Lab. Co potrafi:",
                               f"A new free tool in vizemotion Lab: {esc(name)}. Details and download on the page.",
                               changes(rel.get("body"))[:5], "Zobacz / See it", page,
                               "Dostajesz to, bo zapisałeś się na nowości z vizemotion Lab.",
                               "You get this because you asked for news from vizemotion Lab."),
                     f"{name} new tool")
            else:
                print(f"no subscribers in group {LAB_GROUP}")
    except Exception as e:                     # Lab news must never block the tool's own e-mail
        print(f"lab news skipped: {e}")

    group = group_by_name(group_name)
    if not group or not group.get("active_count"):
        print(f"no subscribers in group {group_name}")
        return 0
    html = mail_html(name, "Jest nowa wersja. Co się zmieniło:",
                     f"A new version of {esc(name)} is out. The list above is the changelog; download it from the page.",
                     changes(rel.get("body")), "Pobierz / Download", page,
                     "Dostajesz to, bo pobrałeś skrypt i zgodziłeś się na powiadomienia o nowych wersjach.",
                     "You get this because you downloaded the tool and asked for update e-mails.")
    send(group, f"{name} – nowa wersja / new version", html, f"{name} release")
    return 0


if __name__ == "__main__":
    sys.exit(main())
