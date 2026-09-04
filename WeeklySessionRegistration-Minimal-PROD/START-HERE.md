# Weekly Session Registration â€” Minimal Edition (Production Kit)

Everything needed to stand up the **three-screen minimal edition**
(`scrIntro`, `scrEventQuickReg`, `scrAdmin`) in a new environment.

> **Note:** the `SharePoint/` PowerShell scripts folder is **not included
> in this copy**. Create the lists manually using the column reference in
> `Docs/LISTS.md` (every list, column, and type is documented there).

Follow the documents in this order:

| Step | Document / folder | What it covers |
|---|---|---|
| 1 | **`DEPLOYMENT.md`** | The complete step-by-step deployment: lists â†’ flows â†’ app â†’ configuration â†’ smoke test |
| 2 | `SharePoint/` | Scripts that create the lists and columns (`RUN-SCRIPT.md` explains how to run them) |
| 3 | `Flow/` | The flow solution zip (v1.0.0.16, 7 flows) + legacy per-flow packages + `MANUAL-FLOWS.md` (build-by-hand guide) |
| 4 | `App/` | `OnStart.txt` and the three screen YAML files to paste into a new canvas app |
| 5 | `Docs/LISTS.md` | **List metadata reference** â€” every list, every column, types, choices, and the external-list contract |
| 6 | `Docs/SOP.md` | Standard operating procedures for admins (promote an event, roles, external list, reportsâ€¦) |
| 7 | `Docs/HOW-TO.md` | End-user guide (register, switch, cancel, add to calendar) |
| 8 | `Docs/DEVELOPER-GUIDE.md` | Architecture, screens, variables, flows, and conventions for whoever maintains this |
| 9 | `Docs/FLOWS-DEVELOPER-GUIDE.md` | Deep action-by-action developer guide to all 7 flows: parameters, expressions, packaging, debugging |

## What this edition is

- **3 screens**: dark intro/hero page with a featured (promoted) event, a
  combined event page with on-screen registration/switch/cancel, and a
  full admin console.
- **4 SharePoint lists**: `EventSessionRegistration_Events`,
  `_SessionTimeSlots`, `_Registrations`, `_AppRoles`.
  **No EmailTemplates list** â€” email wording is hardcoded in the screens
  and flows (NoTemplates flow build).
- **7 flows** (prefix `EventSession_`): SendAppEmail, ExportCSV,
  AddToCalendar, SessionReminderDaily, SendReportEmail, ShareEvent,
  SyncExternalList.
- **Promoted event** is controlled from the backend (the `IsPromoted`
  column on the Events list, or an ID pinned in `App.OnStart`) â€” there is
  no Settings screen in this edition.

## Contents

```
WeeklySessionRegistration-Minimal-PROD/
â”œâ”€ START-HERE.md                  <- you are here
â”œâ”€ DEPLOYMENT.md                  <- the deployment runbook
â”œâ”€ App/
â”‚  â”œâ”€ OnStart.txt                 <- paste into App.OnStart
â”‚  â””â”€ Screens/
â”‚     â”œâ”€ scrIntro.yaml
â”‚     â”œâ”€ scrEventQuickReg.yaml
â”‚     â””â”€ scrAdmin.yaml
â”œâ”€ Flow/
â”‚  â”œâ”€ EventSessionFlows_NoTemplates_1_0_0_16.zip   <- solution import (preferred)
â”‚  â”œâ”€ Packages/                   <- legacy per-flow zips (fallback) + bundle
â”‚  â””â”€ MANUAL-FLOWS.md             <- click-by-click designer guide
â”œâ”€ SharePoint/
â”‚  â”œâ”€ CreateLists-Graph.ps1       <- creates the lists (device-code sign-in, no modules)
â”‚  â”œâ”€ CreateLists.ps1             <- same, PnP.PowerShell variant
â”‚  â”œâ”€ AddMetadataColumns-Graph.ps1<- adds the newer metadata columns to existing lists
â”‚  â”œâ”€ SetupExternalList-Graph.ps1 <- provisions an external sync list (optional feature)
â”‚  â””â”€ RUN-SCRIPT.md               <- how to run the Graph scripts
â””â”€ Docs/
   â”œâ”€ LISTS.md                    <- list & column metadata reference
   â”œâ”€ SOP.md                      <- admin operating procedures
   â”œâ”€ HOW-TO.md                   <- end-user guide
   â”œâ”€ DEVELOPER-GUIDE.md          <- maintainer documentation
   â””â”€ FLOWS-DEVELOPER-GUIDE.md    <- deep developer guide to the 7 flows
```
