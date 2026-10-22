# Shared collection discovery

All six Seer Press collections share the same image-card feature. This site shows the other five collections, excluding itself. Home and individual book pages carry the compact cards; `/other-series/` provides a full grid with descriptions and audience labels. Every footer links to the other five websites and the local full grid. Existing cross-series sections are replaced.

The feature uses local assets and static HTML, with a separate namespaced stylesheet that matches this site’s palette. No carousel, remote image dependency, or JavaScript requirement. Site-specific content and maps remain intact.

Run `python scripts/update_collections.py` to refresh this site from `data/seer-collections.json`. Where `scripts/build_site.py` exists, it runs that refresh automatically. To update every local series site from the shared publisher registry, run `python C:/SEERWEB/scripts/sync_collection_sites.py`.

Shared feature source: C:/SEERWEB/scripts/collection_feature.py and C:/SEERWEB/assets/collection-feature.css. Artwork and approved site addresses come from C:/SEERWEB/data/series.json. Images use content-versioned URLs. CNAME and hosting configuration are preserved. This local refresh does not deploy the sites.
