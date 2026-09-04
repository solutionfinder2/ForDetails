# Flows — Developer How-To Guide

A deep, action-by-action reference for the seven `EventSession_` Power
Automate flows: what each one does internally, every trigger parameter,
the key expressions, how the app calls them, and how to safely modify,
repackage, and troubleshoot them.

Companion docs: `DEVELOPER-GUIDE.md` (app architecture),
`LISTS.md` (list schemas), `../Flow/IMPORT.md` (importing),
`../Flow/MANUAL-FLOWS.md` (building by hand in the designer).

---

## 1. Inventory

| Flow | Trigger | Connections | Called by the app? |
|---|---|---|---|
| `EventSession_SendAppEmail` | Power Apps (V2) | Outlook, Teams | Yes |
| `EventSession_ExportCSV` | Power Apps (V2) | OneDrive | Yes |
| `EventSession_AddToCalendar` | Power Apps (V2) | Outlook | Yes |
| `EventSession_SendReportEmail` | Power Apps (V2) | Outlook | Yes |
| `EventSession_ShareEvent` | Power Apps (V2) | Outlook | Yes |
| `EventSession_SyncExternalList` | Power Apps (V2) | SharePoint | Yes |
| `EventSession_SessionReminderDaily` | Recurrence (daily, 7 AM ET) | SharePoint, Outlook, Teams | **No** — schedule-only |

Source of truth: `Flow/SolutionPackage-NoTemplates/Workflows/*.json`
(one JSON per flow, named `<Name>-<GUID>.json`). The shipped zip is
**v1.0.0.18**.

---

## 2. Shared plumbing (read this first)

### 2.1 The Power Apps V2 trigger and parameter naming

Every app-called flow uses trigger `type: Request`, `kind: PowerAppV2`.
Parameters live in the trigger's JSON schema and follow Power Apps'
auto-naming: the first text parameter is `text`, then `text_1`,
`text_2`, …; the first number is `number`. The `title` is what shows in
the designer; **the app passes arguments positionally** in
`Flow.Run(arg1, arg2, …)`, in the order the properties are declared.

Consequences when editing:

- **Never reorder or rename** existing schema properties — every
  `Flow.Run(...)` call in the app would silently shift its arguments.
- **Append** new parameters at the end, then in Studio remove and re-add
  the flow so it picks up the new signature, and update every call site.
- Prefer keeping new parameters in the `required` array. Inputs left
  **optional** (not in `required`) are passed to `Run` inside a
  *record* as the final argument, e.g.
  `SendAppEmail.Run(to, subject, body, {text_3: link})` — older call
  sites that omit the record keep working. SendAppEmail's
  `CalendarLink` uses this deliberately so 3-argument callers
  (cancellations, other editions) need no edits.

### 2.2 Connection references

The solution declares connection references with logical names
`wsr_sharedoffice365`, `wsr_sharedsharepointonline`,
`wsr_sharedonedriveforbusiness`, `wsr_sharedteams`. At import you map
each to a real connection. All actions authenticate with
`@parameters('$authentication')` — do not remove that property when
editing JSON.

Operational guidance — who should own the connections, the **Run only
users** settings, sender identity, and rebinding a mis-imported
environment — lives in **`CONNECTIONS.md`**.

`runtimeSource` is `embedded` (runs as the connection owner) except
AddToCalendar, which is **`invoker`** — the calendar event must be
created in the *user's* calendar, not the flow owner's. Keep that
distinction when rebuilding.

### 2.3 Responding to the app

App-called flows end with a `Response` action (`kind: PowerApp`)
returning a small JSON object (usually `{"result": "ok"}`; ExportCSV
returns `{"fileurl": …}`). Power Fx sees this as a **record**, which is
why call sites use:

```
If(IsError(EventSession_SomeFlow.Run(...)), Notify("...", NotificationType.Warning))
```

`IfError(Flow.Run(...), Notify(...))` does **not** work — the two arms
have different types (record vs boolean) and the formula fails to
compile.

### 2.4 The branded HTML email shell

Emails are wrapped in an inline-styled shell: light-gray page
(`#F6F7FB`), white 600px card with rounded corners, dark header bar
(`#373F4B`) titled "Weekly Session Registration", gray footer ("This is
an automated message…"). The app sends **plain text** bodies with
`Char(10)` newlines; the flow converts them for HTML:

```
replace(triggerBody()?['text_2'], decodeUriComponent('%0A'), '<br>')
```

`decodeUriComponent('%0A')` is the standard trick for a literal newline
character in a Workflow Definition Language (WDL) expression. To
rebrand, edit the `emailMessage/Body` HTML in SendAppEmail,
SessionReminderDaily, SendReportEmail, and ShareEvent — the shell is
duplicated in each.

### 2.5 Teams adaptive cards and the escaping rules (important)

SendAppEmail and SessionReminderDaily post an adaptive card via the
Teams action `PostCardToConversation` (poster **Flow bot**, location
**Chat with Flow bot**). The card is a JSON *string* in
`body/messageBody`, with WDL expressions inlined. Because the card is
parsed as JSON *after* the expressions run, dynamic text must be escaped
into the card exactly one level:

| To render… | The replace must insert… | WDL replacement literal |
|---|---|---|
| a line break | `\n` (backslash + n) in the raw card JSON | `'\n\n'` |
| a double quote | `\"` in the raw card JSON | `'\"'` |

The working body expression (inside the card string):

```
replace(replace(triggerBody()?['text_2'], '"', '\"'), decodeUriComponent('%0A'), '\n\n')
```

**History lesson:** v1.0.0.14 double-escaped these (`\\n`), and Teams
rendered literal `\n` text. If you ever see raw `\n` in a card, check
this escaping first. Note the file on disk shows one extra escaping
level again (JSON encoding of the flow definition itself) — always edit
by decoding the JSON, not by counting backslashes by eye.

Card structure (both flows): an `emphasis` header container ("WEEKLY
SESSION REGISTRATION" + a small subtitle), a bold `Large` title (the
subject), the body (SendAppEmail) or a `FactSet` with Event / Date /
Time / Reference rows (reminder), and a subtle footer. `msteams.width:
Full`, schema version 1.4.

### 2.6 "Optional" Teams step pattern

After each card post there is a `Compose` named `Teams_card_optional`
with:

```json
"runAfter": { "Post_adaptive_card_in_Teams": ["Succeeded", "Failed", "Skipped", "TimedOut"] }
```

and the flow's `Response` runs after *that*. This is deliberate: if the
recipient has no Teams (or the card fails for any reason), the flow
still succeeds and the email still counts. Keep this pattern if you add
more best-effort steps.

### 2.7 CSV byte-order mark (Excel readability)

Both CSV producers prepend a UTF-8 BOM so Excel opens the file with
correct encoding:

```
concat(decodeUriComponent('%EF%BB%BF'), triggerBody()?['text_1'])
```

Removing the BOM is how you get "the excel file is not readable" bug
reports. Leave it in.

---

## 3. Flow-by-flow reference

### 3.1 EventSession_SendAppEmail

The workhorse: one call = one branded email + one Teams card to the same
person. All register/switch/cancel notifications go through it.

**Parameters** (in `Run` order):

| # | Internal | Title | Meaning |
|---|---|---|---|
| 1 | `text` | To | Recipient email |
| 2 | `text_1` | Subject | Email subject / card title |
| 3 | `text_2` | Body | Plain text with `Char(10)` newlines |
| 4 | `text_3` | CalendarLink | **Optional.** Outlook "add event" deep link. When non-blank, the email gets an **Add to calendar** button and the Teams card gets an `Action.OpenUrl` action. The app passes it on register/switch confirmations and omits it on cancellations |

**Actions:** `Send_an_email_(V2)` (HTML shell, § 2.4) →
`Post_adaptive_card_in_Teams` (§ 2.5) → `Teams_card_optional` (§ 2.6) →
`Respond_to_a_PowerApp_or_flow` (`{"result":"ok"}`).

**App call sites** (subject/body built in Power Fx):
`btnRegModalConfirm_EvQ` (register + switch), `btnCancelEvQConfirm`
(self cancel) in `scrEventQuickReg.yaml`; `btnRRowCancel` (admin cancel)
in `scrAdmin.yaml`.

**Send as someone else:** swap `SendEmailV2` for "Send an email from a
shared mailbox (V2)" and grant the connection owner Send-As rights on
the mailbox — the trigger contract doesn't change, so no app edits.

### 3.2 EventSession_ExportCSV

**Parameters:** `text` = FileName (e.g. `Registrations.csv`),
`text_1` = CsvContent (full CSV text, built by the app).

**Actions:**

1. `Create_file` — OneDrive `CreateFile` into the fixed folder
   **`/CSV Exports`** (must exist in the connection owner's OneDrive),
   content = BOM + CSV (§ 2.7).
2. `Create_share_link` — `CreateShareLinkV2`, `type: view`,
   `scope: organization` (anyone in the tenant with the link can view).
3. `Response` — returns `{"fileurl": "<share link>"}`; the app runs
   `Launch()`/`Download()` on it.

**Notes:** the folder path and the link scope are the two things you'd
realistically change. The CSV itself (columns, filtering) is built in
the app (Admin > Reports), not in the flow.

### 3.3 EventSession_AddToCalendar

**Parameters:** `text` = Subject, `text_1` = Body,
`text_2` = Start, `text_3` = End (both `yyyy-MM-ddTHH:mm:ss` local),
`text_4` = Location.

**Actions:**

1. `Get_calendars_(V2)` (`CalendarGetTables_V2`) — lists the invoking
   user's calendars.
2. `Create_event_(V4)` (`V4CalendarPostItem`) — creates the event in
   the **first** calendar (the default). The calendar id is picked
   defensively: `coalesce(first(...)?['id'], first(...)?['Id'],
   first(...)?['Name'])` because the connector has returned different
   casings over time.
3. `Response` — `{"result":"ok"}`.

**Two hard-won gotchas:**

- `item/timeZone` must be one of the connector's **enum display
  strings** — here `(UTC-05:00) Eastern Time (US & Canada)`. Windows
  zone IDs like `Eastern Standard Time` are **rejected at save time**
  (`OpenApiOperationParameterValidationFailed`). Change this string to
  relocate the app to another timezone.
- Connection `runtimeSource` is **`invoker`** — the event lands in the
  end user's calendar. If you rebuild manually and leave it as the
  owner's connection, every event goes to the flow owner instead.

`reminderMinutesBeforeStart` is 60.

### 3.4 EventSession_SessionReminderDaily

**Trigger:** Recurrence — daily, `timeZone: Eastern Standard Time`
(valid *here*: recurrence triggers use Windows zone IDs, unlike the
calendar action above), at hour 7.

**Actions:**

1. `Get_tomorrows_registrations` — SharePoint `GetItems` with:
   - `dataset`: **`https://yourtenant.sharepoint.com/sites/YourSite`
     placeholder — the one hardcoded site in the whole solution.** Must
     be repointed after every import.
   - `table`: `EventSessionRegistration_Registrations`
   - OData `$filter`:

     ```
     Status eq 'Confirmed' and SessionDate ge '<tomorrow>' and SessionDate lt '<day after>'
     ```

     with the dates from
     `formatDateTime(addDays(utcNow(), 1), 'yyyy-MM-dd')`.
   - `$top: 500` — raise it if a single day can exceed 500
     registrations.
2. `Apply_to_each_registration` — per row: reminder **email** (HTML
   shell; Hi {UserName}, event/date/time/`WSR-{ID}` reference, "please
   cancel or switch if you can't attend"), then reminder **Teams card**
   (FactSet layout), then the optional-step Compose (§ 2.6).

**Notes:** all wording is hardcoded inside this flow (this is the
NoTemplates build) — edit the two action bodies to change it. Date
formatting uses `formatDateTime(..., 'dddd, MMMM d, yyyy')`.

### 3.5 EventSession_SendReportEmail

**Parameters:** `text` = To (semicolon-separated emails),
`text_1` = Subject, `text_2` = Body (plain text),
`text_3` = FileName, `text_4` = FileContent (CSV text).

**Actions:** one `Send_an_email_(V2)` with an attachment —
`ContentBytes: base64(concat(BOM, text_4))` (§ 2.7) — then `Response`.
Note this flow's body is a simple `<p>` wrapper, not the full branded
shell (reports go to staff, not end users).

**App call site:** Admin > Reports > Send Report modal
(`scrAdmin.yaml`, ~line 5428) — recipients come from the people picker
as a semicolon-joined string.

**If the attachment arrives as unreadable gibberish:** the
`ContentBytes` base64 expression was lost. `ContentBytes` expects
**base64** — if it holds the raw `FileContent` token (plain CSV text),
Outlook decodes that text *as if it were base64* and the attachment
becomes binary garbage. This almost always happens when someone opens
the action in the designer and re-picks the field from the
dynamic-content panel, which silently replaces the expression with the
raw token. Fix: open **Send an email (V2) > Attachments > Content**,
delete what's there, and re-enter this as an *expression* (fx tab, not
plain text):

```
base64(concat(decodeUriComponent('%EF%BB%BF'), triggerBody()?['text_4']))
```

### 3.6 EventSession_ShareEvent

**Parameters:** `text` = To (semicolon-separated), `text_1` = Subject,
`text_2` = Body, `text_3` = EventName, `text_4` = EventLink.

**Actions:** one `Send_an_email_(V2)` → `Response`. The body renders
the personal note, then a styled dark button —
`Open "{EventName}" in the app` — linking to `EventLink`, plus a
plain-text fallback link underneath.

**The deep link is built by the app**, not the flow:
`varAppURL & "?eventid=" & <event ID>`. It only works after `varAppURL`
is set in `App.OnStart` (post-first-publish step) and `StartScreen`
routes `Param("eventid")` to `scrEventQuickReg`.

### 3.7 EventSession_SyncExternalList

The most complex flow: mirrors register/switch/cancel into a
**per-event external SharePoint list** whose site and name arrive as
parameters — which is why it uses the SharePoint connector's raw
`HttpRequest` (REST) action instead of typed Get/Create/Update actions
(those require design-time site/list picks).

**Parameters (18):**

| # | Internal | Title |
|---|---|---|
| 1 | `text` | Action — `Register`, `Switch`, or `Cancel` |
| 2 | `number` | RegistrationID — item ID in `_Registrations` (the upsert key) |
| 3 | `text_1` | SiteURL (event's `SPSiteURL`) |
| 4 | `text_2` | ListName (event's `SPListName`) |
| 5 | `text_3` | Status — `Confirmed` / `Cancelled` |
| 6–17 | `text_4`…`text_16` | EventID, EventName, SessionDate, TimeSlot, UserName, UserEmail, ForSelf, SubmittedBy, PhoneNumber, DepartmentName, SiteLocation, Question1, Question2 |

**Action pipeline** (all inside the guard):

1. **`If_external_list_configured`** — outer condition: both SiteURL
   and ListName non-blank (`empty(trim(coalesce(...)))` = false). Blank
   ⇒ the flow does nothing and still returns ok — that's how events
   "opt out".
2. **`Find_existing_row`** — REST GET
   `_api/web/lists/getbytitle('<list>')/items?$select=Id&$top=1&$filter=RegistrationID eq <n>`.
   Note the list title escaping: `replace(<name>, '''', '''''')`
   doubles single quotes so a list named `O'Brien's List` can't break
   the URL.
3. **`Get_list_fields`** — REST GET
   `.../fields?$select=InternalName&$filter=Hidden eq false` — the
   basis for column-awareness.
4. **`Ensure_staff_user`** / **`Ensure_author_user`** — POST
   `_api/web/ensureuser` with claims logon
   `i:0#.f|membership|<email>` to resolve the **registrant**
   (`text_9`) and the **submitter** (`text_11`, falling back to the
   registrant when blank) into site user IDs. `ensureuser` also *adds*
   the user to the site's user list if they've never visited it.
5. **`Build_payload`** — Compose with the 16 contract fields plus
   `Title` (`"<UserName> - <EventName>"`) and
   `LastActionOn: utcNow()`.
6. **Column-aware enrichment** — three chained Composes, each checking
   `contains(string(body('Get_list_fields')), '"InternalName":"<col>"')`:
   - `Payload_with_staff` — adds `staffId` (person columns are set via
     `<InternalName>Id` in REST) when a `staff` column exists.
   - `Payload_with_author` — adds `author0Id` when `author0` exists
     (display name "author"; internal name differs because "Author" is
     reserved).
   - `Payload_final` — adds `hour` when the column exists: the slot
     label's **start time**, extracted by normalizing the **en dash**
     to a hyphen, splitting, trimming, lowercasing, and stripping
     spaces — `1:00 PM – 2:00 PM` → `1:00pm`:

     ```
     toLower(replace(trim(first(split(replace(coalesce(triggerBody()?['text_7'], ''), '–', '-'), '-'))), ' ', ''))
     ```

7. **`If_row_exists`** — `length(body('Find_existing_row')?['value']) > 0`:
   - **yes** → `Update_external_item`: POST to `/items(<id>)` with
     headers `X-HTTP-Method: MERGE`, `IF-MATCH: *` (SharePoint REST's
     "update, last write wins").
   - **no** → `Create_external_item`: POST to `/items`.
   Both send `string(outputs('Payload_final'))` with
   `odata=nometadata` content type. This makes the flow an **upsert
   keyed on RegistrationID** — Register creates, Switch updates the same
   row, Cancel updates `Status`/`LastAction` to Cancelled. Rows are
   never deleted.

**App call sites (11):** immediately after every register/switch/cancel
`Patch` in `scrEventQuickReg.yaml` and `scrAdmin.yaml`, always
best-effort:

```
If(IsError(EventSession_SyncExternalList.Run(
    "Register", regID, evSPSite, evSPList, "Confirmed", ...)),
  Notify("Saved, but the event's external list could not be updated.", NotificationType.Warning))
```

**Permissions:** the SharePoint connection owner needs **Edit** on
every external site used. `ensureuser` additionally requires the target
users to be resolvable in that site's tenant.

**Built-in mapping profile for a pre-existing legacy list (v1.0.0.18):** the flow can
also target an existing list whose internal names don't follow the
contract. After `Payload_final`, a Compose named
`Payload_testing_profile` builds an alternate payload, and
`Payload_send` picks which one to send: if the target list has the
signature column **`Division_x0020__x0023_`**, the profile payload is
used; otherwise the generic contract payload is. Profile mapping:

| Target column (internal) | Display name | Value written |
|---|---|---|
| `Title` | Div # | `WSR-<RegistrationID>` |
| `RegistrationID` | RegistrationID | Upsert key (added column) |
| `Division_x0020__x0023_` | Division # | DepartmentName |
| `Status` | Pixel Number (required) | Phone number |
| `RegStatus` | RegStatus (added column) | `Confirmed` / `Cancelled` |
| `Session_x0020_Date` | Session Date (text) | `yyyy-MM-dd` |
| `Description` | Session Time (choice) | Slot start (`9:00am` … `3:00pm`) |
| `Rsa_x0020_token` | Yubikey (choice yes/no) | Question1, lowercased |
| `Do_x0020_you_x0020_know_x003f_` | Do you know? | Question2 |
| `Staff_x0020_NameId` | Staff Name (person) | Registrant via `ensureuser` |
| `EventID`, `EventName` | (added columns) | Event item ID / name |
| `UserName`, `UserEmail` | (added columns) | Registrant name / email |
| `ForSelf`, `SubmittedBy` | (added columns) | Self-flag / submitter email |
| `LastAction`, `LastActionOn` | (added columns) | `Register`/`Switch`/`Cancel` + UTC timestamp |

Caveats: the Session Time choices are hourly (9:00am–3:00pm), so events
syncing to this list should use 60-minute slots in that window
(anything else, e.g. `9:30am`, is rejected by the choice column); blank
choice values are sent as `null` (field cleared) to avoid 400s; the
read-only calculated `TImeSlot` column is never written — and note the
full slot label is deliberately **not** mirrored, because a `TimeSlot`
contract column can't coexist with the list's calculated `TImeSlot`
(SharePoint blocks near-duplicate names and the calculated column is
read-only).

**Preparing such a list so runs don't fail:** follow the step-by-step
checklist in `LISTS.md` § 6 ("Preparing the legacy list"). The short
version: add `RegistrationID` (Number) — without it the very first
query (`Find_existing_row`) 400s on every run — plus `RegStatus`
(Choice: Confirmed / Cancelled), the text columns `EventID`,
`EventName`, `UserName`, `UserEmail`, `ForSelf`, `SubmittedBy`,
`LastAction`, and `LastActionOn` (Date and time); make sure no *other*
column is Required unless the profile maps it; keep the `Session Time`
choices in `9:00am`-style lowercase; and do **not** add a `TimeSlot`
column (it collides with the calculated `TImeSlot`).

**Extending to a new optional column:** add another chained Compose
after `Payload_final` following the same
`if(contains(..., '"InternalName":"<col>"'), addProperty(...), passthrough)`
pattern, and point `parameters/body` in *both* the create and update
actions at the new final Compose. Person columns must be written as
`<InternalName>Id` with an `ensureuser` result; choice columns as plain
strings matching a choice (or enable fill-in).

---

## 4. How the app invokes flows (Power Fx patterns)

```
// Fire-and-check (most flows return {result:"ok"})
If(
    IsError(
        EventSession_SendAppEmail.Run(
            varRegTargetEmail,
            "Registration Confirmed - " & evName & " (WSR-" & newID & ")",
            "Hi " & varRegTargetName & "," & Char(10) & Char(10) &
            "Your registration is confirmed." & Char(10) & ...
        )
    ),
    Notify("Registered, but the confirmation email could not be sent.", NotificationType.Warning)
);

// Using a returned value (ExportCSV)
With({res: EventSession_ExportCSV.Run(fileName, csvText)},
    If(IsBlank(res.fileurl),
        Notify("Export failed.", NotificationType.Error),
        Launch(res.fileurl)))
```

Rules of thumb:

- Bodies are plain text; use `Char(10)` for newlines (flows convert).
- A failed flow must never abort the SharePoint patch that preceded it —
  patch first, notify on flow failure, move on.
- After changing a flow's **trigger schema**, remove and re-add the flow
  in Studio (Power Automate pane) and re-check every `.Run(` call site —
  arguments are positional.

---

## 5. Editing, packaging, and versioning

### 5.1 Two ways to edit

1. **Designer** (quick, per-environment): edit the imported flow at
   make.powerautomate.com. Remember to back-port the change into the
   JSON in source control, or the next import overwrites it.
2. **JSON** (source of truth): edit
   `Flow/SolutionPackage-NoTemplates/Workflows/<Flow>-<GUID>.json`,
   rebuild the zip, re-import. Prefer this for anything you want to
   keep.

When editing JSON with a script, **load it with a JSON parser** and
modify decoded values — hand-editing escaped strings (especially the
adaptive cards) is how escaping bugs happen (§ 2.5).

### 5.2 Rebuilding the solution zip

The zip layout (all at the zip root):

```
solution.xml            <- version, unique name, RootComponents, connection refs
customizations.xml      <- the Workflow entities (name, GUID, JSON file path)
[Content_Types].xml
Workflows/*.json        <- one per flow
```

Checklist for every rebuild:

1. **Bump `<Version>` in `solution.xml`** (e.g. `1.0.0.18`) — Dataverse
   may reject importing the same version over itself.
2. Zip the three XML files + the `Workflows/` folder (folder structure
   preserved, files at root).
3. Name the zip to match: `EventSessionFlows_NoTemplates_1_0_0_18.zip`.

### 5.3 Adding a brand-new flow to the solution

1. Create `Workflows/<Name>-<NEW-GUID>.json` (copy a similar flow;
   generate a fresh GUID).
2. Add a `<Workflow>` entity block in `customizations.xml` (name
   `EventSession_<Name>`, the GUID, `JsonFileName` pointing at the
   file, and the connection references it uses).
3. Add `<RootComponent type="29" id="{GUID}" behavior="0" />` to
   `solution.xml` — **forgetting this causes** the import error
   *"component … of type 29 is not declared in the solution file as a
   root component"*.
4. Bump version, re-zip, import, map connections, turn on, add to the
   app in Studio.

### 5.4 Legacy per-flow packages

`Flow/Packages/EventSession_*.zip` are Power Automate **Package
(Legacy)** exports (each contains a `definition.json` + manifest) for
environments where solution import fails. They are built from the same
definitions — when you change a flow, update both formats, and refresh
the bundle zip (`EventSessionFlows_NoTemplates_Packages.zip`).

---

## 6. Testing and debugging

- **Run history:** each flow > 28-day run list > click a run > expand
  actions to see exact inputs/outputs. For SyncExternalList, the
  `Payload_final` Compose output shows precisely what was written to
  the external list; `Find_existing_row` output shows whether it
  updated or created.
- **Test pane:** designer > Test > Manually — Power Apps-triggered
  flows let you type each trigger parameter by hand; this is the
  fastest way to iterate on SyncExternalList without touching the app.
- **Reminder flow off-schedule test:** designer > Test > Manually runs
  the recurrence flow immediately (it will email real registrants for
  *tomorrow* — use a test list/site first).
- Common failures:

| Symptom | Cause |
|---|---|
| `WorkflowOperationParametersExtraParameter` on save | An action carries a parameter the connector no longer accepts (e.g. a stale `permission` on the share-link action) — remove it |
| `OpenApiOperationParameterValidationFailed` … `item/timeZone` | Windows zone ID used where the calendar connector wants its enum string (§ 3.3) |
| Card shows literal `\n` | Card escaping regression (§ 2.5) |
| CSV opens garbled in Excel | BOM removed (§ 2.7) |
| Report email attachment is unreadable gibberish | SendReportEmail's `ContentBytes` lost its `base64(...)` expression — usually by re-picking `FileContent` from the dynamic-content panel (§ 3.5) |
| Sync 404 `getbytitle` | Wrong `SPListName` (it's the display name, not the URL name) or connection owner lacks access to the site |
| Sync 400 on create/update | Payload column missing on the target list, or a choice value not in the column's choices (enable fill-in or fix the value) |
| `ensureuser` 500 | Email not resolvable in the tenant (external/guest user not provisioned) |
| Everything to flow owner's calendar | AddToCalendar connection set to `embedded` instead of `invoker` (§ 3.3) |

---

## 7. Quick answers

- **Change email wording?** Register/switch/cancel: in the *screens*
  (see § 3.1). Reminder/report/share: in the *flow* bodies.
- **Change branding/colors?** The HTML shell in four flows (§ 2.4) and
  the card header text in two (§ 2.5).
- **Different timezone?** Reminder trigger `timeZone` (Windows ID) and
  AddToCalendar `item/timeZone` (connector enum string) — two different
  formats, both must change.
- **Point reminders at production?** The `dataset` in
  `Get_tomorrows_registrations` — the only hardcoded site URL.
- **Send from a shared mailbox?** Swap the send action (§ 3.1); no app
  changes needed.
- **More than 500 reminders/day?** Raise `$top` (§ 3.4).
- **New external-list column?** Follow the chained-Compose pattern
  (§ 3.7, last paragraph).
