# DeTLeng Read

A simple multilingual Word-document reader for https://read.detleng.com/.
The reading typography, Noto Naskh Arabic font, English/Spanish LTR and Arabic/Urdu/Shahmukhi RTL paragraph handling, spacing, font controls, fullscreen, in-document search and changing soft backgrounds are retained from Tafseer Bright Reader V3.0.

## Start on Windows

Extract this folder to `D:\DETLENG2\read-detleng` and double-click `START_WINDOWS.bat`. Python 3 is required; no pip packages are needed. The local preview opens at http://127.0.0.1:8100/. Keep the command window open. Port 8100 must be free. Mac/Linux: run `python3 tools/serve.py` from this folder.

To view the already-built snapshot without running the converter, serve `_site` with any static HTTP server. Opening index.html directly with file:// is not supported because the reader loads JSON files.

## Your content folders are the menu

Put `.docx` files anywhere under `content/`. Create, rename, move or delete topic folders and subfolders as needed. The builder discovers all levels automatically. It includes empty folders (keep a `.gitkeep` inside them so Git tracks them), ignores hidden/temporary files and symlinks, and lists folders before documents alphabetically. Filenames become document labels without the `.docx` suffix.

Six sample root folders: English, Urdu, Punjabi, Español, Arabic, More Topics. Eight supplied documents are arranged under English, Urdu and Punjabi. The other folders are empty placeholders, not translated content. Rename them freely. Files and folders can coexist at every level.

Supported reading format: DOCX text. Images, PDF, PPTX, legacy DOC and embedded Word graphics are not converted. This retains the original reader's paragraph-based conversion, not Microsoft Word's full formatting engine. Table cells become sequential paragraphs, as in the original converter. The original Noto Naskh Arabic web font requires internet access when it is not already cached; fallback fonts remain available.

## Library controls

- Library beside the brand opens a compact left-aligned, wide dropdown. Nested folders expand in the same list; long lists scroll inside the dropdown. Deep nesting reduces indentation to protect label space.
- Expand library opens a full-window view in the same tab. Navigate folders, use Back or the folder breadcrumbs, and select a file to return to reading.
- Back to reading closes the expanded library without changing the document. Escape closes either view. The last selected file is remembered on this browser.
- The footer's Explore DeTLeng link opens https://www.detleng.com/ in a new tab.

## Build and publish later

Nothing has been pushed or deployed by this delivery.

1. Keep the existing remote README/CNAME history. Pull or clone `Navid-Ishaq/read-detleng` before adding these project files. Do not force-push over the existing repository.
2. Add this folder's contents, including `.github/workflows/pages.yml`, to your repository. The supplied CNAME is `read.detleng.com`; README can replace the initial placeholder.
3. **One-time change:** GitHub repository Settings → Pages → Build and deployment → Source → **GitHub Actions**. Your screenshot currently shows “Deploy from a branch”; switch it for the automatic Word conversion workflow.
4. Commit and push to `main`. The included workflow converts all DOCX files, generates the recursive catalogue, and deploys only `_site` to Pages. No custom backend, database, API key or paid service is required.
5. Keep the existing custom-domain DNS. Check HTTPS availability in Pages settings and enable Enforce HTTPS when available.
6. Afterward, adding, renaming or deleting content and committing to main triggers a new build and deployment automatically. Visitors receive it after the successful deployment; an open reader checks the catalogue every 30 seconds. File content changes also change its revision.

Manual build: `python tools/build.py`. Output: `_site/`. Do not edit that generated folder; edit `interface.html` and `content/`. `_site/` is included in this ZIP for convenience and ignored by Git. The repository workflow rebuilds it each time.

A malformed DOCX fails the build instead of publishing silently missing content. The last successful hosted deployment remains available. Local previews print conversion errors in the terminal.

## Public content

Only put documents you intend to publish under `content/`. The site never scans your D: drive or unrelated folders. Repository contents and published document text are public when the repository/site are public.
