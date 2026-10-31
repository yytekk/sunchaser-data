# SunChaser data

Weekly copy of the cafés, bars and restaurants of Paris, Montrouge and Malakoff from OpenStreetMap, read by the SunChaser iOS app.

`build_data.py` queries the Overpass API and keeps a file only if it is valid. The workflow in `.github/workflows/update.yml` runs it every Monday and commits the result. GitHub Pages serves the `.tsv` files.

Data © OpenStreetMap contributors, available under the [Open Database License](https://www.openstreetmap.org/copyright).
