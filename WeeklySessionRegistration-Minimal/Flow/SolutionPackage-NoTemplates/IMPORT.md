# These Dataverse solution files are NOT for import

The files under `SolutionPackage-NoTemplates/` were an attempt at a
Dataverse **Solutions** package. Power Platform rejects that zip as the
**wrong format** for this hand-built content.

**Use instead:**

- `../Packages/*.zip` — Power Automate **Import Package (Legacy)**  
  See `../Packages/IMPORT.md`
- Or build the flows manually — `../MANUAL-FLOWS.md`

This folder is kept only as source JSON/XML reference for the packager
script (`../build_pa_packages.py`).
