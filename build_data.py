#!/usr/bin/env python3
"""Génère les copies OpenStreetMap lues par l'app SunChaser.

Mêmes requêtes et même format que VenueService.swift : si les requêtes changent
là-bas, les changer ici aussi. Un fichier n'est remplacé que s'il est valide :
en cas de panne, la copie précédente reste en ligne.

Usage : build_data.py <dossier de sortie>
"""

import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]
USER_AGENT = "SunChaser-data/1.0 (weekly build)"
COLUMNS = (
    '::type,::id,::lat,::lon,amenity,name,cuisine,opening_hours,outdoor_seating,'
    '"addr:housenumber","addr:street","addr:city","contact:housenumber","contact:street"'
)
COLUMN_COUNT = 14
AMENITIES = 'nwr["amenity"~"^(cafe|bar|pub|restaurant|fast_food|biergarten|ice_cream)$"]'
SUBURBS = "92046|92049"  # Malakoff, Montrouge

# Fichier -> (requête, nombre minimal de lignes pour accepter le résultat)
DATASETS = {
    "osm-places-paris.tsv": (
        f'[out:csv({COLUMNS};false)][timeout:90];\n'
        f'{AMENITIES}(48.815,2.224,48.902,2.470);\n'
        'out center;\n',
        10_000,
    ),
    "osm-places-banlieue.tsv": (
        f'[out:csv({COLUMNS};false)][timeout:90];\n'
        f'area["ref:INSEE"~"^({SUBURBS})$"]["boundary"="administrative"]->.communes;\n'
        f'{AMENITIES}(area.communes);\n'
        'out center;\n',
        50,
    ),
}


def download(mirror, query):
    request = urllib.request.Request(
        mirror,
        data=urllib.parse.urlencode({"data": query}).encode(),
        headers={"User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        return response.read()


def problem_with(data, minimum):
    """Raison de refuser `data`, ou None s'il est valide."""
    # Un serveur surchargé répond 200 avec une page HTML d'erreur.
    if data[:1] == b"<":
        return "page d'erreur HTML"
    lines = data.decode("utf-8").splitlines()
    if len(lines) < minimum:
        return f"{len(lines)} lignes, minimum {minimum}"
    malformed = sum(1 for line in lines if line.count("\t") != COLUMN_COUNT - 1)
    if malformed > len(lines) / 100:
        return f"{malformed} lignes mal formées"
    return None


def fetch(query, minimum):
    for attempt in range(3):
        for mirror in MIRRORS:
            try:
                data = download(mirror, query)
                problem = problem_with(data, minimum)
                if problem is None:
                    return data
                print(f"  {mirror} : {problem}")
            except (OSError, urllib.error.URLError, UnicodeDecodeError) as error:
                print(f"  {mirror} : {error}")
        time.sleep(60 * (attempt + 1))
    return None


def main():
    output = pathlib.Path(sys.argv[1])
    output.mkdir(parents=True, exist_ok=True)
    failed = []
    for name, (query, minimum) in DATASETS.items():
        print(name)
        data = fetch(query, minimum)
        if data is None:
            failed.append(name)
            continue
        (output / name).write_bytes(data)
        print(f"  {len(data.splitlines())} lignes, {len(data) // 1024} Ko")
    if failed:
        sys.exit("Échec : " + ", ".join(failed))


if __name__ == "__main__":
    main()
