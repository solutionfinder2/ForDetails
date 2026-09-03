# Showme Accordion — End-User SOP (Standard Operating Procedure)

**Applies to:** Showme Accordion web part, version 1.0.8 (MVP 1)
**Audience:** Page editors and content authors (no technical skills required)
**Created by:** IT Department
**Last updated:** September 1, 2026

---

## 1. What is the Showme Accordion?

The Showme Accordion is a SharePoint web part that displays content from a SharePoint
list as **expandable sections** (an "accordion"). Readers click a section title to open
it and read the content — text, images, links, tables, and formatting all display
exactly as they were written in the list.

Typical uses: FAQs, policies and procedures, how-to guides, announcements grouped by
topic, department handbooks.

**Important to know:**

- The web part is **read-only**. It never changes your list — all content is added and
  edited in the SharePoint list itself.
- You do **not** need a specially built list. Any list with at least one text column can
  be used, and optional columns unlock extra features (explained in section 4).

### The three roles

| Role | What they do | What they need |
|---|---|---|
| **Reader** | Views the page, opens/closes sections, searches and filters | Read access to the site |
| **Content author** | Adds and edits the sections in the SharePoint list | Edit access to the list |
| **Page editor** | Adds the web part to a page and configures its settings | Edit access to the page |

---

## 2. Adding the web part to a page (page editors)

1. Go to the page and click **Edit** (top right).
2. Hover where you want the accordion and click the **+** (plus) button.
3. In the web part picker, search for **Showme Accordion** (look for the accordion
   instrument icon) and click it.
4. The web part appears with a setup panel that says
   *"Showme Accordion - choose a list to get started"*. This is normal — it ships
   unconfigured on purpose. The panel lists exactly which columns are required and
   which optional columns unlock extra features.
5. Continue with section 3 to connect it to your list.

---

## 3. First-time setup: connecting your list (page editors)

1. With the page in edit mode, select the web part and click the **pencil (Edit web
   part)** icon — or click the **Open the settings** button on the setup panel.
2. **Step 1 - Pick your list:** choose your content list from the **Content list**
   dropdown. The dropdown shows every visible list on the current site.
   - A status line under the dropdown tells you immediately whether the list has all
     the optional columns or which ones are missing. Missing columns are fine — each
     one simply switches its feature off.
3. **Step 2 - Pick the columns:**
   - **Content column (required):** the column that holds the section body text. Only
     text columns from your list are offered.
   - **Category column (optional):** a Choice column used to group sections, power the
     category filter dropdown, and enable the "Tabs by category" layout. Pick
     **(No category column)** if you don't want grouping.
4. Close the settings pane. Your sections should now appear.
5. While the page is in edit mode, a **column checklist card** shows on the web part
   summarizing the list ("works, with N optional improvements available"). Click
   **Show details** to see per-column suggestions. Readers never see this card, and you
   can hide it entirely with the "Column checklist" setting.
6. Click **Republish** to save the page.

---

## 4. Managing content (content authors)

All content lives in the SharePoint list. To open it: **Site contents** → your list.

### 4a. Adding a section

1. In the list, click **+ New**.
2. Fill in:
   - **Title** — the section heading readers click on.
   - **Your content column** (often called *Content*) — the section body. Use the
     toolbar to format text, and insert links, images, and tables. What you see here is
     what readers see on the page.
   - **Category** (if your list has one) — pick the topic; the web part groups by it.
3. Click **Save**. Click **Refresh** on the web part (or reload the page) to see it.

### 4b. Optional columns and what they do

These columns are optional. If your list has them, they work automatically; if not,
the web part simply ignores that feature.

| Column | Type | What it does |
|---|---|---|
| **SortOrder** | Number | Controls the order of sections (1, 2, 3...). Without it, sections are sorted alphabetically by title. |
| **Expanded** | Yes/No | *Yes* = the section starts **open** when the page loads. |
| **Display** | Yes/No | *No* = the section is **hidden** from the page without deleting it. Great for drafts. |
| **StartDate** | Date and Time | With scheduling on, the section appears **from** this date. |
| **EndDate** | Date and Time | With scheduling on, the section disappears **after** this date. |

### 4c. Scheduling content (StartDate / EndDate)

Scheduling only takes effect when the page editor has turned **Use schedule** on in the
web part settings.

- **Both dates set** — the section shows only between them.
- **Only StartDate** — the section appears on that date and stays.
- **Only EndDate** — the section shows now and disappears after that date.
- **No dates** — the section always shows.
- A section with **Display = No** stays hidden regardless of its dates.

### 4d. Hiding a section temporarily

Set **Display** to **No** in the list. The section vanishes from the page but stays in
the list, ready to be switched back on. (Note: hidden sections are hidden for tidiness,
not security — anyone with read access to the list itself can still open the list and
see the item.)

---

## 5. Everyday reader features

- **Search box** — type to filter sections; it matches titles, categories, and the
  visible text of the content. Matching sections expand automatically.
- **Category filter** — the dropdown next to the search narrows to one category.
- **Expand all / Collapse all** — open or close every visible section at once.
- **Refresh** — re-pulls the list without reloading the page.

Each of these can be shown or hidden by the page editor in the settings.

---

## 6. Settings reference (page editors)

Open the web part settings (pencil icon) to find these groups:

### Step 1 - Pick your list / Step 2 - Pick the columns
Covered in section 3. Change the list or columns any time; the web part re-checks the
columns and auto-corrects the pickers.

### Display
- **Heading** — the title text above the accordion (default "Content Sections").
- **Header (heading and section count)** — hides/shows the heading and the
  "Showing X of Y sections." line together.
- **Search box / Category filter dropdown / Expand all / Refresh button** — show or
  hide each toolbar control.
- **Column checklist (edit mode only)** — hides/shows the setup checklist card that
  appears in edit mode.
- **Use schedule (Start / End date)** — turns date-based scheduling on or off
  (see section 4c).
- **Maximum sections to show** — how many sections display, from 1 to 500
  (default **30**). If the list has more, the page shows a small note that some
  sections are hidden by the limit.

### Styling
- **Layout** — four ways to present the same content:
  - **Accordion** (default) — stacked expandable sections, grouped by category.
  - **Sidebar menu (left)** / **Sidebar menu (right)** — section titles become a
    navigation menu; one section shows at a time in a reading panel.
  - **Tabs by category (top)** — one tab per category (only offered when a category
    column is connected).
- **Accent color** — follow the site theme or pick a preset color.
- **Custom accent color (hex)** — overrides the dropdown (e.g. `#0078d4`).
- **Accent color on section titles** — title bars become colored banners.
- **Background** — transparent, white card, subtle gray, or one of seven soft color
  tints (blue, teal, green, yellow, peach, pink, lavender).
- **Custom background color (hex)** — overrides the background dropdown.
- **Item size** — Small / Medium / Large text and spacing.

---

## 7. Troubleshooting

| What you see | What it means | What to do |
|---|---|---|
| *"Showme Accordion - choose a list to get started"* | No list is connected yet | Page editor: open the settings and pick a list (section 3) |
| *"Could not load content from ... Show details"* | The list could not be read | Click **Show details** and send the text to your site owner; usually the list was renamed or deleted, or you lack permission |
| A section is missing from the page | It may be hidden or scheduled out | Check the item in the list: **Display** = Yes? Dates current? Also check the search box and category filter aren't narrowing the view |
| *"...more are hidden by the section limit"* | The list has more sections than the limit | Page editor: raise **Maximum sections to show** in the settings |
| Checklist card says "optional improvements available" | Optional columns are missing — nothing is broken | Optional: add the suggested columns to the list to unlock those features |
| New list item doesn't appear | The page shows cached data | Click the **Refresh** button on the web part, or reload the page |
| Content looks unformatted | The content column is plain text | Ask the list owner to use an enhanced rich text ("Multiple lines of text") column |

---

## 8. Good practices

- **Keep titles short and specific** — readers scan them like a table of contents.
- **Use SortOrder in steps of 10** (10, 20, 30...) so you can insert items later
  without renumbering everything.
- **Use Display = No for drafts** instead of deleting and re-creating sections.
- **Don't paste from Word directly** if formatting looks odd — paste as plain text and
  reformat in the list's editor.
- **One list per accordion** keeps things simple, but several web parts can safely
  point at the same list (each with its own layout and styling).

---

## 9. Support

- **Content questions** (adding/editing sections): contact your list owner.
- **Page and settings questions**: contact the page editor or site owner.
- **Technical issues**: contact your SharePoint administrator with the text from the
  error's **Show details** link, if one is shown.

*Solution: spfx-content-accordion v1.0.8.0 — "Showme Accordion" MVP 1, created by the IT Department.*
