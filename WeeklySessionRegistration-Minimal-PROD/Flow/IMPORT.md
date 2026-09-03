# Importing the flows (Minimal edition)

`EventSessionFlows_NoTemplates_1_0_0_15.zip` is the flow package that
pairs with the minimal app. It contains all **seven** flows, is
tenant-neutral, and has **no EmailTemplates list dependency** (this
edition sends emails with hardcoded subject/body from the screens).

| Flow | What it does | Added to the app in Studio? |
|---|---|---|
| `EventSession_SendAppEmail` | Register / switch / cancel email + Teams adaptive card | Yes |
| `EventSession_ExportCSV` | Builds the CSV for Download (OneDrive `/CSV Exports`) | Yes |
| `EventSession_AddToCalendar` | Creates the Outlook event for a registration | Yes |
| `EventSession_SendReportEmail` | Emails the registration report with CSV attached | Yes |
| `EventSession_ShareEvent` | "Someone shared an event with you" email with deep link | Yes |
| `EventSession_SyncExternalList` | Mirrors register/switch/cancel to an event's external list | Yes |
| `EventSession_SessionReminderDaily` | Day-before reminder, 7 AM ET (email + Teams card) | **No** — schedule-only |

## Import steps (solution — preferred)

1. [make.powerautomate.com](https://make.powerautomate.com) > pick the
   target environment > **Solutions** > **Import solution** > select the
   zip.
2. Map the **four connections** when prompted — SharePoint, Office 365
   Outlook, OneDrive for Business, Microsoft Teams — creating them if
   needed. (The Teams connection posts the adaptive cards; if a recipient
   has no Teams, that step fails quietly and the flow still succeeds.)
3. After import, open **`EventSession_SessionReminderDaily`** > Edit >
   **Get items** step > set **Site Address** to the site hosting the
   `EventSessionRegistration_*` lists (it ships with a
   `https://yourtenant.sharepoint.com/...` placeholder) and re-pick the
   **List Name**. This is the only flow that needs it — the others get
   their values from the app at run time.
4. Create the folder **`/CSV Exports`** in the flow owner's OneDrive.
5. Turn **all seven flows On**.
6. In Power Apps Studio, add the six app-called flows (table above) via
   the Power Automate pane.

## If the solution import fails

Some environments (e.g. without a Dataverse database) reject hand-built
solution zips. Use the **legacy per-flow packages** in `Packages/`
instead — see `Packages/IMPORT.md`. Same flows, same IDs.

## Versioning

Same solution unique name and flow IDs as the full project's NoTemplates
build — import only one flow package per environment. Re-importing over
an existing install replaces the flows in place; if Dataverse rejects a
same-version import, bump `<Version>` in `solution.xml` and re-zip.
