# Pika Backup Log Analysis

Common error patterns in Pika Backup logs and their meanings.

## Viewing Logs

```bash
journalctl --user -n 100 | grep -i pika
```

## Error Patterns

### Secret Portal Not Found (most common)

```
Error using keyring, using in-memory password store. Keyring error:
'PasswordStorage(File(Portal(PortalNotFound(OwnedInterfaceName("org.freedesktop.portal.Secret")))))'
```

**Meaning**: `xdg-desktop-portal` is running but did not register the `org.freedesktop.portal.Secret` interface. This happens when the portal started before gnome-keyring was fully initialized. The Flatpak sandbox cannot retrieve stored passwords.

**Fix**: Restart `xdg-desktop-portal` so it picks up the gnome-keyring Secret backend:
```bash
kill $(pgrep -f '/usr/libexec/xdg-desktop-portal$')
sleep 3
# Verify
gdbus introspect --session --dest org.freedesktop.portal.Desktop \
  --object-path /org/freedesktop/portal/desktop 2>&1 | grep -i secret
```
Then restart Pika Backup.

### D-Bus Service Unknown

```
Error using keyring, using in-memory password store. Keyring error:
'PasswordStorage(DBus(Service(ZBus(MethodError(OwnedErrorName(ErrorName(Str(Owned("org.freedesktop.DBus.Error.ServiceUnknown")))), Some("org.freedesktop.DBus.Error.ServiceUnknown"), ...
```

**Meaning**: Flatpak sandbox cannot access the secret service D-Bus API. Less common than the portal variant above; indicates missing Flatpak permissions.

**Fix**: Add `org.freedesktop.secrets=talk` to Flatpak override.

### GNOME Shell Version Mismatch

```
Error setting background status: RequiresVersion(2, 1)
```

**Meaning**: Pika Backup expects Background portal version 2.1, but system provides version 2.

**Fix**: This is a compatibility issue with GNOME Platform 49. The warning may persist, but backups should work if monitor process is running.

### Failed to Store Password

```
Message { text: "Failed to Store Password", secondary_text: Some("DBus error service error org.freedesktop.zbus.Error: org.freedesktop.DBus.Error.ServiceUnknown")
```

**Meaning**: Same root cause as D-Bus Service Unknown - cannot access keyring.

**Fix**: Add `org.freedesktop.secrets=talk` permission.

### Unable to Acquire Bus Name

```
Failed to register: Unable to acquire bus name 'org.gnome.World.PikaBackup'
```

**Meaning**: Another instance already holds the D-Bus name, or previous instance didn't clean up properly.

**Fix**: Kill all Pika Backup processes before restarting:
```bash
flatpak kill org.gnome.World.PikaBackup
killall -9 pika-backup pika-backup-monitor
sleep 2
```

### Repository Locked

```
Failed to create archive: Repository is locked
```

**Meaning**: Previous backup process left a stale lock file on remote repository.

**Fix**: SSH to backup server and remove locks:
```bash
ssh <server> "rm -rf /path/to/backup/repo/lock.*"
```

### Backup Location Filling Up

```
Backup location might be filling up. Estimated space missing to store all data: X GB.
```

**Meaning**: Remote storage is nearly full.

**Fix**: Check storage on backup server:
```bash
ssh <server> "df -h /path/to/backup"
```

Consider pruning old archives:
```bash
flatpak run --command=borg org.gnome.World.PikaBackup prune --keep-daily 7 --keep-weekly 4 <repo>
```

## Log Severity Levels

| Pattern | Severity | Action Required |
|---------|----------|-----------------|
| Secret PortalNotFound | High | Restart xdg-desktop-portal |
| D-Bus ServiceUnknown | High | Apply permissions override |
| RequiresVersion | Medium | May be benign; check functionality |
| Failed to Store Password | High | Apply permissions override |
| Unable to acquire bus name | High | Kill processes, restart |
| Repository is locked | High | Remove lock files |
| Backup location filling up | Medium | Check storage, prune |

## Proactive Monitoring

Set up a cron job to monitor for issues:

```bash
# Check every hour
crontab -e
# Add:
0 * * * * journalctl --user -n 20 | grep -i "pika.*error" && echo "Pika Backup errors detected" | mail -s "Pika Backup Alert" user@example.com
```