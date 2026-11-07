# AGENTS

## RULE NO. 1 — zero information about the owner (overrides everything else)

Nothing produced in this repo may reveal anything about the owner, their computers, hardware or installed software.
This covers files, code, comments, README / CHANGELOG / docs, commit messages, branches, tags, packages, releases,
screenshots and their metadata, logs, test output and website material. Forbidden:
- paths from the owner's computers (drive letters, `C:\Users\...`, home or user folder names, temp folders),
- computer names, the Windows user name, domain, hardware (GPU, CPU, monitors, scaling),
- the owner's software setup: which programs, plugins, versions, licences or accounts they have installed or use
  (a tool's own requirement such as "needs Corona Renderer" is fine; "the owner uses X" is not),
- server, VPN and network names, host names, IP addresses, ports, process ids, instance / session ids, serial numbers.

Allowed: the supported program version ("3ds Max 2026", "tested on 2026"), vizemotion.com, lab@vizemotion.com,
author "Adam Iwanowicz".

How: relative paths (`..\<repo>`, `<folder>`), placeholders in logs (`<path>`, `<user>`, `<pc>`, `<scene>`, `<pid>`),
everything that leaves the computer is anonymized first (VE tools: `ui.anonymize()`), screenshots without title bars or
fields that show paths. Review the diff, the commit message and every image before each commit, release or publication.
