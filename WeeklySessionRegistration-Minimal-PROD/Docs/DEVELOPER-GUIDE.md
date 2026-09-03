# Developer Guide — Minimal Edition

Maintainer documentation: architecture, screen internals, data patterns,
flows, and the conventions this codebase relies on. Read `LISTS.md` for
the data schema and `../DEPLOYMENT.md` for environment setup.

---

## 1. Architecture

```
Canvas app (3 screens, source-code YAML)
├─ scrIntro          hero page + promoted event card
├─ scrEventQuickReg  event page: calendar, sessions, register/switch/cancel modals
└─ scrAdmin          admin console: dashboard / events / sessions / registrations / reports
        │
        ├─ SharePoint (4 lists, prefix EventSessionRegistration_)
        │    Events · SessionTimeSlots · Registrations · AppRoles
        ├─ Connectors: Office 365 Users (people search, photos),
        │    Office 365 Groups (event audience)
        └─ Power Automate (7 flows, prefix EventSession_)
             SendAppEmail · ExportCSV · AddToCalendar · SessionReminderDaily
             · SendReportEmail · ShareEvent · SyncExternalList
```

Differences from the full edition: no Settings / Home / Register /
MyRegistrations / Profile / Help screens, no `EmailTemplates` list (email
text is hardcoded), promoted event is backend-driven.

## 2. Source layout and edit workflow

- `App/OnStart.txt` — paste into **App.OnStart** (comments included).
- `App/Screens/*.yaml` — one file per screen, Power Apps **source code
  format**. Edit workflow: change the YAML → in Studio, right-click the
  screen > **View code** > select-all > paste → save/publish. Screen
  `OnVisible` logic is inside each YAML.
- Studio requires **Scale to fit OFF**; layout is fully responsive via
  auto-layout `GroupContainer`s (`FillPortions`, `LayoutMinWidth`,
  `LayoutWrap`).

Control naming: `<type><Name>_<screen suffix>` — suffixes `_EvQ`
(scrEventQuickReg) and none/`_Adm`-style names on scrAdmin. Modals are an
overlay `Rectangle` + centered `GroupContainer`, both driven by a
`varShow…` variable; modal height uses `Min(MaxH, Parent.Height - 24)`
and Y `Max(12, (Parent.Height - Self.Height)/2)` to stay on-screen.

## 3. State: key variables and collections

Set in **OnStart** (see the commented file):

| Name | Purpose |
|---|---|
| `varUserName` / `varUserEmail` | Current user (email lowercased) |
| `varPromotedEventID` | Pinned featured event; 0 = use the `IsPromoted` column |
| `varAppURL` | Published app web link; base for `?eventid=` deep links |
| `varDetailEventID`, `varDeepEvent` | Deep-link routing (with `StartScreen`) |
| `colAppRoles`, `varMyRole`, `varIsAdmin`, `varIsCoordinator` | Role lookup — the small list is collected and matched **in memory** (person-column comparisons don't delegate). Empty list ⇒ everyone is Admin (bootstrap) |
| `varSidebarOpen` | Sidebar default: open for admins/coordinators |
| `colFutureRegs` | Future confirmed registrations (seat counts) |

Main screen-level collections:

| Collection | Screen | Contents |
|---|---|---|
| `colEvqSlots` | EvQ | Active slots for the current event (+ seat/registered flags) |
| `colMyEvRegs_EvQ` | EvQ | My confirmed registrations for the event |
| `colOthersTmp_EvQ` → `colOthersRegs_EvQ` | EvQ | Registrations I submitted for others (two-step collect keeps the filter delegable) |
| `colAllRegs_EvQ` | EvQ | Union of mine + for-others (drives the All tab) |
| `colEvents`, `colEventSessions`, `colAdminSlots`, `colAdminRegs` | Admin | Event/session/registration working sets |

Registration modal state: `varRegModalStep` (1–2), `varRegForSelf`,
`varRegOnBehalf` (selected person record), `varRegTargetEmail/Name`,
`varRegPrefill` (switch scenarios), `varEvqSwitchRegID` (non-zero =
switching, skips step 1).

## 4. Power Fx conventions (do not regress these)

- **Delegation:** `Registrations.Status` is *text* and `EventID` is a
  plain *number* so `Filter(...)` delegates. Small lists (AppRoles) are
  collected then queried in memory. Don't introduce person/choice-column
  comparisons in delegated filters.
- **`ForAll` + `Patch`:** always alias — `ForAll(col As x, Patch(list,
  LookUp(list, ID = x.ID), …))`. Bare `ThisRecord.ID` inside the lookup
  produces "invalid string in filter query" at runtime.
- **Flow error handling:** flows return records, so use
  `If(IsError(Flow.Run(...)), Notify(...))` — **never**
  `IfError(Flow.Run(...), Notify(...))` (type mismatch: record vs
  boolean).
- **Choice columns:** patch as `{Value: "..."}`, blank as
  `If(IsBlank(x), Blank(), {Value: x})`.
- **Person columns:** patch the full claims record
  (`'@odata.type': "#Microsoft.Azure.Connectors.SharePoint.SPListExpandedUser"`,
  `Claims: "i:0#.f|membership|" & Lower(email)`, plus DisplayName/Email).
- **Image column (`EventImage`):** requires the 5-field record —
  `{Value, Full, Large, Medium, Small}` all set to the image.
- **People pickers** are custom (text input + suggestion gallery on
  `Office365Users.SearchUser`); photos via
  `If(IsBlank(Id), Blank(), IfError(Office365Users.UserPhotoV2(Id), Blank()))`
  with an initials fallback. People with no email are non-selectable.
- **Slot labels use an en dash (`–`, U+2013)** — e.g.
  `9:00 AM – 10:00 AM`. The sync flow's hour extraction and various UI
  bits split on it. Don't "fix" it to a hyphen.
- **Soft deletes everywhere:** cancel = `Status: "Cancelled"`;
  deactivate = `IsActive: false`. Nothing user-facing deletes rows.
- Cutoff rule: registration blocked inside
  `Coalesce(RegistrationCutoffHours, 48)` hours before start; **switch is
  exempt** by design.

## 5. Notifications (hardcoded in this edition)

`EventSession_SendAppEmail.Run(to, subject, body)` — plain text body with
`Char(10)` newlines; the flow converts breaks, wraps the branded HTML
shell, and posts a styled Teams adaptive card to the same person (card
failure never fails the flow).

| Trigger | Where the Power Fx lives |
|---|---|
| Register + switch confirmation | `scrEventQuickReg.yaml` → `btnRegModalConfirm_EvQ.OnSelect` |
| Self-service cancel | `scrEventQuickReg.yaml` → `btnCancelEvQConfirm.OnSelect` |
| Admin cancel | `scrAdmin.yaml` → `btnRRowCancel.OnSelect` |
| Daily reminder | hardcoded **inside** `EventSession_SessionReminderDaily` |

> Adaptive-card escaping is delicate: the card JSON is built as a string
> in the flow; body newlines must become a **single-escaped** `\n` in the
> raw card JSON (fixed in v1.0.0.15 — double-escaping renders literal
> `\n` in Teams).

## 6. The flows

| Flow | Trigger | Notes |
|---|---|---|
| `EventSession_SendAppEmail` | Power Apps (to, subject, body) | HTML shell + Teams card |
| `EventSession_ExportCSV` | Power Apps (CSV text, filename) | Writes OneDrive `/CSV Exports`, returns/attaches the file |
| `EventSession_AddToCalendar` | Power Apps (registration details) | Creates the Outlook event (timezone enum, not name) |
| `EventSession_SessionReminderDaily` | Recurrence 7 AM ET | Only flow with a **hardcoded site address** — must be repointed after import |
| `EventSession_SendReportEmail` | Power Apps (recipients, note, CSV) | Report email with attachment |
| `EventSession_ShareEvent` | Power Apps (recipients, note, event link) | Deep link `varAppURL & "?eventid=" & ID` |
| `EventSession_SyncExternalList` | Power Apps (18 params: Action, RegistrationID, SiteURL, ListName, registration fields…) | See below |

### SyncExternalList behavior

1. No-ops when SiteURL/ListName are blank (event has sync disabled).
2. Uses **SharePoint HTTP (REST)** actions so the site/list are dynamic.
3. Fetches the target list's fields, then **upserts by
   `RegistrationID`**: GET by filter → POST (create) or MERGE (update).
4. **Column-aware extras:** only if the columns exist on the target —
   `staff` (ensureuser on registrant email), `author0` (ensureuser on
   submitter email; display name "author"), `hour` (slot start time:
   en dash normalized to hyphen, split, trimmed, lowercased, spaces
   stripped → `1:00pm`).
5. App calls it best-effort after every register/switch/cancel patch:
   `If(IsError(EventSession_SyncExternalList.Run(...)), Notify(warning))`
   — 11 call sites across `scrEventQuickReg.yaml` and `scrAdmin.yaml`.

## 7. Flow package maintenance

- Source of truth: `Flow/SolutionPackage-NoTemplates/` in the source
  repo (solution.xml, customizations.xml, [Content_Types].xml,
  `Workflows/*.json`). The shipped zip here is **v1.0.0.15**.
- To change a flow: edit its `Workflows/*.json`, **bump `<Version>` in
  `solution.xml`** (Dataverse rejects same-version reimports), re-zip the
  three XML files + `Workflows/` at the zip root.
- Adding a new flow needs **both** a `customizations.xml` entry and a
  `<RootComponent type="29">` line in `solution.xml`, or import fails
  with "not declared … as a root component".
- Legacy per-flow zips (`Flow/Packages/`) are the fallback for
  environments where solution import fails; keep them in sync when flows
  change (each zip contains a `definition.json` in the package format).
- Flow renames: keep the `EventSession_` prefix; the app references
  flows by name, so re-add them in Studio after a rename.

## 8. Extending safely

- **New registration fields:** add the column (script or manual), add
  the input to the modal step 2, wire into **both** patch statements
  (new + switch) in `btnRegModalConfirm_EvQ`, add to the confirm
  button's `DisplayMode` validation if required, add a `Reset()` after
  success, and — if it should sync — extend the SyncExternalList
  contract + flow payload.
- **New event settings:** add the column, extend the event modal
  (Details or Settings tab) and both event patch statements in
  `scrAdmin.yaml`.
- **Adding a screen back** (e.g. Settings from the full edition): also
  restore its sidebar entry and any `Navigate` targets; full-edition
  YAML lives in the main `WeeklySessionRegistration` project.
- Always run the smoke test in `../DEPLOYMENT.md` Phase 5 after changes.
