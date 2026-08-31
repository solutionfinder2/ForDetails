# Flow solution for the MINIMAL edition

`EventSessionRegistrationFlows_NoTemplates_1_0_0_9.zip` (one folder up) is
the flow package that pairs with the minimal app. It contains all six
flows, is tenant-neutral, and has **no EmailTemplates list dependency** -
which matches this edition, where the app sends emails with hardcoded
subject/body.

## Styled email notifications

Every email the solution sends is wrapped in the branded HTML shell
(dark `#373F4B` header bar, white content card, gray footer):

| Flow | Email it sends | Where the text comes from |
|---|---|---|
| `EventSessionRegistration_SendAppEmail` | Register / switch / cancel notifications | The app passes plain text; the flow converts line breaks and wraps it in the HTML shell |
| `EventSessionRegistration_SessionReminderDaily` | Day-before reminder (7 AM ET) | Hardcoded inside the flow, already in the HTML shell |
| `EventSessionRegistration_ShareEvent` | "Someone shared an event with you" | Built inside the flow, in the HTML shell |
| `EventSessionRegistration_SendReportEmail` | Registration report with CSV attachment | Built inside the flow, in the HTML shell |
| `EventSessionRegistration_ExportCSV` | (no email - returns the CSV to the app) | - |
| `EventSessionRegistration_AddToCalendar` | (no email - creates an Outlook event) | - |

To change email wording in this edition: app-triggered text lives in the
screens (`btnRegModalConfirm_EvQ`, `btnCancelEvQConfirm` in
`scrEventQuickReg.yaml`; `btnRRowCancel` in `scrAdmin.yaml`); the reminder
text lives in the `SessionReminderDaily` flow designer; the shared HTML
shell lives in each flow's "Send an email (V2)" action body.

## Import steps

1. Open **Power Apps** or **Power Automate** → pick the target environment →
   **Solutions** → **Import solution** → select
   `EventSessionRegistrationFlows_NoTemplates_1_0_0_9.zip`.
   - Do **not** use **My flows → Import** (legacy package). That path
     expects a different zip format and will fail on this file.
2. Map the three connections when prompted:
   - **WSR SharePoint** → a SharePoint connection
   - **WSR Office 365 Outlook** → an Outlook connection
   - **WSR OneDrive for Business** → a OneDrive connection
   Create any missing connection first, then finish the mapping.
3. Enter the **SharePoint Site URL** environment variable value: the full
   URL of the site that hosts the `EventSessionRegistration_*` lists,
   e.g. `https://yourtenant.sharepoint.com/sites/YourSite`.
4. After import, open the solution and turn every flow **On**.
5. In the app, remove/re-add the flows if Studio flags stale references.

## Troubleshooting import errors

| Symptom | Fix |
|---|---|
| Import rejected / "same or older version" | This package is **1.0.0.9**. It upgrades an existing `EventSessionRegistrationFlows` install (including the Universal 1.0.0.8 package). If you still hit a version block, delete the old solution (keep customizations if offered) or bump `<Version>` in `solution.xml` and re-zip. |
| "Invalid package" / missing manifest | You used **My flows → Import**. Use **Solutions → Import solution** instead. |
| Connection mapping step fails | Create SharePoint, Outlook, and OneDrive connections in the environment first, then re-run import. |
| Flows import but stay Off | Open the solution → select each flow → **Turn on**. |

> Same solution unique name (`EventSessionRegistrationFlows`) and flow IDs
> as the Universal package. Import **only one** of these flow packages per
> environment; NoTemplates replaces Universal in place when the version is
> higher.
