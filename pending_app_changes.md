# Pending App Changes & Notes

This document tracks all requested changes during testing. All items are now completed and verified!

---

## ✅ Change 1 — GUI Refresh Bug & Column Ordering — **DONE**

- ✅ `_add_column()` now calls `_reload_columns_keep_selection()` — list refreshes instantly after adding.
- ✅ **▲ Move Up / ▼ Move Down** buttons added to the **Profiles** sidebar.
- ✅ **▲ Move Up / ▼ Move Down** buttons added to the **Columns** center panel.
- ✅ **Settings column order follows profile order**: Column checkboxes in the **Configure Output Columns** (Settings) window now appear in the exact order defined in the profile rather than discovery order.

---

## ✅ Change 2 — Editable Extraction Rules (No Hardcoded Python Logic) — **DONE**

- ✅ `regex` rule type added to `logic.py` — accepts `pattern`, `group`, `pick: "first"/"last"`.
- ✅ `regex_combine` rule type added to `logic.py` — accepts `patterns` list + `format` string (e.g. `"{0} / {1}"`).
- ✅ `pdf_profiles.json` updated: `special: strecke_extractor` replaced with 4 cascading `regex` rules.
- ✅ `pdf_profiles.json` updated: `special: meterzahlen_extractor` replaced with `regex` + 2 `regex_combine` rules.
- ✅ Both new rule types are fully editable from the GUI rule editor.
- ✅ `_test_extraction()` (full profile test) and `_test_selected_rule()` (per-rule test) both handle `regex` and `regex_combine`.

---

## ✅ Change 3 — PDF Visual Preview in Calibration Window — **DONE**

- ✅ PDF page image viewer panel added.
- ✅ Page rendering as image using PyMuPDF pixmap with PIL/Pillow highlight overlays.
- ✅ Clicking on the PDF image identifies text at coordinates and auto-selects matching text line in listbox.
- ✅ Clicking a text line highlights the corresponding region on the PDF image.

---

## ✅ Change 4 — Calibration Panel UX Improvements — **DONE**

- ✅ **Trigger Keywords section**: inline hint label added — *"Comma-separated keywords — if ANY appears in the PDF, this profile activates."*
- ✅ **Rule type dropdown**: now shows full descriptive labels (e.g. `"inline — value on the SAME line as keyword"`).
- ✅ **Dynamic param fields**: selecting a rule type shows only relevant input fields.
- ✅ **▶ Test Rule** button added — tests selected rule inline with result display.

---

## ✅ Change 5 — Multi-page Preview, In-place Rule Editing & Copyable Text — **DONE**

- ✅ **Multi-Page Navigation in Calibration**:
  - Added `◀ Prev Page`, `Page X / Y`, `Next Page ▶` controls to the Calibration preview panel.
  - Users can now navigate multi-page sample PDFs; text lines, bounding boxes, alert banners, and image rendering reload dynamically for the selected page.
- ✅ **In-place Rule Editing**:
  - Selecting an existing rule in the *Extraction Rules for selected Column* listbox automatically populates the rule type combo and parameter fields with the rule's exact settings.
  - Added a **`✓ Update Selected Rule`** button so users can modify existing rules directly without having to delete and re-create them.
- ✅ **Copyable Text Lines & Context Menu**:
  - Bound `Ctrl+C` on the `PDF Text Lines` listbox to copy selected line text directly to system clipboard.
  - Added a **`📋 Copy Selected Line`** button and a right-click context menu (`Copy Line Text`, `Set as Trigger Keyword`).
- ✅ **Visual Text Selection Regression**: Address issues with space-separated values (`Anfang S1901`) without breaking hyphenated labels by improving the InlineExtractor.
- ✅ **Multi-Page Support in Calibration**: Ensure the visual PDF preview, text line listbox, and coordinate mapping correctly paginate through multi-page PDFs.
- ✅ **In-Place Rule Updates**: Allow selecting a rule to auto-populate the editing fields, making it easy to adjust and apply changes directly without deleting/recreating.
- ✅ **Copy PDF Line Text**: Implement Ctrl+C and a context menu on the text lines listbox to quickly copy sample text for writing Regex/Inline rules.
- ✅ **Progress bar should show the numbers**: Update the progress bar label to show the fraction and percentage processed (`Processed 5 of 10 PDFs (50%)`).
- ✅ **Selectable sector titles**: Make all LabelFrame headers on the Calibration window into selectable `tk.Entry` widgets for easy copy-pasting.
- ✅ **Hausanschluss Special Extractors Test**: Support testing `special: hausanschluss_` rules inside the Calibration window, returning dummy or true results when tested.
- ✅ **Metadata Columns**: Add `File Size`, `Created Date`, `Created By`, and `Last Modify Date` properties as optional extraction columns and populate them.
- ✅ **Colon Optional Handling**: Address the request that regex rules should process lines with and without `:`.

---

## ✅ Polish & Bugfixes — **DONE**

- ✅ **Fixed Corrupted UI Layout (`_build_ui`)**: Restored the missing layout configurations and `_build_ui` method that was accidentally truncated during automated patching, ensuring all three panels render properly.
- ✅ **Fixed ValueError: document closed Loop Crash**: Fixed PyMuPDF boolean check crash when closing Calibration window.
- ✅ **Fixed Profile Deletion Sync**: `reload_column_categories()` now purges deleted profiles and columns immediately.
- ✅ **Simplified Profile Naming**: Default profile names simplified (`SpeedNet`, `Einblas`, `Hausanschluss`, `Standortsicherung`).
- ✅ **Fixed UI Cutoff (2-Column Layout)**: Horizontal split ensures all buttons fit on non-maximized laptop screens.
- ✅ **Fixed Date Normalization**: Fixed colon-separated dates (`04:05:2026`) and time digit erasure typo (`[\dots\-]` -> `[.\-]`).
- ✅ **Enhanced Inline Rule Separator Parsing**: Updated the `InlineExtractor` logic to support space-separated label-value pairs (making colons/hyphens optional) so lines like `Anfang S1901` parse correctly, while ensuring compound words (e.g. `Rohr-Temperatur`) are not false matched.

---

## Notes
- To highlight search zones in the PDF viewer, ensure PIL/Pillow is installed: `pip install Pillow`
- The `special:` extractor remains fully supported for Hausanschluss widgets, signatures, and image verification logic.

