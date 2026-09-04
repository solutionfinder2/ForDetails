# Connections & Sender Identity — How-To Guide

Who do the notification emails come *from*? Why does a solution imported
into another tenant seem to "carry" connections? How do you rebind an
environment that was set up wrong? This guide covers all of it.

Companion docs: `../DEPLOYMENT.md` (Phase 2 — importing the flows),
`FLOWS-DEVELOPER-GUIDE.md` § 2.2 (connection references in the JSON).

---

## 1. How connections actually work

**Connections never move between tenants.** The solution zip contains no
credentials. What it contains are four **connection references** —
named, empty pointers:

| Logical name | Connector | Used by |
|---|---|---|
| `wsr_sharedoffice365` | Office 365 Outlook | SendAppEmail, AddToCalendar, SendReportEmail, ShareEvent, SessionReminderDaily |
| `wsr_sharedsharepointonline` | SharePoint | SessionReminderDaily, SyncExternalList |
| `wsr_sharedonedriveforbusiness` | OneDrive for Business | ExportCSV |
| `wsr_sharedteams` | Microsoft Teams | SendAppEmail, SessionReminderDaily |

During **Import solution**, Power Apps asks you to bind each reference to
a real connection **in the target environment** — you pick an existing
one or create one on the spot. Whoever's account owns that connection is
who the flow *runs as*: their mailbox sends the emails, their
permissions read/write SharePoint, their OneDrive stores the CSV
exports.

If your target tenant "inherited" the wrong identity, it's because the
person importing bound the references to their own personal connections
— not because anything carried over.

**One deliberate exception:** `EventSession_AddToCalendar` runs as the
**invoker** (the end user), so calendar events land in the *user's* own
calendar, not the flow owner's. Don't "fix" that one.

---

## 2. Recommended setup: a service account

Emails should come from a neutral account, not from whichever admin
happened to import the solution — and definitely not from end users.
The clean way needs **no Exchange "Send As" permission at all**: make
the sender *be* the connection owner.

### 2.1 Create the account (target tenant, one time)

1. Microsoft 365 admin center > create a user, e.g.
   `wsr-notify@yourtenant.com` (name it what you want the "From" line to
   read, e.g. *Session Registration*).
2. License it with **Exchange Online** (it must have a real mailbox) and
   **Power Automate** (a seeded Office 365 license is usually enough for
   these standard connectors).
3. Give it **Edit** permission on the SharePoint site that hosts the
   `EventSessionRegistration_*` lists (and on any external sync sites).
4. Optional but recommended: exclude it from MFA-interrupting policies
   using a proper service-account conditional-access exclusion, or be
   prepared to re-authenticate its connections when tokens expire.

### 2.2 Import using the service account

1. Sign in to [make.powerautomate.com](https://make.powerautomate.com)
   **as the service account**, pick the target environment.
2. **Solutions > Import solution** >
   `EventSessionFlows_NoTemplates_1_0_0_18.zip`.
3. When prompted for the four connections, **create new** ones — they
   will be owned by the service account.
4. Turn the seven flows On.
5. Share each flow with your real admin(s) as **co-owner** so humans can
   maintain them without signing in as the service account.

If you already imported as yourself, don't re-import — rebind instead
(§ 4).

---

## 3. Run-only users — why emails come from the registrant

Power Apps–triggered flows have a second, easy-to-miss setting that
overrides everything above. On the flow's details page there is a
**Run only users** panel. For each connector it offers two modes:

- **Provided by run-only user** — the flow uses *each end user's own
  connection*. Result: the registration confirmation is sent **by the
  registrant, from their mailbox**. This is the "emails come from the
  person that registered" symptom, and some import paths (especially
  the legacy per-flow packages) default to it.
- **Use this connection (…)** — the flow always uses the named
  connection, whoever runs it. This is what you want for email.

### Fix, per flow (SendAppEmail, ExportCSV, SendReportEmail, ShareEvent, SyncExternalList):

1. Open the flow (not in edit mode — the **details** page).
2. Find the **Run only users** tile > **Edit**.
3. For every connector listed, switch from *Provided by run-only user*
   to **Use this connection (service account's connection)**.
4. Save.

**Exception — `EventSession_AddToCalendar`: leave it on "Provided by
run-only user"** for Outlook. It must run as the end user so the event
is created in *their* calendar. (Each user consents to the connector the
first time they use the app — that's normal.)

`SessionReminderDaily` has no run-only setting (it's schedule-triggered)
— it always runs as the bound connections.

---

## 4. Rebinding an environment that was imported wrong

No re-import and no app changes needed:

1. **Create the connections under the right account:** sign in as the
   service account > **Connections** > New connection > add SharePoint,
   Office 365 Outlook, OneDrive for Business, and Microsoft Teams.
2. **Repoint the connection references:** as an owner of the solution,
   open **Solutions > Event Session Flows > Connection references**.
   Select each of the four references > **Edit** > pick the service
   account's connection > Save.
   - If the service account's connections aren't offered, share them
     first (Connections > select > Share), or do the rebind signed in
     as the service account after making it a co-owner of the solution.
3. **Bounce the flows:** turn each flow Off and back On so it picks up
   the new binding.
4. **Do the run-only pass** from § 3 — rebinding alone does not change
   flows that are set to "Provided by run-only user".
5. **Send a test:** register in the app and confirm the email now comes
   from the service account.

For flows imported via the **legacy per-flow packages** there are no
connection references — instead, open each flow > **Edit** > each action
shows its connection under the "Connected to …" label > **Change
connection** > pick the service account's. Then do the run-only pass.

---

## 5. "Send as" options compared

| Approach | From address | Needs Exchange admin? | Verdict |
|---|---|---|---|
| Service account owns the Outlook connection (§ 2) | The service account itself | **No** — an account may always send as itself | **Recommended** |
| "Send an email from a shared mailbox (V2)" action | A shared mailbox | **Yes** — connection owner must be granted *Send As* on that mailbox | Use only if you can get the grant; swap the action in SendAppEmail (§ 3.1 of the flows guide) — the trigger contract doesn't change, so no app edits |
| Keep a personal connection | The admin who imported | No | Avoid — emails break when that person leaves or changes their password |
| Provided by run-only user | Each registrant themselves | No | Avoid for email (confusing, and users may lack mailbox rights); **correct** for AddToCalendar only |

---

## 6. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| Emails sent **from the person who registered** | A connector on an app-called flow is set to *Provided by run-only user* — § 3 |
| Emails sent from the admin who imported | Connection references bound to a personal connection — rebind, § 4 |
| Emails stopped after a password change / someone left | Personal connection broke — rebind to a service account, § 4 |
| "Connection not found / not authorized" right after import | A reference was left unbound, or bound to a connection the flow owner can't use — Solutions > Connection references |
| Users prompted to consent to connectors on first app run | Normal — the app's own connectors (SharePoint, Office 365 Users, the flows) require one-time per-user consent |
| Calendar events land in the wrong calendar | AddToCalendar was switched away from *Provided by run-only user* — switch it back (§ 3 exception) |
| CSV exports missing | ExportCSV saves to the **connection owner's** OneDrive (`/CSV Exports`) — after rebinding, look in the service account's OneDrive |

---

## 7. Post-deployment checklist

- [ ] Service account created, licensed (Exchange + Power Automate), Edit on the SharePoint site
- [ ] All four connection references bound to the service account's connections
- [ ] All seven flows On; real admins added as co-owners
- [ ] Run-only users set to **Use this connection** on SendAppEmail, ExportCSV, SendReportEmail, ShareEvent, SyncExternalList
- [ ] AddToCalendar left on **Provided by run-only user**
- [ ] SessionReminderDaily's Get items step repointed at the production site (DEPLOYMENT.md § 2.2)
- [ ] Test register → confirmation email arrives **from the service account**
- [ ] Test "Add to calendar" → event lands in the **user's** calendar
