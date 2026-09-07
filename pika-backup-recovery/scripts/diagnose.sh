#!/bin/bash
# Pika Backup Diagnostic Script
# Usage: ./diagnose.sh [--verbose]

set -e

VERBOSE=0
[[ "$1" == "--verbose" ]] && VERBOSE=1

echo "=== Pika Backup Diagnostic Report ==="
echo "Date: $(date)"
echo

# 1. Check processes
echo "## Running Processes"
pika_processes=$(ps aux | grep -E "pika-backup|pika-backup-monitor|borg" | grep -v grep || true)
borg_processes=$(ps aux | grep "borg" | grep -v grep || true)

if [[ -z "$pika_processes" ]]; then
    echo "❌ No Pika Backup processes running"
else
    echo "✓ Pika Backup processes found:"
    echo "$pika_processes" | while read line; do
        echo "  $line"
    done
fi
echo

# 2. Check D-Bus services
echo "## D-Bus Services"
dbus_services=$(busctl --user list 2>/dev/null | grep -i pika || true)

expected_services=(
    "org.gnome.World.PikaBackup"
    "org.gnome.World.PikaBackup.Api"
    "org.gnome.World.PikaBackup.Monitor"
)

for service in "${expected_services[@]}"; do
    if echo "$dbus_services" | grep -q "$service"; then
        echo "✓ $service registered"
    else
        echo "❌ $service NOT registered"
    fi
done
echo

# 3. Check Flatpak override
echo "## Flatpak Permissions Override"
override_file="$HOME/.local/share/flatpak/overrides/org.gnome.World.PikaBackup"

if [[ -f "$override_file" ]]; then
    echo "✓ Override file exists: $override_file"

    # Check for critical permissions
    if grep -q "org.freedesktop.secrets=talk" "$override_file"; then
        echo "✓ org.freedesktop.secrets permission present"
    else
        echo "❌ org.freedesktop.secrets permission MISSING"
    fi

    if grep -q "org.gnome.Shell=talk" "$override_file"; then
        echo "✓ org.gnome.Shell permission present"
    else
        echo "❌ org.gnome.Shell permission MISSING"
    fi
else
    echo "❌ Override file MISSING: $override_file"
fi
echo

# 4. Check autostart entry
echo "## Autostart Configuration"
autostart_file="$HOME/.config/autostart/pika-backup-monitor.desktop"

if [[ -f "$autostart_file" ]]; then
    echo "✓ Autostart entry exists: $autostart_file"
else
    echo "❌ Autostart entry MISSING: $autostart_file"
fi
echo

# 5. Check systemd drop-in for portal-keyring ordering
portal_dropin="$HOME/.config/systemd/user/xdg-desktop-portal.service.d/30-after-keyring.conf"

echo "## Portal-Keyring Ordering Drop-in"
if [[ -f "$portal_dropin" ]]; then
    echo "✓ Drop-in exists: $portal_dropin"
    if grep -q "After=gnome-keyring-daemon.service" "$portal_dropin"; then
        echo "✓ After=gnome-keyring-daemon.service present"
    else
        echo "❌ After=gnome-keyring-daemon.service MISSING from drop-in"
    fi
else
    echo "⚠ Drop-in MISSING: $portal_dropin"
    echo "  Prevent portal race condition: see SKILL.md Step 2A-P"
fi
echo

# 6. Check Secret Portal (most common root cause)
echo "## Secret Portal Availability"
secret_portal=$(gdbus introspect --session --dest org.freedesktop.portal.Desktop \
    --object-path /org/freedesktop/portal/desktop 2>&1 | grep "interface org.freedesktop.portal.Secret" || true)

if [[ -n "$secret_portal" ]]; then
    echo "✓ org.freedesktop.portal.Secret interface registered"
else
    echo "❌ org.freedesktop.portal.Secret interface MISSING"
    echo "  Fix: kill \$(pgrep -f '/usr/libexec/xdg-desktop-portal\$') and wait for D-Bus re-activation"
fi
echo

# 7. Check gnome-keyring
echo "## Secret Service (Keyring)"
keyring_status=$(systemctl --user is-active gnome-keyring-daemon 2>/dev/null || echo "unknown")

if [[ "$keyring_status" == "active" ]]; then
    echo "✓ gnome-keyring-daemon is active"

    secrets_service=$(busctl --user list 2>/dev/null | grep "org.freedesktop.secrets" || true)
    if [[ -n "$secrets_service" ]]; then
        echo "✓ org.freedesktop.secrets D-Bus service available"
    else
        echo "❌ org.freedesktop.secrets D-Bus service NOT available"
    fi
else
    echo "❌ gnome-keyring-daemon status: $keyring_status"
fi
echo

# 8. Check Background Portal
echo "## Background Portal"
portal_version=$(gdbus call --session --dest org.freedesktop.portal.Desktop \
    --object-path /org/freedesktop/portal/desktop \
    --method org.freedesktop.DBus.Properties.Get \
    org.freedesktop.portal.Background version 2>/dev/null || echo "error")

if [[ "$portal_version" != "error" ]]; then
    echo "✓ Background portal available: version $portal_version"
else
    echo "❌ Background portal NOT available"
fi
echo

# 9. Check recent logs for errors
echo "## Recent Log Errors (last 50 lines)"
log_errors=$(journalctl --user -n 50 --no-pager 2>/dev/null | grep -iE "(pika|borg)" | grep -iE "(error|fail|warning|inactive)" || true)

if [[ -n "$log_errors" ]]; then
    echo "⚠ Errors found in logs:"
    echo "$log_errors" | while read line; do
        echo "  $line"
    done
else
    echo "✓ No recent errors in logs"
fi
echo

# 10. Check backup configuration
echo "## Backup Configuration"
config_file="$HOME/.var/app/org.gnome.World.PikaBackup/config/pika-backup/backup.json"

if [[ -f "$config_file" ]]; then
    echo "✓ Configuration file exists"
    backup_count=$(jq length "$config_file" 2>/dev/null || echo "parse error")
    if [[ "$backup_count" != "parse error" ]]; then
        echo "  Backup configs: $backup_count"
    fi
else
    echo "⚠ Configuration file not found (app may not be configured)"
fi
echo

# Summary
echo "## Summary"
issues=0

# Count issues
[[ -z "$pika_processes" ]] && ((issues++))
! echo "$dbus_services" | grep -q "org.gnome.World.PikaBackup.Monitor" && ((issues++))
[[ ! -f "$override_file" ]] && ((issues++))
grep -q "org.freedesktop.secrets=talk" "$override_file" 2>/dev/null || ((issues++))
grep -q "org.gnome.Shell=talk" "$override_file" 2>/dev/null || ((issues++))
[[ ! -f "$autostart_file" ]] && ((issues++))
[[ ! -f "$portal_dropin" ]] && ((issues++))
[[ -z "$secret_portal" ]] && ((issues++))
[[ -n "$log_errors" ]] && ((issues++))

if [[ $issues -eq 0 ]]; then
    echo "✓ All checks passed - Pika Backup appears healthy"
else
    echo "⚠ $issues issues detected - follow recovery procedure in SKILL.md"
fi

exit $issues