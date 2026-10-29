# vizemotion releases

Download packages of the vizemotion tools for 3ds Max (VE Measure, VE Pivot Placer, VE Clean, VE Gutter,
VE Scene Doctor, VE Panels, VE Roof, VE Manager). Get them from **https://vizemotion.com/lab/** — the tool pages
always link the newest version.

- One release = one tool version: tag `ve-<tool>-<version>` (e.g. `ve-measure-0.8`), the package as its file.
  **Pre-release** = test version.
- `versions.json` (built automatically from the releases) is read by the tools, VE Manager and vizemotion.com:
  `https://raw.githubusercontent.com/deadmanborn/vizemotion-releases/main/versions.json`
- The source code lives in private repositories; this repository holds only the packages.

## How a release happens (nothing is typed twice)

1. In the tool's source repository: version bump, changelog, tag — then
   `python tools/release.py <tool> <version> --publish` (repo max-vizemotion-scripts) builds the package and publishes
   the release here (pre-release with `--test`).
2. `.github/workflows/on-release.yml` then rebuilds `versions.json`, refreshes vizemotion.com (secret `SITE_HOOK_URL`)
   and e-mails the people who downloaded the tool (stable only; secret `MAILERLITE_TOKEN`, MailerLite group `ve-<tool>`).

Free tools. Support: https://ko-fi.com/onedeadman · Bugs: "Send logs" in the tool window → lab@vizemotion.com
