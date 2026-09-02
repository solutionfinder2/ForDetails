# Registration metadata columns

Add these five columns to the SharePoint list **`EventSessionRegistration_Registrations`**.
The Power App registration flows (wizard + quick-reg) collect and save them on create and switch.

| Internal name | Display name | Type | Required | Choices |
|---|---|---|---|---|
| `JobTitle` | Job Title | Single line of text | Yes | — |
| `ExperienceLevel` | Experience Level | Choice (single) | Yes | Beginner, Intermediate, Advanced |
| `AttendancePreference` | Attendance Preference | Choice (single) | Yes | In-Person, Virtual, No Preference |
| `OrgUnit` | Organization Unit | Choice (single) | Yes | HR, IT, Finance, Operations, Other |
| `HeardFrom` | How Did You Hear | Choice (single) | Yes | Manager, Email, Teams, Colleague, Other |

## Setup notes

1. Create the columns with the **exact internal names** above (Power Apps `Patch` uses them).
2. After adding columns, refresh the `EventSessionRegistration_Registrations` data source in Power Apps Studio.
3. Re-paste / republish the updated screens:
   - Full app: `scrRegister.yaml`, `scrEventQuickReg.yaml`, `scrAdmin.yaml`
   - Minimal: `scrEventQuickReg.yaml`, `scrAdmin.yaml`
4. Admin clipboard / CSV export includes these fields after `Email`.

## Where values are written

- Full registration wizard step 3 (`scrRegister`) — form + validation before confirm
- Event quick-register confirm modal (`scrEventQuickReg`) — form + validation before Patch
- Both **new registration** and **switch** Patch paths
