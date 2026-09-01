#!/usr/bin/env python3
"""Build Power Automate Import Package (Legacy) zips from solution-format flow JSON.

These packages import via: Power Automate > My flows > Import > Import Package (Legacy).
That path is the supported format for non-solution flow zips. Hand-crafted Dataverse
solution zips often fail with "not the correct format" / invalid solution file.
"""
from __future__ import annotations

import copy
import json
import uuid
import zipfile
from pathlib import Path

SRC = Path(
    "/workspace/WeeklySessionRegistration-Minimal/Flow/SolutionPackage-NoTemplates/Workflows"
)
OUT_DIR = Path("/workspace/WeeklySessionRegistration-Minimal/Flow/Packages")
FLOW_COPY = Path("/workspace/Flow/Packages")

# Stable GUIDs so re-builds stay consistent (folder / resource ids).
FLOWS = [
    {
        "file": "SendAppEmail-3F2504E0-4F89-41D3-9A0C-0305E82C3301.json",
        "name": "EventSessionRegistration_SendAppEmail",
        "package_guid": "3f2504e0-4f89-41d3-9a0c-0305e82c3301",
        "flow_guid": "3f2504e0-4f89-41d3-9a0c-0305e82c3301",
        "description": "Sends branded register/switch/cancel emails from the app.",
    },
    {
        "file": "ExportCSV-3F2504E0-4F89-41D3-9A0C-0305E82C3302.json",
        "name": "EventSessionRegistration_ExportCSV",
        "package_guid": "3f2504e0-4f89-41d3-9a0c-0305e82c3302",
        "flow_guid": "3f2504e0-4f89-41d3-9a0c-0305e82c3302",
        "description": "Writes a CSV to OneDrive and returns a share link.",
    },
    {
        "file": "AddToCalendar-3F2504E0-4F89-41D3-9A0C-0305E82C3303.json",
        "name": "EventSessionRegistration_AddToCalendar",
        "package_guid": "3f2504e0-4f89-41d3-9a0c-0305e82c3303",
        "flow_guid": "3f2504e0-4f89-41d3-9a0c-0305e82c3303",
        "description": "Creates an Outlook calendar event for the signed-in user.",
    },
    {
        "file": "SessionReminderDaily-3F2504E0-4F89-41D3-9A0C-0305E82C3304.json",
        "name": "EventSessionRegistration_SessionReminderDaily",
        "package_guid": "3f2504e0-4f89-41d3-9a0c-0305e82c3304",
        "flow_guid": "3f2504e0-4f89-41d3-9a0c-0305e82c3304",
        "description": "Daily 7 AM ET reminders for tomorrow's confirmed registrations.",
        "replace_env_var": True,
    },
    {
        "file": "SendReportEmail-3F2504E0-4F89-41D3-9A0C-0305E82C3305.json",
        "name": "EventSessionRegistration_SendReportEmail",
        "package_guid": "3f2504e0-4f89-41d3-9a0c-0305e82c3305",
        "flow_guid": "3f2504e0-4f89-41d3-9a0c-0305e82c3305",
        "description": "Emails a registration report with CSV attachment.",
    },
    {
        "file": "ShareEvent-3F2504E0-4F89-41D3-9A0C-0305E82C3306.json",
        "name": "EventSessionRegistration_ShareEvent",
        "package_guid": "3f2504e0-4f89-41d3-9a0c-0305e82c3306",
        "flow_guid": "3f2504e0-4f89-41d3-9a0c-0305e82c3306",
        "description": "Shares an event link by email.",
    },
]

CONNECTOR_META = {
    "shared_office365": {
        "id": "/providers/Microsoft.PowerApps/apis/shared_office365",
        "displayName": "Office 365 Outlook",
        "apiName": "office365",
    },
    "shared_sharepointonline": {
        "id": "/providers/Microsoft.PowerApps/apis/shared_sharepointonline",
        "displayName": "SharePoint",
        "apiName": "sharepointonline",
    },
    "shared_onedriveforbusiness": {
        "id": "/providers/Microsoft.PowerApps/apis/shared_onedriveforbusiness",
        "displayName": "OneDrive for Business",
        "apiName": "onedriveforbusiness",
    },
}

# Deterministic secondary GUIDs derived from package guid + connector name.
def secondary_guid(seed: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, seed))


def fix_connector_inputs(node: dict | None) -> None:
    """PA legacy import rejects inputs.authentication; wants connectionReferenceName."""
    if not isinstance(node, dict):
        return

    kind = node.get("type", "")
    if isinstance(kind, str) and kind.startswith("OpenApiConnection"):
        inputs = node.get("inputs")
        if isinstance(inputs, dict):
            inputs.pop("authentication", None)
            host = inputs.get("host")
            if isinstance(host, dict):
                conn = (
                    host.get("connectionName")
                    or host.get("connectionReferenceName")
                    or host.get("connection")
                )
                if conn:
                    host.pop("connection", None)
                    host["connectionName"] = conn
                    host["connectionReferenceName"] = conn

    if kind in ("Foreach", "Scope", "Until") and isinstance(node.get("actions"), dict):
        for action in node["actions"].values():
            fix_connector_inputs(action)
    elif kind == "If":
        if isinstance(node.get("actions"), dict):
            for action in node["actions"].values():
                fix_connector_inputs(action)
        else_actions = (node.get("else") or {}).get("actions")
        if isinstance(else_actions, dict):
            for action in else_actions.values():
                fix_connector_inputs(action)
    elif kind == "Switch":
        cases = node.get("cases") or {}
        if isinstance(cases, dict):
            for case in cases.values():
                if isinstance(case, dict) and isinstance(case.get("actions"), dict):
                    for action in case["actions"].values():
                        fix_connector_inputs(action)
        default_actions = (node.get("default") or {}).get("actions")
        if isinstance(default_actions, dict):
            for action in default_actions.values():
                fix_connector_inputs(action)


def fix_action_map(action_map: dict | None) -> None:
    if isinstance(action_map, dict):
        for action in action_map.values():
            fix_connector_inputs(action)


def convert_connection_references(sol_refs: dict) -> dict:
    """Solution-export connection refs -> package-style refs with api id."""
    out = {}
    for name, body in (sol_refs or {}).items():
        meta = CONNECTOR_META.get(name, {})
        api_name = (body.get("api") or {}).get("name", name)
        runtime = body.get("runtimeSource", "embedded")
        out[name] = {
            "runtimeSource": runtime,
            "connection": {"name": name},
            "api": {"name": api_name},
            # Fields used by the package resource graph:
            "id": meta.get("id", f"/providers/Microsoft.PowerApps/apis/{api_name}"),
            "apiName": meta.get("apiName", api_name.replace("shared_", "")),
            "source": "Embedded" if runtime == "embedded" else "Invoker",
            "connectionName": name,
            "displayName": meta.get("displayName", name),
        }
    return out


def replace_sharepoint_env_var(definition: dict) -> dict:
    """Swap Dataverse env-var parameter for a plain string site URL parameter."""
    params = definition.setdefault("parameters", {})
    old_key = "SharePoint Site URL (wsr_SharePointSiteUrl)"
    if old_key in params:
        params.pop(old_key)
    params["SharePointSiteUrl"] = {
        "defaultValue": "https://YOURTENANT.sharepoint.com/sites/YourSite",
        "type": "String",
        "metadata": {
            "description": "Full URL of the SharePoint site hosting EventSessionRegistration_* lists"
        },
    }

    def rewrite(obj):
        if isinstance(obj, dict):
            for k, v in list(obj.items()):
                if isinstance(v, str) and old_key in v:
                    obj[k] = v.replace(
                        f"parameters('{old_key}')", "parameters('SharePointSiteUrl')"
                    )
                else:
                    rewrite(v)
        elif isinstance(obj, list):
            for item in obj:
                rewrite(item)

    rewrite(definition)
    return definition


def build_inner_definition(sol_json: dict, replace_env_var: bool) -> dict:
    props = sol_json["properties"]
    definition = copy.deepcopy(props["definition"])

    # Keep custom parameters (e.g. SharePointSiteUrl) plus PA required ones.
    parameters = definition.get("parameters") or {}
    parameters.setdefault(
        "$authentication", {"defaultValue": {}, "type": "SecureObject"}
    )
    parameters.setdefault("$connections", {"defaultValue": {}, "type": "Object"})
    definition["parameters"] = parameters

    if replace_env_var:
        definition = replace_sharepoint_env_var(definition)

    fix_action_map(definition.get("triggers"))
    fix_action_map(definition.get("actions"))
    return definition


def build_package(flow_meta: dict) -> Path:
    sol_json = json.loads((SRC / flow_meta["file"]).read_text())
    props = sol_json["properties"]
    conn_refs = convert_connection_references(props.get("connectionReferences", {}))
    inner_def = build_inner_definition(
        sol_json, replace_env_var=flow_meta.get("replace_env_var", False)
    )

    package_guid = flow_meta["package_guid"]
    flow_guid = flow_meta["flow_guid"]
    name = flow_meta["name"]

    # Resource graph: one API + one connection per connector used
    conn_resources = []
    for ref_name, body in conn_refs.items():
        api_guid = secondary_guid(f"{package_guid}:api:{ref_name}")
        connection_guid = secondary_guid(f"{package_guid}:conn:{ref_name}")
        conn_resources.append(
            {
                "ref_name": ref_name,
                "api_id": body["id"],
                "api_display_name": body.get("displayName", ref_name),
                "api_guid": api_guid,
                "connection_guid": connection_guid,
            }
        )

    flow_depends = []
    for r in conn_resources:
        flow_depends.append(r["api_guid"])
        flow_depends.append(r["connection_guid"])

    resources = {
        package_guid: {
            "type": "Microsoft.Flow/flows",
            "suggestedCreationType": "New",
            "creationType": "Existing, New, Update",
            "details": {"displayName": name},
            "configurableBy": "User",
            "hierarchy": "Root",
            "dependsOn": flow_depends,
        }
    }
    for r in conn_resources:
        resources[r["api_guid"]] = {
            "id": r["api_id"],
            "name": r["ref_name"],
            "type": "Microsoft.PowerApps/apis",
            "suggestedCreationType": "Existing",
            "details": {"displayName": r["api_display_name"]},
            "configurableBy": "System",
            "hierarchy": "Child",
            "dependsOn": [],
        }
        resources[r["connection_guid"]] = {
            "type": "Microsoft.PowerApps/apis/connections",
            "suggestedCreationType": "Existing",
            "creationType": "Existing",
            "details": {"displayName": r["api_display_name"]},
            "configurableBy": "User",
            "hierarchy": "Child",
            "dependsOn": [r["api_guid"]],
        }

    root_manifest = {
        "schema": "1.0",
        "details": {
            "displayName": name,
            "description": flow_meta.get("description", ""),
            "createdTime": "2026-08-31T00:00:00.0000000Z",
            "packageTelemetryId": secondary_guid(f"{package_guid}:telemetry"),
            "creator": "N/A",
            "sourceEnvironment": "",
        },
        "resources": resources,
    }

    inner_manifest = {
        "packageSchemaVersion": "1.0",
        "flowAssets": {"assetPaths": [package_guid]},
    }

    # Package-style connectionReferences for the envelope (drop logical-name shape)
    envelope_conn_refs = {}
    for ref_name, body in conn_refs.items():
        envelope_conn_refs[ref_name] = {
            "runtimeSource": body["runtimeSource"],
            "connection": {"name": ref_name},
            "api": {"name": body["api"]["name"]},
        }

    definition_envelope = {
        "name": flow_guid,
        "id": f"/providers/Microsoft.Flow/flows/{flow_guid}",
        "type": "Microsoft.Flow/flows",
        "properties": {
            "apiId": "/providers/Microsoft.PowerApps/apis/shared_logicflows",
            "displayName": name,
            "definition": inner_def,
            "connectionReferences": envelope_conn_refs,
            "flowFailureAlertSubscribed": False,
            "isManaged": False,
        },
    }

    apis_map = {r["ref_name"]: r["api_guid"] for r in conn_resources}
    connections_map = {r["ref_name"]: r["connection_guid"] for r in conn_resources}

    out_path = OUT_DIR / f"{name}.zip"
    files = {
        "manifest.json": json.dumps(root_manifest, indent=2).encode("utf-8"),
        "Microsoft.Flow/flows/manifest.json": json.dumps(
            inner_manifest, indent=2
        ).encode("utf-8"),
        f"Microsoft.Flow/flows/{package_guid}/apisMap.json": json.dumps(
            apis_map, indent=2
        ).encode("utf-8"),
        f"Microsoft.Flow/flows/{package_guid}/connectionsMap.json": json.dumps(
            connections_map, indent=2
        ).encode("utf-8"),
        f"Microsoft.Flow/flows/{package_guid}/definition.json": json.dumps(
            definition_envelope, indent=2
        ).encode("utf-8"),
    }

    if out_path.exists():
        out_path.unlink()
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for arcname, data in files.items():
            info = zipfile.ZipInfo(filename=arcname)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3  # Unix
            z.writestr(info, data)

    return out_path


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FLOW_COPY.mkdir(parents=True, exist_ok=True)
    built = []
    for flow in FLOWS:
        path = build_package(flow)
        copy_path = FLOW_COPY / path.name
        copy_path.write_bytes(path.read_bytes())
        built.append(path)
        # Validate structure
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            assert "manifest.json" in names, path
            assert any(n.endswith("definition.json") for n in names), path
            json.loads(z.read("manifest.json"))
        print(f"OK {path.name} ({path.stat().st_size} bytes)")

    # Combined archive of all six packages for easy download
    combined = OUT_DIR / "EventSessionRegistrationFlows_NoTemplates_Packages.zip"
    if combined.exists():
        combined.unlink()
    with zipfile.ZipFile(combined, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in built:
            info = zipfile.ZipInfo(filename=p.name)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            z.writestr(info, p.read_bytes())
    (FLOW_COPY / combined.name).write_bytes(combined.read_bytes())
    print(f"OK {combined.name} ({combined.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
