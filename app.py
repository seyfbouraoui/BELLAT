import datetime as dt
import io
import json
import unicodedata
import urllib.request
from pathlib import Path
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="BELLAT - Gestion de la flotte", page_icon="🚚", layout="wide")

DOSSIER = Path(__file__).parent
F_LIVRAISONS = DOSSIER / "livraisons.csv"
F_CAMIONS = DOSSIER / "camions.csv"
F_COORDS = DOSSIER / "coordonnees_wilayas.csv"
F_OSRM = DOSSIER / "distances_osrm.csv"

AFFECTATION_CSV = {
    "2 dépôts": """client,servi_par,distance_km,Q_tonnes
Adrar,Relizane,1100.6005,40.0
Alger (DD Eucalyptus),Centre existant,37.0729,135.0
Annaba,Sétif,284.28,140.0
Aïn M'lila,Sétif,126.228,60.0
Batna,Sétif,126.1214,140.0
Beni-Merad (Blida),Centre existant,0.0,45.0
Biskra,Sétif,205.3749,20.0
Blida (dépôt Meftah),Centre existant,7.9446,340.0
Bordj Bou Arreridj,Sétif,71.5401,80.0
Bouira,Centre existant,127.3348,100.0
Boumerdès,Centre existant,73.9284,105.0
Béjaïa,Sétif,106.781,100.0
Chelghoum Laïd,Sétif,74.8544,60.0
Chlef,Centre existant,169.3498,15.0
Constantine,Sétif,126.4039,40.0
Djelfa,Centre existant,265.9752,95.0
El Oued,Sétif,428.8829,55.0
Guelma,Sétif,226.342,60.0
Jijel,Sétif,128.6081,15.0
Laghouat,Centre existant,375.4907,20.0
M'Sila,Centre existant,257.5528,75.0
Mascara,Relizane,67.5617,40.0
Mila,Sétif,124.5634,15.0
Mostaganem,Relizane,77.1282,30.0
Médéa,Centre existant,44.394,80.0
Oran,Relizane,136.3091,120.0
Oum El Bouaghi,Sétif,202.7364,20.0
Relizane,Relizane,0.0,55.0
Saïda,Relizane,136.4358,35.0
Sidi Bel Abbès,Relizane,156.4291,40.0
Skikda,Sétif,212.6803,60.0
Souk Ahras,Sétif,328.028,20.0
Sétif,Sétif,0.0,120.0
Tamanrasset,Centre existant,1891.7755,20.0
Tiaret,Relizane,95.1827,160.0
Timimoun,Relizane,903.3979,15.0
Tizi Ouzou,Centre existant,130.3194,60.0
Tlemcen,Relizane,237.1419,80.0
Tébessa,Sétif,319.8565,80.0""",
    "3 dépôts": """client,servi_par,distance_km,Q_tonnes
Adrar,Relizane,1100.6005,40.0
Alger (DD Eucalyptus),Centre existant,37.0729,135.0
Annaba,Constantine,153.9439,140.0
Aïn M'lila,Constantine,40.3309,60.0
Batna,Bordj Bou Arreridj,194.2678,140.0
Beni-Merad (Blida),Centre existant,0.0,45.0
Biskra,Bordj Bou Arreridj,197.8273,20.0
Blida (dépôt Meftah),Centre existant,7.9446,340.0
Bordj Bou Arreridj,Bordj Bou Arreridj,0.0,80.0
Bouira,Centre existant,127.3348,100.0
Boumerdès,Centre existant,73.9284,105.0
Béjaïa,Bordj Bou Arreridj,140.2054,100.0
Chelghoum Laïd,Bordj Bou Arreridj,140.8392,60.0
Chlef,Centre existant,169.3498,15.0
Constantine,Constantine,0.0,40.0
Djelfa,Centre existant,265.9752,95.0
El Oued,Bordj Bou Arreridj,421.3353,55.0
Guelma,Constantine,105.8018,60.0
Jijel,Bordj Bou Arreridj,195.5769,15.0
Laghouat,Centre existant,375.4907,20.0
M'Sila,Bordj Bou Arreridj,57.2868,75.0
Mascara,Relizane,67.5617,40.0
Mila,Constantine,49.7771,15.0
Mostaganem,Relizane,77.1282,30.0
Médéa,Centre existant,44.394,80.0
Oran,Relizane,136.3091,120.0
Oum El Bouaghi,Constantine,82.1963,20.0
Relizane,Relizane,0.0,55.0
Saïda,Relizane,136.4358,35.0
Sidi Bel Abbès,Relizane,156.4291,40.0
Skikda,Constantine,82.3442,60.0
Souk Ahras,Constantine,197.6919,20.0
Sétif,Bordj Bou Arreridj,71.0104,120.0
Tamanrasset,Centre existant,1891.7755,20.0
Tiaret,Relizane,95.1827,160.0
Timimoun,Relizane,903.3979,15.0
Tizi Ouzou,Centre existant,130.3194,60.0
Tlemcen,Relizane,237.1419,80.0
Tébessa,Constantine,199.3164,80.0""",
}

OSRM_URL = "https://router.project-osrm.org"
DEPOT_ORIGINE = ("Centre d'expédition Ben Khelil", 36.600, 3.250)

CONSO_L_100KM = {"20 T": 35.0, "15 T": 30.0}
PRIX_GASOIL_DA_L = 29.0
AUTRES_COUTS_DA_KM = 20.0

ANNEE = 2026
CAPACITES = {"20 T": 20, "15 T": 15}
NB_CAMIONS = {"20 T": 14, "15 T": 4}
NB_CHAUFFEURS = 27
CHAUFFEURS = [f"CH{i:03d}" for i in range(1, NB_CHAUFFEURS + 1)]
TYPES = ["20 T", "15 T"]
REGIONS = ["EST", "EXTRÊME", "CENTRE", "OUEST", "DÉPÔT"]

HEURE_DEPART_DEFAUT = dt.time(6, 0)
VITESSE_MOY_KMH = 50.0
TEMPS_CHARG_DECHARG_H = 2.0
REPOS_CHAUFFEUR_H = 10.0
MARGE_CAMION_H = 1.0


def estimer_duree(distance_km):
    if distance_km is None or pd.isna(distance_km):
        return 8.0
    return round(2 * float(distance_km) / VITESSE_MOY_KMH + TEMPS_CHARG_DECHARG_H, 1)

COL_LIV = ["ID", "Region", "Client", "Wilaya", "Distance_km", "Date_livraison", "Heure_depart", "Duree_h",
           "Type_camion", "Quantite_t", "Camion", "Chauffeur", "Statut", "Remarque"]
COL_CAM = ["Camion", "Type", "Capacite_t", "Etat"]


def _j(types_dates):
    return [(d, t) for d, t in types_dates]


def _meme(t, dates):
    return [(d, t) for d in dates]


SEED = [
    ("EST", "Allal Meftah", "M'SILA", 247, _meme("20 T", ["16/05", "16/05"])),
    ("EST", "EURL SOTRAMCO", "M'SILA", 256, [("06/05", "20 T"), ("31/05", "15 T")]),
    ("EST", "Eurl GKWST", "BATNA", 421, _meme("20 T", ["03/05", "06/05", "10/05", "14/05", "17/05", "21/05", "26/05"])),
    ("EST", "Farhat Lamloum", "JIJEL", 454, [("18/05", "15 T")]),
    ("EST", "Eurl Frahtia GPA", "BORJ BOU ARRERIDJ", 219, _meme("20 T", ["05/05", "13/05", "20/05", "31/05"])),
    ("EST", "Harbouch Nadhir", "DJELFA", 277, _meme("20 T", ["11/05", "24/05", "26/05", "31/05"]) + [("26/05", "15 T")]),
    ("EST", "Rahmoune Rabie", "BISKRA", 438, [("21/05", "20 T")]),
    ("EST", "SARL CHENITI DIS", "SETIF", 296, _meme("20 T", ["03/05", "05/05", "11/05", "13/05", "18/05", "25/05"])),
    ("EXTRÊME", "INCONNU", "CHELGHOUM EL AID", 358, _meme("20 T", ["04/05", "12/05", "27/05"])),
    ("EXTRÊME", "EURL KOSSAY LILTAGHDIA", "GUELMA", 516, _meme("20 T", ["04/05", "12/05", "27/05"])),
    ("EXTRÊME", "Aïn El Beïda", "OUM EL BOUAGHI", 517, [("28/05", "20 T")]),
    ("EXTRÊME", "HAIDER-BEN DJAB ALLAH", "CONSTANTINE", 420, _meme("20 T", ["14/05", "30/05"])),
    ("EXTRÊME", "SARL G/FAR, MAR", "AIN M'LILA", 437, _meme("20 T", ["09/05", "21/05", "25/05"])),
    ("EXTRÊME", "GUIAS ABDELAZIZ", "ANNABA", 557, _meme("20 T", ["03/05", "06/05", "10/05", "14/05", "18/05", "24/05", "31/05"])),
    ("EXTRÊME", "LARGOT SALIM", "EL OUED", 645, [("06/05", "20 T"), ("21/05", "20 T"), ("31/05", "15 T")]),
    ("EXTRÊME", "SARL MAHDJOUBI DIST", "SKIKDA", 503, _meme("20 T", ["05/05", "13/05", "20/05"])),
    ("EXTRÊME", "SAIFI MESSAOUD", "SOUK AHRAS", 609, [("28/05", "20 T")]),
    ("EXTRÊME", "EURL ABDELKHAHAR YOURT", "MILA", 392, [("14/05", "15 T")]),
    ("EXTRÊME", "INCONNU", "TEBESSA", 605, _meme("20 T", ["06/05", "14/05", "25/05", "31/05"])),
    ("CENTRE", "BABOURI AHMED", "TIMIMOUN", 1195, [("28/05", "15 T")]),
    ("CENTRE", "BOUDELLAA MED", "LAGHOUAT", 386, [("14/05", "20 T")]),
    ("CENTRE", "BOURKAB KRIMO", "ADRAR", 1403, _meme("20 T", ["07/05", "28/05"])),
    ("CENTRE", "RAFIK CHEURFA", "BOUIRA", 171, _meme("20 T", ["07/05", "28/05"])),
    ("CENTRE", "HADJAR MERHOUN MED", "BOUIRA", 140, _meme("20 T", ["09/05", "21/05", "30/05"])),
    ("CENTRE", "CHOHRI SIDALI", "MEDEA", 110, _meme("20 T", ["04/05", "12/05", "20/05", "28/05"])),
    ("CENTRE", "EURL MS FOOD", "BEJAIA", 254, _meme("20 T", ["08/05", "16/05", "21/05", "24/05", "28/05"])),
    ("CENTRE", "HOUAILYA BELKACEM", "TAMANRASSET", None, [("31/05", "20 T")]),
    ("CENTRE", "DJOTTO MOHAMED", "BENI MERAD (BLIDA)", 8.5, _meme("15 T", ["04/05", "17/05", "31/05"])),
    ("CENTRE", "ETS HOUACINE K", "TIZI OUZOU", 142, _meme("20 T", ["10/05", "19/05", "31/05"])),
    ("CENTRE", "Client 1", "BOUMERDES", 60, _meme("15 T", ["10/05", "24/05"])),
    ("CENTRE", "Client 2", "BOUMERDES", 61.2, _meme("15 T", ["05/05", "13/05", "19/05", "27/05"])),
    ("CENTRE", "Client 3", "BOUMERDES", 57.9, [("28/05", "15 T")]),
    ("OUEST", "EURL BARMOTT", "RELIZANE", 263, [("05/05", "20 T"), ("14/05", "20 T"), ("31/05", "15 T")]),
    ("OUEST", "INCONNU", "MASCARA", 355, _meme("20 T", ["05/05", "28/05"])),
    ("OUEST", "INCONNU", "ORAN", 380, _meme("20 T", ["03/05", "06/05", "10/05", "14/05", "18/05", "24/05"])),
    ("OUEST", "INCONNU", "SIDI BEL ABBES", 413, _meme("20 T", ["05/05", "27/05"])),
    ("OUEST", "INCONNU", "TLEMCEN", 480, _meme("20 T", ["07/05", "13/05", "21/05", "31/05"])),
    ("OUEST", "REDA HADDACHE", "SAIDA", 425, [("11/05", "15 T"), ("28/05", "20 T")]),
    ("OUEST", "Client 1 (ROUANE ABDELHADI)", "TIARET", 268, _meme("20 T", ["04/05", "18/05", "26/05"])),
    ("OUEST", "EURL BRAHIMI SABER", "CHLEF", 179, [("27/05", "15 T")]),
    ("OUEST", "Client 2", "TIARET", 268, _meme("20 T", ["06/05", "12/05", "17/05", "21/05", "28/05"])),
    ("OUEST", "ZEGAG MANSOUR", "MOSTAGANEM", 308, _meme("15 T", ["10/05", "31/05"])),
    ("DÉPÔT", "Dépôt MEFTAH", "BLIDA", 34.9, _meme("20 T", [
        "03/05", "04/05", "05/05", "06/05", "07/05", "10/05", "11/05", "12/05", "13/05",
        "17/05", "18/05", "19/05", "20/05", "21/05", "24/05", "26/05", "27/05"])),
    ("DÉPÔT", "DD Eucalyptus", "ALGER", 35, _meme("15 T", [
        "03/05", "04/05", "05/05", "10/05", "11/05", "12/05", "17/05", "18/05", "24/05"])),
]


def _date(jjmm):
    if not jjmm:
        return None
    j, m = jjmm.split("/")
    return dt.date(ANNEE, int(m), int(j))


def construire_livraisons():
    lignes, n = [], 1
    for region, client, wilaya, dist, items in SEED:
        for jjmm, t in items:
            lignes.append({
                "ID": f"LIV{n:03d}", "Region": region, "Client": client, "Wilaya": wilaya,
                "Distance_km": dist, "Date_livraison": _date(jjmm),
                "Heure_depart": "06:00", "Duree_h": estimer_duree(dist), "Type_camion": t,
                "Quantite_t": CAPACITES[t], "Camion": "", "Chauffeur": "",
                "Statut": "Planifiée",
                "Remarque": ("Date fixée par hypothèse (??? dans le document)"
                             if client == "Harbouch Nadhir" and t == "15 T" else ""),
            })
            n += 1
    return pd.DataFrame(lignes, columns=COL_LIV)


def construire_camions():
    lignes = []
    for t, nb in NB_CAMIONS.items():
        prefixe = t.split()[0]
        for i in range(1, nb + 1):
            lignes.append({"Camion": f"CAM_{prefixe}_{i:02d}", "Type": t,
                           "Capacite_t": CAPACITES[t], "Etat": "Disponible"})
    return pd.DataFrame(lignes, columns=COL_CAM)


COORDS_DEFAUT = {
    "M'SILA": (35.705, 4.542), "BATNA": (35.556, 6.174), "JIJEL": (36.820, 5.766),
    "BORJ BOU ARRERIDJ": (36.073, 4.761), "DJELFA": (34.673, 3.263), "BISKRA": (34.850, 5.728),
    "SETIF": (36.190, 5.410), "CHELGHOUM EL AID": (36.160, 6.700), "GUELMA": (36.462, 7.426),
    "OUM EL BOUAGHI": (35.875, 7.113), "CONSTANTINE": (36.365, 6.615), "AIN M'LILA": (36.040, 6.570),
    "ANNABA": (36.900, 7.767), "EL OUED": (33.368, 6.867), "SKIKDA": (36.876, 6.909),
    "SOUK AHRAS": (36.287, 7.951), "MILA": (36.450, 6.264), "TEBESSA": (35.404, 8.124),
    "TIMIMOUN": (29.260, 0.230), "LAGHOUAT": (33.800, 2.865), "ADRAR": (27.874, -0.294),
    "BOUIRA": (36.375, 3.902), "MEDEA": (36.264, 2.750), "BEJAIA": (36.751, 5.056),
    "TAMANRASSET": (22.785, 5.522), "BENI MERAD (BLIDA)": (36.520, 2.890), "TIZI OUZOU": (36.712, 4.045),
    "BOUMERDES": (36.766, 3.477), "RELIZANE": (35.737, 0.556), "MASCARA": (35.397, 0.140),
    "ORAN": (35.697, -0.633), "SIDI BEL ABBES": (35.190, -0.630), "TLEMCEN": (34.878, -1.315),
    "SAIDA": (34.830, 0.150), "TIARET": (35.371, 1.317), "CHLEF": (36.165, 1.334),
    "MOSTAGANEM": (35.931, 0.089), "BLIDA": (36.470, 2.830), "ALGER": (36.753, 3.042),
}


ALIAS = {
    "ALGER (DD EUCALYPTUS)": "ALGER",
    "BLIDA (DEPOT MEFTAH)": "BLIDA",
    "BORJ BOU ARRERIDJ": "BORDJ BOU ARRERIDJ",
    "CHELGHOUM EL AID": "CHELGHOUM LAID",
}


def norm(txt):
    t = unicodedata.normalize("NFKD", str(txt)).encode("ascii", "ignore").decode()
    t = " ".join(t.upper().replace("\u2019", "'").replace("`", "'").replace("-", " ").split())
    return ALIAS.get(t, t)


DEPOTS = {"Centre existant": (36.600, 3.250), "Sétif": (36.190, 5.410), "Relizane": (35.737, 0.556),
          "Constantine": (36.365, 6.615), "Bordj Bou Arreridj": (36.073, 4.761)}
F_TRANSFERTS = DOSSIER / "transferts_depots.csv"


def haversine_km(a, b):
    import math
    la1, lo1, la2, lo2 = map(math.radians, [a[0], a[1], b[0], b[1]])
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


VILLE_DEPOT = {"Sétif": "SETIF", "Relizane": "RELIZANE", "Constantine": "CONSTANTINE",
               "Bordj Bou Arreridj": "BORDJ BOU ARRERIDJ"}
CENTRE_LABEL = "Centre d'expédition Ben Khelil"


def transferts_defaut(dist_document=None):
    t = {}
    for d, c in DEPOTS.items():
        if d == "Centre existant":
            t[d] = 0.0
            continue
        v = dist_document.get(VILLE_DEPOT.get(d)) if dist_document is not None else None
        t[d] = float(v) if v is not None and pd.notna(v) else round(haversine_km(DEPOTS["Centre existant"], c) * 1.25, 0)
    return t


def charger_transferts(dist_document=None):
    t = transferts_defaut(dist_document)
    if F_TRANSFERTS.exists():
        x = pd.read_csv(F_TRANSFERTS, encoding="utf-8-sig")
        t.update({r["Depot"]: float(r["Distance_km"]) for _, r in x.iterrows()})
    t["Dépôt Meftah"] = 0.0
    return t


def charger_coords():
    if not F_COORDS.exists():
        pd.DataFrame([{"Wilaya": k, "Latitude": v[0], "Longitude": v[1]} for k, v in COORDS_DEFAUT.items()]
                     ).to_csv(F_COORDS, index=False, encoding="utf-8-sig")
    return pd.read_csv(F_COORDS, encoding="utf-8-sig")


@st.cache_data(show_spinner=False, ttl=86400)
def osrm_route(lat1, lon1, lat2, lon2, base):
    url = f"{base}/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false"
    with urllib.request.urlopen(url, timeout=20) as r:
        data = json.loads(r.read().decode())
    if data.get("code") != "Ok":
        raise RuntimeError(data.get("code", "erreur OSRM"))
    route = data["routes"][0]
    return route["distance"] / 1000.0, route["duration"] / 3600.0


def charger_osrm():
    if F_OSRM.exists():
        return pd.read_csv(F_OSRM, encoding="utf-8-sig")
    return pd.DataFrame(columns=["Wilaya", "Distance_OSRM_km", "Duree_OSRM_h"])


def distance_retenue(df):
    osrm = charger_osrm()
    m = dict(zip(osrm["Wilaya"].map(norm), osrm["Distance_OSRM_km"]))
    d_osrm = df["Wilaya"].map(lambda w: m.get(norm(w)))
    return d_osrm.fillna(df["Distance_km"]), d_osrm.notna()


def calculer_couts(df, dist_aller):
    ar = 2 * dist_aller.fillna(0)
    litres = ar / 100 * df["Type_camion"].map(CONSO_L_100KM).fillna(0)
    cout = litres * PRIX_GASOIL_DA_L + ar * AUTRES_COUTS_DA_KM
    return pd.DataFrame({"Distance_AR_km": ar, "Carburant_L": litres, "Cout_DA": cout}, index=df.index)


def lire_csv_souple(source):
    for enc in ("utf-8-sig", "latin-1"):
        try:
            if hasattr(source, "seek"):
                source.seek(0)
            return pd.read_csv(source, sep=None, engine="python", encoding=enc)
        except Exception:
            continue
    raise ValueError("Fichier CSV illisible")


def deviner(colonnes, mots):
    for c in colonnes:
        if any(m in c.lower() for m in mots):
            return c
    return colonnes[0]


def _parse_heure(v):
    if isinstance(v, dt.time):
        return v
    try:
        return dt.datetime.strptime(str(v).strip()[:5], "%H:%M").time()
    except ValueError:
        return HEURE_DEPART_DEFAUT


def charger_livraisons():
    if not F_LIVRAISONS.exists():
        construire_livraisons().to_csv(F_LIVRAISONS, index=False, encoding="utf-8-sig")
    df = pd.read_csv(F_LIVRAISONS, encoding="utf-8-sig")
    for c in COL_LIV:
        if c not in df.columns:
            df[c] = ""
    df = df[COL_LIV].copy()
    df["Date_livraison"] = pd.to_datetime(df["Date_livraison"], errors="coerce").dt.date
    df["Heure_depart"] = df["Heure_depart"].apply(_parse_heure)
    df["Distance_km"] = pd.to_numeric(df["Distance_km"], errors="coerce")
    df["Duree_h"] = pd.to_numeric(df["Duree_h"], errors="coerce")
    manque = df["Duree_h"].isna()
    df.loc[manque, "Duree_h"] = df.loc[manque, "Distance_km"].apply(estimer_duree)
    for c in ["Camion", "Chauffeur", "Remarque", "Statut", "Client", "Wilaya", "Region", "Type_camion"]:
        df[c] = df[c].fillna("").astype(str)
    df["Quantite_t"] = pd.to_numeric(df["Quantite_t"], errors="coerce").fillna(0)
    return df


def enregistrer_livraisons(df):
    df = df[COL_LIV].copy()
    df["Date_livraison"] = df["Date_livraison"].apply(
        lambda d: d.isoformat() if isinstance(d, (dt.date, dt.datetime)) else "")
    df["Heure_depart"] = df["Heure_depart"].apply(
        lambda h: h.strftime("%H:%M") if isinstance(h, dt.time) else "06:00")
    df.to_csv(F_LIVRAISONS, index=False, encoding="utf-8-sig")


def charger_camions():
    if not F_CAMIONS.exists():
        construire_camions().to_csv(F_CAMIONS, index=False, encoding="utf-8-sig")
    return pd.read_csv(F_CAMIONS, encoding="utf-8-sig")[COL_CAM]


def enregistrer_camions(df):
    df[COL_CAM].to_csv(F_CAMIONS, index=False, encoding="utf-8-sig")


def prochain_id(df):
    nums = pd.to_numeric(df["ID"].astype(str).str.replace("LIV", "", regex=False), errors="coerce")
    return f"LIV{int(nums.max() if nums.notna().any() else 0) + 1:03d}"


def intervalles(df):
    def debut(r):
        if not isinstance(r["Date_livraison"], dt.date):
            return pd.NaT
        return dt.datetime.combine(r["Date_livraison"], _parse_heure(r["Heure_depart"]))
    d = df.apply(debut, axis=1)
    d = pd.to_datetime(d)
    f = d + pd.to_timedelta(df["Duree_h"].fillna(0), unit="h")
    return d, f


def _conflit(occupe, d, f, marge):
    h = pd.Timedelta(hours=marge)
    return any(d < bf + h and f + h > bd for bd, bf in occupe)


def verifier(df, camions):
    pb = []
    for _, r in df.iterrows():
        cap = CAPACITES.get(r["Type_camion"])
        if cap and r["Quantite_t"] < cap:
            pb.append(f"{r['ID']} : quantité {r['Quantite_t']:g} t < capacité du camion {r['Type_camion']} "
                      f"(affectation interdite).")
        if cap and r["Quantite_t"] > cap:
            pb.append(f"{r['ID']} : quantité {r['Quantite_t']:g} t > capacité du camion {r['Type_camion']}.")
        if r["Camion"]:
            ligne = camions[camions["Camion"] == r["Camion"]]
            if ligne.empty:
                pb.append(f"{r['ID']} : camion {r['Camion']} inconnu.")
            elif ligne.iloc[0]["Type"] != r["Type_camion"]:
                pb.append(f"{r['ID']} : camion {r['Camion']} n'est pas de type {r['Type_camion']}.")
            elif ligne.iloc[0]["Etat"] != "Disponible":
                pb.append(f"{r['ID']} : camion {r['Camion']} est « {ligne.iloc[0]['Etat']} ».")
    d, f = intervalles(df)
    x = df.assign(Debut=d, Fin=f).dropna(subset=["Debut"])
    for col, nom, marge in [("Camion", "camion", MARGE_CAMION_H), ("Chauffeur", "chauffeur", REPOS_CHAUFFEUR_H)]:
        for val, g in x[x[col] != ""].groupby(col):
            g = g.sort_values("Debut")
            prec = None
            for _, r in g.iterrows():
                if prec is not None and r["Debut"] < prec["Fin"] + pd.Timedelta(hours=marge):
                    pb.append(f"Conflit {nom} {val} : {prec['ID']} (fin {prec['Fin']:%d/%m %H:%M}) et "
                              f"{r['ID']} (début {r['Debut']:%d/%m %H:%M}), marge/repos requis {marge:g} h.")
                prec = r if prec is None or r["Fin"] > prec["Fin"] else prec
    return pb


def affecter_auto(df, camions):
    df = df.copy()
    d, f = intervalles(df)
    dispo = {t: camions[(camions["Type"] == t) & (camions["Etat"] == "Disponible")]["Camion"].tolist()
             for t in TYPES}
    occ_cam, occ_ch, heures = {}, {c: [] for c in CHAUFFEURS}, {c: 0.0 for c in CHAUFFEURS}
    for i in df.index[df["Date_livraison"].notna()]:
        if df.at[i, "Camion"]:
            occ_cam.setdefault(df.at[i, "Camion"], []).append((d[i], f[i]))
        c = df.at[i, "Chauffeur"]
        if c in occ_ch:
            occ_ch[c].append((d[i], f[i]))
            heures[c] += df.at[i, "Duree_h"]

    manque = 0
    ordre = d[d.notna() & (df["Camion"] == "")].sort_values().index
    for i in ordre:
        t = df.at[i, "Type_camion"]
        if t not in CAPACITES or df.at[i, "Quantite_t"] < CAPACITES[t]:
            continue
        libres = [c for c in dispo[t] if not _conflit(occ_cam.get(c, []), d[i], f[i], MARGE_CAMION_H)]
        chs = sorted([c for c in CHAUFFEURS if not _conflit(occ_ch[c], d[i], f[i], REPOS_CHAUFFEUR_H)],
                     key=lambda c: heures[c])
        if not libres or not chs:
            df.at[i, "Statut"] = "Ressource manquante"
            df.at[i, "Remarque"] = f"Aucun camion {t} libre" if not libres else "Aucun chauffeur libre"
            manque += 1
            continue
        cam, ch = libres[0], chs[0]
        df.at[i, "Camion"], df.at[i, "Chauffeur"], df.at[i, "Statut"] = cam, ch, "Affectée"
        occ_cam.setdefault(cam, []).append((d[i], f[i]))
        occ_ch[ch].append((d[i], f[i]))
        heures[ch] += df.at[i, "Duree_h"]
    return df, manque


def charge_horaire(df):
    d, f = intervalles(df)
    ok = d.notna()
    if not ok.any():
        return pd.DataFrame()
    horizon = pd.date_range(d[ok].min().floor("D"), f[ok].max().ceil("h"), freq="h")
    lignes = []
    for h in horizon:
        actifs = df[ok & (d <= h) & (f > h)]
        lignes.append({"Heure": h, "20 T": int((actifs["Type_camion"] == "20 T").sum()),
                       "15 T": int((actifs["Type_camion"] == "15 T").sum()), "Chauffeurs": len(actifs)})
    return pd.DataFrame(lignes).set_index("Heure")


MARINE, TURQUOISE, ORANGE, GRIS, PRUNE = "#12355B", "#1D8A99", "#F28C28", "#6B7A8F", "#8E6C8A"
COULEURS_REGION = {"EST": MARINE, "EXTRÊME": ORANGE, "CENTRE": TURQUOISE, "OUEST": PRUNE, "DÉPÔT": GRIS}
COULEURS_TYPE = {"20 T": TURQUOISE, "15 T": ORANGE}
COULEURS_SCEN = {"Actuel": GRIS, "2 dépôts": TURQUOISE, "3 dépôts": ORANGE}

st.markdown(f"""
<style>
.bandeau {{background: linear-gradient(90deg, {MARINE} 0%, {TURQUOISE} 100%); padding: 22px 28px;
          border-radius: 14px; margin-bottom: 18px; color: white;}}
.bandeau h1 {{color: white; margin: 0; font-size: 1.9rem; padding: 0;}}
.bandeau p {{color: rgba(255,255,255,.85); margin: 4px 0 0 0;}}
[data-testid="stMetric"] {{background: rgba(29,138,153,.10); border-left: 5px solid {TURQUOISE};
          padding: 12px 16px; border-radius: 10px;}}
[data-testid="stMetricValue"] {{color: {TURQUOISE}; font-size: 1.7rem;}}
.stTabs [aria-selected="true"] {{color: {ORANGE} !important;}}
.stTabs [data-baseweb="tab-highlight"] {{background-color: {ORANGE} !important;}}
.stButton > button, .stDownloadButton > button {{background: {MARINE}; color: white; border: none;
          border-radius: 8px; padding: 8px 18px;}}
.stButton > button:hover, .stDownloadButton > button:hover {{background: {ORANGE}; color: white;}}
h2, h3 {{color: {TURQUOISE};}}
</style>
<div class="bandeau"><h1>🚚 BELLAT · Gestion de la flotte</h1>
<p>Livraisons · Camions · Chauffeurs · Distances · Coûts · Affectation des dépôts</p></div>
""", unsafe_allow_html=True)


def barres(serie, couleurs=None, hauteur=300, titre_y=None):
    d = serie.rename("Valeur").rename_axis("Categorie").reset_index()
    d["Categorie"] = d["Categorie"].astype(str)
    if couleurs is None:
        couleur = alt.value(TURQUOISE)
    else:
        couleur = alt.Color("Categorie:N", legend=None,
                            scale=alt.Scale(domain=list(couleurs), range=list(couleurs.values())))
    graph = alt.Chart(d).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
        x=alt.X("Categorie:N", sort=None, title=None, axis=alt.Axis(labelAngle=-30)),
        y=alt.Y("Valeur:Q", title=titre_y), color=couleur, tooltip=["Categorie", "Valeur"])
    st.altair_chart(graph.properties(height=hauteur), use_container_width=True)


def courbes(donnees, couleurs):
    d = donnees.reset_index().melt(donnees.index.name or "index", var_name="Ressource", value_name="Nombre")
    d = d.rename(columns={donnees.index.name or "index": "Heure"})
    graph = alt.Chart(d).mark_line(interpolate="step-after", strokeWidth=2.5).encode(
        x=alt.X("Heure:T", title=None), y=alt.Y("Nombre:Q", title=None),
        color=alt.Color("Ressource:N", scale=alt.Scale(domain=list(couleurs), range=list(couleurs.values()))),
        tooltip=["Heure", "Ressource", "Nombre"])
    st.altair_chart(graph.properties(height=280), use_container_width=True)


with st.sidebar:
    st.markdown("### ⚙️ Paramètres globaux")
    with st.expander("Coûts d'exploitation"):
        CONSO_L_100KM["20 T"] = st.number_input("Conso 20 T (L/100 km)", value=CONSO_L_100KM["20 T"])
        CONSO_L_100KM["15 T"] = st.number_input("Conso 15 T (L/100 km)", value=CONSO_L_100KM["15 T"])
        PRIX_GASOIL_DA_L = st.number_input("Prix du gasoil (DA/L)", value=PRIX_GASOIL_DA_L)
        AUTRES_COUTS_DA_KM = st.number_input("Maintenance + pneus (DA/km)", value=AUTRES_COUTS_DA_KM)
    with st.expander("Temps de mission"):
        VITESSE_MOY_KMH = st.number_input("Vitesse moyenne (km/h)", min_value=20.0, value=VITESSE_MOY_KMH)
        TEMPS_CHARG_DECHARG_H = st.number_input("Chargement + déchargement (h)", min_value=0.0,
                                                value=TEMPS_CHARG_DECHARG_H)
        REPOS_CHAUFFEUR_H = st.number_input("Repos chauffeur (h)", min_value=0.0, value=REPOS_CHAUFFEUR_H)
        MARGE_CAMION_H = st.number_input("Marge entre missions d'un camion (h)", min_value=0.0, value=MARGE_CAMION_H)
        HEURES_UTILES_JOUR = st.number_input("Heures utiles par jour et par camion", min_value=1.0, value=14.0)
    with st.expander("Dépôts"):
        cout_depot = st.number_input("Exploitation mensuelle par dépôt (DA)", min_value=0.0, value=500000.0, step=50000.0)
        invest_depot = st.number_input("Investissement initial par dépôt (DA)", min_value=0.0, value=5000000.0,
                                       step=500000.0)
        periode = st.number_input("Mois couverts par les données", min_value=1.0, value=1.0, step=1.0)
        lat_centre = st.number_input("Latitude du centre d'expédition", value=36.600, format="%.4f")
        lon_centre = st.number_input("Longitude du centre d'expédition", value=3.250, format="%.4f")
        DEPOTS["Centre existant"] = (lat_centre, lon_centre)
        DEPOT_ORIGINE = (DEPOT_ORIGINE[0], lat_centre, lon_centre)
        LIVRE_DEPUIS_DEPOTS = st.checkbox("Bellat livre aussi les clients depuis les dépôts régionaux", value=False,
                                          help="Décoché : les clients d'un dépôt régional retirent eux-mêmes leurs produits.")
        AVANCE_APPRO_J = st.number_input("Approvisionnement des dépôts : jours d'avance", min_value=0, max_value=7, value=1)
    with st.expander("Croissance : petits et moyens clients"):
        INCLURE_CROISSANCE = st.checkbox("Inclure les nouveaux clients attirés par les dépôts", value=True)
        marge_t = st.number_input("Marge brute par tonne vendue (DA/t)", min_value=0.0, value=2000.0, step=100.0)
        rampe_1 = st.slider("Année 1 : part de la cible atteinte (%)", 0, 100, 40)
        rampe_2 = st.slider("Année 2 : part de la cible atteinte (%)", 0, 100, 70)
    with st.expander("Finance"):
        horizon = st.slider("Horizon d'analyse (années)", 1, 10, 5)
        taux_a = st.slider("Taux d'actualisation annuel (%)", 0.0, 20.0, 8.0, 0.5)
        taux_impot = st.slider("Impôt sur les bénéfices (%)", 0.0, 40.0, 19.0, 1.0)
        infl_carb = st.slider("Inflation du carburant (%/an)", 0.0, 15.0, 3.0, 0.5)
        infl_autres = st.slider("Inflation maintenance + pneus (%/an)", 0.0, 15.0, 3.0, 0.5)
        infl_expl = st.slider("Inflation exploitation des dépôts (%/an)", 0.0, 15.0, 3.0, 0.5)
        croiss_vol = st.slider("Croissance du volume (%/an)", -10.0, 20.0, 0.0, 0.5)
        amort_ans = st.slider("Durée d'amortissement (ans)", 1, 10, 5)
        val_res = st.slider("Valeur résiduelle (% de l'investissement)", 0, 60, 0)

df = charger_livraisons()
camions = charger_camions()

scenarios = {nom: pd.read_csv(io.StringIO(txt)) for nom, txt in AFFECTATION_CSV.items()}
cle_wilaya = df["Wilaya"].map(norm)
dist_doc = df.groupby(cle_wilaya)["Distance_km"].first()

jeux = {}
for nom, tab in scenarios.items():
    t = tab.assign(_k=tab["client"].map(norm)).set_index("_k")
    jeux[nom] = {"dist": cle_wilaya.map(t["distance_km"]), "depot": cle_wilaya.map(t["servi_par"])}
dist_actuelle = cle_wilaya.map(dist_doc)
manque_doc = dist_actuelle.isna()
dist_actuelle[manque_doc] = jeux["2 dépôts"]["dist"][manque_doc]
jeux = {"Actuel": {"dist": dist_actuelle, "depot": pd.Series("Dépôt Meftah", index=df.index)}, **jeux}
commun = pd.concat([v["dist"] for v in jeux.values()], axis=1).notna().all(axis=1)
dfc = df[commun]
dist_transfert = charger_transferts(dist_doc)
for _nom, _v in jeux.items():
    _v["regional"] = _v["depot"].notna() & ~_v["depot"].isin(["Centre existant", "Dépôt Meftah"])
    _v["tr"] = _v["depot"].map(dist_transfert).fillna(0.0).astype(float).where(_v["regional"], 0.0)
    _v["dist_bellat"] = _v["dist"].where(~_v["regional"] | LIVRE_DEPUIS_DEPOTS, 0.0)
    _v["depot"] = _v["depot"].replace({"Centre existant": CENTRE_LABEL, "Dépôt Meftah": CENTRE_LABEL})


def transfert_df(nom, d):
    """Approvisionnement du dépôt régional depuis le centre (camions 20 T pleins, aller-retour), au prorata du tonnage."""
    km = 2 * jeux[nom]["tr"].reindex(d.index).fillna(0.0) * d["Quantite_t"] / 20
    litres = km / 100 * CONSO_L_100KM["20 T"]
    return pd.DataFrame({"km": km, "litres": litres, "cout": litres * PRIX_GASOIL_DA_L + km * AUTRES_COUTS_DA_KM})


def detail(nom):
    d_ = jeux[nom]["dist"][commun]
    base = calculer_couts(dfc, jeux[nom]["dist_bellat"][commun])
    tr = transfert_df(nom, dfc)
    x = pd.DataFrame({
        "Wilaya": dfc["Wilaya"], "Servi par": jeux[nom]["depot"][commun], "Livraisons": 1,
        "Quantité (t)": dfc["Quantite_t"], "Distance dépôt→client (km)": d_,
        "Distribution A/R (km)": base["Distance_AR_km"], "Transfert A/R (km)": tr["km"],
        "Distance A/R (km)": base["Distance_AR_km"] + tr["km"], "Carburant (L)": base["Carburant_L"] + tr["litres"],
        "Coût carburant (DA)": (base["Carburant_L"] + tr["litres"]) * PRIX_GASOIL_DA_L,
        "Maintenance + pneus (DA)": (base["Distance_AR_km"] + tr["km"]) * AUTRES_COUTS_DA_KM,
        "Coût total (DA)": base["Cout_DA"] + tr["cout"]})
    g = x.groupby("Wilaya").agg({
        "Servi par": "first", "Livraisons": "sum", "Quantité (t)": "sum", "Distance dépôt→client (km)": "first",
        "Distribution A/R (km)": "sum", "Transfert A/R (km)": "sum",
        "Distance A/R (km)": "sum", "Carburant (L)": "sum", "Coût carburant (DA)": "sum",
        "Maintenance + pneus (DA)": "sum", "Coût total (DA)": "sum"})
    return g

tables = {nom: detail(nom) for nom in jeux}
resume = pd.DataFrame({nom: {
    "Livraisons": t["Livraisons"].sum(), "Distribution A/R (km)": t["Distribution A/R (km)"].sum(),
    "Transfert A/R (km)": t["Transfert A/R (km)"].sum(), "Distance A/R (km)": t["Distance A/R (km)"].sum(),
    "Carburant (L)": t["Carburant (L)"].sum(), "Coût carburant (DA)": t["Coût carburant (DA)"].sum(),
    "Coût total (DA)": t["Coût total (DA)"].sum()} for nom, t in tables.items()}).T
resume["Réduction distance (%)"] = (resume.loc["Actuel", "Distance A/R (km)"] - resume["Distance A/R (km)"]) \
    / resume.loc["Actuel", "Distance A/R (km)"] * 100
resume["Économie (DA)"] = resume.loc["Actuel", "Coût total (DA)"] - resume["Coût total (DA)"]

nouveaux = {nom: len(set(scenarios[nom]["servi_par"]) - {"Centre existant"}) for nom in scenarios}


def cout_scenario(nom, pf=1.0, cf=1.0, af=1.0):
    ar = 2 * jeux[nom]["dist_bellat"][commun]
    litres = ar / 100 * dfc["Type_camion"].map(CONSO_L_100KM) * cf
    tr = transfert_df(nom, dfc)
    return (litres * PRIX_GASOIL_DA_L * pf + ar * AUTRES_COUTS_DA_KM * af).sum() \
        + (tr["litres"] * cf * PRIX_GASOIL_DA_L * pf + tr["km"] * AUTRES_COUTS_DA_KM * af).sum()


tab_bord, tab_liv, tab_flotte, tab_plan, tab_week, tab_osrm, tab_cout, tab_comp, tab_sens, tab_fin, tab_carte, tab_export = st.tabs(
    ["📊 Tableau de bord", "📦 Livraisons & dates", "🚛 Flotte & chauffeurs", "📅 Planning & ressources",
     "🗓️ Planification hebdo", "🗺️ Distances OSRM", "💰 Coûts", "🔀 Affectation & comparaison", "🧪 Sensibilité & rentabilité", "📈 Analyse financière", "🌍 Carte", "⬇️ Export"])

with tab_bord:
    f_a, f_b, f_c, f_d = st.columns([2, 2, 2, 2])
    sel_reg = f_a.multiselect("Régions", REGIONS, default=REGIONS, key="d_reg")
    sel_typ = f_b.multiselect("Type de camion", TYPES, default=TYPES, key="d_typ")
    dates_ok = df["Date_livraison"].dropna()
    d_min, d_max = (dates_ok.min(), dates_ok.max()) if len(dates_ok) else (dt.date(ANNEE, 5, 1), dt.date(ANNEE, 5, 31))
    periode_sel = f_c.date_input("Période", value=(d_min, d_max), format="DD/MM/YYYY", key="d_per")
    mode_d = f_d.selectbox("Base de calcul des distances", list(jeux), key="d_mode",
                           format_func=lambda m: "Situation actuelle" if m == "Actuel" else f"Avec {m}")
    if isinstance(periode_sel, tuple) and len(periode_sel) == 2:
        p0, p1 = periode_sel
    else:
        p0, p1 = d_min, d_max
    masque = df["Region"].isin(sel_reg) & df["Type_camion"].isin(sel_typ) & (
        df["Date_livraison"].isna() | ((df["Date_livraison"] >= p0) & (df["Date_livraison"] <= p1)))
    dd = df[masque].copy()
    dist_d = jeux[mode_d]["dist_bellat"].reindex(dd.index).fillna(dd["Distance_km"])
    dist_cl = jeux[mode_d]["dist"].reindex(dd.index).fillna(dd["Distance_km"])
    cout_d = calculer_couts(dd, dist_d)
    tr_d = transfert_df(mode_d, dd)
    dd = dd.assign(Dist=dist_d, DistClient=dist_cl, DistAR=cout_d["Distance_AR_km"] + tr_d["km"], Cout=cout_d["Cout_DA"] + tr_d["cout"],
                   Litres=cout_d["Carburant_L"] + tr_d["litres"], TransfertKm=tr_d["km"])

    tonnes = dd["Quantite_t"].sum()
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Livraisons", f"{len(dd):,}")
    k2.metric("Tonnage (t)", f"{tonnes:,.0f}")
    k3.metric("Distance A/R (km)", f"{dd['DistAR'].sum():,.0f}",
              f"dont transfert {dd['TransfertKm'].sum():,.0f}" if dd["TransfertKm"].sum() else None, delta_color="off")
    k4.metric("Coût estimé (DA)", f"{dd['Cout'].sum():,.0f}")
    k5.metric("Coût par tonne (DA)", f"{dd['Cout'].sum() / tonnes:,.0f}" if tonnes else "—")
    k6.metric("Coût par km (DA)", f"{dd['Cout'].sum() / dd['DistAR'].sum():,.1f}" if dd["DistAR"].sum() else "—")

    deb, fin_ = intervalles(dd)
    nb_cam = int((camions["Etat"] == "Disponible").sum())
    jours_actifs = dd["Date_livraison"].dropna().nunique()
    heures_mission = dd.loc[deb.notna(), "Duree_h"].sum()
    taux_flotte = heures_mission / (nb_cam * jours_actifs * HEURES_UTILES_JOUR) * 100 if jours_actifs and nb_cam else 0
    pic = dd.groupby("Date_livraison").size().max() if jours_actifs else 0
    aff = (dd["Camion"] != "").mean() * 100 if len(dd) else 0
    j1, j2, j3, j4, j5, j6 = st.columns(6)
    j1.metric("Utilisation de la flotte", f"{taux_flotte:.0f} %")
    j2.metric("Livraisons affectées", f"{aff:.0f} %")
    j3.metric("Pic de livraisons / jour", int(pic))
    j4.metric("Clients actifs", dd["Client"].nunique())
    j5.metric("Wilayas servies", dd["Wilaya"].nunique())
    j6.metric("Distance moyenne pondérée (km)",
              f"{(dd['Dist'] * dd['Quantite_t']).sum() / tonnes:,.0f}" if tonnes else "—")

    st.markdown("#### Impact des dépôts (par rapport à la situation actuelle)")
    e1, e2, e3 = st.columns(3)
    e1.metric("Situation actuelle", f"{resume.loc['Actuel', 'Coût total (DA)']:,.0f} DA")
    for col, nom in zip([e2, e3], ["2 dépôts", "3 dépôts"]):
        col.metric(f"{nom} · économie {resume.loc[nom, 'Réduction distance (%)']:.0f} % de distance",
                   f"{resume.loc[nom, 'Économie (DA)']:,.0f} DA")

    st.markdown("#### Évolution et structure")
    g1, g2 = st.columns([3, 2])
    with g1:
        hebdo = dd.dropna(subset=["Date_livraison"]).copy()
        hebdo["Semaine"] = pd.to_datetime(hebdo["Date_livraison"]).dt.to_period("W-SAT").dt.start_time
        hs = hebdo.groupby("Semaine").agg(Tonnes=("Quantite_t", "sum"), Cout=("Cout", "sum")).reset_index()
        hs["Libellé"] = hs["Semaine"].dt.strftime("%d/%m")
        barres_h = alt.Chart(hs).mark_bar(color=TURQUOISE, cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
            x=alt.X("Libellé:N", sort=None, title="Semaine (début)"), y=alt.Y("Tonnes:Q", title="Tonnes"),
            tooltip=["Libellé", "Tonnes", "Cout"])
        ligne_h = alt.Chart(hs).mark_line(color=ORANGE, strokeWidth=3, point=True).encode(
            x=alt.X("Libellé:N", sort=None), y=alt.Y("Cout:Q", title="Coût (DA)", axis=alt.Axis(titleColor=ORANGE)))
        st.altair_chart(alt.layer(barres_h, ligne_h).resolve_scale(y="independent").properties(
            height=300, title="Tonnage et coût par semaine"), use_container_width=True)
    with g2:
        reg = dd.groupby("Region")["Quantite_t"].sum().reset_index()
        donut = alt.Chart(reg).mark_arc(innerRadius=60, outerRadius=115).encode(
            theta="Quantite_t:Q", tooltip=["Region", "Quantite_t"],
            color=alt.Color("Region:N", scale=alt.Scale(domain=list(COULEURS_REGION),
                                                         range=list(COULEURS_REGION.values()))))
        st.altair_chart(donut.properties(height=300, title="Répartition du tonnage par région"),
                        use_container_width=True)

    h1_, h2_ = st.columns(2)
    with h1_:
        par_w = dd.groupby("Wilaya").agg(Cout=("Cout", "sum")).sort_values("Cout", ascending=False).reset_index()
        par_w["Cumul %"] = par_w["Cout"].cumsum() / par_w["Cout"].sum() * 100
        top = par_w.head(15)
        b_p = alt.Chart(top).mark_bar(color=MARINE, cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
            x=alt.X("Wilaya:N", sort=None, title=None, axis=alt.Axis(labelAngle=-45)), y=alt.Y("Cout:Q", title="Coût (DA)"),
            tooltip=["Wilaya", "Cout", "Cumul %"])
        l_p = alt.Chart(top).mark_line(color=ORANGE, strokeWidth=3, point=True).encode(
            x=alt.X("Wilaya:N", sort=None), y=alt.Y("Cumul %:Q", axis=alt.Axis(titleColor=ORANGE), scale=alt.Scale(domain=[0, 100])))
        st.altair_chart(alt.layer(b_p, l_p).resolve_scale(y="independent").properties(
            height=320, title="Pareto : les 15 wilayas les plus coûteuses"), use_container_width=True)
    with h2_:
        top_cl = dd.groupby("Client")["Quantite_t"].sum().sort_values(ascending=False).head(10).reset_index()
        st.altair_chart(alt.Chart(top_cl).mark_bar(color=TURQUOISE, cornerRadiusTopRight=5, cornerRadiusBottomRight=5).encode(
            y=alt.Y("Client:N", sort="-x", title=None), x=alt.X("Quantite_t:Q", title="Tonnes"),
            tooltip=["Client", "Quantite_t"]).properties(height=320, title="Top 10 clients (tonnage)"),
            use_container_width=True)

    i1, i2 = st.columns(2)
    with i1:
        bulles = dd.groupby(["Wilaya", "Region"]).agg(Tonnes=("Quantite_t", "sum"), Distance=("DistClient", "first"),
                                                     Cout=("Cout", "sum")).reset_index()
        st.altair_chart(alt.Chart(bulles).mark_circle(opacity=0.75).encode(
            x=alt.X("Distance:Q", title="Distance aller (km)"), y=alt.Y("Tonnes:Q", title="Tonnes"),
            size=alt.Size("Cout:Q", legend=None, scale=alt.Scale(range=[40, 1200])),
            color=alt.Color("Region:N", scale=alt.Scale(domain=list(COULEURS_REGION), range=list(COULEURS_REGION.values()))),
            tooltip=["Wilaya", "Region", "Tonnes", "Distance", "Cout"]).properties(
            height=330, title="Distance, tonnage et coût par wilaya"), use_container_width=True)
    with i2:
        chaleur = dd.dropna(subset=["Date_livraison"]).assign(
            Jour=lambda x: pd.to_datetime(x["Date_livraison"]).dt.strftime("%d/%m")).groupby(
            ["Jour", "Region"]).size().reset_index(name="Livraisons")
        ordre_j = sorted(chaleur["Jour"].unique(), key=lambda x: (x[3:], x[:2]))
        st.altair_chart(alt.Chart(chaleur).mark_rect().encode(
            x=alt.X("Jour:N", sort=ordre_j, title=None, axis=alt.Axis(labelAngle=-60)), y=alt.Y("Region:N", title=None),
            color=alt.Color("Livraisons:Q", scale=alt.Scale(scheme="teals"), legend=alt.Legend(title="Livraisons")),
            tooltip=["Jour", "Region", "Livraisons"]).properties(height=330, title="Intensité des livraisons par jour et région"),
            use_container_width=True)

    st.markdown("#### Flotte et chauffeurs")
    l1, l2, l3 = st.columns(3)
    with l1:
        par_type = dd.groupby("Type_camion").agg(Livraisons=("ID", "count"), Heures=("Duree_h", "sum")).reset_index()
        st.altair_chart(alt.Chart(par_type).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
            x=alt.X("Type_camion:N", title=None), y=alt.Y("Heures:Q", title="Heures de mission"),
            color=alt.Color("Type_camion:N", legend=None, scale=alt.Scale(domain=list(COULEURS_TYPE),
                                                                          range=list(COULEURS_TYPE.values()))),
            tooltip=["Type_camion", "Livraisons", "Heures"]).properties(height=260, title="Charge par type de camion"),
            use_container_width=True)
    with l2:
        par_cam = dd[dd["Camion"] != ""].groupby("Camion")["Duree_h"].sum().sort_values(ascending=False).head(12).reset_index()
        if par_cam.empty:
            st.info("Aucun camion affecté : lancez l'affectation dans l'onglet Planning.")
        else:
            st.altair_chart(alt.Chart(par_cam).mark_bar(color=TURQUOISE, cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
                y=alt.Y("Camion:N", sort="-x", title=None), x=alt.X("Duree_h:Q", title="Heures"),
                tooltip=["Camion", "Duree_h"]).properties(height=260, title="Camions les plus sollicités"),
                use_container_width=True)
    with l3:
        par_ch = dd[dd["Chauffeur"] != ""].groupby("Chauffeur")["Duree_h"].sum().sort_values(ascending=False).head(12).reset_index()
        if par_ch.empty:
            st.info("Aucun chauffeur affecté.")
        else:
            st.altair_chart(alt.Chart(par_ch).mark_bar(color=ORANGE, cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
                y=alt.Y("Chauffeur:N", sort="-x", title=None), x=alt.X("Duree_h:Q", title="Heures"),
                tooltip=["Chauffeur", "Duree_h"]).properties(height=260, title="Chauffeurs les plus sollicités"),
                use_container_width=True)

    st.markdown("#### Alertes")
    alertes = []
    n_sans_date = int(df["Date_livraison"].isna().sum())
    if n_sans_date:
        alertes.append(f"🟠 {n_sans_date} livraison(s) sans date")
    n_incoh = int((df["Quantite_t"] < df["Type_camion"].map(CAPACITES).fillna(0)).sum())
    if n_incoh:
        alertes.append(f"🔴 {n_incoh} livraison(s) dont la quantité est inférieure à la capacité du camion")
    conflits = [p for p in verifier(df, camions) if p.startswith("Conflit")]
    if conflits:
        alertes.append(f"🔴 {len(conflits)} conflit(s) de camion ou de chauffeur")
    charge_d = charge_horaire(df)
    if not charge_d.empty:
        n20 = int(((camions["Type"] == "20 T") & (camions["Etat"] == "Disponible")).sum())
        n15 = int(((camions["Type"] == "15 T") & (camions["Etat"] == "Disponible")).sum())
        jours_exc = charge_d[(charge_d["20 T"] > n20) | (charge_d["15 T"] > n15)].index.normalize().nunique()
        if jours_exc:
            alertes.append(f"🔴 {jours_exc} jour(s) où la demande dépasse le parc disponible")
    n_non_aff = int(((df["Camion"] == "") & (df["Statut"] != "Livrée")).sum())
    if n_non_aff:
        alertes.append(f"🟡 {n_non_aff} livraison(s) non encore affectée(s)")
    if alertes:
        for a in alertes:
            st.write(a)
    else:
        st.success("Aucune alerte.")

    with st.expander("Détail des livraisons filtrées"):
        st.dataframe(dd[["ID", "Region", "Client", "Wilaya", "Date_livraison", "Type_camion", "Quantite_t", "Dist",
                         "DistAR", "Cout", "Camion", "Chauffeur", "Statut"]].round(1), use_container_width=True,
                     hide_index=True)

with tab_liv:
    st.subheader("Ajouter une livraison")
    with st.form("form_liv", clear_on_submit=True):
        a, b, c = st.columns(3)
        region = a.selectbox("Région", REGIONS)
        client = a.text_input("Client")
        wilaya = b.text_input("Wilaya")
        distance = b.number_input("Distance aller (km)", min_value=0.0, step=1.0)
        date_liv = b.date_input("Date de livraison", value=dt.date(ANNEE, 5, 1), format="DD/MM/YYYY")
        heure = b.time_input("Heure de départ", value=HEURE_DEPART_DEFAUT, step=900)
        duree = b.number_input("Durée aller-retour (h) — 0 = calcul auto", min_value=0.0, step=0.5, value=0.0)
        type_c = c.selectbox("Type de camion", TYPES)
        quantite = c.number_input("Quantité (t)", min_value=0.0, step=1.0, value=20.0,
                                  help="Doit être égale à la capacité du camion (20 ou 15 t).")
        camion = c.selectbox("Camion (optionnel)", [""] + camions[camions["Type"] == type_c]["Camion"].tolist())
        chauffeur = a.selectbox("Chauffeur (optionnel)", [""] + CHAUFFEURS)

        if st.form_submit_button("Ajouter la livraison"):
            if not client.strip():
                st.error("Veuillez saisir le nom du client.")
            elif quantite < CAPACITES[type_c]:
                st.error(f"Quantité inférieure à la capacité du camion {type_c} ({CAPACITES[type_c]} t) : "
                         "affectation interdite.")
            else:
                nouvelle = {"ID": prochain_id(df), "Region": region, "Client": client.strip(),
                            "Wilaya": wilaya.strip().upper(), "Distance_km": distance,
                            "Date_livraison": date_liv, "Heure_depart": heure,
                            "Duree_h": duree if duree > 0 else estimer_duree(distance),
                            "Type_camion": type_c, "Quantite_t": quantite,
                            "Camion": camion, "Chauffeur": chauffeur,
                            "Statut": "Affectée" if camion else "Planifiée", "Remarque": ""}
                df = pd.concat([df, pd.DataFrame([nouvelle])], ignore_index=True)
                enregistrer_livraisons(df)
                st.success("Livraison ajoutée.")
                st.rerun()

    st.subheader("Clôture")
    k1, k2 = st.columns(2)
    if k1.button("✅ Marquer toutes les livraisons comme livrées"):
        df["Statut"] = "Livrée"
        df["Remarque"] = df["Remarque"].where(~df["Remarque"].str.startswith("Aucun"), "")
        enregistrer_livraisons(df)
        st.success(f"{len(df)} livraisons marquées « Livrée ».")
        st.rerun()
    k2.metric("Livrées", f"{int((df['Statut'] == 'Livrée').sum())} / {len(df)}")

    st.subheader("Modifier les livraisons (dates, camions, chauffeurs)")
    filtre = st.multiselect("Filtrer par région", REGIONS)
    vue = df[df["Region"].isin(filtre)] if filtre else df
    edite = st.data_editor(
        vue, use_container_width=True, num_rows="dynamic", hide_index=True, key="ed_liv",
        column_config={
            "Date_livraison": st.column_config.DateColumn("Date", format="DD/MM/YYYY"),
            "Heure_depart": st.column_config.TimeColumn("Départ", format="HH:mm", step=900),
            "Duree_h": st.column_config.NumberColumn("Durée A/R (h)", min_value=0.0, step=0.5),
            "Region": st.column_config.SelectboxColumn("Région", options=REGIONS),
            "Type_camion": st.column_config.SelectboxColumn("Type camion", options=TYPES, required=True),
            "Camion": st.column_config.SelectboxColumn("Camion", options=[""] + camions["Camion"].tolist()),
            "Chauffeur": st.column_config.SelectboxColumn("Chauffeur", options=[""] + CHAUFFEURS),
            "Statut": st.column_config.SelectboxColumn(
                "Statut", options=["Planifiée", "Affectée", "Livrée", "Annulée", "À vérifier",
                                   "Ressource manquante"]),
            "Quantite_t": st.column_config.NumberColumn("Quantité (t)", min_value=0.0),
            "Distance_km": st.column_config.NumberColumn("Distance (km)", min_value=0.0),
        })
    if st.button("💾 Enregistrer les modifications"):
        reste = df.drop(vue.index) if filtre else df.iloc[0:0]
        complet = pd.concat([reste, edite[COL_LIV]], ignore_index=True)
        complet["ID"] = complet["ID"].replace("", pd.NA)
        for i in complet.index[complet["ID"].isna()]:
            complet.at[i, "ID"] = prochain_id(complet.dropna(subset=["ID"]))
        complet = complet.fillna({"Camion": "", "Chauffeur": "", "Remarque": ""})
        complet["Heure_depart"] = complet["Heure_depart"].apply(_parse_heure)
        sans_duree = complet["Duree_h"].isna()
        complet.loc[sans_duree, "Duree_h"] = complet.loc[sans_duree, "Distance_km"].apply(estimer_duree)
        enregistrer_livraisons(complet)
        st.success("Modifications enregistrées.")
        st.rerun()

with tab_flotte:
    st.subheader("Parc de camions")
    k1, k2, k3 = st.columns(3)
    k1.metric("Camions 20 T", int((camions["Type"] == "20 T").sum()))
    k2.metric("Camions 15 T", int((camions["Type"] == "15 T").sum()))
    k3.metric("Chauffeurs", NB_CHAUFFEURS)

    cam_edit = st.data_editor(
        camions, use_container_width=True, hide_index=True, key="ed_cam", num_rows="dynamic",
        column_config={
            "Type": st.column_config.SelectboxColumn("Type", options=TYPES, required=True),
            "Etat": st.column_config.SelectboxColumn("État", options=["Disponible", "Maintenance", "Hors service"]),
        })
    if st.button("💾 Enregistrer la flotte"):
        cam_edit["Capacite_t"] = cam_edit["Type"].map(CAPACITES)
        enregistrer_camions(cam_edit)
        st.success("Flotte enregistrée.")
        st.rerun()

    st.subheader("Activité par camion")
    act = (df[df["Camion"] != ""].groupby("Camion")
           .agg(Livraisons=("ID", "count"), Quantite_t=("Quantite_t", "sum"), Distance_aller_km=("Distance_km", "sum")))
    st.dataframe(camions.merge(act, how="left", on="Camion").fillna(0), use_container_width=True, hide_index=True)

    st.subheader("Activité par chauffeur")
    ch = (df[df["Chauffeur"] != ""].groupby("Chauffeur").agg(Livraisons=("ID", "count"), Quantite_t=("Quantite_t", "sum")))
    st.dataframe(pd.DataFrame({"Chauffeur": CHAUFFEURS}).merge(ch, how="left", on="Chauffeur").fillna(0),
                 use_container_width=True, hide_index=True)

with tab_plan:
    st.subheader("Affectation automatique")
    if st.button("⚙️ Affecter automatiquement les livraisons non affectées"):
        nouveau, manque = affecter_auto(df, camions)
        enregistrer_livraisons(nouveau)
        (st.warning if manque else st.success)(
            f"{manque} livraison(s) sans ressource disponible." if manque else "Toutes les livraisons sont affectées.")
        st.rerun()

    st.subheader("Charge des ressources heure par heure")
    charge = charge_horaire(df)
    n20 = int(((camions["Type"] == "20 T") & (camions["Etat"] == "Disponible")).sum())
    n15 = int(((camions["Type"] == "15 T") & (camions["Etat"] == "Disponible")).sum())
    if not charge.empty:
        jours = charge.groupby(charge.index.date).max()
        jours.columns = ["Pic camions 20 T", "Pic camions 15 T", "Pic chauffeurs"]
        jours["Alerte"] = jours.apply(
            lambda r: "⚠️ dépassement" if (r["Pic camions 20 T"] > n20 or r["Pic camions 15 T"] > n15
                                           or r["Pic chauffeurs"] > NB_CHAUFFEURS) else "OK", axis=1)
        st.dataframe(jours, use_container_width=True)
        courbes(charge, {"20 T": TURQUOISE, "15 T": ORANGE, "Chauffeurs": MARINE})

    st.subheader("Ressources libres à un instant donné")
    q1, q2 = st.columns(2)
    jour_t = q1.date_input("Date", value=dt.date(ANNEE, 5, 3), format="DD/MM/YYYY", key="jt")
    heure_t = q2.time_input("Heure", value=dt.time(6, 0), key="ht")
    t0 = pd.Timestamp(dt.datetime.combine(jour_t, heure_t))
    d_all, f_all = intervalles(df)
    en_cours = df[d_all.notna() & (d_all <= t0) & (f_all > t0)]
    occ_c, occ_h = set(en_cours["Camion"]) - {""}, set(en_cours["Chauffeur"]) - {""}
    libres_c = camions[(camions["Etat"] == "Disponible") & ~camions["Camion"].isin(occ_c)]
    r1, r2, r3 = st.columns(3)
    r1.metric("Missions en cours", len(en_cours))
    r2.metric("Camions libres", f"{len(libres_c)} / {len(camions)}")
    r3.metric("Chauffeurs libres", f"{NB_CHAUFFEURS - len(occ_h)} / {NB_CHAUFFEURS}")
    with st.expander("Détail des camions libres et des missions en cours"):
        st.write("Camions libres : " + (", ".join(libres_c["Camion"]) or "aucun"))
        st.dataframe(en_cours[["ID", "Client", "Wilaya", "Type_camion", "Camion", "Chauffeur", "Heure_depart",
                               "Duree_h"]], use_container_width=True, hide_index=True)

    st.subheader("Diagramme de Gantt des camions")
    g_df = df.assign(Debut=d_all, Fin=f_all)
    g_df = g_df[g_df["Debut"].notna() & (g_df["Camion"] != "")]
    if not g_df.empty:
        st.altair_chart(
            alt.Chart(g_df).mark_bar().encode(
                x=alt.X("Debut:T", title="Date / heure"), x2="Fin:T",
                y=alt.Y("Camion:N", title=None, sort=camions["Camion"].tolist()),
                color=alt.Color("Type_camion:N", title="Type", scale=alt.Scale(domain=list(COULEURS_TYPE), range=list(COULEURS_TYPE.values()))),
                tooltip=["ID", "Client", "Wilaya", "Chauffeur", "Debut", "Fin"]
            ).properties(height=26 * len(camions) + 40),
            use_container_width=True)

    st.subheader("Contrôles")
    problemes = verifier(df, camions)
    if problemes:
        for p in problemes[:50]:
            st.warning(p)
    else:
        st.success("Aucun conflit détecté.")

    jour = st.date_input("Voir le programme d'un jour", value=dt.date(ANNEE, 5, 3), format="DD/MM/YYYY")
    st.dataframe(df[df["Date_livraison"] == jour].sort_values("Heure_depart")[
                     ["ID", "Client", "Wilaya", "Heure_depart", "Duree_h", "Type_camion", "Quantite_t",
                      "Camion", "Chauffeur", "Statut"]],
                 use_container_width=True, hide_index=True)

with tab_week:
    import math

    def decomposer(q):
        q = int(round(q))
        meilleur = None
        for b in range(0, q // 15 + 1):
            for a in range(0, (q - 15 * b) // 20 + 1):
                couvert = 20 * a + 15 * b
                cle = (-couvert, a + b)
                if meilleur is None or cle < meilleur[0]:
                    meilleur = (cle, a, b)
        _, a, b = meilleur
        return ["20 T"] * a + ["15 T"] * b, q - (20 * a + 15 * b)

    st.subheader("Planification de la semaine")
    premiere = df["Date_livraison"].dropna().min() if df["Date_livraison"].notna().any() else dt.date(ANNEE, 5, 3)
    mercredi_def = premiere - dt.timedelta(days=(premiere.weekday() - 2) % 7)
    w1, w2, w3, w4 = st.columns(4)
    mercredi = w1.date_input("Mercredi de planification", value=mercredi_def, format="DD/MM/YYYY", key="w_mer")
    debut_sem = w2.date_input("Début de la semaine planifiée", value=mercredi + dt.timedelta(days=4),
                              format="DD/MM/YYYY", key="w_deb")
    nb_jours = w3.number_input("Durée (jours)", min_value=1, max_value=14, value=7, key="w_nj")
    mode_w = w4.selectbox("Situation", list(jeux), key="w_mode",
                          format_func=lambda m: "Avant création des dépôts" if m == "Actuel" else f"Après création : {m}")
    fin_sem = debut_sem + dt.timedelta(days=int(nb_jours))

    with st.expander("➕ Ajouter une commande (décomposition automatique en camions 20 T / 15 T)"):
        a1, a2, a3, a4 = st.columns(4)
        n_client = a1.text_input("Client", key="wn_cl")
        n_wilaya = a2.text_input("Wilaya", key="wn_wi")
        n_date = a3.date_input("Date de livraison", value=debut_sem, format="DD/MM/YYYY", key="wn_da")
        n_q = a4.number_input("Quantité commandée (t)", min_value=0.0, step=5.0, value=40.0, key="wn_q")
        a5, a6, a7 = st.columns(3)
        n_region = a5.selectbox("Région", REGIONS, key="wn_re")
        n_dist = a6.number_input("Distance aller (km)", min_value=0.0, value=0.0, key="wn_di")
        n_heure = a7.time_input("Heure de départ", value=HEURE_DEPART_DEFAUT, key="wn_he")
        camions_n, reste_n = decomposer(n_q)
        st.write(f"Décomposition : **{camions_n.count('20 T')} × 20 T + {camions_n.count('15 T')} × 15 T**"
                 + (f" · {reste_n} t non transportables (inférieur à la capacité d'un camion)" if reste_n else ""))
        if st.button("Ajouter les livraisons", key="wn_ok"):
            if not n_client.strip() or not camions_n:
                st.error("Client et quantité valides requis.")
            else:
                nouvelles = []
                dist_n = n_dist if n_dist > 0 else float("nan")
                nid = int(pd.to_numeric(df["ID"].str.replace("LIV", "", regex=False), errors="coerce").max())
                for k_, t_ in enumerate(camions_n, 1):
                    nouvelles.append({"ID": f"LIV{nid + k_:03d}", "Region": n_region, "Client": n_client.strip(),
                                      "Wilaya": n_wilaya.strip().upper(), "Distance_km": dist_n,
                                      "Date_livraison": n_date, "Heure_depart": n_heure,
                                      "Duree_h": estimer_duree(dist_n), "Type_camion": t_,
                                      "Quantite_t": CAPACITES[t_], "Camion": "", "Chauffeur": "",
                                      "Statut": "Planifiée", "Remarque": "Ajoutée depuis la planification"})
                enregistrer_livraisons(pd.concat([df, pd.DataFrame(nouvelles)], ignore_index=True))
                st.rerun()

    def construire_missions(mode):
        w = df[(df["Date_livraison"] >= debut_sem) & (df["Date_livraison"] < fin_sem)]
        v = jeux[mode]
        lignes = []
        for idx, r in w.iterrows():
            regional = bool(v["regional"].get(idx, False))
            if regional:
                continue
            dist = v["dist_bellat"].get(idx)
            dist = r["Distance_km"] if pd.isna(dist) else dist
            dist = 0.0 if pd.isna(dist) else float(dist)
            lignes.append({"ID": r["ID"], "Nature": "Livraison client", "Client": r["Client"],
                           "Destination": r["Wilaya"], "Date": r["Date_livraison"], "Départ": r["Heure_depart"],
                           "Type": r["Type_camion"], "Quantité (t)": r["Quantite_t"], "Distance aller (km)": dist,
                           "Durée (h)": estimer_duree(dist)})
        regs = w[[bool(v["regional"].get(i, False)) for i in w.index]]
        for (depot, date), g in regs.assign(_d=[v["depot"].get(i) for i in regs.index]).groupby(["_d", "Date_livraison"]):
            q = g["Quantite_t"].sum()
            dist = float(dist_transfert.get(depot, 0.0))
            jour = max(date - dt.timedelta(days=int(AVANCE_APPRO_J)), debut_sem - dt.timedelta(days=int(AVANCE_APPRO_J)))
            for k_ in range(int(math.ceil(q / 20))):
                charge_ = min(20.0, q - 20.0 * k_)
                lignes.append({"ID": f"APP-{depot[:3].upper()}-{date:%d%m}-{k_ + 1}", "Nature": "Approvisionnement dépôt",
                               "Client": f"Dépôt {depot}", "Destination": depot, "Date": jour, "Départ": HEURE_DEPART_DEFAUT,
                               "Type": "20 T", "Quantité (t)": charge_, "Distance aller (km)": dist,
                               "Durée (h)": estimer_duree(dist)})
        return pd.DataFrame(lignes)

    def planifier(miss):
        miss = miss.copy()
        miss["Camion"], miss["Chauffeur"], miss["Statut"], miss["Remarque"] = "", "", "À affecter", ""
        if miss.empty:
            miss["Début"] = pd.Series(dtype="datetime64[ns]")
            miss["Fin"] = pd.Series(dtype="datetime64[ns]")
            return miss
        miss["Début"] = [pd.Timestamp(dt.datetime.combine(d, h)) for d, h in zip(miss["Date"], miss["Départ"])]
        miss["Fin"] = miss["Début"] + pd.to_timedelta(miss["Durée (h)"], unit="h")
        dispo = {t: camions[(camions["Type"] == t) & (camions["Etat"] == "Disponible")]["Camion"].tolist() for t in TYPES}
        occ_c, occ_h, heures = {}, {c: [] for c in CHAUFFEURS}, {c: 0.0 for c in CHAUFFEURS}
        ordre = miss.sort_values(["Début", "Durée (h)"], ascending=[True, False]).index
        for i in ordre:
            t = miss.at[i, "Type"]
            if miss.at[i, "Nature"] == "Livraison client" and miss.at[i, "Quantité (t)"] < CAPACITES.get(t, 0):
                miss.at[i, "Statut"], miss.at[i, "Remarque"] = "Refusée", "Quantité inférieure à la capacité du camion"
                continue
            d0, f0 = miss.at[i, "Début"], miss.at[i, "Fin"]
            libres = [c for c in dispo.get(t, []) if not _conflit(occ_c.get(c, []), d0, f0, MARGE_CAMION_H)]
            chs = sorted([c for c in CHAUFFEURS if not _conflit(occ_h[c], d0, f0, REPOS_CHAUFFEUR_H)], key=lambda c: heures[c])
            if not libres or not chs:
                miss.at[i, "Statut"] = "Ressource manquante"
                miss.at[i, "Remarque"] = f"Aucun camion {t} libre" if not libres else "Aucun chauffeur libre"
                continue
            cam, ch = libres[0], chs[0]
            miss.at[i, "Camion"], miss.at[i, "Chauffeur"], miss.at[i, "Statut"] = cam, ch, "Affectée"
            occ_c.setdefault(cam, []).append((d0, f0))
            occ_h[ch].append((d0, f0))
            heures[ch] += miss.at[i, "Durée (h)"]
        km = 2 * miss["Distance aller (km)"]
        litres = km / 100 * miss["Type"].map(CONSO_L_100KM)
        miss["Distance A/R (km)"] = km
        miss["Coût (DA)"] = litres * PRIX_GASOIL_DA_L + km * AUTRES_COUTS_DA_KM
        miss["Retour"] = miss["Fin"]
        return miss

    plan = planifier(construire_missions(mode_w))
    st.caption(f"Semaine du {debut_sem:%d/%m/%Y} au {(fin_sem - dt.timedelta(days=1)):%d/%m/%Y} · "
               f"planification établie le {mercredi:%d/%m/%Y}.")
    if plan.empty:
        st.info("Aucune livraison sur cette période.")
    else:
        aff_ = plan[plan["Statut"] == "Affectée"]
        q_tot = plan["Quantité (t)"].sum()
        u1, u2, u3, u4, u5, u6 = st.columns(6)
        u1.metric("Missions", len(plan))
        u2.metric("Tonnage (t)", f"{q_tot:,.0f}")
        u3.metric("Camions mobilisés", aff_["Camion"].nunique())
        u4.metric("Chauffeurs mobilisés", aff_["Chauffeur"].nunique())
        u5.metric("Distance A/R (km)", f"{plan['Distance A/R (km)'].sum():,.0f}")
        u6.metric("Coût (DA)", f"{plan['Coût (DA)'].sum():,.0f}")
        manque = plan[plan["Statut"].isin(["Ressource manquante", "Refusée"])]
        if len(manque):
            st.warning(f"{len(manque)} mission(s) sans affectation : " + ", ".join(manque["ID"].head(10)))
        else:
            st.success("Toutes les missions de la semaine sont affectées.")

        cols_aff = ["ID", "Nature", "Client", "Destination", "Date", "Départ", "Durée (h)", "Retour", "Type",
                    "Quantité (t)", "Camion", "Chauffeur", "Distance A/R (km)", "Coût (DA)", "Statut", "Remarque"]
        sous_w = st.tabs(["Programme", "Gantt camions", "Besoins par jour", "Feuilles de route chauffeurs", "Comparaison des situations"])
        with sous_w[0]:
            st.dataframe(plan.sort_values(["Date", "Départ"])[cols_aff].style.format(
                {"Durée (h)": "{:.1f}", "Quantité (t)": "{:,.0f}", "Distance A/R (km)": "{:,.0f}", "Coût (DA)": "{:,.0f}",
                 "Retour": lambda x: f"{x:%d/%m %H:%M}", "Départ": lambda h: h.strftime("%H:%M"),
                 "Date": lambda d: d.strftime("%d/%m/%Y")}), use_container_width=True, hide_index=True, height=520)
        with sous_w[1]:
            g_ = plan[plan["Camion"] != ""]
            if g_.empty:
                st.info("Aucune affectation.")
            else:
                st.altair_chart(alt.Chart(g_).mark_bar(cornerRadius=4).encode(
                    x=alt.X("Début:T", title="Date / heure"), x2="Fin:T",
                    y=alt.Y("Camion:N", sort=camions["Camion"].tolist(), title=None),
                    color=alt.Color("Nature:N", scale=alt.Scale(domain=["Livraison client", "Approvisionnement dépôt"],
                                                                range=[TURQUOISE, ORANGE])),
                    tooltip=["ID", "Client", "Destination", "Chauffeur", "Début", "Fin"]).properties(
                    height=26 * len(camions) + 50), use_container_width=True)
        with sous_w[2]:
            n20 = int(((camions["Type"] == "20 T") & (camions["Etat"] == "Disponible")).sum())
            n15 = int(((camions["Type"] == "15 T") & (camions["Etat"] == "Disponible")).sum())
            jours = plan.assign(Jour=plan["Date"].map(lambda d: d.strftime("%a %d/%m"))).groupby(["Jour", "Type"]).size().unstack(fill_value=0)
            jours = jours.reindex(columns=TYPES, fill_value=0)
            jours.columns = [f"Besoin {c}" for c in jours.columns]
            jours["Parc 20 T"], jours["Parc 15 T"] = n20, n15
            jours["Statut"] = ["⚠️ Insuffisant" if (r["Besoin 20 T"] > n20 or r["Besoin 15 T"] > n15) else "OK"
                               for _, r in jours.iterrows()]
            st.dataframe(jours, use_container_width=True)
        with sous_w[3]:
            ch_sel = st.selectbox("Chauffeur", sorted(aff_["Chauffeur"].unique()) or [""], key="w_ch")
            fiche = aff_[aff_["Chauffeur"] == ch_sel].sort_values("Début")
            st.dataframe(fiche[["Date", "Départ", "ID", "Client", "Destination", "Camion", "Type", "Quantité (t)",
                                "Distance A/R (km)", "Retour"]], use_container_width=True, hide_index=True)
            charge_ch = aff_.groupby("Chauffeur").agg(Missions=("ID", "count"), Heures=("Durée (h)", "sum"),
                                                      Km=("Distance A/R (km)", "sum")).reset_index()
            st.altair_chart(alt.Chart(charge_ch).mark_bar(color=ORANGE, cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
                x=alt.X("Chauffeur:N", sort="-y", title=None), y=alt.Y("Heures:Q", title="Heures de mission"),
                tooltip=["Chauffeur", "Missions", "Heures", "Km"]).properties(height=240), use_container_width=True)
        with sous_w[4]:
            comp_lignes = []
            for m_ in jeux:
                p_ = planifier(construire_missions(m_))
                if p_.empty:
                    continue
                a_ = p_[p_["Statut"] == "Affectée"]
                comp_lignes.append({"Situation": m_, "Missions": len(p_), "Camions mobilisés": a_["Camion"].nunique(),
                                    "Distance A/R (km)": p_["Distance A/R (km)"].sum(), "Coût (DA)": p_["Coût (DA)"].sum(),
                                    "Sans affectation": int((p_["Statut"] != "Affectée").sum()),
                                    "Coût par tonne (DA)": p_["Coût (DA)"].sum() / max(p_["Quantité (t)"].sum(), 1)})
            comp_w = pd.DataFrame(comp_lignes).set_index("Situation")
            comp_w["Économie (DA)"] = comp_w.loc["Actuel", "Coût (DA)"] - comp_w["Coût (DA)"]
            st.dataframe(comp_w.style.format({"Distance A/R (km)": "{:,.0f}", "Coût (DA)": "{:,.0f}",
                                              "Coût par tonne (DA)": "{:,.0f}", "Économie (DA)": "{:,.0f}"}),
                         use_container_width=True)
            cw1, cw2 = st.columns(2)
            with cw1:
                barres(comp_w["Distance A/R (km)"], COULEURS_SCEN, titre_y="km A/R")
            with cw2:
                barres(comp_w["Coût (DA)"], COULEURS_SCEN, titre_y="DA")

        e1_, e2_, e3_ = st.columns(3)
        tampon_w = io.BytesIO()
        with pd.ExcelWriter(tampon_w, engine="openpyxl") as xl:
            ex = plan[cols_aff].copy()
            ex["Départ"] = ex["Départ"].map(lambda h: h.strftime("%H:%M"))
            ex["Retour"] = ex["Retour"].map(lambda x: f"{x:%d/%m/%Y %H:%M}")
            ex.to_excel(xl, sheet_name="Programme", index=False)
            aff_.groupby("Chauffeur").agg(Missions=("ID", "count"), Heures=("Durée (h)", "sum"),
                                         Km=("Distance A/R (km)", "sum")).to_excel(xl, sheet_name="Chauffeurs")
            aff_.groupby("Camion").agg(Missions=("ID", "count"), Heures=("Durée (h)", "sum"),
                                       Km=("Distance A/R (km)", "sum")).to_excel(xl, sheet_name="Camions")
        e1_.download_button("📥 Exporter le planning (Excel)", tampon_w.getvalue(), f"planning_{debut_sem:%Y%m%d}.xlsx",
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        if mode_w == "Actuel" and e2_.button("✅ Appliquer l'affectation aux livraisons", key="w_app"):
            maj = df.copy()
            for _, r in aff_[aff_["Nature"] == "Livraison client"].iterrows():
                m_ = maj["ID"] == r["ID"]
                maj.loc[m_, ["Camion", "Chauffeur", "Statut"]] = [r["Camion"], r["Chauffeur"], "Affectée"]
            enregistrer_livraisons(maj)
            st.rerun()

with tab_osrm:
    st.subheader("Distances routières (OSRM)")
    base = st.text_input("Serveur OSRM", OSRM_URL)
    o1, o2, o3 = st.columns(3)
    nom_o = o1.text_input("Point de départ", DEPOT_ORIGINE[0])
    lat_o = o2.number_input("Latitude départ", value=DEPOT_ORIGINE[1], format="%.4f")
    lon_o = o3.number_input("Longitude départ", value=DEPOT_ORIGINE[2], format="%.4f")

    coords = charger_coords()
    coords_ed = st.data_editor(coords, use_container_width=True, hide_index=True, num_rows="dynamic", key="ed_coord")
    if st.button("💾 Enregistrer les coordonnées"):
        coords_ed.to_csv(F_COORDS, index=False, encoding="utf-8-sig")
        st.success("Coordonnées enregistrées.")

    if st.button("🧭 Calculer les distances OSRM"):
        cmap = {norm(r["Wilaya"]): (r["Latitude"], r["Longitude"]) for _, r in coords_ed.iterrows()}
        resultats, erreurs = [], []
        barre = st.progress(0.0)
        wilayas = sorted(df["Wilaya"].dropna().unique())
        for k, w in enumerate(wilayas):
            if norm(w) not in cmap:
                erreurs.append(f"{w} : coordonnées manquantes")
            else:
                try:
                    dkm, dh = osrm_route(lat_o, lon_o, cmap[norm(w)][0], cmap[norm(w)][1], base)
                    resultats.append({"Wilaya": w, "Distance_OSRM_km": round(dkm, 1), "Duree_OSRM_h": round(dh, 2)})
                except Exception as e:
                    erreurs.append(f"{w} : {e}")
            barre.progress((k + 1) / len(wilayas))
        if resultats:
            pd.DataFrame(resultats).to_csv(F_OSRM, index=False, encoding="utf-8-sig")
            st.success(f"{len(resultats)} distances calculées depuis « {nom_o} ».")
        for e in erreurs:
            st.warning(e)

    osrm = charger_osrm()
    if not osrm.empty:
        ref = df.groupby("Wilaya").agg(Distance_document_km=("Distance_km", "first"), Livraisons=("ID", "count")).reset_index()
        ref["_k"] = ref["Wilaya"].map(norm)
        osrm["_k"] = osrm["Wilaya"].map(norm)
        cmp_ = ref.merge(osrm.drop(columns="Wilaya"), on="_k", how="left").drop(columns="_k")
        cmp_["Ecart_km"] = cmp_["Distance_OSRM_km"] - cmp_["Distance_document_km"]
        cmp_["Ecart_%"] = cmp_["Ecart_km"] / cmp_["Distance_document_km"] * 100
        st.dataframe(cmp_.round(1), use_container_width=True, hide_index=True)

    st.subheader("Distances d'approvisionnement : centre d'expédition → dépôts régionaux")
    tr_tab = pd.DataFrame([{"Dépôt": d_, "Distance aller (km)": v_} for d_, v_ in dist_transfert.items()
                           if d_ in DEPOTS and d_ != "Centre existant"])
    tr_ed = st.data_editor(tr_tab, use_container_width=True, hide_index=True, key="ed_tr",
                           disabled=["Dépôt"])
    t1, t2 = st.columns(2)
    if t1.button("💾 Enregistrer les distances de transfert"):
        pd.DataFrame({"Depot": tr_ed["Dépôt"], "Distance_km": tr_ed["Distance aller (km)"]}).to_csv(
            F_TRANSFERTS, index=False, encoding="utf-8-sig")
        st.success("Distances de transfert enregistrées.")
        st.rerun()
    if t2.button("🧭 Calculer par OSRM"):
        res_t, err_t = [], []
        for d_ in tr_tab["Dépôt"]:
            try:
                dkm, _ = osrm_route(DEPOTS["Centre existant"][0], DEPOTS["Centre existant"][1],
                                    DEPOTS[d_][0], DEPOTS[d_][1], base)
                res_t.append({"Depot": d_, "Distance_km": round(dkm, 1)})
            except Exception as e:
                err_t.append(f"{d_} : {e}")
        if res_t:
            pd.DataFrame(res_t).to_csv(F_TRANSFERTS, index=False, encoding="utf-8-sig")
            st.rerun()
        for e in err_t:
            st.warning(e)

with tab_cout:
    st.subheader("Coûts par région et par livraison")
    dist_c, est_osrm = distance_retenue(df)
    det = pd.concat([df[["ID", "Region", "Client", "Wilaya", "Type_camion"]], dist_c.rename("Distance_aller_km"),
                     calculer_couts(df, dist_c)], axis=1)
    reg = det.groupby("Region").agg(Livraisons=("ID", "count"), Distance_AR_km=("Distance_AR_km", "sum"),
                                    Carburant_L=("Carburant_L", "sum"), Cout_DA=("Cout_DA", "sum"))
    st.dataframe(reg.round(0), use_container_width=True)
    st.dataframe(det.round(1), use_container_width=True, hide_index=True)

with tab_comp:
    st.subheader("Synthèse : distances parcourues et coûts")
    cols = st.columns(3)
    for col, (nom, r) in zip(cols, resume.iterrows()):
        col.metric(f"{nom} · {r['Distance A/R (km)']:,.0f} km A/R", f"{r['Coût total (DA)']:,.0f} DA")
    st.dataframe(resume.style.format({
        "Livraisons": "{:,.0f}", "Distribution A/R (km)": "{:,.0f}", "Transfert A/R (km)": "{:,.0f}",
        "Distance A/R (km)": "{:,.0f}", "Carburant (L)": "{:,.0f}",
        "Coût carburant (DA)": "{:,.0f}", "Coût total (DA)": "{:,.0f}", "Réduction distance (%)": "{:.1f}",
        "Économie (DA)": "{:,.0f}"}), use_container_width=True)
    g1, g2 = st.columns(2)
    with g1:
        barres(resume["Distance A/R (km)"], COULEURS_SCEN, titre_y="km A/R")
    with g2:
        barres(resume["Coût total (DA)"], COULEURS_SCEN, titre_y="DA")

    st.subheader("Détail par wilaya")
    formats = {"Livraisons": "{:,.0f}", "Quantité (t)": "{:,.0f}", "Distance dépôt→client (km)": "{:,.1f}",
               "Distribution A/R (km)": "{:,.0f}", "Transfert A/R (km)": "{:,.0f}",
               "Distance A/R (km)": "{:,.0f}", "Carburant (L)": "{:,.0f}", "Coût carburant (DA)": "{:,.0f}",
               "Maintenance + pneus (DA)": "{:,.0f}", "Coût total (DA)": "{:,.0f}"}
    sous = st.tabs(["Méthode actuelle", "2 dépôts", "3 dépôts"])
    for onglet, nom in zip(sous, ["Actuel", "2 dépôts", "3 dépôts"]):
        with onglet:
            t = tables[nom].copy()
            t["Distance dépôt→client (km)"] = t["Distance dépôt→client (km)"].astype(float)
            tot = t.drop(columns=["Servi par", "Distance dépôt→client (km)"]).sum()
            tot.name = "TOTAL"
            aff = pd.concat([t, tot.to_frame().T])
            aff["Servi par"] = aff["Servi par"].fillna("")
            st.dataframe(aff.style.format(formats, na_rep="").apply(
                lambda r: [f"font-weight:bold; background-color:{ORANGE}40" if r.name == "TOTAL" else ""
                           for _ in r], axis=1), use_container_width=True, height=620)

    st.subheader("Réduction par dépôt (par rapport à la méthode actuelle)")
    reductions = {}
    for nom in ["2 dépôts", "3 dépôts"]:
        t = tables[nom]
        a = tables["Actuel"].loc[t.index]
        x = pd.DataFrame({"Dépôt": t["Servi par"], "Quantité (t)": t["Quantité (t)"],
                          "Distance actuelle A/R (km)": a["Distance A/R (km)"],
                          "Distance scénario A/R (km)": t["Distance A/R (km)"],
                          "Coût actuel (DA)": a["Coût total (DA)"], "Coût scénario (DA)": t["Coût total (DA)"]})
        r = x.groupby("Dépôt").sum()
        r.insert(0, "Wilayas servies", x.groupby("Dépôt").size())
        r["Réduction distance (%)"] = (r["Distance actuelle A/R (km)"] - r["Distance scénario A/R (km)"]) \
            / r["Distance actuelle A/R (km)"] * 100
        r["Réduction coût (%)"] = (r["Coût actuel (DA)"] - r["Coût scénario (DA)"]) / r["Coût actuel (DA)"] * 100
        tot = r.sum()
        tot["Réduction distance (%)"] = (tot["Distance actuelle A/R (km)"] - tot["Distance scénario A/R (km)"]) \
            / tot["Distance actuelle A/R (km)"] * 100
        tot["Réduction coût (%)"] = (tot["Coût actuel (DA)"] - tot["Coût scénario (DA)"]) / tot["Coût actuel (DA)"] * 100
        tot.name = "TOTAL"
        reductions[nom] = pd.concat([r, tot.to_frame().T])
    fmt_r = {"Wilayas servies": "{:,.0f}", "Quantité (t)": "{:,.0f}", "Distance actuelle A/R (km)": "{:,.0f}",
             "Distance scénario A/R (km)": "{:,.0f}", "Coût actuel (DA)": "{:,.0f}", "Coût scénario (DA)": "{:,.0f}",
             "Réduction distance (%)": "{:.1f} %", "Réduction coût (%)": "{:.1f} %"}
    for onglet, nom in zip(st.tabs(["2 dépôts", "3 dépôts"]), ["2 dépôts", "3 dépôts"]):
        with onglet:
            rd = reductions[nom]
            st.dataframe(rd.style.format(fmt_r).apply(
                lambda r_: [f"font-weight:bold; background-color:{ORANGE}40" if r_.name == "TOTAL" else "" for _ in r_],
                axis=1), use_container_width=True)
            palette_r = [TURQUOISE, ORANGE, MARINE, PRUNE, GRIS]
            barres(rd.drop(index="TOTAL")["Réduction distance (%)"],
                   {d: palette_r[k % 5] for k, d in enumerate(rd.index[:-1])}, titre_y="% de réduction")

    st.subheader("Affectation par dépôt (distance dépôt → client : le client retire ses produits)")
    choix = st.radio("Scénario", list(scenarios), horizontal=True)
    sc = scenarios[choix]
    sc = sc.assign(Tonnes_km=sc["Q_tonnes"] * sc["distance_km"])
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Clients", len(sc))
    m2.metric("Quantité (t)", f"{sc['Q_tonnes'].sum():,.0f}")
    m3.metric("Tonnes-km", f"{sc['Tonnes_km'].sum():,.0f}")
    m4.metric("Distance moyenne pondérée (km)", f"{sc['Tonnes_km'].sum() / sc['Q_tonnes'].sum():,.1f}")
    par_depot = sc.groupby("servi_par").agg(Clients=("client", "count"), Quantite_t=("Q_tonnes", "sum"),
                                            Tonnes_km=("Tonnes_km", "sum"))
    par_depot["Distance_moy_km"] = par_depot["Tonnes_km"] / par_depot["Quantite_t"]
    st.dataframe(par_depot.round(1), use_container_width=True)
    palette = [TURQUOISE, ORANGE, MARINE, PRUNE]
    barres(par_depot["Quantite_t"], {d: palette[k % 4] for k, d in enumerate(par_depot.index)}, titre_y="Tonnes")
    st.dataframe(sc.rename(columns={"servi_par": "Servi par", "distance_km": "Distance (km)", "Q_tonnes": "Q (t)"}),
                 use_container_width=True, hide_index=True)
    st.session_state["comparaison"] = resume

with tab_sens:
    st.subheader("Coût d'un dépôt supplémentaire")
    st.caption(f"Coût mensuel par dépôt : {cout_depot:,.0f} DA · données couvrant {periode:g} mois (réglages dans la barre latérale).")

    def economie_nette(nom, pf=1.0, cf=1.0, af=1.0, df_=1.0):
        gain = cout_scenario("Actuel", pf, cf, af) - cout_scenario(nom, pf, cf, af)
        return gain, gain - nouveaux[nom] * cout_depot * df_ * periode

    lignes_r = []
    for nom in scenarios:
        gain, net = economie_nette(nom)
        lignes_r.append({"Scénario": nom, "Dépôts supplémentaires": nouveaux[nom],
                         "Économie de transport (DA)": gain,
                         "Coût des dépôts (DA)": nouveaux[nom] * cout_depot * periode,
                         "Économie nette (DA)": net,
                         "Seuil de rentabilité par dépôt (DA/mois)": gain / nouveaux[nom] / periode,
                         "Rentable": "Oui" if net > 0 else "Non"})
    rent = pd.DataFrame(lignes_r).set_index("Scénario")
    cr = st.columns(len(rent))
    for col, (nom, r) in zip(cr, rent.iterrows()):
        col.metric(f"{nom} · économie nette", f"{r['Économie nette (DA)']:,.0f} DA")
    st.dataframe(rent.style.format({
        "Dépôts supplémentaires": "{:,.0f}", "Économie de transport (DA)": "{:,.0f}",
        "Coût des dépôts (DA)": "{:,.0f}", "Économie nette (DA)": "{:,.0f}",
        "Seuil de rentabilité par dépôt (DA/mois)": "{:,.0f}"}), use_container_width=True)

    st.subheader("Analyse de sensibilité")
    param = st.radio("Paramètre qui varie", ["Prix du gasoil", "Consommation", "Maintenance + pneus",
                                             "Coût des dépôts"], horizontal=True)
    variations = list(range(-30, 31, 10))
    lignes_s = []
    for v in variations:
        f = 1 + v / 100
        args = {"Prix du gasoil": {"pf": f}, "Consommation": {"cf": f}, "Maintenance + pneus": {"af": f},
                "Coût des dépôts": {"df_": f}}[param]
        ligne = {"Variation (%)": v}
        for nom in scenarios:
            gain, net = economie_nette(nom, **args)
            ligne[f"Économie nette {nom} (DA)"] = net
        lignes_s.append(ligne)
    sens = pd.DataFrame(lignes_s)
    st.dataframe(sens.style.format({c: "{:,.0f}" for c in sens.columns if c != "Variation (%)"}
                                   | {"Variation (%)": "{:+d} %"}), use_container_width=True, hide_index=True)
    long = sens.melt("Variation (%)", var_name="Scénario", value_name="Économie nette (DA)")
    long["Scénario"] = long["Scénario"].str.replace("Économie nette ", "", regex=False).str.replace(" (DA)", "", regex=False)
    ligne_c = alt.Chart(long).mark_line(point=True, strokeWidth=3).encode(
        x=alt.X("Variation (%):Q", title=f"Variation de : {param} (%)"), y=alt.Y("Économie nette (DA):Q"),
        color=alt.Color("Scénario:N", scale=alt.Scale(domain=list(COULEURS_SCEN)[1:],
                                                      range=list(COULEURS_SCEN.values())[1:])),
        tooltip=["Scénario", "Variation (%)", "Économie nette (DA)"])
    zero = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(color=GRIS, strokeDash=[5, 5]).encode(y=alt.Y("y:Q", title="Économie nette (DA)"))
    st.altair_chart((ligne_c + zero).properties(height=320), use_container_width=True)

    st.subheader("Économie nette selon le coût d'un dépôt")
    couts_grille = list(range(0, int(max(rent["Seuil de rentabilité par dépôt (DA/mois)"].max() * 1.3, 1)), 
                              max(int(rent["Seuil de rentabilité par dépôt (DA/mois)"].max() / 20), 1)))
    courbe = pd.DataFrame([{"Coût mensuel par dépôt (DA)": c, "Scénario": nom,
                            "Économie nette (DA)": economie_nette(nom)[0] - nouveaux[nom] * c * periode}
                           for c in couts_grille for nom in scenarios])
    g_cd = alt.Chart(courbe).mark_line(strokeWidth=3).encode(
        x="Coût mensuel par dépôt (DA):Q", y="Économie nette (DA):Q",
        color=alt.Color("Scénario:N", scale=alt.Scale(domain=list(COULEURS_SCEN)[1:],
                                                      range=list(COULEURS_SCEN.values())[1:])),
        tooltip=["Scénario", "Coût mensuel par dépôt (DA)", "Économie nette (DA)"])
    st.altair_chart((g_cd + zero).properties(height=320), use_container_width=True)

with tab_fin:
    st.subheader("Hypothèses d'investissement (barre latérale)")
    NB_MOIS = horizon * 12
    st.caption(f"Coût d'exploitation mensuel par dépôt : {cout_depot:,.0f} DA (barre latérale) · "
               f"données couvrant {periode:g} mois.")

    st.subheader("Croissance : nouveaux clients attirés par les dépôts régionaux")
    DEPOTS_REG = ["Sétif", "Relizane", "Constantine", "Bordj Bou Arreridj"]
    croiss_ed = st.data_editor(
        pd.DataFrame({"Dépôt": DEPOTS_REG, "Nouveaux clients": [4, 4, 4, 4], "Quantité par commande (t)": [10.0] * 4,
                      "Commandes par client et par mois": [2.0] * 4}),
        hide_index=True, use_container_width=True, key="ed_croiss", disabled=["Dépôt"])
    croiss_ed["Tonnes / mois"] = (croiss_ed["Nouveaux clients"] * croiss_ed["Quantité par commande (t)"]
                                  * croiss_ed["Commandes par client et par mois"])
    tonnes_nv = dict(zip(croiss_ed["Dépôt"], croiss_ed["Tonnes / mois"]))
    st.caption("Ces clients retirent leurs produits au dépôt avec leur propre flotte : Bellat n'ajoute que l'approvisionnement du dépôt.")

    def composantes(nom):
        ar = 2 * jeux[nom]["dist_bellat"][commun]
        litres = ar / 100 * dfc["Type_camion"].map(CONSO_L_100KM)
        tr = transfert_df(nom, dfc)
        return ((litres + tr["litres"]) * PRIX_GASOIL_DA_L).sum(), ((ar + tr["km"]) * AUTRES_COUTS_DA_KM).sum()

    comp_a = composantes("Actuel")
    base_f = {}
    for nom in scenarios:
        c = composantes(nom)
        deps = set(scenarios[nom]["servi_par"]) - {"Centre existant"}
        t_g = sum(tonnes_nv.get(d_, 0.0) for d_ in deps)
        km_g = sum(2 * dist_transfert.get(d_, 0.0) * tonnes_nv.get(d_, 0.0) / 20 for d_ in deps)
        base_f[nom] = {"Tg": t_g, "Mg": t_g * marge_t,
                       "Cgf": km_g / 100 * CONSO_L_100KM["20 T"] * PRIX_GASOIL_DA_L, "Cga": km_g * AUTRES_COUTS_DA_KM,
                       "Fg": (comp_a[0] - c[0]) / periode, "Ag": (comp_a[1] - c[1]) / periode, "n": nouveaux[nom],
                       "dist_an": (2 * jeux[nom]["dist_bellat"][commun].sum() + transfert_df(nom, dfc)["km"].sum()) / periode * 12,
                       "transport_an": (c[0] + c[1]) / periode * 12}

    def facteur_annuite(i, n):
        return n if i == 0 else (1 - (1 + i) ** -n) / i

    def indicateurs(nom, vol=1.0, pf=1.0, cf=1.0, af=1.0, ex=1.0, inv=1.0, taux=None, adopt=1.0):
        b = base_f[nom]
        taux = taux_a if taux is None else taux
        i = (1 + taux / 100) ** (1 / 12) - 1
        net_g = adopt * (b["Mg"] - pf * cf * b["Cgf"] - af * b["Cga"]) if INCLURE_CROISSANCE else 0.0
        gain = vol * (pf * cf * b["Fg"] + af * b["Ag"]) + net_g
        m = gain - b["n"] * cout_depot * ex
        capital = b["n"] * invest_depot * inv
        van = -capital + m * facteur_annuite(i, NB_MOIS)
        return {"m": m, "I": capital, "van": van, "gain": gain, "i": i}

    def delai_simple(m, capital):
        return capital / m if m > 0 else np.nan

    def delai_actualise(m, capital, i):
        if m <= 0:
            return np.nan
        if i == 0:
            return capital / m
        x = capital * i / m
        return -np.log(1 - x) / np.log(1 + i) if x < 1 else np.nan

    def tri_annuel(m, capital):
        if m <= 0 or m * NB_MOIS <= capital or capital <= 0:
            return np.nan
        lo, hi = 1e-9, 5.0
        for _ in range(200):
            mid = (lo + hi) / 2
            if -capital + m * facteur_annuite(mid, NB_MOIS) > 0:
                lo = mid
            else:
                hi = mid
        return (1 + lo) ** 12 - 1

    lignes_i = []
    for nom in scenarios:
        r = indicateurs(nom)
        b = base_f[nom]
        i_m = r["i"]
        m_requis = r["I"] / facteur_annuite(i_m, NB_MOIS)
        net_g0 = (b["Mg"] - b["Cgf"] - b["Cga"]) if INCLURE_CROISSANCE else 0.0
        vol_min = (m_requis + b["n"] * cout_depot - net_g0) / (b["Fg"] + b["Ag"]) * 100 if (b["Fg"] + b["Ag"]) > 0 else np.nan
        lignes_i.append({
            "Scénario": nom, "Investissement (DA)": r["I"], "Gain total / mois (DA)": r["gain"],
            "Tonnes nouvelles / mois": b["Tg"] if INCLURE_CROISSANCE else 0.0,
            "Flux net / mois (DA)": r["m"], "VAN (DA)": r["van"],
            "TRI annuel (%)": tri_annuel(r["m"], r["I"]) * 100,
            "ROI sur l'horizon (%)": (r["m"] * NB_MOIS - r["I"]) / r["I"] * 100 if r["I"] else np.nan,
            "Indice de rentabilité": (r["van"] + r["I"]) / r["I"] if r["I"] else np.nan,
            "Délai de récupération (mois)": delai_simple(r["m"], r["I"]),
            "Délai actualisé (mois)": delai_actualise(r["m"], r["I"], i_m),
            "Volume minimal pour VAN = 0 (%)": vol_min})
    indic = pd.DataFrame(lignes_i).set_index("Scénario")

    st.subheader("Indicateurs de rentabilité")
    cols_i = st.columns(len(indic))
    for col, (nom, r) in zip(cols_i, indic.iterrows()):
        delai = r["Délai de récupération (mois)"]
        col.metric(f"{nom} · VAN · récupération " + (f"{delai:.1f} mois" if pd.notna(delai) else "jamais"),
                   f"{r['VAN (DA)']:,.0f} DA")
    def fm(modele):
        return lambda v: "—" if pd.isna(v) else modele.format(v)

    def texte(tableau, formats):
        t = tableau.copy()
        for c_, m_ in formats.items():
            t[c_] = t[c_].map(fm(m_))
        return t

    formats_i = {
        "Investissement (DA)": "{:,.0f}", "Gain total / mois (DA)": "{:,.0f}", "Tonnes nouvelles / mois": "{:,.0f}",
        "Flux net / mois (DA)": "{:,.0f}", "VAN (DA)": "{:,.0f}", "TRI annuel (%)": "{:.1f}",
        "ROI sur l'horizon (%)": "{:.0f}", "Indice de rentabilité": "{:.2f}",
        "Délai de récupération (mois)": "{:.1f}", "Délai actualisé (mois)": "{:.1f}",
        "Volume minimal pour VAN = 0 (%)": "{:.0f}"}
    st.dataframe(indic.apply(lambda c: c.map(fm(formats_i[c.name]))), use_container_width=True)

    st.subheader("Flux de trésorerie cumulés")
    mois = np.arange(0, NB_MOIS + 1)
    flux = []
    for nom in scenarios:
        r = indicateurs(nom)
        i_m = r["i"]
        for t in mois:
            flux.append({"Mois": int(t), "Scénario": nom, "Type": "Cumulé", "Valeur (DA)": -r["I"] + r["m"] * t})
            flux.append({"Mois": int(t), "Scénario": nom, "Type": "Actualisé",
                         "Valeur (DA)": -r["I"] + r["m"] * facteur_annuite(i_m, t)})
    flux = pd.DataFrame(flux)
    g_flux = alt.Chart(flux).mark_line(strokeWidth=3).encode(
        x=alt.X("Mois:Q"), y=alt.Y("Valeur (DA):Q"),
        color=alt.Color("Scénario:N", scale=alt.Scale(domain=list(COULEURS_SCEN)[1:], range=list(COULEURS_SCEN.values())[1:])),
        strokeDash=alt.StrokeDash("Type:N", scale=alt.Scale(domain=["Cumulé", "Actualisé"], range=[[1, 0], [6, 4]])),
        tooltip=["Scénario", "Type", "Mois", "Valeur (DA)"])
    zero_f = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(color=GRIS).encode(y=alt.Y("y:Q", title="Valeur (DA)"))
    st.altair_chart((g_flux + zero_f).properties(height=340), use_container_width=True)

    st.subheader("Diagramme tornade : impact sur la VAN (±20 %)")
    nom_t = st.radio("Scénario analysé", list(scenarios), horizontal=True, key="tornade")
    van0 = indicateurs(nom_t)["van"]
    params_t = {"Prix du gasoil": "pf", "Consommation": "cf", "Maintenance + pneus": "af", "Volume transporté": "vol",
                "Coût d'exploitation des dépôts": "ex", "Investissement initial": "inv",
                "Adoption des nouveaux clients": "adopt"}
    lt = []
    for lib, arg in params_t.items():
        bas, haut = indicateurs(nom_t, **{arg: 0.8})["van"], indicateurs(nom_t, **{arg: 1.2})["van"]
        lt.append({"Paramètre": lib, "VAN -20 %": bas, "VAN +20 %": haut, "Amplitude": abs(haut - bas)})
    bas, haut = indicateurs(nom_t, taux=taux_a * 0.8)["van"], indicateurs(nom_t, taux=taux_a * 1.2)["van"]
    lt.append({"Paramètre": "Taux d'actualisation", "VAN -20 %": bas, "VAN +20 %": haut, "Amplitude": abs(haut - bas)})
    torn = pd.DataFrame(lt).sort_values("Amplitude", ascending=False)
    ordre = torn["Paramètre"].tolist()
    base_t = alt.Chart(torn).mark_bar(height=18, color=TURQUOISE).encode(
        y=alt.Y("Paramètre:N", sort=ordre, title=None), x=alt.X("VAN -20 %:Q", title="VAN (DA)"), x2="VAN +20 %:Q",
        tooltip=["Paramètre", "VAN -20 %", "VAN +20 %"])
    ligne_van = alt.Chart(pd.DataFrame({"x": [van0]})).mark_rule(color=ORANGE, strokeWidth=3).encode(x="x:Q")
    st.altair_chart((base_t + ligne_van).properties(height=300), use_container_width=True)

    st.subheader("Simulation Monte-Carlo (5 000 tirages)")
    rng = np.random.default_rng(42)
    NS = 5000
    tir = lambda a, m_, b: rng.triangular(a, m_, b, NS)
    alea = {"vol": tir(0.85, 1, 1.15), "pf": tir(0.8, 1, 1.3), "cf": tir(0.9, 1, 1.15), "af": tir(0.8, 1, 1.3),
            "ex": tir(0.9, 1, 1.3), "inv": tir(0.9, 1, 1.4), "adopt": tir(0.4, 1, 1.4)}
    sims, stats, van_sim = [], [], {}
    for nom in scenarios:
        r = indicateurs(nom, **alea)
        v = np.asarray(r["van"])
        sims.append(pd.DataFrame({"Scénario": nom, "VAN (DA)": v}))
        van_sim[nom] = v
        m_arr = np.asarray(r["m"])
        cap = np.asarray(r["I"])
        stats.append({"Scénario": nom, "VAN moyenne (DA)": v.mean(), "VAN médiane (DA)": np.median(v),
                      "VAN pessimiste P5 (DA)": np.percentile(v, 5), "CVaR 5 % (DA)": v[v <= np.percentile(v, 5)].mean(), "VAN optimiste P95 (DA)": np.percentile(v, 95),
                      "Probabilité VAN > 0 (%)": (v > 0).mean() * 100,
                      "Délai médian (mois)": pd.Series(np.where(m_arr > 0, cap / np.where(m_arr > 0, m_arr, 1), np.nan)).median()})
    sims = pd.concat(sims)
    st_mc = pd.DataFrame(stats).set_index("Scénario")
    cm = st.columns(len(st_mc))
    for col, (nom, r) in zip(cm, st_mc.iterrows()):
        col.metric(f"{nom} · probabilité de rentabilité", f"{r['Probabilité VAN > 0 (%)']:.0f} %")
    st.dataframe(st_mc.style.format({c: "{:,.0f}" for c in st_mc.columns if "%" not in c and "mois" not in c}
                                    | {"Probabilité VAN > 0 (%)": "{:.1f}", "Délai médian (mois)": "{:.1f}", "CVaR 5 % (DA)": "{:,.0f}"}),
                 use_container_width=True)
    g_mc = alt.Chart(sims).mark_bar(opacity=0.65).encode(
        x=alt.X("VAN (DA):Q", bin=alt.Bin(maxbins=45), title="VAN (DA)"), y=alt.Y("count()", title="Fréquence", stack=None),
        color=alt.Color("Scénario:N", scale=alt.Scale(domain=list(COULEURS_SCEN)[1:], range=list(COULEURS_SCEN.values())[1:])))
    st.altair_chart((g_mc + alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(color=MARINE, strokeWidth=2).encode(x=alt.X("x:Q", title="VAN (DA)")))
                    .properties(height=300), use_container_width=True)

    st.subheader("Facteurs d'incertitude : corrélation de rang avec la VAN")
    sc_corr = st.radio("Scénario", list(scenarios), horizontal=True, key="corr_sc")
    table_c = pd.DataFrame(alea)
    table_c["VAN"] = van_sim[sc_corr]
    corr = table_c.rank().corr()["VAN"].drop("VAN")
    noms_f = {"vol": "Volume", "pf": "Prix du gasoil", "cf": "Consommation", "af": "Maintenance + pneus",
              "ex": "Exploitation des dépôts", "inv": "Investissement", "adopt": "Adoption des nouveaux clients"}
    corr_df = pd.DataFrame({"Facteur": [noms_f[k] for k in corr.index], "Corrélation": corr.values})
    st.altair_chart(alt.Chart(corr_df).mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
        y=alt.Y("Facteur:N", sort=alt.EncodingSortField("Corrélation", order="descending"), title=None),
        x=alt.X("Corrélation:Q", scale=alt.Scale(domain=[-1, 1])),
        color=alt.condition(alt.datum.Corrélation > 0, alt.value(TURQUOISE), alt.value(ORANGE)),
        tooltip=["Facteur", "Corrélation"]).properties(height=240), use_container_width=True)

    st.subheader("Modèle détaillé : après impôt, inflation, croissance et amortissement")

    def modele_annuel(nom, pf=1.0, cf=1.0, af=1.0, vol=1.0, ex=1.0, inv=1.0, adopt=1.0):
        b = base_f[nom]
        n = b["n"]
        capital = n * invest_depot * inv
        lignes = []
        for t in range(1, horizon + 1):
            v_t = vol * (1 + croiss_vol / 100) ** (t - 1)
            gain_f = 12 * v_t * pf * cf * b["Fg"] * (1 + infl_carb / 100) ** (t - 1)
            gain_a = 12 * v_t * af * b["Ag"] * (1 + infl_autres / 100) ** (t - 1)
            expl = 12 * n * cout_depot * ex * (1 + infl_expl / 100) ** (t - 1)
            amort = capital / amort_ans if t <= amort_ans else 0.0
            rampe_t = (rampe_1 / 100 if t == 1 else rampe_2 / 100 if t == 2 else 1.0) * adopt if INCLURE_CROISSANCE else 0.0
            marge_g = 12 * rampe_t * b["Mg"]
            cout_g = 12 * rampe_t * (pf * cf * b["Cgf"] * (1 + infl_carb / 100) ** (t - 1)
                                     + af * b["Cga"] * (1 + infl_autres / 100) ** (t - 1))
            resultat = gain_f + gain_a + marge_g - cout_g - expl - amort
            impot = max(resultat, 0.0) * taux_impot / 100
            flux_ = gain_f + gain_a + marge_g - cout_g - expl - impot + (capital * val_res / 100 if t == horizon else 0.0)
            lignes.append({"Année": t, "Gain carburant": gain_f, "Gain maintenance": gain_a,
                           "Marge nouveaux clients": marge_g, "Approvisionnement nouveaux clients": -cout_g,
                           "Exploitation dépôts": -expl,
                           "Amortissement": -amort, "Résultat avant impôt": resultat, "Impôt": -impot,
                           "Flux de trésorerie": flux_})
        return capital, pd.DataFrame(lignes)

    def van_annuelle(capital, flux_, taux):
        return -capital + sum(f / (1 + taux / 100) ** t for t, f in enumerate(flux_, 1))

    def tri_flux(capital, flux_):
        if capital <= 0 or sum(flux_) <= capital:
            return np.nan
        lo, hi = -0.99, 20.0
        for _ in range(200):
            mid = (lo + hi) / 2
            if -capital + sum(f / (1 + mid) ** t for t, f in enumerate(flux_, 1)) > 0:
                lo = mid
            else:
                hi = mid
        return lo * 100

    def trim_flux(capital, flux_):
        r = taux_a / 100
        n_ = len(flux_)
        vf = sum(max(f, 0) * (1 + r) ** (n_ - t) for t, f in enumerate(flux_, 1))
        vp = capital + sum(-min(f, 0) / (1 + r) ** t for t, f in enumerate(flux_, 1))
        return ((vf / vp) ** (1 / n_) - 1) * 100 if vp > 0 and vf > 0 else np.nan

    def delai_mois(capital, flux_, taux=0.0):
        cumul = -capital
        for t, f in enumerate(flux_, 1):
            fa = f / (1 + taux / 100) ** t
            if cumul + fa >= 0 and fa > 0:
                return ((t - 1) + (-cumul) / fa) * 12
            cumul += fa
        return np.nan

    def seuil(nom, parametre, cible_haut=6.0):
        def f(x):
            cap_, fl_ = modele_annuel(nom, **{parametre: x})
            return van_annuelle(cap_, fl_["Flux de trésorerie"].tolist(), taux_a)
        if f(cible_haut) < 0:
            return np.nan
        if f(0.0) > 0:
            return 0.0
        lo, hi = 0.0, cible_haut
        for _ in range(80):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if f(mid) < 0 else (lo, mid)
        return hi

    lignes_d = []
    for nom in scenarios:
        cap_, fl_ = modele_annuel(nom)
        flux_l = fl_["Flux de trésorerie"].tolist()
        van_d = van_annuelle(cap_, flux_l, taux_a)
        i_ = taux_a / 100
        eaa = van_d * i_ / (1 - (1 + i_) ** -horizon) if i_ > 0 else van_d / horizon
        sp, sv = seuil(nom, "pf"), seuil(nom, "vol")
        lignes_d.append({"Scénario": nom, "Investissement (DA)": cap_, "VAN après impôt (DA)": van_d,
                         "Annuité équivalente (DA/an)": eaa, "TRI (%)": tri_flux(cap_, flux_l),
                         "TRI modifié (%)": trim_flux(cap_, flux_l),
                         "Indice de profitabilité": (van_d + cap_) / cap_ if cap_ else np.nan,
                         "Délai simple (mois)": delai_mois(cap_, flux_l), "Délai actualisé (mois)": delai_mois(cap_, flux_l, taux_a),
                         "Prix du gasoil d'équilibre (DA/L)": sp * PRIX_GASOIL_DA_L if pd.notna(sp) else np.nan,
                         "Volume d'équilibre (% du volume)": sv * 100 if pd.notna(sv) else np.nan})
    detail_f = pd.DataFrame(lignes_d).set_index("Scénario")
    cdm = st.columns(len(detail_f))
    for col, (nom, r) in zip(cdm, detail_f.iterrows()):
        col.metric(f"{nom} · VAN après impôt", f"{r['VAN après impôt (DA)']:,.0f} DA")
    st.dataframe(texte(detail_f, {
        "Investissement (DA)": "{:,.0f}", "VAN après impôt (DA)": "{:,.0f}",
        "Annuité équivalente (DA/an)": "{:,.0f}", "TRI (%)": "{:.1f}", "TRI modifié (%)": "{:.1f}",
        "Indice de profitabilité": "{:.2f}", "Délai simple (mois)": "{:.1f}",
        "Délai actualisé (mois)": "{:.1f}", "Prix du gasoil d'équilibre (DA/L)": "{:,.1f}",
        "Volume d'équilibre (% du volume)": "{:.0f}"}), use_container_width=True)

    sous_f = st.tabs([f"Flux annuels · {nom}" for nom in scenarios] + ["Pessimiste / Base / Optimiste"])
    for onglet, nom in zip(sous_f, scenarios):
        with onglet:
            _, fl_ = modele_annuel(nom)
            st.dataframe(fl_.set_index("Année").style.format("{:,.0f}"), use_container_width=True)
            long_f = fl_.melt("Année", value_vars=["Gain carburant", "Gain maintenance", "Marge nouveaux clients",
                                        "Approvisionnement nouveaux clients", "Exploitation dépôts", "Impôt"],
                              var_name="Poste", value_name="DA")
            st.altair_chart(alt.Chart(long_f).mark_bar().encode(
                x=alt.X("Année:O"), y=alt.Y("DA:Q"), color=alt.Color("Poste:N", scale=alt.Scale(
                    range=[TURQUOISE, MARINE, "#2E9E6B", "#C8553D", ORANGE, PRUNE])), tooltip=["Année", "Poste", "DA"]).properties(height=260),
                use_container_width=True)
    with sous_f[-1]:
        presets = {"Pessimiste": dict(pf=0.85, cf=1.10, af=1.20, vol=0.90, ex=1.20, inv=1.25, adopt=0.5),
                   "Base": {}, "Optimiste": dict(pf=1.15, cf=0.95, af=0.90, vol=1.10, ex=0.90, inv=0.90, adopt=1.4)}
        lp = []
        for nom in scenarios:
            for lib, kw in presets.items():
                cap_, fl_ = modele_annuel(nom, **kw)
                fl_l = fl_["Flux de trésorerie"].tolist()
                lp.append({"Scénario": nom, "Hypothèse": lib, "VAN après impôt (DA)": van_annuelle(cap_, fl_l, taux_a),
                           "TRI (%)": tri_flux(cap_, fl_l), "Délai (mois)": delai_mois(cap_, fl_l)})
        pres = pd.DataFrame(lp)
        st.dataframe(texte(pres, {"VAN après impôt (DA)": "{:,.0f}", "TRI (%)": "{:.1f}", "Délai (mois)": "{:.1f}"}),
                     use_container_width=True, hide_index=True)
        st.altair_chart(alt.Chart(pres).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
            x=alt.X("Hypothèse:N", sort=["Pessimiste", "Base", "Optimiste"], title=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y("VAN après impôt (DA):Q"), xOffset="Scénario:N",
            color=alt.Color("Scénario:N", scale=alt.Scale(domain=list(COULEURS_SCEN)[1:], range=list(COULEURS_SCEN.values())[1:])),
            tooltip=["Scénario", "Hypothèse", "VAN après impôt (DA)"]).properties(height=280), use_container_width=True)

    st.subheader("Classement multicritère (TOPSIS)")
    crit = {"VAN (DA)": ("max", 3), "Investissement (DA)": ("min", 2), "Coût logistique annuel (DA)": ("min", 3),
            "Distance annuelle A/R (km)": ("min", 2), "Nombre de dépôts": ("min", 1),
            "Tonnes supplémentaires / an": ("max", 2)}
    wc = st.columns(len(crit))
    poids = {k: w.slider(k, 0, 5, v[1], key=f"w_{k}") for w, (k, v) in zip(wc, crit.items())}
    alternatives = {"Actuel": {"VAN (DA)": 0.0, "Investissement (DA)": 0.0,
                               "Coût logistique annuel (DA)": comp_a[0] / periode * 12 + comp_a[1] / periode * 12,
                               "Distance annuelle A/R (km)": 2 * jeux["Actuel"]["dist_bellat"][commun].sum() / periode * 12,
                               "Nombre de dépôts": 1, "Tonnes supplémentaires / an": 0.0}}
    for nom in scenarios:
        r = indicateurs(nom)
        alternatives[nom] = {"VAN (DA)": r["van"], "Investissement (DA)": r["I"],
                             "Coût logistique annuel (DA)": base_f[nom]["transport_an"] + base_f[nom]["n"] * cout_depot * 12,
                             "Distance annuelle A/R (km)": base_f[nom]["dist_an"],
                             "Nombre de dépôts": 1 + base_f[nom]["n"],
                             "Tonnes supplémentaires / an": base_f[nom]["Tg"] * 12 if INCLURE_CROISSANCE else 0.0}
    X = pd.DataFrame(alternatives).T[list(crit)]
    W = pd.Series(poids, dtype=float)
    W = W / W.sum() if W.sum() > 0 else W + 1 / len(W)
    N_ = X / np.sqrt((X ** 2).sum()).replace(0, 1)
    V = N_ * W
    ideal = pd.Series({k: (V[k].max() if crit[k][0] == "max" else V[k].min()) for k in crit})
    pire = pd.Series({k: (V[k].min() if crit[k][0] == "max" else V[k].max()) for k in crit})
    d_plus = np.sqrt(((V - ideal) ** 2).sum(axis=1))
    d_moins = np.sqrt(((V - pire) ** 2).sum(axis=1))
    score = (d_moins / (d_plus + d_moins)).rename("Score TOPSIS")
    resultat = X.assign(**{"Score TOPSIS": score}).sort_values("Score TOPSIS", ascending=False)
    resultat["Rang"] = range(1, len(resultat) + 1)
    st.dataframe(resultat.style.format({"VAN (DA)": "{:,.0f}", "Investissement (DA)": "{:,.0f}",
                                        "Coût logistique annuel (DA)": "{:,.0f}", "Distance annuelle A/R (km)": "{:,.0f}",
                                        "Nombre de dépôts": "{:.0f}", "Tonnes supplémentaires / an": "{:,.0f}", "Score TOPSIS": "{:.3f}"}),
                 use_container_width=True)
    barres(score.sort_values(ascending=False), COULEURS_SCEN, titre_y="Score (0 à 1)")

with tab_carte:
    couleurs_depot = {"Centre existant": MARINE, "Sétif": TURQUOISE, "Relizane": PRUNE,
                      "Constantine": ORANGE, "Bordj Bou Arreridj": "#C8553D"}
    choix_carte = st.radio("Situation affichée", ["Actuel", "2 dépôts", "3 dépôts"], horizontal=True, key="carte",
                           format_func=lambda m: "Avant création des dépôts" if m == "Actuel" else f"Après création : {m}")
    cmap = {norm(r["Wilaya"]): (r["Latitude"], r["Longitude"]) for _, r in charger_coords().iterrows()}
    base_sc = scenarios["2 dépôts"].assign(servi_par="Centre existant") if choix_carte == "Actuel" else scenarios[choix_carte]
    lignes_c = []
    for _, r in base_sc.iterrows():
        k = norm(r["client"])
        if k in cmap and r["servi_par"] in DEPOTS:
            lignes_c.append({"client": r["client"], "depot": r["servi_par"], "q": float(r["Q_tonnes"]),
                             "lat": float(cmap[k][0]), "lon": float(cmap[k][1]), "dist": float(r["distance_km"])})
    cc = pd.DataFrame(lignes_c)
    depots_actifs = sorted(set(cc["depot"]) | {"Centre existant"}) if choix_carte != "Actuel" else ["Centre existant"]

    carte_tab, schema_tab = st.tabs(["🗺️ Carte OpenStreetMap", "📐 Schéma (sans internet)"])
    with carte_tab:
        try:
            import folium
            from streamlit.components.v1 import html as composant_html
            carte = folium.Map(location=[33.5, 3.0], zoom_start=6, tiles="OpenStreetMap", control_scale=True)
            centre_c = DEPOTS["Centre existant"]
            for _, r in cc.iterrows():
                col = couleurs_depot[r["depot"]]
                retrait = r["depot"] != "Centre existant"
                folium.PolyLine([DEPOTS[r["depot"]], (r["lat"], r["lon"])], color=col, weight=1.6, opacity=0.75,
                                dash_array="5,6" if retrait else None).add_to(carte)
                folium.CircleMarker((r["lat"], r["lon"]), radius=4 + (r["q"] ** 0.5) * 0.9, color=col, weight=1, fill=True,
                                    fill_color=col, fill_opacity=0.65,
                                    tooltip=f"{r['client']} · {r['q']:g} t · {CENTRE_LABEL if r['depot'] == 'Centre existant' else r['depot']} · {r['dist']:,.0f} km" +
                                            (" (retrait client)" if retrait else " (livré par Bellat)")).add_to(carte)
            if choix_carte != "Actuel":
                for d_ in depots_actifs:
                    if d_ != "Centre existant":
                        folium.PolyLine([centre_c, DEPOTS[d_]], color="#111111", weight=4, opacity=0.8,
                                        tooltip=f"Approvisionnement : Centre → {d_} ({dist_transfert.get(d_, 0):,.0f} km)").add_to(carte)
            for d_ in depots_actifs:
                col = couleurs_depot[d_]
                folium.CircleMarker(DEPOTS[d_], radius=13, color="white", weight=3, fill=True, fill_color=col,
                                    fill_opacity=1, tooltip=f"{CENTRE_LABEL if d_ == 'Centre existant' else 'Dépôt : ' + d_}").add_to(carte)
                folium.Marker(DEPOTS[d_], icon=folium.DivIcon(html=(
                    f"<div style='font-weight:700;font-size:13px;color:{col};text-shadow:1px 1px 2px white,-1px -1px 2px white;"
                    f"white-space:nowrap;margin-left:16px;margin-top:-26px'>{CENTRE_LABEL if d_ == 'Centre existant' else d_}</div>"))).add_to(carte)
            composant_html(carte.get_root().render(), height=680)
        except ImportError:
            st.error("La bibliothèque folium est absente. Installez-la avec : python -m pip install folium")
            points = pd.concat([cc[["lat", "lon"]], pd.DataFrame([{"lat": v[0], "lon": v[1]} for v in DEPOTS.values()])])
            st.map(points)


    with schema_tab:
        nom_aff = lambda d_: CENTRE_LABEL if d_ == "Centre existant" else d_
        domaine = [nom_aff(d_) for d_ in depots_actifs]
        palette_s = [couleurs_depot[d_] for d_ in depots_actifs]
        liens = cc.assign(Dépôt=cc["depot"].map(nom_aff), dlat=cc["depot"].map(lambda d_: DEPOTS[d_][0]),
                          dlon=cc["depot"].map(lambda d_: DEPOTS[d_][1]),
                          Mode=cc["depot"].map(lambda d_: "Livré par Bellat" if d_ == "Centre existant" else "Retrait par le client"))
        echelle = alt.Scale(domain=domaine, range=palette_s)
        axes = dict(x=alt.X("lon:Q", title="Longitude", scale=alt.Scale(zero=False)),
                    y=alt.Y("lat:Q", title="Latitude", scale=alt.Scale(zero=False)))
        segments = alt.Chart(liens).mark_rule(opacity=0.6, strokeWidth=1.5).encode(
            x="lon:Q", y="lat:Q", x2="dlon:Q", y2="dlat:Q", color=alt.Color("Dépôt:N", scale=echelle, legend=None),
            strokeDash=alt.StrokeDash("Mode:N", scale=alt.Scale(domain=["Livré par Bellat", "Retrait par le client"],
                                                                range=[[1, 0], [5, 4]]), legend=alt.Legend(title="Mode")))
        points = alt.Chart(liens).mark_circle(opacity=0.8).encode(
            **axes, size=alt.Size("q:Q", scale=alt.Scale(range=[40, 700]), legend=None),
            color=alt.Color("Dépôt:N", scale=echelle, legend=alt.Legend(title="Servi par")),
            tooltip=["client", "Dépôt", "q", "dist", "Mode"])
        dep_df = pd.DataFrame([{"Dépôt": nom_aff(d_), "lat": DEPOTS[d_][0], "lon": DEPOTS[d_][1]} for d_ in depots_actifs])
        marques = alt.Chart(dep_df).mark_point(shape="square", size=260, filled=True, stroke="white", strokeWidth=2).encode(
            x="lon:Q", y="lat:Q", color=alt.Color("Dépôt:N", scale=echelle, legend=None), tooltip=["Dépôt"])
        etiquettes = alt.Chart(dep_df).mark_text(dy=-16, fontWeight="bold", fontSize=12).encode(
            x="lon:Q", y="lat:Q", text="Dépôt:N", color=alt.Color("Dépôt:N", scale=echelle, legend=None))
        couches_s = [segments, points, marques, etiquettes]
        if choix_carte != "Actuel":
            appro = pd.DataFrame([{"lon": DEPOTS["Centre existant"][1], "lat": DEPOTS["Centre existant"][0],
                                   "dlon": DEPOTS[d_][1], "dlat": DEPOTS[d_][0], "Approvisionnement": d_}
                                  for d_ in depots_actifs if d_ != "Centre existant"])
            couches_s.insert(0, alt.Chart(appro).mark_rule(color="#111111", strokeWidth=4, opacity=0.85).encode(
                x="lon:Q", y="lat:Q", x2="dlon:Q", y2="dlat:Q", tooltip=["Approvisionnement"]))
        st.altair_chart(alt.layer(*couches_s).properties(height=640), use_container_width=True)

    leg = "  ".join(f"<span style='color:{couleurs_depot[n]};font-size:18px'>●</span> "
                    f"{CENTRE_LABEL if n == 'Centre existant' else n}" for n in depots_actifs)
    st.markdown(leg, unsafe_allow_html=True)
    if choix_carte != "Actuel":
        st.markdown("Trait plein : livraison par Bellat · Trait pointillé : le client retire ses produits au dépôt · "
                    "Trait noir épais : approvisionnement du dépôt depuis le centre d'expédition.")

with tab_export:
    tampon = io.BytesIO()
    dist_x, _ = distance_retenue(df)
    with pd.ExcelWriter(tampon, engine="openpyxl") as xl:
        df.assign(Heure_depart=df["Heure_depart"].map(lambda h: h.strftime("%H:%M"))).to_excel(xl, sheet_name="Livraisons", index=False)
        camions.to_excel(xl, sheet_name="Flotte", index=False)
        pd.concat([df[["ID", "Client", "Wilaya", "Type_camion"]], dist_x.rename("Distance_aller_km"),
                   calculer_couts(df, dist_x)], axis=1).to_excel(xl, sheet_name="Couts", index=False)
        osrm_x = charger_osrm()
        if not osrm_x.empty:
            osrm_x.to_excel(xl, sheet_name="OSRM", index=False)
        if "comparaison" in st.session_state:
            st.session_state["comparaison"].to_excel(xl, sheet_name="Comparaison")
    st.download_button("📥 Télécharger le classeur Excel complet", tampon.getvalue(), "bellat_complet.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
with tab_export:
    st.download_button("Télécharger les livraisons (CSV)",
                       df.to_csv(index=False).encode("utf-8-sig"), "livraisons_bellat.csv", "text/csv")
    st.download_button("Télécharger la flotte (CSV)",
                       camions.to_csv(index=False).encode("utf-8-sig"), "camions_bellat.csv", "text/csv")
    if st.button("♻️ Réinitialiser avec les données du document Word"):
        enregistrer_livraisons(construire_livraisons())
        enregistrer_camions(construire_camions())
        st.rerun()