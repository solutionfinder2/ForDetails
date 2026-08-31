# Flow solution for the MINIMAL edition

`EventSessionRegistrationFlows_NoTemplates_1_0_0_8.zip` (one folder up) is
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

1. Power Automate (make.powerautomate.com) > pick the target environment >
   **Solutions** > **Import solution** > select the zip.
2. Map the three connections when prompted (SharePoint, Outlook,
   Office 365 Users) - create them if they don't exist yet.
3. Enter the **SharePoint Site URL** environment variable value: the full
   URL of the site that hosts the `EventSessionRegistration_*` lists,
   e.g. `https://yourtenant.sharepoint.com/sites/YourSite`.
4. After import, open the solution and turn every flow **On**.
5. In the app, remove/re-add the flows if Studio flags stale references.

> This is the same package as the full project's NoTemplates build - same
> solution unique name and flow IDs. Import only one flow package per
> environment; importing this over an existing install replaces the flows
> in place (if Dataverse rejects a same-version import, bump `<Version>`
> in `solution.xml` and re-zip).
