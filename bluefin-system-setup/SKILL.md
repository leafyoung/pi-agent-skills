---
name: bluefin-system-setup
description: >
  This skill should be used when the user asks to "set up Bluefin", "configure Bluefin system",
  "install services on Bluefin", "check Bluefin services", "configure podman containers",
  "auto-start containers", "Bluefin system services", "what services are running",
  "system setup checklist", or mentions setting up, configuring, or troubleshooting
  system-level services on Bluefin Linux. Also covers Pika Backup recovery.
  For SearXNG / web search issues, use the `web-search` skill instead.
version: 0.2.0
---

# Bluefin System Setup

Setup and configuration guide for system-level services on Bluefin (Fedora Silverblue + GNOME).
Bluefin uses ostree for the OS and **podman** (not Docker) for containers — the `docker` CLI binary is actually a podman binary.

## Services Overview

| Service | Purpose | Auto-start | Managed by | Skill |
|---------|---------|------------|------------|-------|
| SearXNG | Local meta-search engine for `web_search` tool | systemd user unit | podman container | `web-search` |
| Pika Backup | Borg-based backup GUI | autostart + systemd | flatpak | (below) |

## SearXNG

**All SearXNG setup, troubleshooting, and recovery is in the `web-search` skill.**
That skill covers container creation, JSON format enablement, systemd registration,
a one-shot recovery script, and **persistent configuration** — baking config
(JSON format + reliable engine toggles like bing/qwant/mojeek) into a custom
image so it survives container recreation.

Trigger phrases: "fix web search", "searxng not working", "search returns 403", "restart searxng".

## Pika Backup

Pika Backup (borg-based) has a known issue on Bluefin where the background process goes inactive after system updates, caused by stale portal service chains.

### Backup Destinations

| Title | Repo URI | Schedule | Includes |
|-------|----------|----------|----------|
| config | `ssh://192.168.88.11/mnt/bob/backup/config` | 18:00 daily | .config, .local, .var, app, certbot, keep, kunlun |
| work | `ssh://192.168.88.11/mnt/bob/backup/work` | 19:00 daily | Desktop, Documents, Downloads, Music, Pictures, Public, Templates, Videos, devv, work |
| book | `ssh://192.168.88.11/mnt/bob/backup/book` | 20:00 daily | Carbon, book |

All three repos are on **bob** (`192.168.88.11`), mounted at `/mnt/bob/backup/`.
SSH key: `~/.ssh/ed25519-1.pem`. Encryption: repokey.

### Config Locations

| File | Purpose |
|------|----------|
| `~/.var/app/org.gnome.World.PikaBackup/config/pika-backup/backup.json` | Main Pika config (repo URIs, include/exclude, schedule, prune) |
| `~/.var/app/org.gnome.World.PikaBackup/config/borg/security/<repo_id>/location` | Per-repo cached location (must match backup.json) |
| `~/.var/app/org.gnome.World.PikaBackup/cache/borg/<repo_id>/config` | Borg cache config with `previous_location` (must match backup.json) |
| `~/devv/backup/pika-config.yaml` | CLI executor config (SSH key, repo IDs, passphrase lookup) |
| `~/devv/backup/pika_commands.json` | Auto-generated borg commands (regenerate via `extract_pika_commands.py`) |

### Changing Backup Destination

When the NAS IP changes, update **all three** config layers:

1. **backup.json** — edit `repo.uri` for each backup entry
2. **borg security location** — write new URI to each `security/<repo_id>/location` file
3. **borg cache config** — update `previous_location` in each `cache/borg/<repo_id>/config` file
4. **Regenerate** `pika_commands.json`: `cd ~/devv/backup && python3 extract_pika_commands.py`
5. **Restart** Pika Backup to pick up changes

### Recovery

For the background-process-inactive issue, the fix is:

```bash
# Kill stale portal chains and restart Pika
eflatpak kill org.gnome.World.PikaBackup
killall -9 xdg-desktop-portal-gnome 2>/dev/null
# Wait 3 seconds, then relaunch Pika Backup
sleep 3 && flatpak run org.gnome.World.PikaBackup &
```

If persistent, create `~/.local/bin/fix-pika-backup`:

```bash
#!/bin/bash
flatpak kill org.gnome.World.PikaBackup
systemctl --user restart xdg-desktop-portal
sleep 5
flatpak run org.gnome.World.PikaBackup &
```

Trigger phrases: "fix pika backup", "pika backup background process inactive", "borg backup stuck".

## Bluefin-specific Notes

- **No `sudo systemctl`** — use `systemctl --user` for user services. System-level systemctl may require `rpm-ostree` or toolbox.
- **Container CLI is podman** — `docker` is a podman binary, not Docker Engine. Use `podman` commands for reliability.
- **Flatpak for GUI apps** — Pika Backup and other GUI apps are Flatpaks, not RPMs.
- **Ostree updates** can reset or conflict with some system configs. User-level configs (`~/.config/systemd/user/`, `~/.local/`) persist across updates.
- **`rpm-ostree`** for layering system packages (use sparingly; prefer containers and Flatpaks).
