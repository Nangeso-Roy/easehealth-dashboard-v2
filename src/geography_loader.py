"""
Geography data loader — facility -> UBOS sub-county crosswalk and assessment counts.
Add these to src/data_loader.py (or import from here).

The crosswalk maps each cleaned facility name to its UBOS ADM4 sub-county
(adm4_name), based on the National Health Facility Master List placements.
All 135 Kobo-tagged assessments map cleanly; zero unmapped.
"""

# Facility (facility_clean) -> UBOS ADM4 sub-county name (matches luwero_adm4.geojson adm4_name)
FACILITY_TO_SUBCOUNTY = {
    "Makulubita HC III":                     "Makulubita",
    "Bbowa HC III":                          "Makulubita",
    "Kasozi HC III":                         "Makulubita",
    "Kanyanda HC II":                        "Makulubita",
    "Nsanvu HC II":                          "Makulubita",
    "Ssambwe HC II":                         "Nyimbwa",
    "Nsawo HC III":                          "Katikamu",
    "Katikamu HC III":                       "Katikamu",
    "Buyuki HC II":                          "Katikamu",
    "Kikoma HC III":                         "Katikamu",
    "Kyalugondo HC III":                     "Katikamu",
    "Bukalasa HC III":                       "Wobulenzi Town Council",
    "Bukolwa HC II":                         "Wobulenzi Town Council",
    "Good Samaritan Katikamu Kisule HC III": "Wobulenzi Town Council",
    "Bombo HC III":                          "Bombo Town Council",
    "Nakatanya HC III":                      "Bombo Town Council",
    "Nyimbwa HC IV":                         "Nyimbwa",
    "Ndejje HC II":                          "Nyimbwa",
    "St. Mary's Mother of Jesus HC IV":      "Nyimbwa",
    "St. Luke Namaliga HC IV":               "Nyimbwa",
}


def subcounty_assessment_counts(kobo_df, facility_col="facility_clean"):
    """
    Given the tagged Kobo dataframe (135 rows with facility_clean),
    return a dict {adm4_name: assessment_count} for the choropleth.
    Computed at runtime so the map reflects the current data.
    """
    counts = {}
    for fac in kobo_df[facility_col].dropna():
        sc = FACILITY_TO_SUBCOUNTY.get(fac)
        if sc:
            counts[sc] = counts.get(sc, 0) + 1
    return counts
