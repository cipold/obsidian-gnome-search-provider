#!/usr/bin/env python3
import json
import logging
import subprocess
import sys
import traceback
import urllib.parse
from pathlib import Path
from typing import Dict

import gi

gi.require_version("GLib", "2.0")
gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib  # noqa: E402

# Configure logging to go to stderr, which systemd/dbus captures and puts in journalctl
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("obsidian-search-provider")

DBUS_XML = """<node>
  <interface name="org.gnome.Shell.SearchProvider2">
    <method name="GetInitialResultSet">
      <arg type="as" name="terms" direction="in"/>
      <arg type="as" name="results" direction="out"/>
    </method>
    <method name="GetSubsearchResultSet">
      <arg type="as" name="previous_results" direction="in"/>
      <arg type="as" name="terms" direction="in"/>
      <arg type="as" name="results" direction="out"/>
    </method>
    <method name="GetResultMetas">
      <arg type="as" name="identifiers" direction="in"/>
      <arg type="aa{sv}" name="metas" direction="out"/>
    </method>
    <method name="ActivateResult">
      <arg type="s" name="identifier" direction="in"/>
      <arg type="as" name="terms" direction="in"/>
      <arg type="u" name="timestamp" direction="in"/>
    </method>
    <method name="LaunchSearch">
      <arg type="as" name="terms" direction="in"/>
      <arg type="u" name="timestamp" direction="in"/>
    </method>
  </interface>
</node>"""


class ObsidianSearchProvider:
    def __init__(self) -> None:
        self.vaults: Dict[str, str] = self._load_vaults()

    def _load_vaults(self) -> Dict[str, str]:
        """Load vault IDs and their base paths from obsidian.json."""
        config_path = Path.home() / ".config" / "obsidian" / "obsidian.json"
        vaults = {}
        if config_path.exists():
            try:
                with config_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                    for v_id, v_data in data.get("vaults", {}).items():
                        vault_path = v_data.get("path", "")
                        if vault_path:
                            vaults[v_id] = Path(vault_path).name
            except Exception as e:
                logger.error(f"Failed to read obsidian.json: {e}")
        return vaults

    def handle_method_call(
        self,
        connection: Gio.DBusConnection,
        sender: str,
        object_path: str,
        interface: str,
        method: str,
        params: GLib.Variant,
        invocation: Gio.DBusMethodInvocation,
    ) -> None:
        try:
            # Reload vaults on every request to ensure we have the latest
            self.vaults = self._load_vaults()

            if method in ("GetInitialResultSet", "GetSubsearchResultSet"):
                terms = params.unpack()[1] if method == "GetSubsearchResultSet" else params.unpack()[0]
                query = " ".join(terms).lower()

                # If query exactly matches 'obsidian' or 'vault', show all vaults
                if ("obsidian".startswith(query) or "vault".startswith(query)) and len(query) >= 3:
                    results = list(self.vaults.keys())
                else:
                    results = [v_id for v_id, name in self.vaults.items() if query in name.lower()]

                invocation.return_value(GLib.Variant("(as)", (results,)))

            elif method == "GetResultMetas":
                identifiers = params.unpack()[0]
                metas = []
                for v_id in identifiers:
                    name = self.vaults.get(v_id, "Unknown Vault")
                    metas.append(
                        {
                            "id": GLib.Variant("s", v_id),
                            "name": GLib.Variant("s", name),
                            "description": GLib.Variant("s", "Obsidian Vault"),
                            "icon": GLib.Variant("v", GLib.Variant("s", "obsidian")),
                        }
                    )
                invocation.return_value(GLib.Variant("(aa{sv})", (metas,)))

            elif method == "ActivateResult":
                identifier = params.unpack()[0]
                if identifier in self.vaults:
                    name = self.vaults[identifier]
                    uri = f"obsidian://open?vault={urllib.parse.quote(name)}"
                    subprocess.Popen(["xdg-open", uri])
                invocation.return_value(None)

            elif method == "LaunchSearch":
                subprocess.Popen(["xdg-open", "obsidian://"])
                invocation.return_value(None)

        except Exception as e:
            logger.error(f"Error handling method {method}: {traceback.format_exc()}")
            invocation.return_dbus_error("org.freedesktop.DBus.Error.Failed", str(e))


PROVIDER_INSTANCE = None


def on_bus_acquired(connection: Gio.DBusConnection, name: str) -> None:
    global PROVIDER_INSTANCE
    logger.info("Acquired D-Bus name, registering object...")
    PROVIDER_INSTANCE = ObsidianSearchProvider()
    node_info = Gio.DBusNodeInfo.new_for_xml(DBUS_XML.strip())
    connection.register_object(
        "/md/obsidian/Obsidian/SearchProvider",
        node_info.interfaces[0],
        PROVIDER_INSTANCE.handle_method_call,
        None,
        None,
    )


def on_name_lost(connection: Gio.DBusConnection, name: str) -> None:
    logger.error("Lost D-Bus name, exiting.")
    sys.exit(1)


def main() -> None:
    Gio.bus_own_name(
        Gio.BusType.SESSION,
        "md.obsidian.Obsidian.SearchProvider",
        Gio.BusNameOwnerFlags.NONE,
        on_bus_acquired,
        None,
        on_name_lost,
    )

    loop = GLib.MainLoop()
    try:
        loop.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user, shutting down.")
        loop.quit()


if __name__ == "__main__":
    main()
