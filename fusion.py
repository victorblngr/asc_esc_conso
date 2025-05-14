import pandas as pd
import os
import glob
import csv


def fusionner_csv(racine_dossier, fichier_sortie):
    """
    Fusionne un échantillon de fichiers CSV présents dans l'arborescence de dossiers,
    en conservant pour chaque 'Code équipement' et 'Début indispo' unique,
    la valeur maximale de 'Fin indispo'.

    Args:
        racine_dossier (str): Le chemin du dossier racine contenant tous les dossiers.
        fichier_sortie (str): Le nom du fichier CSV de sortie.
    """
    all_files = glob.glob(os.path.join(racine_dossier, "**", "*.csv"), recursive=True)

    list_of_dfs = []
    for f in all_files:
        print(f"Lecture du fichier : {f}")
        try:
            df = pd.read_csv(
                f,
                encoding="latin1",
                sep=";",
                escapechar="\\",
                quoting=csv.QUOTE_MINIMAL,
            )
            list_of_dfs.append(df)
        except pd.errors.ParserError as e:
            print(f"Erreur de parsing dans le fichier : {f}")
            print(f"Détails de l'erreur : {e}")
            continue  # Passer au fichier suivant en cas d'erreur

    if not list_of_dfs:
        print("Aucun fichier CSV n'a pu être lu correctement dans l'échantillon.")
        return

    concatenated_df = pd.concat(list_of_dfs, ignore_index=True)

    # Convertir la colonne 'Fin indispo' en datetime pour la comparaison
    concatenated_df["Fin indispo"] = pd.to_datetime(
        concatenated_df["Fin indispo"], errors="coerce"
    )
    concatenated_df["Début indispo"] = pd.to_datetime(
        concatenated_df["Début indispo"], errors="coerce"
    )

    # Grouper par 'Code équipement' et 'Début indispo' et prendre la date de fin max
    df_merged = concatenated_df.groupby(
        ["Code équipement", "Début indispo"], as_index=False
    ).agg(
        {
            "Code lieu": "first",
            "Code station": "first",
            "Nom station": "first",
            "Code équipement": "first",
            "Type équipement": "first",
            "Equipement": "first",
            "Cause": "first",
            "Conséquence": "first",
            "Fin indispo": "max",
        }
    )

    # Formatter la colonne 'Fin indispo' comme dans le fichier d'origine (si nécessaire)
    df_merged["Fin indispo"] = df_merged["Fin indispo"].dt.strftime("%d/%m/%Y %H:%M:%S")

    df_merged.to_csv(fichier_sortie, index=False)
    print(
        f"L'échantillon de fichiers CSV a été fusionné et enregistré dans : {fichier_sortie}"
    )


racine_dossier = r"C:\Users\VBO\code\asc_esc_consolide\extracted_zip_contents"
fichier_sortie = "fichier_fusionne_echantillon.csv"

if __name__ == "__main__":
    fusionner_csv(racine_dossier, fichier_sortie)
