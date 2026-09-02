# Build Walkthrough — Content Accordion (spfx-content-accordion)

**Creator:** Teshome S. | **Release:** MVP 1 (v1.0.0)

This document explains how the **Content Accordion** web part was built, step by step, as if
you were building it manually. It reads sections from a SharePoint list and renders the
**rich text (HTML)** in a `Content` column as a searchable, category-filterable accordion.

It is a sibling of the FAQ Accordion (`spfx-faq-accordion`) with three additions the FAQ
does not have:

1. **Rich text body** — the `Content` column is an *enhanced rich text* column; its HTML is
   rendered inside the panel (headings, lists, links, images, tables).
2. **`Expanded` column (Yes/No)** — sections marked *Yes* start expanded when the page loads.
3. **`Display` column (Yes/No)** — sections marked *No* are removed before rendering, so
   editors can stage drafts in the list without publishing them.

Like the FAQ, it also has a **category filter dropdown** next to the search box, plus a
**refresh button** and an org-chart-style settings pane (heading, show/hide toggles for every
toolbar control, accent color with custom hex override, background style, and item size).

It supports three **layouts**: the accordion; a **sidebar menu** (left or right) where the
section titles become a grouped navigation menu and one section at a time is shown in a
content panel beside it; or **tabs by category** where each category is a tab on top and its
sections render as an accordion below.

Stack: SPFx 1.23.2 (Heft build), React 17, Fluent UI 8, PnPjs 4. Node 22.

---

## Step 1 — Create the SharePoint list

List title: `ContentSections` (Generic list). Columns:

| Column     | Type                                    | Purpose                                 |
| ---------- | --------------------------------------- | --------------------------------------- |
| Title      | Single line of text (built-in)          | Section heading                         |
| Content    | Multiple lines — **enhanced rich text** | Section body (HTML)                     |
| Category   | Choice (General, Policies, How To, Announcements) | Grouping + filter dropdown  |
| SortOrder  | Number                                   | Order within the list (lower = earlier) |
| Expanded   | Yes/No, default **No**                   | Start expanded on page load             |
| Display    | Yes/No, default **Yes**                  | Show or hide the section                |
| StartDate  | Date and Time (optional)                 | Schedule: show on/after this moment     |
| EndDate    | Date and Time (optional)                 | Schedule: show until this moment        |

Run `scripts/create-contentsections-list.ps1` (PnP PowerShell in `pwsh`). Two details worth
copying if you provision manually:

- The rich text column must be created from XML so SharePoint gives editors the full
  formatting toolbar:

```powershell
Add-PnPFieldFromXml -List 'ContentSections' -FieldXml `
  "<Field Type='Note' Name='Content' StaticName='Content' DisplayName='Content' RichText='TRUE' RichTextMode='FullHtml' NumLines='10' />"
```

- The Yes/No columns are also created from XML so they get the right defaults
  (`Expanded` defaults to No, `Display` defaults to Yes):

```powershell
Add-PnPFieldFromXml -List 'ContentSections' -FieldXml `
  "<Field Type='Boolean' Name='Expanded' StaticName='Expanded' DisplayName='Expanded'><Default>0</Default></Field>"
Add-PnPFieldFromXml -List 'ContentSections' -FieldXml `
  "<Field Type='Boolean' Name='Display' StaticName='Display' DisplayName='Display'><Default>1</Default></Field>"
```

- The schedule columns use `Format='DateTime'` so editors can set a time of day, not just a
  date (`update-contentsections-columns.ps1` adds them to an existing list):

```powershell
Add-PnPFieldFromXml -List 'ContentSections' -FieldXml `
  "<Field Type='DateTime' Name='StartDate' StaticName='StartDate' DisplayName='Start Date' Format='DateTime' />"
Add-PnPFieldFromXml -List 'ContentSections' -FieldXml `
  "<Field Type='DateTime' Name='EndDate' StaticName='EndDate' DisplayName='End Date' Format='DateTime' />"
```

The sample data includes one item with `Display = No` ("Draft: printer migration notes") so
you can verify hiding works: it exists in the list but never appears in the web part.

## Step 2 — Scaffold

The solution was cloned from `spfx-faq-accordion` and re-identified. If you do this by hand,
change every identity value — this is what was updated:

- `config/package-solution.json` — new solution **name**, **id**, feature **id**, and
  `zippedPackage` path (`solution/spfx-content-accordion.sppkg`).
- `src/webparts/contentAccordion/ContentAccordionWebPart.manifest.json` — new web part **id**
  (`7aeb6905-a5bc-4ffd-b1f3-a674c5f44b09`), alias, title, description, icon
  (`TextDocument`), and default `listTitle` = `ContentSections`.
- `config/config.json` — bundle name, entrypoint path, manifest path, localized-resources key
  (`ContentAccordionWebPartStrings`).
- `package.json` name, `.yo-rc.json` solution/component names and `libraryId`.
- `teams/` icon PNGs renamed to the new web part id.

## Step 3 — PnPjs setup: `src/services/pnpjsConfig.ts`

Unchanged from the FAQ solution — a `getSP(context?)` singleton that initializes
`spfi().using(SPFx(context))` once in `onInit` and returns the cached instance everywhere else.

## Step 4 — Model: `src/models/IContentItem.ts`

```typescript
export interface IContentItem {
  Id: number;
  Title: string;         // section heading
  /** Rich text (HTML) body rendered inside the accordion panel. */
  Content: string;
  Category?: string;
  SortOrder?: number;
  // FEATURE (ask: "a column for the expanding on collapse field"):
  // Yes/No list column; Yes = the section starts expanded when the page loads.
  Expanded?: boolean;
  // FEATURE (ask: "a display column to display it or not"):
  // Yes/No list column; No = the section is not rendered at all.
  Display?: boolean;
  // FEATURE (ask: start/end date scheduling): ISO date-time strings; only
  // enforced when the "Use schedule" setting is on.
  StartDate?: string;
  EndDate?: string;
}
```

Note the model keeps the fixed names `Content` and `Category` even though the real list
columns are pickable — the hook maps whatever columns the user chose onto these fields,
so the component code never changes.

## Step 5 — Hook: `src/hooks/useContentItems.ts`

Same shape as `useFaqItems` (items / loading / error / refresh) with these changes:

- **Signature**: `useContentItems(listTitle, contentField, categoryField, useSchedule)`.
  The content and category column names come from the property pane pickers (see Step 5b),
  so nothing in the UI is hard-coded to `Content` or `Category`.
- **Schema-aware select**: before querying items the hook reads the list's columns
  (`getListColumns`, Step 5b) and only selects the ones that actually exist, so the item
  query can never fail with "column does not exist". It returns a `schema` status object
  (`contentMissing`, `hasCategory`, `hasSchedule`, `missingOptional`) that the component
  uses to degrade gracefully: no `SortOrder` = list order, no `Display` = everything
  shows, no dates = schedule ignored, no category column = flat list without the filter.
  A missing content column sets `schema.contentMissing` and the component shows a friendly
  message instead of a raw REST error.
- **The Display column and the schedule are enforced here**, before the UI ever sees the
  data. `useSchedule` is fed by the property pane toggle:

```typescript
const isInScheduleWindow = (item: IContentItem, now: Date): boolean => {
  if (item.StartDate && now < new Date(item.StartDate)) { return false; }
  if (item.EndDate && now > new Date(item.EndDate)) { return false; }
  return true;
};

// inside refresh():
const now = new Date();
const visible = results.filter(item =>
  item.Display !== false &&
  (!useSchedule || isInScheduleWindow(item, now))
);
```

Filtering client-side (instead of an OData `$filter`) means an item with an empty Display
value is still shown, which matches the column's "default Yes" intent — and empty dates
mean "no restriction". The window is evaluated on every load, so the Refresh button
re-applies the schedule without a page reload. When the toggle is off, dates are ignored
entirely.

Sorting is `SortOrder` ascending (missing values last), then `Title` alphabetically.

## Step 5b — List schema service: `src/services/listSchema.ts`

FEATURE (ask: pickable content/category columns + core-column check). One small service
powers both the property pane pickers and the hook's graceful degradation:

```typescript
// Titles of the site's visible custom lists, for the list-picker dropdown
export const getSiteLists = async (): Promise<string[]> => {
  const sp = getSP();
  const lists = await sp.web.lists.select('Title')
    .filter('Hidden eq false and BaseTemplate eq 100')();
  return lists.map(l => l.Title).sort((a, b) => a.localeCompare(b));
};

// Reads the visible columns of the list (throws if the list doesn't exist)
export const getListColumns = async (listTitle: string): Promise<IListColumn[]> => {
  const sp = getSP();
  const fields = await sp.web.lists.getByTitle(listTitle)
    .fields.select('InternalName', 'Title', 'TypeAsString')
    .filter('Hidden eq false')();
  return fields.map(f => ({ internalName: f.InternalName, title: f.Title, type: f.TypeAsString }));
};

// Column pickers: Note/Text columns qualify as content, Choice columns as category
export const contentColumnCandidates = (columns) =>
  columns.filter(c => (c.type === 'Note' || c.type === 'Text') && c.internalName !== 'Title');
export const categoryColumnCandidates = (columns) =>
  columns.filter(c => c.type === 'Choice');

// Core-column check: compares against the fixed core set
// SortOrder (Number), Expanded (Yes/No), Display (Yes/No),
// StartDate (Date and Time), EndDate (Date and Time)
export const checkCoreColumns = (columns): ICoreColumnCheck => { /* missing + wrongType */ };
```

Two details worth knowing:

- Columns are matched by **internal name** (`SortOrder`, not "Sort Order"), which is what
  the REST API uses. The pickers display the friendly name but save the internal name, so
  a column whose display name was renamed still works.
- `checkCoreColumns` reports two buckets: columns that are **missing** entirely, and
  columns that exist with the **wrong type** (e.g. an `Expanded` text column instead of
  Yes/No). Both appear in the property pane status line.

## Step 6 — Component: `src/webparts/contentAccordion/components/ContentAccordion.tsx`

Everything the FAQ accordion does (Set-of-ids expand state, pure-CSS animation, groups by
category, search auto-expands matches, expand/collapse all) plus the new behaviors:

### 6a. Expanded column → initial state

Applied **once per data load** using a ref, so it seeds the initial view but never fights
the user's own toggling afterwards:

```tsx
const initializedRef = React.useRef<boolean>(false);
React.useEffect(() => {
  if (!initializedRef.current && items.length > 0) {
    initializedRef.current = true;
    setExpandedIds(new Set(items.filter(i => i.Expanded === true).map(i => i.Id)));
  }
}, [items]);
```

### 6b. Search against rich text

Searching raw HTML would match tag names and attribute noise (`<strong>`, `href=...`).
The component strips tags once per data load and searches the visible text:

```tsx
/** Strip HTML tags so search can match against the visible text of the rich content. */
const plainTextOf = (html: string): string => {
  const div = document.createElement('div');
  div.innerHTML = html || '';
  return div.textContent || '';
};

const searchText = React.useMemo(() => {
  const map = new Map<number, string>();
  items.forEach(item => map.set(item.Id, plainTextOf(item.Content).toLowerCase()));
  return map;
}, [items]);
```

### 6c. Category filter dropdown (same pattern as the FAQ)

Options are the distinct categories that occur in the list plus "All categories"; the filter
and the search compose (an item must satisfy both):

```tsx
const filtered: IContentItem[] = React.useMemo(() => {
  const q = query.trim().toLowerCase();
  return items.filter(item => {
    if (categoryFilter && (item.Category || 'General') !== categoryFilter) {
      return false;
    }
    if (!q) {
      return true;
    }
    return item.Title.toLowerCase().indexOf(q) !== -1 ||
      (searchText.get(item.Id) || '').indexOf(q) !== -1 ||
      (item.Category || '').toLowerCase().indexOf(q) !== -1;
  });
}, [items, query, categoryFilter, searchText]);
```

### 6d. Rendering the rich text

The panel body renders the HTML directly:

```tsx
<div
  className={styles.richText}
  dangerouslySetInnerHTML={{ __html: item.Content || '' }}
/>
```

This is acceptable because the `Content` column is a SharePoint **enhanced rich text**
column: SharePoint sanitizes what editors can save there, and only users with list edit
rights can author it. If you ever feed this component HTML from an untrusted source,
sanitize it first (e.g. DOMPurify).

### 6e. Refresh button

Re-pulls the list without reloading the page. The hook already exposes `refresh()`; the
button just wraps it with a busy flag so it disables itself while loading. The user's
expand/collapse choices are intentionally kept across refreshes:

```tsx
const [refreshing, setRefreshing] = React.useState<boolean>(false);
const onRefresh = React.useCallback(async (): Promise<void> => {
  setRefreshing(true);
  try {
    await refresh();
  } finally {
    setRefreshing(false);
  }
}, [refresh]);
```

### 6f. Settings-driven rendering (same pattern as the org chart)

- Every toolbar control checks its toggle with `props.showX !== false`, so instances that
  predate a setting default to "shown".
- The accent color travels as a CSS variable: the component validates the custom hex, falls
  back to the preset dropdown value, and sets `--accAccent` inline. "Follow site theme"
  leaves it unset so the stylesheet falls back to `--themePrimary`, which the web part class
  sets from the site theme in `onThemeChanged`.

```tsx
const customAccent = (props.customAccentColor || '').trim();
const accentHex = /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.test(customAccent)
  ? customAccent
  : props.accentColor && props.accentColor !== 'theme' ? props.accentColor : undefined;
const accentStyle = accentHex
  ? ({ '--accAccent': accentHex } as React.CSSProperties)
  : undefined;
```

- Background (`transparent` / `white` / `neutral`) and item size (`small` / `medium` /
  `large`) are applied as extra classes on the root `<section>`. The soft color presets
  use hex values as their dropdown keys; those (and the custom background hex, which
  wins over the dropdown) are passed inline as the `--accBgColor` CSS variable consumed
  by the `.bgCustom` class.

### 6g. Sidebar menu layout (left or right)

The `layout` setting switches between `accordion`, `sidebarLeft` and `sidebarRight`. In
sidebar mode:

- The grouped section titles render as a `<nav>` of buttons; the active one gets an
  accent-colored left border and bold text (`aria-current` for accessibility).
- The selected section's title and rich text render in a content panel next to the menu.
  "Right" simply flips the flex direction (`.sidebarOnRight { flex-direction: row-reverse }`).
- Selection is kept valid automatically: on first load it prefers the first section marked
  **Expanded**, then the first visible one; if search/filter removes the selected section,
  it falls back to the first remaining match.
- Search, the category filter, and Refresh keep working (they narrow the menu); Expand all /
  Collapse all is hidden because it has no meaning with one section shown at a time — its
  property pane toggle is also disabled while a sidebar layout is selected.
- On screens narrower than 768px the sidebar stacks on top of the content panel.

```tsx
const isSidebar = props.layout === 'sidebarLeft' || props.layout === 'sidebarRight';
const [selectedId, setSelectedId] = React.useState<number | undefined>(undefined);

React.useEffect(() => {
  if (!isSidebar) { return; }
  if (filtered.length === 0) { setSelectedId(undefined); return; }
  if (selectedId === undefined || !filtered.some(i => i.Id === selectedId)) {
    const preferred = filtered.find(i => i.Expanded === true) || filtered[0];
    setSelectedId(preferred.Id);
  }
}, [isSidebar, filtered, selectedId]);
```

### 6h. Tabs by category

The `layout` value `tabs` renders a Fluent UI `Pivot` (headers only) with one tab per
category, including an item count badge. The accordion markup is shared between layouts via
a `renderAccordionItems(groupItems)` helper — the accordion layout calls it once per group
under a category header, and the tabs layout calls it once for the active tab's group.

- Selecting a tab is plain state (`activeCategory`); a `useEffect` keeps it valid, so if
  search or the filter dropdown removes the active category, the first remaining tab is
  selected automatically.
- Search auto-expand, Expand all / Collapse all, and Refresh all still apply inside the
  active tab.

```tsx
const isTabs = props.layout === 'tabs';
const [activeCategory, setActiveCategory] = React.useState<string | undefined>(undefined);

React.useEffect(() => {
  if (!isTabs) { return; }
  if (groups.length === 0) { setActiveCategory(undefined); return; }
  if (activeCategory === undefined || !groups.some(g => g.category === activeCategory)) {
    setActiveCategory(groups[0].category);
  }
}, [isTabs, groups, activeCategory]);
```

## Step 7 — Styles: `ContentAccordion.module.scss`

Carried over from the FAQ: the card look, the rotating chevron, and the
`grid-template-rows: 0fr → 1fr` expand/collapse animation.

New: a `.richText` block that styles the *tags inside the rendered HTML* via `:global` —
paragraph/list spacing, theme-colored links, responsive images (`max-width: 100%`),
blockquotes with an accent-colored left border, and bordered table cells. Without this, raw
rich text HTML looks unstyled inside the web part.

Settings support:

- `--accent: var(--accAccent, var(--themePrimary, #0078d4))` on `.app` — every accent-colored
  element (category header underline, chevron, focus outline, blockquote border) uses
  `var(--accent)`.
- `.bgWhite` / `.bgNeutral` for the background setting; `.sizeSmall` / `.sizeLarge` adjust
  button padding and font sizes for the item size setting.

## Step 8 — Web part class and manifest

`ContentAccordionWebPart.ts` initializes PnPjs in `onInit` and maps theme slots to CSS
variables in `onThemeChanged` (including `--themePrimary`, which feeds the "Follow site
theme" accent option). The property pane has three groups:

**First-run experience** (FEATURE, ask: no list selected by default + explain the
needed columns on the page): the manifest ships `listTitle`, `contentField` and
`categoryField` empty. With no list picked, the component renders a *setup panel*
instead of an error: an intro, a "Required column" table (any text column for the
body), an "Optional columns" table (Category / SortOrder / Expanded / Display /
StartDate / EndDate, each with the feature it unlocks), a tip about the provisioning
script, and — in edit mode — an "Open the settings" button wired to
`this.context.propertyPane.open()` via the `onConfigure` prop. Once a list is picked,
an edit-mode-only *checklist card* names the list and marks every core/optional
column present (✓) or missing (✗) with a suggestion per gap; the hook exposes the
list's raw `columns` so the card is computed with the same `checkCoreColumns` used by
the pane. Readers never see the checklist — only a blocked message if the content
column itself is missing.

The property pane groups are numbered steps so the order is obvious:

- **Step 1 - Pick your list / Step 2 - Pick the columns** — a list dropdown, a live
  status line, and two column pickers (disabled until a list is chosen):
  - **Content list** is a dropdown of every visible regular list on the site
    (`getSiteLists`: `Hidden eq false and BaseType eq 0`), so there is nothing to
    type and no way to point at a list that doesn't exist.
  - A `PropertyPaneLabel` under it reports the core-column check — "Core columns: all
    present" or e.g. "Missing columns: Expanded (Yes/No), EndDate (Date and Time)".
  - **Content column** dropdown lists every *Multiple lines of text* / *Single line of
    text* column on the list; **Category column** lists every *Choice* column plus a
    "(No category column)" option that turns grouping and the filter off.
  - Lists and columns load in `onPropertyPaneConfigurationStart` (when the pane opens);
    `onPropertyPaneFieldChanged` re-reads the columns when a different list is picked
    and **auto-corrects the configuration**: a content/category column that doesn't
    exist on the new list falls back to the first eligible column (or "(No category
    column)"), and a tabs layout without a category column falls back to the accordion.
    `this.context.propertyPane.refresh()` re-renders the pane with the fresh options.
  - Category-dependent controls follow `_categoryAvailable()`: without a category
    column the "Category filter dropdown" toggle is disabled and "Tabs by category"
    is removed from the layout options.
- **Display** — Heading text; Shown/Hidden toggles for the search box, category filter
  dropdown, Expand all / Collapse all buttons, and the Refresh button; the
  **Use schedule (Start / End date)** toggle that turns date-window filtering on or off;
  **Maximum sections to show** (a text field validated to a whole number 1-500,
  default 30 — the limit is applied *after* Display/schedule filtering and sorting,
  and the page shows a small note whenever it cuts sections off); and the
  **Column checklist (edit mode only)** toggle that hides the on-page checklist card.
- **Styling** — Layout (Accordion / Sidebar menu left / Sidebar menu right / Tabs by
  category), accent color (Follow site theme + 7 presets), custom accent color (hex,
  overrides the dropdown), **Accent color on section titles** (a toggle that adds the
  `titleAccentBg` class: section title bars get `background: var(--accent)` with white
  text and chevrons; in sidebar mode the active menu item and the content panel title
  get the same treatment), background (Transparent / White card / Subtle gray plus soft
  blue, teal, green, yellow, peach, pink and lavender tints), custom background color
  (hex, overrides the dropdown), and item size (Small / Medium / Large). The **Display**
  group also has a **Header (heading and section count)** toggle that hides the heading
  and the "Showing X of Y sections." line together.

All defaults live in `ContentAccordionWebPart.manifest.json` under
`preconfiguredEntries.properties`.

**Name and custom picker icon** — the web part is titled **Showme Accordion** in the
manifest, and its `iconImageUrl` holds a base64-encoded PNG data URI (a musical
accordion line-art icon: piano keys, bellows, buttons; source image in
`webpart-icon.png` at the project root), which SharePoint shows in the web part picker
instead of the generic Fluent font icon. Embedding the image as a data URI means no
external hosting is needed — the icon travels inside the package.
Solution authorship ("Teshome S.") is recorded in `package-solution.json` under
`solution.developer.name` and in the catalog descriptions under `solution.metadata`.

## Step 9 — Run, test, package

```powershell
npm install
npm run start    # add "Content Accordion" in the workbench
npm run build    # -> sharepoint/solution/spfx-content-accordion.sppkg
```

Test checklist:

- Sections render formatted content (bold, lists, links, table in "Password and MFA
  requirements", blockquote in "Remote work policy").
- "Welcome to the IT knowledge base" and "Scheduled maintenance window" start **expanded**
  (their `Expanded` column is Yes); everything else starts collapsed.
- "Draft: printer migration notes" does **not** appear (its `Display` column is No). Flip
  Display to Yes in the list and refresh — it appears.
- Search "maintenance" — the announcement auto-expands; search text inside a table works too.
- Category filter: pick "How To" — only that group remains; combine with a search query.
- Expand all / collapse all respect the current filter.
- Refresh: edit a section in the list, click **Refresh** — new content appears without a page
  reload, and your open/closed sections stay as they were.
- Settings: change the heading, hide each toolbar control, switch the accent color (and
  override it with a custom hex), try the white/gray backgrounds and the three item sizes.
- Accent on titles: turn on **Accent color on section titles** — title bars become accent
  banners with white text and chevrons; check the sidebar layout (active item + content
  title) and that changing the accent color recolors the banners.
- Layout: switch to "Sidebar menu (left)" — titles become a menu, clicking one shows its
  content; try "Sidebar menu (right)", then search so the selected item is filtered out and
  confirm the selection jumps to the first match.
- Layout: switch to "Tabs by category (top)" — one tab per category with item counts;
  switch tabs, expand sections inside a tab, then search and confirm the active tab follows
  the remaining matches.
- Schedule: turn on **Use schedule** — "Scheduled maintenance window" stays visible (its
  demo window is active). Set its End Date to yesterday, click Refresh, and it disappears;
  turn the toggle off and it comes back (dates ignored). Sections with empty dates are
  never affected.
- Column pickers: open the pane — the Content list dropdown shows the site's custom
  lists, the status line reads "Core columns: all present", and the Content/Category
  dropdowns list the eligible columns from the selected list. Switch to another list and
  confirm the column pickers re-populate and auto-correct.
- Category options: pick "(No category column)" — the "Category filter dropdown" toggle
  grays out and "Tabs by category" disappears from the Layout options (an active tabs
  layout switches back to Accordion automatically).
- Degradation: point the web part at a list that's missing `Expanded`/`Display`/dates —
  the status line names the missing columns and the web part still renders; pick
  "(No category column)" — the filter and the "General" headers disappear; pick a content
  column the list later loses — a friendly message explains what to fix instead of a REST
  error.

---

## Design decisions worth knowing

- **Display enforced in the hook, not the component** — hidden items never reach the UI, so
  no count, group, or filter option can leak a hidden section.
- **Expanded seeds initial state once** — a plain `useEffect` on `items` would re-expand
  sections every refresh, undoing the user's clicks.
- **Search on stripped text** — searching raw HTML matches markup, not meaning.
- **`dangerouslySetInnerHTML` is fine here** — the HTML comes from a SharePoint rich text
  column that SharePoint itself sanitizes; do not reuse this pattern for arbitrary input.
- **Columns validated before items are queried** — reading the field list first costs one
  extra REST call per load, but it means a misconfigured list produces a specific,
  actionable message ("Missing: Expanded (Yes/No)") instead of a raw OData error, and the
  item query is built only from columns that exist so it can never 400.
- **Internal names, not display names** — the pickers save `InternalName`, which is what
  the REST API addresses. Renaming a column's display name in SharePoint doesn't break
  the web part.
