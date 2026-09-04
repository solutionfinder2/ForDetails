# Deployment Runbook â€” Minimal Edition

Step-by-step guide to deploy the minimal (3-screen) Weekly Session
Registration app into a new environment/tenant. Total time: roughly
60â€“90 minutes. Do the phases **in order** â€” the app expects the lists
and flows to exist before you paste the screens.

Full column-by-column list metadata lives in **`Docs/LISTS.md`**.

---

## Phase 0 â€” Prerequisites

- A SharePoint site to host the lists (you need at least **Edit** on it;
  the list-creation scripts need **Sites.Manage.All** consent via
  device-code sign-in).
- A Power Platform environment where you can import flows and create
  canvas apps.
- Licenses/connectors: SharePoint, Office 365 Outlook, Office 365 Users,
  Office 365 Groups, OneDrive for Business, Microsoft Teams.
- Windows PowerShell 5.1 or newer (for the Graph scripts â€” no modules
  needed).

---

## Phase 1 â€” SharePoint lists

### 1.1 Run the list creation script

From this kit's `SharePoint/` folder (see `RUN-SCRIPT.md` for the
click-by-click version):

```powershell
.\CreateLists-Graph.ps1 -SitePath "yourtenant.sharepoint.com:/sites/YourSite" -WeeksToSeed 4 -Capacity 20
```

The script signs in with a device code, then creates (or completes) the
lists with all their columns:

| List | Used by minimal edition? |
|---|---|
| `EventSessionRegistration_Events` | Yes |
| `EventSessionRegistration_SessionTimeSlots` | Yes |
| `EventSessionRegistration_Registrations` | Yes |
| `EventSessionRegistration_AppRoles` | Yes |
| `EventSessionRegistration_EmailTemplates` | **No** â€” created by the script but ignored by this edition; you can leave it or delete it |

It also seeds a **General Sessions** catch-all event and Monâ€“Fri time
slots for the number of weeks you chose (`-WeeksToSeed 0` for none).

### 1.2 Run the metadata columns script

Adds the newer registration/event metadata columns (safe to run on lists
that already have some of them â€” it skips existing columns):

```powershell
.\AddMetadataColumns-Graph.ps1 -SitePath "yourtenant.sharepoint.com:/sites/YourSite"
```

> Edit the `$DepartmentChoices`, `$SiteLocationChoices` and
> `$OrgUnitChoices` arrays at the top of the script **before** running it
> so the dropdowns match your organization.

### 1.3 Manual columns (Graph API cannot create these)

On **`EventSessionRegistration_Events`**, add three columns by hand
(list > **+ Add column**):

| Column name | Type |
|---|---|
| `EventImage` | **Image** |
| `EventLink` | **Hyperlink** |
| `SPSiteURL` | **Hyperlink** |

### 1.4 Verify

Open each list > list settings and compare against `Docs/LISTS.md`.
The most common miss is the three manual columns above.

---

## Phase 2 â€” Power Automate flows

### 2.1 Import the solution (preferred)

1. [make.powerautomate.com](https://make.powerautomate.com) > pick the
   environment > **Solutions** > **Import solution**.
2. Select `Flow/EventSessionFlows_NoTemplates_1_0_0_17.zip`.
3. Map the **four connections** when prompted: SharePoint, Office 365
   Outlook, OneDrive for Business, Microsoft Teams (create them if they
   don't exist).
4. After import, open the solution and turn **all seven flows On**:
   - `EventSession_SendAppEmail`
   - `EventSession_ExportCSV`
   - `EventSession_AddToCalendar`
   - `EventSession_SessionReminderDaily`
   - `EventSession_SendReportEmail`
   - `EventSession_ShareEvent`
   - `EventSession_SyncExternalList`

> If the solution import fails in your environment (for example no
> Dataverse database), fall back to the **legacy per-flow packages** in
> `Flow/Packages/` â€” **My flows > Import > Import Package (Legacy)**,
> one zip at a time. See `Flow/Packages/IMPORT.md`.

### 2.2 Post-import touch-ups

1. **`EventSession_SessionReminderDaily`** â€” edit the flow, open the
   **Get items** step, and change **Site Address** from the
   `https://yourtenant.sharepoint.com/...` placeholder to your real site;
   re-pick **List Name** = `EventSessionRegistration_Registrations`.
   This is the only flow with a hardcoded site.
2. **`EventSession_ExportCSV`** â€” create the folder **`/CSV Exports`**
   in the flow owner's OneDrive (the flow writes the CSV there before
   attaching it).
3. The other flows receive site/list/recipient values from the app at
   run time â€” nothing to edit.

---

## Phase 3 â€” Build the canvas app

### 3.1 Create the app

1. [make.powerapps.com](https://make.powerapps.com) > **Create** >
   **Blank app** > Blank **canvas** app > **Tablet** format.
2. **Settings > Display**: turn **Scale to fit OFF** (required for the
   responsive containers).

### 3.2 Add data sources

**Data pane > Add data:**

- The four lists: `EventSessionRegistration_Events`,
  `_SessionTimeSlots`, `_Registrations`, `_AppRoles`.
- Connectors: **Office 365 Users**, **Office 365 Groups**.

**Power Automate pane (âš¡) > Add flow** â€” add the six app-called flows:

- `EventSession_SendAppEmail`
- `EventSession_ExportCSV`
- `EventSession_AddToCalendar`
- `EventSession_SendReportEmail`
- `EventSession_ShareEvent`
- `EventSession_SyncExternalList`

(Do **not** add `SessionReminderDaily` â€” it is schedule-only.)

### 3.3 App.OnStart and StartScreen

1. Select the **App** object in the tree view, pick **OnStart**, and
   paste the entire contents of `App/OnStart.txt`.
2. Set the **StartScreen** property to:

```
If(!IsBlank(Param("eventid")), scrEventQuickReg, scrIntro)
```

### 3.4 Paste the screens

For each YAML file in `App/Screens/` (any order):

1. In the tree view: **New screen** > blank.
2. Right-click the new screen > **View code** (or Ctrl+Shift+V, requires
   the "Power Apps Studio source code" preview feature if not visible).
3. Select everything, paste the file contents, save.
4. Rename the screen if Studio did not pick up the name (`scrIntro`,
   `scrEventQuickReg`, `scrAdmin`).
5. Delete the default `Screen1`.

Screen `OnVisible` formulas are embedded in the YAML â€” there is nothing
to set per screen.

### 3.5 First publish + app URL

1. **Save** and **Publish** the app once.
2. Get the app's web link: make.powerapps.com > **Apps** > **â€¦** on the
   app > **Details** > **Web link**.
3. Back in Studio, open `App.OnStart` and paste the link into
   `Set(varAppURL, "â€¦")` â€” this powers the Share Event deep links
   (`?eventid=<ID>`).
4. Save and publish again.

---

## Phase 4 â€” Configuration

### 4.1 Bootstrap your admin role

While `EventSessionRegistration_AppRoles` is **empty, everyone is
treated as an Admin** (so you can't lock yourself out). Immediately:

1. Open the list and add a row: `UserEmail` = yourself (people picker),
   `Role` = **Admin**.
2. Then add other Admins/Coordinators as needed. Everyone not in the
   list is a regular user.

### 4.2 Promote the featured event (Intro page)

Pick one (details in `App/OnStart.txt` comments):

- **Option A (recommended, no republish):** set the **IsPromoted**
  column to Yes on exactly one item in `EventSessionRegistration_Events`.
- **Option B:** set `Set(varPromotedEventID, <ID>)` in `App.OnStart` and
  republish. A value > 0 wins over the IsPromoted column.

### 4.3 External list sync (optional, per event)

Only needed if an event should mirror its registrations to another
SharePoint list (the `EventSession_SyncExternalList` flow):

1. Provision the target list with the contract columns:

```powershell
.\SetupExternalList-Graph.ps1 -SiteUrl "https://yourtenant.sharepoint.com/sites/OtherSite" -ListName "EventRegistrations_External"
# add -WithScenarioColumns for the optional staff / author / hour columns
```

2. In the app: **Admin > edit the event > Settings tab**, set
   **SharePoint Site URL** and **SharePoint List Name** to the values
   above. Leave them blank to disable syncing for that event.
3. The account that owns the flows' SharePoint connection must have
   **Edit** rights on the target site.

Contract and optional columns are documented in `Docs/LISTS.md`.

### 4.4 Share the app

Share the canvas app with your users (make.powerapps.com > Apps > Share).
Data-source permission notes are in `Docs/SOP.md` Â§ "Access and roles".

---

## Phase 5 â€” Smoke test

Run through this list end to end before announcing the app:

1. **Intro** loads and shows the promoted event card; "Get Started"
   opens the event page.
2. **Register** for a session (fill phone, department, site, questions)
   â€” you get the confirmation modal, a **confirmation email**, and a
   **Teams card** with proper line breaks.
3. The session's seat count decreased; the calendar day shows your green
   "Mine" count.
4. **Switch** to another session â€” confirmation + email.
5. **Register for someone else** (if enabled on the event) â€” the
   registration appears under **My Registrations > For others**.
6. **Cancel** â€” seat released, cancellation email received.
7. **Add to Calendar** on a registration card â€” Outlook event created.
8. **Share Event** â€” recipient gets the email; the link opens the app
   directly on the event page (`?eventid=` deep link).
9. **Admin**: create an event, add sessions, edit a session, watch the
   dashboard tiles update.
10. **Reports** tab: Download CSV works (check the file opens in Excel);
    Send Report delivers the email with attachment.
11. If an event has SPSiteURL/SPListName set: register, switch, and
    cancel each appear in the **external list** (check `Status`,
    `LastAction`, and â€” with scenario columns â€” `staff`, `author`,
    `hour` showing just the start time like `1:00pm`).
12. Next morning: the **daily reminder** flow ran without errors
    (flow run history).

---

## Troubleshooting quick hits

| Symptom | Fix |
|---|---|
| Import error "â€¦not declared in the solution file as a root component" | You are importing an old zip; use `EventSessionFlows_NoTemplates_1_0_0_17.zip` from this kit |
| "The solution file is invalidâ€¦" on import | You picked a legacy per-flow zip under **Solutions > Import**. Legacy zips go through **My flows > Import > Import Package (Legacy)** |
| Emails don't arrive | Flow turned off, or the Outlook connection was mapped to the wrong account. Check the flow run history |
| Teams card shows literal `\n` | Old flow version â€” re-import v1.0.0.17 |
| App treats everyone as Admin | `EventSessionRegistration_AppRoles` is empty â€” add your Admin row (4.1) |
| Deep link opens the Intro instead of the event | `StartScreen` formula not set (3.3), or `varAppURL` still blank (3.5) |
| External list not updating | Event's SPSiteURL/SPListName blank or wrong; flow connection lacks Edit on the target site; check `EventSession_SyncExternalList` run history |
| "List not found" errors in the app | List display names must match exactly, including the `EventSessionRegistration_` prefix |
