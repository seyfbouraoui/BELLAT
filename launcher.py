"""
launcher.py — Point d'entrée de l'exécutable BELLAT.
Lance le serveur Streamlit dans un sous-processus et ouvre le navigateur.
"""

import os
import sys
import time
import threading
import subprocess
import webbrowser

# Lorsque PyInstaller empaquète l'application, les fichiers de données
# se trouvent dans sys._MEIPASS ; sinon, on utilise le répertoire courant.
if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
    # Le répertoire de travail doit pointer vers les CSV (à côté de l'exe)
    APP_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    APP_DIR = BASE_DIR

APP_PY = os.path.join(BASE_DIR, "app.py")
PORT = 8501
URL = f"http://localhost:{PORT}"


def ouvrir_navigateur():
    """Attend que Streamlit soit prêt, puis ouvre le navigateur."""
    time.sleep(4)
    webbrowser.open(URL)


def main():
    # Changer le répertoire de travail pour que les CSV soient trouvés
    os.chdir(APP_DIR)

    # Trouver streamlit dans le même environnement Python
    streamlit_exe = os.path.join(os.path.dirname(sys.executable), "streamlit.exe")
    if not os.path.exists(streamlit_exe):
        # Fallback : utiliser `python -m streamlit`
        cmd = [sys.executable, "-m", "streamlit", "run", APP_PY,
               "--server.port", str(PORT),
               "--server.headless", "true",
               "--browser.serverAddress", "localhost"]
    else:
        cmd = [streamlit_exe, "run", APP_PY,
               "--server.port", str(PORT),
               "--server.headless", "true",
               "--browser.serverAddress", "localhost"]

    # Ouvrir le navigateur dans un thread séparé
    t = threading.Thread(target=ouvrir_navigateur, daemon=True)
    t.start()

    # Lancer Streamlit (bloquant jusqu'à la fermeture de la fenêtre)
    proc = subprocess.Popen(cmd, cwd=APP_DIR)
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()


if __name__ == "__main__":
    main()
