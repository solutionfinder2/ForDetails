# Import the flows via Package (Legacy) — fallback method

Use these zips when **Solutions > Import solution** rejects the solution
package in your environment. Same seven flows, same IDs.

## What to download

| File | Use |
|---|---|
| `EventSessionFlows_NoTemplates_Packages.zip` | All seven flow packages in one download (unzip first) |
| `EventSession_SendAppEmail.zip` | Single flow |
| `EventSession_ExportCSV.zip` | Single flow |
| `EventSession_AddToCalendar.zip` | Single flow |
| `EventSession_SendReportEmail.zip` | Single flow |
| `EventSession_ShareEvent.zip` | Single flow |
| `EventSession_SyncExternalList.zip` | Single flow |
| `EventSession_SessionReminderDaily.zip` | Single flow (scheduled) |

## Import steps (repeat for each of the seven zips)

1. Open [Power Automate](https://make.powerautomate.com) and select your
   environment.
2. **My flows** → **Import** → **Import Package (Legacy)**.
3. **Upload** one of the flow `.zip` files.
4. Under the flow row, set **Import setup** to **Create as new**.
5. Under related resources (SharePoint / Outlook / OneDrive / Teams),
   open each row and select or create the matching **connection**, then
   **Save**.
6. Click **Import**, then open the flow and **Turn on**.

> Do **not** upload these zips under **Solutions → Import solution** —
> that page only accepts the solution package
> (`../EventSessionFlows_NoTemplates_1_0_0_15.zip`) and fails these with
> "The solution file is invalid".

## After all seven are imported

1. **SessionReminderDaily only:** edit the flow → **Get items** → set
   **Site Address** to your SharePoint site (placeholder is
   `https://yourtenant.sharepoint.com/...`); List Name stays
   `EventSessionRegistration_Registrations`.
2. Create the OneDrive folder **`/CSV Exports`** (used by ExportCSV).
3. In Power Apps Studio, **Power Automate pane → Add flow**:
   - `EventSession_SendAppEmail`
   - `EventSession_ExportCSV`
   - `EventSession_AddToCalendar`
   - `EventSession_SendReportEmail`
   - `EventSession_ShareEvent`
   - `EventSession_SyncExternalList`

   (Do not add SessionReminderDaily — it is schedule-only.)

## Prefer building in the designer?

See `../MANUAL-FLOWS.md` for a full click-by-click guide.
