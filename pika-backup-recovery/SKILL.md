---
name: pika-backup-recovery
description: This skill should be used when the user asks to "fix pika backup", "pika backup background process inactive", "pika backup not running", "pika backup backend process", "borg backup stuck", "fix flatpak backup app", "restart pika backup monitor", "pika backup d-bus error", "pika backup keyring error", "pika backup no access to secrets", "pika backup secrets portal error", "pika backup background process inactive", "fix pika after bluefin update", "pika backup after update", or mentions issues with Pika Backup showing errors, backups not running, or the background service being inactive.
version: 0.4.0
---

# Pika Backup Backend Process Recovery

Recovery workflow for fixing Pika Backup when it shows "background process inactive" or fails to run scheduled backups. Optimized for Bluefin (Fedora Silverblue + GNOME) where the issue recurs after system updates.

## Symptoms

- GUI shows "background process inactive"
- GUI shows "no access to secrets" or keyring warning
- Scheduled backups don't run
- Logs show portal errors: `PortalNotFound(OwnedInterfaceName("org.freedesktop.portal.Secret"))`
- Logs show keyring errors: `Error using keyring, using in-memory password store`
- Logs show GNOME Shell errors: `RequiresVersion(2, 1)`

## Root Cause

**Stale portal service chain after reboot/update.** On Bluefin with GNOME 49, `xdg-desktop-portal` (v1.20.x) depends on three backend services: `xdg-desktop-portal-gnome`, `xdg-desktop-portal-gtk`, and the `gnome-keyring` Secret backend. After a Bluefin ostree update and reboot, the portal service chain may start in the wrong order, or the portal may cache stale backend discovery from a previous session. When `xdg-desktop-portal` doesn't discover the gnome-keyring Secret backend, the `org.freedesktop.portal.Secret` interface is never registered, and Pika Backup cannot access stored repository passwords.

**Critical finding:** Killing only the main `xdg-desktop-portal` process is insufficient. All three portal services must be fully stopped before restarting, so the portal re-discovers all backends from scratch.

## Quick Fix (post-Bluefin-update)

Run this single block after each Bluefin update that causes Pika Backup issues:

```bash
# 1. Verify the Secret portal is missing (confirms the diagnosis)
gdbus introspect --session --dest org.freedesktop.portal.Desktop \
  --object-path /org/freedesktop/portal/desktop 2>&1 | grep -q "org.freedesktop.portal.Secret" \
  && echo "Portal OK — skip to Pika restart" || {

# 2. Stop ALL portal services (required: partial stop doesn't work)
echo "Restarting portal service chain..."
systemctl --user stop xdg-desktop-portal.service
systemctl --user stop xdg-desktop-portal-gnome.service
systemctl --user stop xdg-desktop-portal-gtk.service
kill $(pgrep -f xdg-desktop-portal) 2>/dev/null
sleep 3

# 3. Start portal fresh (backends auto-activate)
systemctl --user start xdg-desktop-portal.service
sleep 5

# 4. Verify Secret portal is restored
gdbus introspect --session --dest org.freedesktop.portal.Desktop \
  --object-path /org/freedesktop/portal/desktop 2>&1 | grep -i secret \
  && echo "Secret portal restored" || echo "FAILED: Secret portal still missing"
}

# 5. Restart Pika Backup
flatpak kill org.gnome.World.PikaBackup 2>/dev/null
killall -9 pika-backup pika-backup-monitor 2>/dev/null
sleep 2
flatpak run org.gnome.World.PikaBackup --gapplication-service &
sleep 3
flatpak run --command=pika-backup-monitor org.gnome.World.PikaBackup &
sleep 5

# 6. Verify
busctl --user list | grep -i pika
```

## One-Command Fix Script

A self-contained script that automates the full recovery procedure below:

```bash
~/.local/bin/fix-pika-backup                # full fix + preventive config
~/.local/bin/fix-pika-backup --skip-config  # just fix the portal + restart
```

The script is idempotent and exits early if the Secret portal is already healthy.
It covers all 5 steps (diagnose → restore portal → apply config → restart Pika → verify)
with automatic retry on failure.

Source: `pika-backup-recovery/fix-pika-backup`

## Full Recovery Procedure

### Step 1: Diagnose

```bash
# Check Secret portal (most common root cause)
gdbus introspect --session --dest org.freedesktop.portal.Desktop \
  --object-path /org/freedesktop/portal/desktop 2>&1 | grep -i secret

# If "interface org.freedesktop.portal.Secret" appears → portal healthy, skip to Step 4
# If no output → Secret portal missing, continue to Step 2
```

Also check:
```bash
busctl --user list | grep -i pika     # 3 D-Bus names expected
ps aux | grep pika-backup | grep -v grep  # processes running?
```

### Step 2: Restore Secret Portal

The portal service chain must be fully stopped, not just the main process:

```bash
# Stop the entire chain
systemctl --user stop xdg-desktop-portal.service
systemctl --user stop xdg-desktop-portal-gnome.service
systemctl --user stop xdg-desktop-portal-gtk.service
kill $(pgrep -f xdg-desktop-portal) 2>/dev/null  # catch any stragglers
sleep 3

# Start fresh — backends auto-activate via D-Bus service activation
systemctl --user start xdg-desktop-portal.service
sleep 5

# Verify
gdbus introspect --session --dest org.freedesktop.portal.Desktop \
  --object-path /org/freedesktop/portal/desktop 2>&1 | grep -i secret
# Expected: "  interface org.freedesktop.portal.Secret {"
```

**Why full chain stop is required:** On GNOME 49 / xdg-desktop-portal 1.20.x, the main portal process caches backend discovery results. If only the main process is killed, the auto-activated replacement inherits stale state from the still-running `xdg-desktop-portal-gnome` and `xdg-desktop-portal-gtk` backends. Only a full stop forces clean re-discovery of all backends including gnome-keyring's `org.freedesktop.impl.portal.Secret`.

### Step 3: Ensure Preventive Config (one-time setup)

These files prevent the issue from recurring on future reboots. Apply once; they persist across updates.

#### 3a: Systemd drop-in (portal starts after keyring)

```bash
mkdir -p ~/.config/systemd/user/xdg-desktop-portal.service.d
cat > ~/.config/systemd/user/xdg-desktop-portal.service.d/30-after-keyring.conf << 'EOF'
[Unit]
# Ensure gnome-keyring-daemon is running before the portal starts,
# so the Secret portal backend (org.freedesktop.portal.Secret) is
# available when xdg-desktop-portal probes for backends.
After=gnome-keyring-daemon.service
Wants=gnome-keyring-daemon.service
EOF
systemctl --user daemon-reload
```

#### 3b: Flatpak permissions override

```bash
mkdir -p ~/.local/share/flatpak/overrides
cat > ~/.local/share/flatpak/overrides/org.gnome.World.PikaBackup << 'EOF'
[Context]
shared=ipc;network;
sockets=fallback-x11;ssh-auth;wayland;
devices=all;
filesystems=~/.var/app;xdg-run/gvfsd;xdg-run/pika-backup:create;/var:ro;xdg-run/gvfs;xdg-data/flatpak:ro;host;
unset-environment=LD_PRELOAD;GTK_THEME;

[Session Bus Policy]
org.gtk.vfs.*=talk
org.gtk.MountOperationHandler=talk
org.freedesktop.Flatpak.*=talk
org.freedesktop.secrets=talk
org.gnome.Shell=talk

[System Bus Policy]
org.freedesktop.UPower=talk

[Environment]
LD_PRELOAD=
GTK_THEME=
EOF
```

Key permissions: `org.freedesktop.secrets=talk` (keyring access), `org.gnome.Shell=talk` (background notifications).

#### 3c: Autostart entry for monitor

```bash
if [ ! -f ~/.config/autostart/pika-backup-monitor.desktop ]; then
  mkdir -p ~/.config/autostart
  cat > ~/.config/autostart/pika-backup-monitor.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=Pika Backup Monitor
Exec=flatpak run --command=pika-backup-monitor org.gnome.World.PikaBackup
Icon=org.gnome.World.PikaBackup
X-GNOME-Autostart-Delay=90
X-GNOME-UsesNotifications=true
X-Flatpak=org.gnome.World.PikaBackup
Hidden=false
EOF
fi
```

### Step 4: Restart Pika Backup

```bash
flatpak kill org.gnome.World.PikaBackup 2>/dev/null
killall -9 pika-backup pika-backup-monitor 2>/dev/null
sleep 2
flatpak run org.gnome.World.PikaBackup --gapplication-service &
sleep 3
flatpak run --command=pika-backup-monitor org.gnome.World.PikaBackup &
sleep 5
busctl --user list | grep -i pika
```

Expected: three D-Bus names — `org.gnome.World.PikaBackup`, `.Api`, `.Monitor`.

### Step 5: Verify

```bash
# Secret portal present
gdbus introspect --session --dest org.freedesktop.portal.Desktop \
  --object-path /org/freedesktop/portal/desktop 2>&1 | grep -i secret

# No keyring/portal errors in logs
journalctl --user -n 20 | grep -iE "pika|keyring|portal" 
```

Open the Pika Backup GUI and confirm "background process inactive" is gone.

## Troubleshooting

### Secret portal still missing after full chain restart

Verify the gnome-keyring Secret backend is actually registered:

```bash
# gnome-keyring must be active
systemctl --user is-active gnome-keyring-daemon

# Secret backend must be on the keyring bus name
gdbus introspect --session --dest org.freedesktop.secrets \
  --object-path /org/freedesktop/portal/desktop 2>&1 | grep Secret
```

If `org.freedesktop.impl.portal.Secret` is missing, restart keyring then retry the full chain:

```bash
systemctl --user restart gnome-keyring-daemon
sleep 2
systemctl --user stop xdg-desktop-portal{,-gnome,-gtk}.service
kill $(pgrep -f xdg-desktop-portal) 2>/dev/null
sleep 3
systemctl --user start xdg-desktop-portal.service
sleep 5
gdbus introspect --session --dest org.freedesktop.portal.Desktop \
  --object-path /org/freedesktop/portal/desktop 2>&1 | grep -i secret
```

### "Background process inactive" persists despite portal being healthy

This is a version compatibility issue with GNOME 49 (xdg-desktop-portal-gnome 49.0). Pika Backup 0.7.x expects Background portal version 2.1, but GNOME 49 provides version 2. Check:

```bash
gnome-shell --version
gdbus call --session --dest org.freedesktop.portal.Desktop \
  --object-path /org/freedesktop/portal/desktop \
  --method org.freedesktop.DBus.Properties.Get \
  org.freedesktop.portal.Background version
```

Workaround: ensure both the main service and monitor are running (Step 4). The GUI warning may persist, but backups should work. Upgrade to Pika Backup 0.8.x if available.

### Nuclear option: reinstall

```bash
flatpak uninstall -y --force-remove org.gnome.World.PikaBackup
flatpak install -y flathub org.gnome.World.PikaBackup
# Then re-apply Step 3b (permissions override) and Step 4
```

## Related Files

| File | Purpose |
|------|---------|
| `~/.var/app/org.gnome.World.PikaBackup/config/pika-backup/backup.json` | Backup config |
| `~/.var/app/org.gnome.World.PikaBackup/config/pika-backup/history.json` | Backup history |
| `~/.local/share/flatpak/overrides/org.gnome.World.PikaBackup` | Flatpak sandbox permissions |
| `~/.config/autostart/pika-backup-monitor.desktop` | Monitor autostart on login |
| `~/.config/systemd/user/xdg-desktop-portal.service.d/30-after-keyring.conf` | Portal ordering drop-in |
| `/usr/share/xdg-desktop-portal/gnome-portals.conf` | Portal backend preferences (read-only on Silverblue) |
| `/usr/share/xdg-desktop-portal/portals/gnome-keyring.portal` | Secret backend definition |
| `~/.local/bin/fix-pika-backup` | One-command fix script (installed from skill) |
| `pika-backup-recovery/fix-pika-backup` | Script source in skill directory |
