"""
Mise en forme des fichiers points marquants compilant les incidents sur les ascenseurs et escaliers mécaniques

Victor Boulanger
# 2025-04-10
"""

# Importer les bibliothèques nécessaires
import pandas as pd
import os

# Définir le chemin du dossier contenant les fichiers Excel
folder_path = "points_marquants"

# Charger le dernier fichier Excel ajouté et fusionner les différentes feuilles
all_files = sorted(
    [
        os.path.join(folder_path, f)
        for f in os.listdir(folder_path)
        if f.endswith(".xlsx")
    ],
    key=os.path.getmtime,
    reverse=True,
)

if all_files:
    latest_file = all_files[0]
    excel_sheets = pd.ExcelFile(latest_file)
    all_files = [
        excel_sheets.parse(sheet_name) for sheet_name in excel_sheets.sheet_names
    ]
else:
    all_files = []

# Fusionner les fichiers Excel
merged_df = pd.concat([pd.read_excel(file) for file in all_files])

print(merged_df.head())

# Vérifier les noms de colonnes
expected_columns = ["LIGNE", "STATION", "N° EQUIP."]
if not all(column in merged_df.columns for column in expected_columns):
    raise KeyError(
        f"Les colonnes attendues ne sont pas toutes présentes dans les fichiers. Colonnes trouvées : {merged_df.columns}"
    )

# Identifier les événements prolongés
prolonged_events = merged_df[merged_df.duplicated(subset=expected_columns, keep=False)]
