# Weekly Session Registration — Minimal Edition (Production Kit)

Everything needed to stand up the **three-screen minimal edition**
(`scrIntro`, `scrEventQuickReg`, `scrAdmin`) in a new environment.

> **Note:** the `SharePoint/` PowerShell scripts folder is **not included
> in this copy**. Create the lists manually using the column reference in
> `Docs/LISTS.md` (every list, column, and type is documented there).

Follow the documents in this order:

| Step | Document / folder | What it covers |
|---|---|---|
| 1 | **`DEPLOYMENT.md`** | The complete step-by-step deployment: lists → flows → app → configuration → smoke test |
| 2 | `SharePoint/` | Scripts that create the lists and columns (`RUN-SCRIPT.md` explains how to run them) |
| 3 | `Flow/` | The flow solution zip (v1.0.0.18, 7 flows) + legacy per-flow packages + `MANUAL-FLOWS.md` (build-by-hand guide) |
| 4 | `App/` | `OnStart.txt` and the three screen YAML files to paste into a new canvas app |
| 5 | `Docs/LISTS.md` | **List metadata reference** — every list, every column, types, choices, and the external-list contract |
| 6 | `Docs/SOP.md` | Standard operating procedures for admins (promote an event, roles, external list, reports…) |
| 7 | `Docs/HOW-TO.md` | End-user guide (register, switch, cancel, add to calendar) |
| 8 | `Docs/DEVELOPER-GUIDE.md` | Architecture, screens, variables, flows, and conventions for whoever maintains this |
| 9 | `Docs/FLOWS-DEVELOPER-GUIDE.md` | Deep action-by-action developer guide to all 7 flows: parameters, expressions, packaging, debugging |
| 10 | `Docs/CONNECTIONS.md` | **Connections & sender identity** — service-account setup, run-only users, fixing emails sent from the wrong person |

## What this edition is

- **3 screens**: dark intro/hero page with a featured (promoted) event, a
  combined event page with on-screen registration/switch/cancel, and a
  full admin console.
- **4 SharePoint lists**: `EventSessionRegistration_Events`,
  `_SessionTimeSlots`, `_Registrations`, `_AppRoles`.
  **No EmailTemplates list** — email wording is hardcoded in the screens
  and flows (NoTemplates flow build).
- **7 flows** (prefix `EventSession_`): SendAppEmail, ExportCSV,
  AddToCalendar, SessionReminderDaily, SendReportEmail, ShareEvent,
  SyncExternalList.
- **Promoted event** is controlled from the backend (the `IsPromoted`
  column on the Events list, or an ID pinned in `App.OnStart`) — there is
  no Settings screen in this edition.

## Contents

```
WeeklySessionRegistration-Minimal-PROD/
├─ START-HERE.md                  <- you are here
├─ DEPLOYMENT.md                  <- the deployment runbook
├─ App/
│  ├─ OnStart.txt                 <- paste into App.OnStart
│  └─ Screens/
│     ├─ scrIntro.yaml
│     ├─ scrEventQuickReg.yaml
│     └─ scrAdmin.yaml
├─ Flow/
│  ├─ EventSessionFlows_NoTemplates_1_0_0_18.zip   <- solution import (preferred)
│  ├─ Packages/                   <- legacy per-flow zips (fallback) + bundle
│  └─ MANUAL-FLOWS.md             <- click-by-click designer guide
├─ SharePoint/
│  ├─ CreateLists-Graph.ps1       <- creates the lists (device-code sign-in, no modules)
│  ├─ CreateLists.ps1             <- same, PnP.PowerShell variant
│  ├─ AddMetadataColumns-Graph.ps1<- adds the newer metadata columns to existing lists
│  ├─ SetupExternalList-Graph.ps1 <- provisions an external sync list (optional feature)
│  └─ RUN-SCRIPT.md               <- how to run the Graph scripts
└─ Docs/
   ├─ LISTS.md                    <- list & column metadata reference
   ├─ SOP.md                      <- admin operating procedures
   ├─ HOW-TO.md                   <- end-user guide
   ├─ DEVELOPER-GUIDE.md          <- maintainer documentation
   ├─ FLOWS-DEVELOPER-GUIDE.md    <- deep developer guide to the 7 flows
   └─ CONNECTIONS.md              <- connections & sender identity how-to
```
