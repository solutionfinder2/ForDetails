# Weekly Session Registration - MINIMAL EDITION

A stripped-down, three-screen build of the Weekly Session Registration app.
Use it when you want a single featured event with on-page registration and
an admin console - nothing else.

## What's in / what's out

| | Full app | Minimal edition |
|---|---|---|
| Screens | 11 | **3** - `scrIntro`, `scrEventQuickReg`, `scrAdmin` |
| SharePoint lists | 5 | **4** - Events, SessionTimeSlots, Registrations, AppRoles (**no EmailTemplates**) |
| Emails | Templates from the EmailTemplates list | **Hardcoded** in the screens (register / switch / cancel) |
| Flow package | Standard or Universal | **NoTemplates** - included here in `Flow/` |
| Promote an event | Settings screen | **Backend** - IsPromoted column or an ID in OnStart (see below) |

## User journey

1. **Intro** (`scrIntro`) - dark hero page. Shows the featured event card
   with Register Now / View Details (both open the event page). "Get
   Started" does the same and is disabled when no event is promoted.
   Admins/coordinators also see an "Admin" button.
2. **Event page** (`scrEventQuickReg`) - calendar + session list, "My
   Registration" cards, and on-screen Register / Switch / Cancel with
   confirmation modals. Share Event and Add to Calendar work as in the
   full app.
3. **Admin** (`scrAdmin`) - dashboard, event/session management,
   registrations, and reports. Sidebar only has the Admin entry; the logo
   and app name navigate back to the Intro. (No Settings screen - the
   Settings gear and sidebar links to removed screens are gone.)

## Changing the promoted (featured) event without the Settings screen

Two options, both in `App/OnStart.txt` (see the comments there):

- **Option A - SharePoint only, no republish (recommended):** leave
  `Set(varPromotedEventID, 0)` as is, and flip the **IsPromoted** column
  to Yes on the event item in the `EventSessionRegistration_Events` list.
  Turn it off on the old event when you promote a new one.
- **Option B - pin by ID:** set `varPromotedEventID` to the event's
  SharePoint item ID and republish. A value > 0 always wins over the
  IsPromoted column.

## Setup

1. Create the four lists (use the full project's
   `SharePoint/CreateLists.ps1` or the manual guide in `DEPLOYMENT.md` -
   simply skip the EmailTemplates list).
2. Import `Flow/EventSessionFlows_NoTemplates_1_0_0_12.zip`
   (see `Flow/SolutionPackage-NoTemplates/IMPORT.md`). All emails are sent
   in the branded HTML shell; this build's reminder flow has its text
   hardcoded, so nothing references the EmailTemplates list.
3. In Power Apps Studio, add the data sources: the four lists plus the
   flows (`EventSession_SendAppEmail`, `_ExportCSV`,
   `_AddToCalendar`, `_SendReportEmail`, `_ShareEvent`) and the Office 365
   Users / Groups connectors (used by the Admin event form and Share).
4. Paste `App/OnStart.txt` into App.OnStart, set
   `StartScreen = If(!IsBlank(Param("eventid")), scrEventQuickReg, scrIntro)`.
5. Paste the three screen YAML files (View code > paste) in any order:
   `scrIntro.yaml`, `scrEventQuickReg.yaml`, `scrAdmin.yaml`. Screen
   OnVisible formulas are inside the YAML - nothing to set per screen.
6. Add your row to `EventSessionRegistration_AppRoles` (Role = Admin)
   before adding anyone else.

## Emails in this edition

Register, switch, and cancel emails are sent through
`EventSession_SendAppEmail` with subject/body built directly
in Power Fx (branded HTML shell is applied by the flow). To change the
wording, edit the `OnSelect` of:

| Email | Screen | Control |
|---|---|---|
| Registration confirmed / switched | `scrEventQuickReg.yaml` | `btnRegModalConfirm_EvQ` |
| Cancelled (self-service) | `scrEventQuickReg.yaml` | `btnCancelEvQConfirm` |
| Cancelled (by admin) | `scrAdmin.yaml` | `btnRRowCancel` |

The daily session reminder text lives inside the
`EventSession_SessionReminderDaily` flow (NoTemplates build).
