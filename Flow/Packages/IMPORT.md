# Import the minimal-edition flows (correct format)

The hand-built **Dataverse solution** zip is **not** a reliable import format
for these flows (Power Platform rejects it as the wrong / invalid package
type). Use the **Power Automate Package (Legacy)** zips in this folder instead.

## What to download

| File | Use |
|---|---|
| `EventSessionRegistrationFlows_NoTemplates_Packages.zip` | All six flow packages in one download (unzip first) |
| `EventSession_SendAppEmail.zip` | Single flow |
| `EventSession_ExportCSV.zip` | Single flow |
| `EventSession_AddToCalendar.zip` | Single flow |
| `EventSession_SendReportEmail.zip` | Single flow |
| `EventSession_ShareEvent.zip` | Single flow |
| `EventSession_SessionReminderDaily.zip` | Single flow (scheduled) |

Also mirrored under `/Flow/Packages/` in the repo root.

## Import steps (do this for each of the six zips)

1. Open [Power Automate](https://make.powerautomate.com) and select your environment.
2. Go to **My flows** → **Import** → **Import Package (Legacy)**.
3. **Upload** one of the flow `.zip` files from this folder
   (for example `EventSession_SendAppEmail.zip`).
4. Under the flow row, set **Import setup** to **Create as new**.
5. Under related resources (Outlook / SharePoint / OneDrive), open each row
   and select or create the matching **connection**, then **Save**.
6. Click **Import**.
7. After import, open the flow → **Turn on**.
8. Repeat for the other five packages.

> Do **not** use **Solutions → Import solution** with these files.
> Do **not** use the old `EventSessionRegistrationFlows_NoTemplates_*.zip`
> Dataverse solution package — that is the format that fails validation.

## After all six are imported

1. **SessionReminderDaily only:** edit the flow → open **Get items** →
   set **Site Address** to your SharePoint site  
   (default placeholder is `https://YOURTENANT.sharepoint.com/sites/YourSite`).
   List name stays `EventSessionRegistration_Registrations`.
2. Create OneDrive folder **`/CSV Exports`** (used by ExportCSV).
3. In Power Apps Studio, **Add data → Flows** and add:
   - `EventSession_SendAppEmail`
   - `EventSession_ExportCSV`
   - `EventSession_AddToCalendar`
   - `EventSession_SendReportEmail`
   - `EventSession_ShareEvent`  
   (Do not add SessionReminderDaily to the app — it is schedule-only.)

## Prefer building in the designer?

See `../MANUAL-FLOWS.md` for a full click-by-click guide.
