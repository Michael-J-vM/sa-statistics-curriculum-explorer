# Changelog

All notable changes to the **SA Statistics Curriculum Explorer** are recorded here.

This is a public, read-only dashboard for exploring undergraduate Statistics module information contributed by South African higher education institutions. Version entries describe changes to the **dashboard software**, not individual curriculum updates made in the source Google Sheet.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versions are maintained manually; GitHub also keeps a separate automatic commit history.

## [1.0.0] — Initial public release (November 2026)

### Added
- **National Overview:** Summary of catalogued modules, participating institutions, year levels, disciplines and data completeness.
- **Institution Explorer:** Browse an institution's listed modules and their distribution by year level and discipline.
- **Discipline Explorer:** Explore which institutions list modules in particular disciplines and at which year levels.
- **Compare Institutions:** Compare the recorded module offerings and primary disciplines of two institutions.
- **Module Browser:** Search and inspect module records, including available descriptions, contents, learning outcomes, credits and software information.
- **Google Sheets data feed:** Read curriculum records from a separate public Google Sheet, populated from the contributor-maintained master spreadsheet.
- **Data caching:** Configured the application to refresh its cached data after 24 hours, on a subsequent app request. Changes may also be subject to Google Sheets publication delays.
- **Read-only public access:** Deployed through Streamlit Community Cloud from the GitHub repository.
- **Data safeguards:** The public data feed omits the separate *Information provider* column and the *Participants* worksheet. The application treats missing information as missing rather than as evidence that a topic is not taught.

### Notes
- Curriculum comparisons describe **documented offerings**; they do not rank institutions or establish equivalence between modules.
- The master Google Sheet remains the source of truth for curriculum records.
- The first public release uses the existing classification information; expanded multi-topic classification and deeper module-matching features remain possible future enhancements.

## [Unreleased]

### Under consideration
- Refinements based on feedback from participating Statistics departments.
- More detailed comparisons of modules covering similar subject areas.
- Additional visualisations of statistical software and programming coverage.
- Further improvements to standardised discipline and topic classifications.
- Potential future extension to honours and master's modules.

---

## Maintaining this file

When a dashboard update is approved:
1. Add a short description under **Unreleased** (for example, under `Added`, `Changed` or `Fixed`).
2. When publishing a new version, move those notes into a dated version heading (for example, `## [1.1.0] — 2026-12-15`).
3. Commit the updated `CHANGELOG.md` alongside the changed application files.

Routine updates to module information in Google Sheets do **not** require a new software version or changelog entry.
