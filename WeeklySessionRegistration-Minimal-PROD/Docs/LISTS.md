# SharePoint List Metadata Reference

Complete schema for every list the minimal edition reads or writes.
List **display names must match exactly** (including the
`EventSessionRegistration_` prefix) — the app and flows reference them by
name. Column names below are **internal names** (which equal the display
names unless noted).

Scripted setup: `SharePoint/CreateLists-Graph.ps1` +
`SharePoint/AddMetadataColumns-Graph.ps1` create everything except the
three manual columns flagged below.

---

## 1. EventSessionRegistration_Events

One row per event. Sessions and registrations link back via the item ID.

| Column | Type | Required | Notes |
|---|---|---|---|
| `Title` | Single line of text | Yes | Event name |
| `Description` | Multiple lines of text | No | The app writes HTML from the rich-text editor |
| `StartDate` | Date only | Yes | First day sessions can exist |
| `EndDate` | Date only | Yes | Last day sessions can exist |
| `Location` | Single line of text | No | |
| `Department` | Single line of text | No | Owning department |
| `EventType` | Single line of text | No | App writes `Virtual`, `In-Person`, or `Both` |
| `IsAllDay` | Yes/No | No | All-day events get one "All Day" slot per date |
| `SlotDuration` | Number | No | Slot length in minutes (30/60/90/120) |
| `DayStartTime` | Single line of text | No | e.g. `9:00 AM` — first slot start |
| `DayEndTime` | Single line of text | No | e.g. `3:00 PM` — day cutoff |
| `Coordinator` | Single line of text | No | Display name |
| `CoordinatorEmail` | Single line of text | No | |
| `POC` | Single line of text | No | Point of contact (hidden in UI when blank) |
| `POCEmail` | Single line of text | No | |
| `RegistrationCutoffHours` | Number | No | Blank = 48. Hours before start when self-service registration closes (switching is exempt) |
| `MaxPerUser` | Number | No | Max sessions one person may hold for this event; 0/blank = no limit |
| `DefaultCapacity` | Number | No | Seats per new session; blank = 20 |
| `MeetingLink` | Single line of text | No | Included in confirmation emails for virtual events |
| `AudienceGroupID` | Single line of text | No | Microsoft 365 group ID; blank = event visible to everyone |
| `AudienceGroupName` | Single line of text | No | Display name of that group |
| `IsPromoted` | Yes/No | No | Featured on the Intro page — keep it Yes on **one** event at a time |
| `IsActive` | Yes/No | Yes | No = hidden from users (soft delete) |
| `SPListName` | Single line of text | No | External sync: target list display name; blank = sync off |
| `AllowRegisterForOthers` | Yes/No | No | Enables the "For someone else" option in the registration modal |
| `EventImage` | **Image** | No | **Manual add** — Graph API cannot create Image columns |
| `EventLink` | **Hyperlink** | No | **Manual add** — external info page for the event |
| `SPSiteURL` | **Hyperlink** | No | **Manual add** — external sync: target site URL; blank = sync off |

---

## 2. EventSessionRegistration_SessionTimeSlots

One row per bookable session (a date + a time slot under an event).

| Column | Type | Required | Notes |
|---|---|---|---|
| `Title` | Single line of text | Yes | Slot label, e.g. `9:00 AM – 10:00 AM`. **Uses an en dash (–), not a hyphen** — the app and the sync flow's hour extraction rely on it |
| `SessionDate` | Date only | Yes | |
| `SortOrder` | Number | Yes | Start time in **minutes from midnight** (9:00 AM = 540) — drives sorting and slot generation |
| `Capacity` | Number | Yes | Seats for this session |
| `IsActive` | Yes/No | Yes | No = deactivated (kept for history, not bookable) |
| `EventID` | Number | Yes | Item ID of the parent row in `_Events` (plain number, delegable) |
| `EventName` | Single line of text | Yes | Snapshot of the event name (stamped by the app) |
| `DurationMinutes` | Number | No | Slot length in minutes; 1440 = all-day; blank = legacy 1-hour row |

---

## 3. EventSessionRegistration_Registrations

One row per registration. Rows are **never deleted** by the app — a
cancel sets `Status` to `Cancelled` (audit trail).

| Column | Type | Required | Notes |
|---|---|---|---|
| `Title` | Single line of text | No | Informational |
| `SlotID` | Number | Yes | Item ID of the booked row in `_SessionTimeSlots` |
| `SessionDate` | Date only | Yes | Snapshot from the slot |
| `TimeSlot` | Single line of text | Yes | Snapshot of the slot label |
| `UserName` | Single line of text | Yes | The **registrant** (may differ from the submitter) |
| `UserEmail` | Single line of text | Yes | Registrant's email, lowercase |
| `Status` | Single line of text | Yes | `Confirmed` or `Cancelled`. Deliberately **text, not Choice** so Status filters delegate to SharePoint |
| `EventID` | Number | Yes | Parent event item ID |
| `EventName` | Single line of text | Yes | Snapshot at booking time |
| `SubmittedBy` | Person | No | Who performed the registration (differs from the registrant on "for others") |
| `ForSelf` | Yes/No | No | Yes = self-registration; No = registered on someone's behalf |
| `PhoneNumber` | Single line of text | No* | App validates 10 digits and stores digits only. *Required by the app form |
| `DepartmentName` | Choice (dropdown) | No* | Default choices: Human Resources, Information Technology, Operations, Finance — **edit to fit your org** before/after running the script. *Required by the app form |
| `SiteLocation` | Choice (dropdown) | No* | Default choices: Main Office, North Campus, South Campus, Remote. *Required by the app form |
| `OrganizationUnit` | Choice (dropdown) | No | Default choices: Division A/B/C. Not currently on the form (reserved) |
| `Question1` … `Question5` | Choice (dropdown) | No* | Yes / No. The form uses Question1 and Question2 (*required); 3–5 are reserved |

---

## 4. EventSessionRegistration_AppRoles

Access control. **While this list is empty, everyone is treated as an
Admin** (bootstrap safety) — add your own Admin row first.

| Column | Type | Required | Notes |
|---|---|---|---|
| `Title` | Single line of text | No | Person's name (informational) |
| `UserEmail` | **Person** | Yes | People picker — the app matches on the person's email |
| `Role` | Choice (dropdown) | Yes | Exactly two choices: `Admin`, `Coordinator`. Anyone not listed is a regular user |

---

## 5. EventSessionRegistration_EmailTemplates — *not used*

The creation script builds this list for compatibility with the full
edition, but the **minimal edition never reads it** (email wording is
hardcoded in the screens and the NoTemplates flows). Keep or delete it —
either is fine.

---

## 6. External sync list (per-event, optional)

Any list, on any site the flow connection can edit, that an event points
to via `SPSiteURL` + `SPListName`. The `EventSession_SyncExternalList`
flow **upserts by `RegistrationID`**: register creates a row, switch
updates it, cancel sets `Status = Cancelled`.

Provision with:

```powershell
.\SetupExternalList-Graph.ps1 -SiteUrl "https://tenant.sharepoint.com/sites/OtherSite" -ListName "YourListName" [-WithScenarioColumns]
```

### Required contract columns

| Column | Type | Written with |
|---|---|---|
| `RegistrationID` | Number (indexed) | Item ID of the row in `_Registrations` — the upsert key |
| `Status` | Single line of text | `Confirmed` / `Cancelled` |
| `EventID` | Single line of text | Parent event item ID |
| `EventName` | Single line of text | Event name snapshot |
| `TimeSlot` | Single line of text | Full slot label (`1:00 PM – 2:00 PM`) |
| `SessionDate` | Date only | Session date |
| `UserName` | Single line of text | Registrant name |
| `UserEmail` | Single line of text | Registrant email |
| `ForSelf` | Single line of text | `true` / `false` |
| `SubmittedBy` | Single line of text | Submitter's email |
| `PhoneNumber` | Single line of text | Digits only |
| `DepartmentName` | Single line of text | |
| `SiteLocation` | Single line of text | |
| `Question1`, `Question2` | Single line of text | `Yes` / `No` |
| `LastAction` | Single line of text | `Register`, `Switch`, or `Cancel` |
| `LastActionOn` | Date and time | UTC timestamp of the action |

### Optional scenario columns (`-WithScenarioColumns`)

The flow is **column-aware**: it inspects the target list first and only
writes these when the column exists — lists without them work unchanged.

| Column | Type | Written with |
|---|---|---|
| `staff` | Person (single) | Resolved from the **registrant's** email |
| `author` | Person (single) | Resolved from the **submitter's** (created-by) email. Internal name is **`author0`** — "Author" is reserved by SharePoint |
| `hour` | Choice (fill-in allowed) | **Start time only**, lowercase, no spaces — e.g. `1:00pm` (extracted from the slot label by splitting on the en dash). Script seeds half-hour choices 7:00am–6:30pm |

> Adding your own extra columns to an external list is fine — the flow
> only touches the columns above.
