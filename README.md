# Seer Stories website

Standalone novels by B. Carter at stories.i4seer.com.

Refresh with `python scripts/build_site.py --source C:/SEERTheSeries`. The optional source refresh requires Pillow, fonttools and beautifulsoup4, and exports all 20 current front covers and clean illustrations without rebuilding source books. A normal `python scripts/build_site.py` uses the saved artwork and copy.

The main theme follows The River Run cover: cream slab lettering, deep blue ink and copper sunset artwork. Each book page uses its own clean cover illustration and palette. The seven verified published novels appear on the shelves, followed by a development notice. News and retained detail pages preserve existing publication states; all purchase URLs are retained. Search/filter controls and behavior are removed.

Source records and hashes: `data/stories-artwork.json`. Cover font licenses are in assets/fonts. Artwork theme: assets/stories-cover-theme.css. The builder reapplies this theme and refreshes collection discovery on every run. CNAME and hosting configuration are unchanged; this refresh is local only.

## Domain links prepared October 31, 2026

This local project targets `https://stories.i4seer.com/`. Website links, metadata and page generators use the i4seer.com collection subdomains. The publisher bar links to i4Seer Home and all six collections, with a compact Collections menu on smaller screens. Family links open in the same tab; Amazon links remain unchanged. Local CNAME files are prepared for the target addresses. Deployment, GitHub Pages settings, DNS, redirects and validation are handled by the site owner. No deployment or validation is performed by this update. Historical verification records in docs retain their original addresses and dates.
