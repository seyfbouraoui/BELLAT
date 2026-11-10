# bellat.spec
# Fichier de spécification PyInstaller pour BELLAT Optimisation Dépôts
# Usage : pyinstaller bellat.spec

import os
from PyInstaller.utils.hooks import collect_data_files, collect_all

block_cipher = None

SP = r"C:\Users\admin\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.13_qbz5n2kfra8p0\LocalCache\local-packages\Python313\site-packages"

# Collecter les données nécessaires pour Streamlit et ses dépendances
datas = []
datas += collect_data_files("streamlit")
datas += collect_data_files("altair")
datas += collect_data_files("pandas")
datas += collect_data_files("numpy")
datas += collect_data_files("pyarrow")

# Inclure app.py et les CSV dans le bundle
datas += [
    (r"app.py",                      "."),
    (r"camions.csv",                 "."),
    (r"livraisons.csv",              "."),
    (r"coordonnees_wilayas.csv",     "."),
]

# Masquer les imports non détectés automatiquement
hiddenimports = [
    "streamlit",
    "streamlit.web.cli",
    "streamlit.runtime.scriptrunner.magic_funcs",
    "altair",
    "pandas",
    "numpy",
    "pyarrow",
    "click",
    "toml",
    "tomli",
    "packaging",
    "importlib_metadata",
    "jinja2",
    "markupsafe",
    "watchdog",
    "tornado",
    "pydeck",
    "validators",
    "blinker",
    "cachetools",
    "rich",
    "gitpython",
    "gitdb",
    "tzdata",
    "unicodedata",
    "urllib.request",
    "json",
    "pathlib",
    "datetime",
    "io",
    "math",
    "threading",
    "webbrowser",
    "subprocess",
]

a = Analysis(
    [r"launcher.py"],
    pathex=[r"C:\Users\admin\Desktop\Bellat_Optimisation_Depots"],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "matplotlib", "scipy", "PIL", "tkinter", "unittest",
        "xmlrpc", "distutils", "email", "html", "http.server",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="BELLAT",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,      # Pas de fenêtre console noire
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,          # Remplacez par le chemin vers une icône .ico si disponible
    version=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="BELLAT",
)
