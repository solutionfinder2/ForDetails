# Manual flow build guide — Minimal edition (No Templates)

Use this when you prefer to build the six Power Automate flows by hand
instead of importing `EventSessionRegistrationFlows_NoTemplates_1_0_0_9.zip`.

Flow **names must match exactly** (including underscores). The canvas app
calls them by name.

| # | Flow name | Trigger | Connectors |
|---|---|---|---|
| 1 | `EventSessionRegistration_SendAppEmail` | Power Apps (V2) | Office 365 Outlook |
| 2 | `EventSessionRegistration_ExportCSV` | Power Apps (V2) | OneDrive for Business |
| 3 | `EventSessionRegistration_AddToCalendar` | Power Apps (V2) | Office 365 Outlook |
| 4 | `EventSessionRegistration_SendReportEmail` | Power Apps (V2) | Office 365 Outlook |
| 5 | `EventSessionRegistration_ShareEvent` | Power Apps (V2) | Office 365 Outlook |
| 6 | `EventSessionRegistration_SessionReminderDaily` | Recurrence | SharePoint + Outlook |

**Prerequisites**

1. SharePoint lists exist: `EventSessionRegistration_Events`,
   `_SessionTimeSlots`, `_Registrations`, `_AppRoles`
   (no `EmailTemplates` list for this edition).
2. In Power Automate, create connections for **Office 365 Outlook**,
   **SharePoint**, and **OneDrive for Business** under your account.
3. Create a OneDrive folder named **`CSV Exports`** in the root of the
   account that owns the OneDrive connection (ExportCSV writes there).

**Designer tips used throughout**

- When an input says *Ask in Power Apps*, that becomes a Power Apps (V2)
  trigger parameter. Use the **exact** titles below.
- For HTML email bodies, switch the Outlook **Body** field to **Code view**
  (or the `</>` HTML editor) and paste the HTML.
- After each flow is saved, turn it **On**, then in Power Apps Studio add
  it via **Add data → Flows**.

---

## Shared branded email shell

`SendAppEmail` and `SessionReminderDaily` wrap content in this HTML.
Keep it as one line or paste as-is into the Outlook Body (HTML).

```html
<div style='margin:0;padding:24px;background-color:#F6F7FB;font-family:Segoe UI,Arial,sans-serif;'><div style='max-width:600px;margin:0 auto;background-color:#FFFFFF;border:1px solid #E4E7EF;border-radius:12px;overflow:hidden;'><div style='background-color:#373F4B;padding:20px 28px;'><span style='color:#FFFFFF;font-size:18px;font-weight:bold;'>Weekly Session Registration</span></div><div style='padding:28px;color:#28303F;font-size:14px;line-height:1.6;'>CONTENT_HERE</div><div style='padding:16px 28px;background-color:#F6F7FB;border-top:1px solid #E4E7EF;color:#68738A;font-size:12px;'>This is an automated message from the Weekly Session Registration app. Please do not reply.</div></div></div>
```

Replace `CONTENT_HERE` with the per-flow content noted below.

---

## 1. `EventSessionRegistration_SendAppEmail`

Used for register / switch / cancel emails from the app.

1. Power Automate → **Create** → **Instant cloud flow**.
2. Name: `EventSessionRegistration_SendAppEmail`.
3. Trigger: **Power Apps (V2)** → Create.
4. On the trigger, add three text inputs (**Add an input → Text**), all required:

   | Title | Purpose |
   |---|---|
   | `To` | Recipient email |
   | `Subject` | Email subject |
   | `Body` | Plain-text body from the app |

5. Add action **Office 365 Outlook – Send an email (V2)**:
   - **To**: dynamic value `To` from the trigger  
   - **Subject**: dynamic value `Subject`  
   - **Importance**: Normal  
   - **Body** (HTML / code view): paste the branded shell, and for
     `CONTENT_HERE` insert this expression (Expression tab):

     ```
     replace(triggerBody()?['text_2'], decodeUriComponent('%0A'), '<br>')
     ```

     In the designer, after you name the third input `Body`, the dynamic
     content token is usually shown as **Body**. In **Expression** form it
     is often `triggerBody()?['text_2']` (Power Apps V2 maps inputs as
     `text`, `text_1`, `text_2`, … in creation order). Prefer picking
     **Body** from Dynamic content when available; use the expression only
     if you need the newline→`<br>` replace.

     Practical approach in the designer:
     1. Paste the HTML shell into Body.
     2. Put the cursor where `CONTENT_HERE` was.
     3. Add an **Expression**:
        `replace(<Body dynamic content>, decodeUriComponent('%0A'), '<br>')`
        — or build it with **Compose** first (see tip below).

6. Add action **Respond to a Power App or flow**:
   - Add an output → Text  
   - Title: `result`  
   - Value: `ok`

7. **Save** → turn the flow **On**.

**Compose tip (easier):** before Send email, add **Data Operation – Compose**:

```
replace(triggerBody()?['text_2'], decodeUriComponent('%0A'), '<br>')
```

Then in the HTML shell, insert **Outputs** of that Compose where the
message text goes.

---

## 2. `EventSessionRegistration_ExportCSV`

Creates a CSV in OneDrive and returns a share link to the app.

1. Create → Instant cloud flow → name
   `EventSessionRegistration_ExportCSV` → trigger **Power Apps (V2)**.
2. Trigger inputs (Text, required):

   | Title | Purpose |
   |---|---|
   | `FileName` | e.g. `Registrations_20260831.csv` |
   | `CsvContent` | Full CSV text |

3. Action **OneDrive for Business – Create file**:
   - **Folder Path**: `/CSV Exports` (pick or type; create the folder first)
   - **File Name**: `FileName` from trigger
   - **File Content**: Expression:

     ```
     concat(decodeUriComponent('%EF%BB%BF'), triggerBody()?['text_1'])
     ```

     (`text_1` = second input `CsvContent`; or use Dynamic content
     `CsvContent` inside `concat` via Expression if the designer allows.)

     Simpler alternative: add a **Compose** with
     `concat(decodeUriComponent('%EF%BB%BF'), <CsvContent>)`, then use
     Compose output as File Content. The BOM (`%EF%BB%BF`) helps Excel
     open UTF-8 correctly.

4. Action **OneDrive for Business – Create share link (V2)** (or
   **Create share link** if V2 is not listed):
   - **File**: Id from **Create file**
   - **Link type**: View  
   - **Link scope**: Organization  

5. Action **Respond to a Power App or flow**:
   - Output Text titled **`fileurl`** (name must be exact — the app reads
     `res.fileurl`)
   - Value: **Web URL** (or `WebUrl`) from Create share link

6. Save → turn **On**.

---

## 3. `EventSessionRegistration_AddToCalendar`

Creates an event on the **signed-in user's** Outlook calendar.

1. Instant cloud flow → name
   `EventSessionRegistration_AddToCalendar` → **Power Apps (V2)**.
2. Trigger inputs (Text, all required):

   | Title | Purpose |
   |---|---|
   | `Subject` | Calendar subject |
   | `Body` | Event body (plain text) |
   | `Start` | `yyyy-MM-ddTHH:mm:ss` local |
   | `End` | `yyyy-MM-ddTHH:mm:ss` local |
   | `Location` | Location / meeting link text |

3. Action **Office 365 Outlook – Get calendars (V2)** (no parameters).

4. Action **Office 365 Outlook – Create event (V4)**:
   - **Calendar id**: Expression (first calendar):

     ```
     coalesce(first(outputs('Get_calendars_(V2)')?['body/value'])?['id'], first(outputs('Get_calendars_(V2)')?['body/value'])?['Id'], first(outputs('Get_calendars_(V2)')?['body/value'])?['Name'])
     ```

     If Get calendars renamed your action, adjust the action name in the
     expression, or pick the first calendar Id from Dynamic content if
     shown.
   - **Subject**: trigger `Subject`
   - **Start time**: trigger `Start`
   - **End time**: trigger `End`
   - **Time zone**: `(UTC-05:00) Eastern Time (US & Canada)`  
     (change if your org is not Eastern)
   - **Body**: trigger `Body`
   - **Location**: trigger `Location`
   - **Reminder**: `60` minutes (if the field exists)

5. **Important — run as user:** open the flow’s Outlook connection settings
   (or the **…** menu on the Outlook actions) and set the connection to
   run in the **invoker’s** context when the designer offers
   “Run only users” / invoker connection. The app expects the event on
   the person who clicked **Add to Calendar**.

6. **Respond to a Power App or flow** → Text output `result` = `ok`.

7. Save → turn **On**.

---

## 4. `EventSessionRegistration_SendReportEmail`

Sends a report email with a CSV attachment (Admin screen).

1. Instant cloud flow → name
   `EventSessionRegistration_SendReportEmail` → **Power Apps (V2)**.
2. Trigger inputs (Text, all required):

   | Title | Purpose |
   |---|---|
   | `To` | Semicolon-separated emails |
   | `Subject` | Subject |
   | `Body` | Plain-text body |
   | `FileName` | Attachment name, e.g. `Report.csv` |
   | `FileContent` | CSV text |

3. Action **Office 365 Outlook – Send an email (V2)**:
   - **To** / **Subject**: from trigger
   - **Body** (HTML):

     ```html
     <p>BODY_HTML</p>
     ```

     Where `BODY_HTML` is Expression:
     `replace(<Body>, decodeUriComponent('%0A'), '<br>')`

   - Show advanced options → **Attachments**:
     - **Name**: trigger `FileName`
     - **ContentBytes**: Expression:

       ```
       base64(concat(decodeUriComponent('%EF%BB%BF'), triggerBody()?['text_4']))
       ```

       (`text_4` = fifth input `FileContent`)

4. **Respond to a Power App or flow** → `result` = `ok`.
5. Save → turn **On**.

---

## 5. `EventSessionRegistration_ShareEvent`

Emails a share message with an “Open in the app” button.

1. Instant cloud flow → name
   `EventSessionRegistration_ShareEvent` → **Power Apps (V2)**.
2. Trigger inputs (Text, all required):

   | Title | Purpose |
   |---|---|
   | `To` | Semicolon-separated emails |
   | `Subject` | Subject |
   | `Body` | Plain-text intro from the app |
   | `EventName` | Event title for the button |
   | `EventLink` | Deep link URL |

3. Action **Office 365 Outlook – Send an email (V2)**:
   - **To** / **Subject**: from trigger
   - **Body** (HTML / code view) — paste, then replace tokens with
     Dynamic content / Expressions:

     ```html
     <p>@{replace(triggerBody()?['text_2'], decodeUriComponent('%0A'), '<br>')}</p>
     <p><a href="@{triggerBody()?['text_4']}" style="display:inline-block;padding:10px 22px;background-color:#373F4B;color:#ffffff;text-decoration:none;border-radius:8px;font-weight:600;">Open "@{triggerBody()?['text_3']}" in the app</a></p>
     <p style="color:#68738A;font-size:12px;">If the button doesn't work, copy this link into your browser:<br>@{triggerBody()?['text_4']}</p>
     ```

     Mapping: `text_2` = Body, `text_3` = EventName, `text_4` = EventLink.
     Prefer Dynamic content chips (**Body**, **EventName**, **EventLink**)
     if the designer shows them.

4. **Respond to a Power App or flow** → `result` = `ok`.
5. Save → turn **On**.

---

## 6. `EventSessionRegistration_SessionReminderDaily`

Scheduled flow: every day at 7:00 AM Eastern, email everyone with a
**Confirmed** registration for **tomorrow**. Reminder text is hardcoded
(no EmailTemplates list).

1. Create → **Scheduled cloud flow**.
2. Name: `EventSessionRegistration_SessionReminderDaily`.
3. Recurrence:
   - Frequency: **Day** / Interval: **1**
   - Time zone: **Eastern Time (US & Canada)** (or `Eastern Standard Time`)
   - At these hours: **7** (7:00 AM)
4. Action **SharePoint – Get items**:
   - **Site Address**: your site URL  
     e.g. `https://yourtenant.sharepoint.com/sites/YourSite`
   - **List Name**: `EventSessionRegistration_Registrations`
   - **Filter Query** (open advanced options):

     ```
     Status eq 'Confirmed' and SessionDate ge '@{formatDateTime(addDays(utcNow(), 1), 'yyyy-MM-dd')}' and SessionDate lt '@{formatDateTime(addDays(utcNow(), 2), 'yyyy-MM-dd')}'
     ```

     Paste into Filter Query, then use **Add dynamic content → Expression**
     for each `formatDateTime(...)` segment if the designer does not
     accept `@{...}` inline. Equivalent filters:

     - SessionDate ≥ tomorrow 00:00 (`yyyy-MM-dd`)
     - SessionDate &lt; day-after-tomorrow 00:00

   - **Top Count**: `500`

5. Action **Control – Apply to each**:
   - Select output: **value** from Get items.

6. Inside the loop, **Office 365 Outlook – Send an email (V2)**:
   - **To**: `UserEmail` from current item
   - **Subject** (Expression / concat):

     ```
     Reminder: @{coalesce(items('Apply_to_each')?['EventName'], 'your session')} tomorrow - @{coalesce(items('Apply_to_each')?['TimeSlot'], '')}
     ```

     Or build with Dynamic content:  
     `Reminder: ` + EventName + ` tomorrow - ` + TimeSlot

   - **Body** (HTML): branded shell with this inner content:

     ```html
     Hi @{coalesce(items('Apply_to_each')?['UserName'], 'there')},<br><br>
     This is a reminder that you are registered for a session <b>tomorrow</b>.<br><br>
     Event: @{coalesce(items('Apply_to_each')?['EventName'], '-')}<br>
     Date: @{formatDateTime(items('Apply_to_each')?['SessionDate'], 'dddd, MMMM d, yyyy')}<br>
     Time: @{coalesce(items('Apply_to_each')?['TimeSlot'], '')}<br>
     Reference: WSR-@{items('Apply_to_each')?['ID']}<br><br>
     If you can no longer attend, please cancel or switch your registration in the app so the seat opens up for someone else.
     ```

     Use Dynamic content for UserName, EventName, SessionDate, TimeSlot,
     ID when possible. Format SessionDate with Expression
     `formatDateTime(..., 'dddd, MMMM d, yyyy')`.

7. Save → turn **On**.

**Note:** Column internal names must match what SharePoint uses
(`UserEmail`, `UserName`, `EventName`, `SessionDate`, `TimeSlot`,
`Status`, `ID`). If Get items shows different names, use those instead.

---

## Wire flows into the minimal app

1. In Power Apps Studio, open the app → **Add data**.
2. Add flows (search by name):

   - `EventSessionRegistration_SendAppEmail`
   - `EventSessionRegistration_ExportCSV`
   - `EventSessionRegistration_AddToCalendar`
   - `EventSessionRegistration_SendReportEmail`
   - `EventSessionRegistration_ShareEvent`

   (`SessionReminderDaily` is schedule-only — do **not** add it to the app.)

3. Confirm Power Fx calls still resolve (no red underlines on `.Run(...)`).
4. Test:
   - Register / cancel on Event page → email arrives  
   - Share Event → email with link  
   - Add to Calendar → event on your calendar  
   - Admin export → browser opens OneDrive link  
   - Admin send report → email with CSV attached  

---

## Parameter order cheat sheet (must match app `.Run()` calls)

| Flow | Argument order |
|---|---|
| SendAppEmail | To, Subject, Body |
| ExportCSV | FileName, CsvContent → returns **fileurl** |
| AddToCalendar | Subject, Body, Start, End, Location |
| SendReportEmail | To, Subject, Body, FileName, FileContent |
| ShareEvent | To, Subject, Body, EventName, EventLink |

If you rename trigger inputs or change order, the app will pass values into
the wrong fields. Keep titles and creation order as listed above.

---

## Optional: put flows in a solution

After they work:

1. Solutions → New solution → add the five Power Apps–triggered flows plus
   SessionReminderDaily.
2. Add connection references for Outlook, SharePoint, and OneDrive.
3. Export unmanaged for backup / other environments.

For ready-made packages instead of manual build, import the zips in
`Packages/` via **My flows → Import → Import Package (Legacy)**
(see `Packages/IMPORT.md`). Do not use the Dataverse solution zip under
`SolutionPackage-NoTemplates/` — Power Platform rejects that format.
