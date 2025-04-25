# %%Import des libraires
import streamlit as st
import pandas as pd
import datetime as dt
import plotly.express as px
import matplotlib.pyplot as plt
import re
import os

# %% Load data
file_path = os.path.join(
    os.getcwd(), "points_marquants", "Points marquants maintenance 2024.xlsx"
)
if not os.path.exists(file_path):
    st.error(f"File not found: {file_path}")
    st.stop()
df = pd.read_excel(file_path)

# %% Manipulation données
# Filtrer les colonnes
df = df[
    [
        "DATE Début",
        "HEURE Début",
        "DATE Fin",
        "HEURE Fin",
        "Durée indispo (j) totale",
        "LIGNE",
        "STATION",
        "N° EQUIP.",
        "COMMENTAIRE",
        "Motifs",
    ]
]

df.rename(
    columns={
        "DATE Début": "date_debut_panne",
        "HEURE Début": "heure_debut_panne",
        "DATE Fin": "date_fin_panne",
        "HEURE Fin": "heure_fin_panne",
        "Durée indispo (j) totale": "nb_jours_indispo",
        "LIGNE": "ligne",
        "STATION": "station",
        "N° EQUIP.": "num_equip",
        "COMMENTAIRE": "commentaire",
        "Motifs": "motifs",
    },
    inplace=True,
)

# Convertir les colonnes de date au format dd/mm/yyyy
df["date_debut_panne"] = pd.to_datetime(df["date_debut_panne"]).dt.strftime("%d/%m/%Y")
df["date_fin_panne"] = pd.to_datetime(df["date_fin_panne"]).dt.strftime("%d/%m/%Y")


# Convertir les colonnes de temps au format HH:MM
def convert_time_format(time_str):
    if isinstance(time_str, str):
        time_str = time_str.replace("h", ":").replace("H", ":")
        if ":" in time_str and len(time_str.split(":")[1]) == 0:
            time_str += "00"
    return time_str


df["heure_debut_panne"] = df["heure_debut_panne"].apply(convert_time_format)
df["heure_fin_panne"] = df["heure_fin_panne"].apply(convert_time_format)

# Créer colonne type_equipement
df["type_equipement"] = (
    df["num_equip"].str.startswith("Asc").map({True: "ascenseur", False: "escalier"})
)

# Créer une colonne annee_debut_panne
df["annee_debut_panne"] = pd.to_datetime(
    df["date_debut_panne"], format="%d/%m/%Y"
).dt.year


# Calculer la durée d'indisponibilité en heures et jours
def calculate_duration(row):
    try:
        start = pd.to_datetime(
            f"{row['date_debut_panne']} {row['heure_debut_panne']}",
            format="%d/%m/%Y %H:%M",
        )
        end = pd.to_datetime(
            f"{row['date_fin_panne']} {row['heure_fin_panne']}", format="%d/%m/%Y %H:%M"
        )
        duration = (end - start).total_seconds() / 3600  # Convertir en heures
        return duration, duration / 24  # Retourner heures et jours
    except Exception:
        return None, None


df[["duree_indispo", "jour_indispo"]] = df.apply(
    calculate_duration, axis=1, result_type="expand"
)

# Replace 'T1 ' with 'T1' in the 'ligne' column
df["ligne"] = df["ligne"].str.replace("T1 ", "T1", regex=False)

# Extract integers from the 'num_equip' column and create a new column 'id'
df["id"] = (
    df["num_equip"].str.extract(r"(\d+)").astype(float)
)  # Use raw string for regex

# %% Streamlit app
# Page configuration
st.set_page_config(
    page_title="Ascenseurs et Escaliers Mécaniques",
    layout="wide",
    initial_sidebar_state="expanded",
)

with st.sidebar:
    st.title("Tableau de bord ascenseurs et escaliers mécaniques")

    # Select multiple years
    year_list = list(df.annee_debut_panne.unique())

    selected_years = st.multiselect(
        "Sélectionner une ou plusieurs années", year_list, default=year_list
    )

    df_selected_year = df[df.annee_debut_panne.isin(selected_years)]

    options = st.sidebar.radio(
        "Navigation :",
        [
            "Données",
            "Indisponibilités par mois",
            "Typologie des indisponibilités",
            "Indisponibilités par ligne",
            "Indisponibilités par station",
            "Indisponibilités par équipement",
            "Patrimoine",
            "Croisement données",
            "Scraping",
        ],
    )

# %% Fichier patrimoine
file_path = os.path.join(os.getcwd(), "patrimoine", "asc_esc_caracteristiques2.xlsx")
if not os.path.exists(file_path):
    st.error(f"File not found: {file_path}")
    st.stop()
df2 = pd.read_excel(file_path)

# Ensure proper data type conversion for Arrow compatibility
if "modernisation" in df2.columns:
    df2["modernisation"] = pd.to_numeric(df2["modernisation"], errors="coerce")

# Replace 'int' with 'Int' in df2['situation'] if applicable
df2["situation"] = df2["situation"].str.replace("int", "Int", regex=False)

# %% Merge dataframes
df_merged = pd.merge(df_selected_year, df2, how="inner", left_on="id", right_on="id")

# %% Onglet 1 : Données
if options == "Données":
    st.title("Données")
    st.write(
        "Cette application a pour but d'exploiter les fichiers de points marquants "
        "et de les croiser avec les caractéristiques des ascenseurs et escaliers."
    )
    st.write(
        "Le fichier de points marquants contient des informations sur les incidents "
        "et les maintenances des équipements."
    )
    st.write(
        "Le fichier de caractéristiques contient des informations sur les équipements "
        "et leurs caractéristiques techniques."
    )

    st.subheader(
        f"Données fichiers points marquants entre le {df_selected_year['date_debut_panne'].min()} et le {df_selected_year['date_fin_panne'].max()}"
    )

    st.dataframe(df_selected_year, use_container_width=True)

    st.subheader("Données avec une heure de début et de fin d'indisponibilité")
    total_indisponibilites = df.shape[0]
    with_hours = df[df["duree_indispo"].notnull()].shape[0]
    percentage_with_hours = (with_hours / total_indisponibilites) * 100

    st.write(
        f"Sur {total_indisponibilites} indisponibilités, {with_hours} disposent d'une heure de début et de fin ({percentage_with_hours:.2f}%)."
    )

# %% Onglet 1 bis : Indisponibilités par mois
if options == "Indisponibilités par mois":
    st.title("Indisponibilités par mois")
    st.write(
        "Ajouter graphique de la répartition des indisponibilités par mois avec sélecteur période temporelle, ligne, type d'équipement"
    )

    df_filtered = df_selected_year[df_selected_year["duree_indispo"].notnull()]
    df_filtered["mois"] = pd.to_datetime(df_filtered["date_debut_panne"]).dt.month()
    df_grouped = df_filtered.groupby("mois")["duree_indispo"].sum().reset_index()

    # Multiselect mois
    mois_list = st.multiselect(
        "Sélectionner un ou plusieurs mois",
        df_filtered["mois"].unique(),
        default=df_filtered["mois"].unique(),
    )

    # multiselect ligne
    ligne_list = st.multiselect(
        "Sélectionner une ou plusieurs lignes",
        df_filtered["ligne"].unique(),
        default=df_filtered["ligne"].unique(),
    )

    # Multiselect type d'équipement
    type_equipement_list = st.multiselect(
        "Sélectionner un ou plusieurs types d'équipement",
        df_filtered["type_equipement"].unique(),
        default=df_filtered["type_equipement"].unique(),
    )

    # Plot the data
    fig = px.bar(
        df_grouped,
        x="mois",
        y="duree_indispo",
        title="Durée totale d'indisponibilités par mois",
        labels={"mois": "Mois", "duree_indispo": "Durée totale (heures)"},
        category_orders={"mois": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]},
        color_discrete_sequence=["#636EFA"],
    )
    st.plotly_chart(fig)

# %% Onglet 2 : Typologie des indisponibilités
if options == "Typologie des indisponibilités":
    st.title("Typologie des indisponibilités")

    st.write(
        f"Données fichiers points marquants entre le {df_selected_year['date_debut_panne'].min()} et le {df_selected_year['date_fin_panne'].max()}"
    )

    # %% Travail en nombre d'indisponibilités
    st.subheader("Analyses en nombre d'indisponibilités")

    st.write(
        "**Lecture des graphiques :** à gauche on conserve l'ensemble des données,"
        " à droite on filtre les données pour ne garder que celles avec une durée d'indisponibilité non nulle i.e. "
        "disposant d'une heure de début et de fin d'indisponibilité."
    )

    st.markdown(
        "<span style='color:red; font-weight:bold;'>Attention problèmes matching couleurs pie charts</span>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        df_grouped = (
            df_selected_year.groupby("motifs", dropna=False)
            .size()
            .reset_index(name="count")
            .sort_values(by="count", ascending=False)
        )

        # Replace NaN values in 'motifs' with a label for better visualization
        df_grouped["motifs"] = df_grouped["motifs"].fillna("Non spécifié")

        fig = px.bar(
            df_grouped,
            x="motifs",
            y="count",
            title="Données brutes",
            labels={"motifs": "Motif", "count": "Nombre d'indisponibilités"},
        )
        fig.update_layout(xaxis_title="Motif", yaxis_title=None)
        fig

    with col2:
        fig = px.pie(
            df_grouped,
            names="motifs",
            values="count",
            labels={"motifs": "Motif", "count": "Nombre d'indisponibilités"},
        )
        fig.update_traces(textinfo="percent+label")
        fig

    col1, col2 = st.columns(2)

    with col1:
        # Filter the dataframe to keep only the rows with non-null duration
        df_filtered = df_selected_year[df_selected_year["duree_indispo"].notnull()]
        df_grouped = (
            df_filtered.groupby("motifs", dropna=False)
            .size()
            .reset_index(name="count")
            .sort_values(by="count", ascending=False)
        )

        # Replace NaN values in 'motifs' with a label for better visualization
        df_grouped["motifs"] = df_grouped["motifs"].fillna("Non spécifié")

        fig = px.bar(
            df_grouped,
            x="motifs",
            y="count",
            title="Données filtrées",
            labels={"motifs": "Motif", "count": "Nombre d'indisponibilités"},
        )
        fig.update_layout(xaxis_title="Motif", yaxis_title=None)
        fig

    with col2:
        fig = px.pie(
            df_grouped,
            names="motifs",
            values="count",
            labels={"motifs": "Motif", "count": "Nombre d'indisponibilités"},
        )
        fig.update_traces(textinfo="percent+label")
        fig

    # %% Travail en heures d'indisponibilités
    st.subheader("Analyses en heure d'indisponibilités")

    df_filtered = df_selected_year[df_selected_year["duree_indispo"].notnull()]

    # Replace None values in 'motifs' with "non spécifié"
    df_filtered["motifs"] = df_filtered["motifs"].fillna("Non spécifié")

    df_grouped = (
        df_filtered.groupby("motifs")["duree_indispo"]
        .sum()
        .reset_index(name="count")
        .sort_values(by="count", ascending=False)
    )

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(
            df_grouped,
            x="motifs",
            y="count",
            title="Durée d'indisponibilités par motif (h)",
            labels={"motifs": "Motif", "count": "Heures d'indisponibilités"},
        )
        fig.update_layout(xaxis_title="Motif", yaxis_title="Durée (h)")
        st.plotly_chart(fig)

    with col2:
        fig = px.pie(
            df_grouped,
            names="motifs",
            values="count",
            labels={"motifs": "Motif", "count": "Heures d'indisponibilités"},
        )
        fig.update_traces(textinfo="percent+label")
        fig


# %% Onglet 3 : Indisponibilités par ligne
if options == "Indisponibilités par ligne":
    st.title("Indisponibilités par ligne")

    st.write(
        f"Données fichiers points marquants entre le {df_selected_year['date_debut_panne'].min()} et le {df_selected_year['date_fin_panne'].max()}"
    )

    # %% Travail en nombre d'indisponibilités
    st.subheader("Analyses en nombre d'indisponibilités")

    st.write(
        "**Lecture des graphiques :** à gauche on conserve l'ensemble des données,"
        " à droite on filtre les données pour ne garder que celles avec une durée d'indisponibilité non nulle i.e. "
        "disposant d'une heure de début et de fin d'indisponibilité."
    )

    st.markdown(
        "<span style='color:red; font-weight:bold;'>Attention code couleur des lignes à rajouter</span>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        df_grouped = (
            df_selected_year.groupby("ligne", dropna=False)
            .size()
            .reset_index(name="count")
            .sort_values(by="count", ascending=False)
        )

        # Replace NaN values in 'motifs' with a label for better visualization
        df_grouped["ligne"] = df_grouped["ligne"].fillna("Non spécifié")

        fig = px.bar(
            df_grouped,
            x="ligne",
            y="count",
            title="Données brutes",
            labels={"ligne": "Ligne", "count": "Nombre d'indisponibilités"},
        )
        fig.update_layout(xaxis_title="Ligne", yaxis_title=None)
        fig

    with col2:
        fig = px.pie(
            df_grouped,
            names="ligne",
            values="count",
            labels={"ligne": "Ligne", "count": "Nombre d'indisponibilités"},
        )
        fig.update_traces(textinfo="percent+label")
        fig

    col1, col2 = st.columns(2)

    with col1:
        # Filter the dataframe to keep only the rows with non-null duration
        df_filtered = df_selected_year[df_selected_year["duree_indispo"].notnull()]
        df_grouped = (
            df_filtered.groupby("ligne", dropna=False)
            .size()
            .reset_index(name="count")
            .sort_values(by="count", ascending=False)
        )

        # Replace NaN values in 'motifs' with a label for better visualization
        df_grouped["ligne"] = df_grouped["ligne"].fillna("Non spécifié")

        fig = px.bar(
            df_grouped,
            x="ligne",
            y="count",
            title="Données filtrées",
            labels={"ligne": "Ligne", "count": "Nombre d'indisponibilités"},
        )
        fig.update_layout(xaxis_title="Motif", yaxis_title=None)
        fig

    with col2:
        fig = px.pie(
            df_grouped,
            names="ligne",
            values="count",
            labels={"ligne": "Ligne", "count": "Nombre d'indisponibilités"},
        )
        fig.update_traces(textinfo="percent+label")
        fig

    # %% Travail en heures d'indisponibilités²
    st.subheader("Analyses en heures d'indisponibilités")

    df_filtered = df_selected_year[df_selected_year["duree_indispo"].notnull()]

    # Replace None values in 'ligne' with "non spécifié"
    df_filtered["ligne"] = df_filtered["ligne"].fillna("Non spécifié")

    df_grouped = (
        df_filtered.groupby("ligne")["duree_indispo"]
        .sum()
        .reset_index(name="count")
        .sort_values(by="count", ascending=False)
    )

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(
            df_grouped,
            x="ligne",
            y="count",
            title="Durée d'indisponibilités par ligne - données non filtrées",
            labels={"ligne": "Ligne", "count": "Heures d'indisponibilités"},
        )
        fig.update_layout(xaxis_title="Ligne", yaxis_title="Durée (h)")
        st.plotly_chart(fig)

    with col2:
        fig = px.pie(
            df_grouped,
            names="ligne",
            values="count",
            labels={"ligne": "Ligne", "count": "Heures d'indisponibilités"},
        )
        fig.update_traces(textinfo="percent+label")
        fig

    col1, col2 = st.columns(2)

    df_filtered = df_selected_year[df_selected_year["duree_indispo"].notnull()]

    q75 = df_filtered["duree_indispo"].quantile(0.75)

    df_filtered = df_filtered[df_filtered["duree_indispo"] <= q75]

    # Replace None values in 'ligne' with "non spécifié"
    df_filtered["ligne"] = df_filtered["ligne"].fillna("Non spécifié")

    df_grouped = (
        df_filtered.groupby("ligne")["duree_indispo"]
        .sum()
        .reset_index(name="count")
        .sort_values(by="count", ascending=False)
    )

    with col1:
        fig = px.bar(
            df_grouped,
            x="ligne",
            y="count",
            title="Durée d'indisponibilités par ligne - données filtrées",
            labels={"ligne": "Ligne", "count": "Heures d'indisponibilités"},
        )
        fig.update_layout(xaxis_title="Ligne", yaxis_title="Durée (h)")
        st.plotly_chart(fig)

    with col2:
        fig = px.pie(
            df_grouped,
            names="ligne",
            values="count",
            labels={"ligne": "Ligne", "count": "Heures d'indisponibilités"},
        )
        fig.update_traces(textinfo="percent+label")
        fig

# %% Onglet 3 : Indisponibilités par station
if options == "Indisponibilités par station":
    st.title("Indisponibilités par station")

    st.write(
        f"Données fichiers points marquants entre le {df_selected_year['date_debut_panne'].min()} et le {df_selected_year['date_fin_panne'].max()}"
    )

    # %% Analyses en nombre d'indisponibilités
    st.subheader("Analyses en nombre d'indisponibilités")

    st.write(
        "**Lecture des graphiques :** à gauche on conserve l'ensemble des données,"
        " à droite on filtre les données pour ne garder que celles avec une durée d'indisponibilité non nulle i.e. "
        "disposant d'une heure de début et de fin d'indisponibilité."
    )

    st.markdown(
        "<span style='color:red; font-weight:bold;'>Blabla éventuel</span>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        df_grouped = (
            df_selected_year.groupby(["station", "ligne"], dropna=False)
            .size()
            .reset_index(name="count")
        )

        # Replace NaN values in 'station' and 'ligne' with a label for better visualization
        df_grouped["station"] = df_grouped["station"].fillna("Non spécifié")
        df_grouped["ligne"] = df_grouped["ligne"].fillna("Non spécifié")

        fig = px.bar(
            df_grouped,
            x="station",
            y="count",
            color="ligne",
            title="Données brutes",
            labels={
                "station": "Station",
                "count": "Nombre d'indisponibilités",
                "ligne": "Ligne",
            },
        )
        fig.update_layout(xaxis_title="Station", yaxis_title=None, xaxis_tickangle=-45)
        fig

    with col2:
        # Filter the dataframe to keep only the rows with non-null duration
        df_filtered = df_selected_year[df_selected_year["duree_indispo"].notnull()]
        df_grouped = (
            df_filtered.groupby(["station", "ligne"], dropna=False)
            .size()
            .reset_index(name="count")
        )

        # Replace NaN values in 'station' and 'ligne' with a label for better visualization
        df_grouped["station"] = df_grouped["station"].fillna("Non spécifié")
        df_grouped["ligne"] = df_grouped["ligne"].fillna("Non spécifié")

        fig = px.bar(
            df_grouped,
            x="station",
            y="count",
            color="ligne",
            title="Données filtrées",
            labels={
                "station": "Station",
                "count": "Nombre d'indisponibilités",
                "ligne": "Ligne",
            },
        )
        fig.update_layout(
            xaxis_title="Station", yaxis_title=None, xaxis_tickangle=-45
        )  # Rotate x-axis labels
        fig
    # %% Travail en heures d'indisponibilités
    st.subheader("Analyses en heures d'indisponibilités")

    df_filtered = df_selected_year[df_selected_year["duree_indispo"].notnull()]

    # Replace None values in 'station' with "non spécifié"
    df_filtered["station"] = df_filtered["station"].fillna("Non spécifié")
    df_filtered["ligne"] = df_filtered["ligne"].fillna("Non spécifié")

    df_grouped = (
        df_filtered.groupby(["station", "ligne"])["duree_indispo"]
        .sum()
        .reset_index(name="count")
    )

    q75 = df_filtered["duree_indispo"].quantile(0.75)

    st.write(
        f"Parmi l'ensemble des indisponibilités avec une heure de début et de fin, 75% durent : **{q75:.2f} heures** ou moins."
    )
    st.write(
        f"On filtrera les données pour ne garder que celles avec une durée d'indisponibilité inférieure à {q75:.2f} heures."
    )

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(
            df_grouped,
            x="station",
            y="count",
            color="ligne",
            title="Durée d'indisponibilités par station - données non filtrées",
            labels={"station": "Station", "count": "Heures d'indisponibilités"},
        )
        fig.update_layout(xaxis_title="Station", yaxis_title="Durée (h)")
        st.plotly_chart(fig)

    with col2:
        df_filtered = df_selected_year[df_selected_year["duree_indispo"].notnull()]
        df_filtered = df_filtered[df_filtered["duree_indispo"] <= q75]

        # Replace None values in 'station' with "non spécifié"
        df_filtered["station"] = df_filtered["station"].fillna("Non spécifié")
        df_filtered["ligne"] = df_filtered["ligne"].fillna("Non spécifié")

        df_grouped = (
            df_filtered.groupby(["station", "ligne"])["duree_indispo"]
            .sum()
            .reset_index(name="count")
        )

        fig = px.bar(
            df_grouped,
            x="station",
            y="count",
            color="ligne",
            title="Durée d'indisponibilités par station - données filtrées",
            labels={"station": "Station", "count": "Heures d'indisponibilités"},
        )
        fig.update_layout(xaxis_title="Station", yaxis_title="Durée (h)")
        st.plotly_chart(fig)


# %% Onglet 4 : Indisponibilités par équipement
if options == "Indisponibilités par équipement":
    st.title("Indisponibilités par équipement")

    st.write(
        f"Données fichiers points marquants entre le {df_selected_year['date_debut_panne'].min()} et le {df_selected_year['date_fin_panne'].max()}"
    )

    # %% Analyses en nombre d'indisponibilités
    st.header("Analyses en nombre d'indisponibilités")

    st.write(
        "**Lecture des graphiques :** à gauche on conserve l'ensemble des données,"
        " à droite on filtre les données pour ne garder que celles avec une durée d'indisponibilité non nulle i.e. "
        "disposant d'une heure de début et de fin d'indisponibilité."
    )

    st.markdown(
        "<span style='color:red; font-weight:bold;'>Blabla éventuel</span>",
        unsafe_allow_html=True,
    )

    st.subheader("Tout équipement confondu")

    col1, col2 = st.columns(2)

    with col1:
        df_grouped = (
            df_selected_year.groupby(["num_equip", "ligne"], dropna=False)
            .size()
            .reset_index(name="count")
        )

        # Replace NaN values in 'station' and 'ligne' with a label for better visualization
        df_grouped["num_equip"] = df_grouped["num_equip"].fillna("Non spécifié")
        df_grouped["ligne"] = df_grouped["ligne"].fillna("Non spécifié")

        fig = px.bar(
            df_grouped,
            x="num_equip",
            y="count",
            color="ligne",
            title="Données brutes",
            labels={
                "num_equip": "Numéro d'équipement",
                "count": "Nombre d'indisponibilités",
                "ligne": "Ligne",
            },
        )
        fig.update_layout(
            xaxis_title="Numéro d'équipement",
            yaxis_title=None,
            xaxis_tickangle=-45,  # Rotate x-axis labels
        )
        fig

    with col2:
        # Filter the dataframe to keep only the rows with non-null duration
        df_filtered = df_selected_year[df_selected_year["duree_indispo"].notnull()]

        df_grouped = (
            df_filtered.groupby(["num_equip", "ligne"], dropna=False)
            .size()
            .reset_index(name="count")
        )

        # Replace NaN values in 'station' and 'ligne' with a label for better visualization
        df_grouped["num_equip"] = df_grouped["num_equip"].fillna("Non spécifié")
        df_grouped["ligne"] = df_grouped["ligne"].fillna("Non spécifié")

        fig = px.bar(
            df_grouped,
            x="num_equip",
            y="count",
            color="ligne",
            title="Données filtrées",
            labels={
                "num_equip": "Numéro d'équipement",
                "count": "Nombre d'indisponibilités",
                "ligne": "Ligne",
            },
        )

        fig.update_layout(
            xaxis_title="Numéro d'équipement",
            yaxis_title=None,
            xaxis_tickangle=-45,  # Rotate x-axis labels
        )
        fig

    st.subheader("Ascenseurs")

    col1, col2 = st.columns(2)

    with col1:
        df_asc = df_selected_year[df_selected_year["type_equipement"] == "ascenseur"]

        df_grouped = (
            df_asc.groupby(["num_equip", "ligne"], dropna=False)
            .size()
            .reset_index(name="count")
        )

        # Replace NaN values in 'station' and 'ligne' with a label for better visualization
        df_grouped["num_equip"] = df_grouped["num_equip"].fillna("Non spécifié")
        df_grouped["ligne"] = df_grouped["ligne"].fillna("Non spécifié")

        fig = px.bar(
            df_grouped,
            x="num_equip",
            y="count",
            color="ligne",
            title="Données brutes",
            labels={
                "num_equip": "Numéro d'équipement",
                "count": "Nombre d'indisponibilités",
                "ligne": "Ligne",
            },
        )
        fig.update_layout(
            xaxis_title="Numéro d'équipement",
            yaxis_title=None,
            xaxis_tickangle=-45,  # Rotate x-axis labels
        )
        fig

    with col2:
        # Filter the dataframe to keep only the rows with non-null duration
        df_filtered = df_selected_year[df_selected_year["duree_indispo"].notnull()]
        df_filtered = df_filtered[df_filtered["type_equipement"] == "ascenseur"]

        df_grouped = (
            df_filtered.groupby(["num_equip", "ligne"], dropna=False)
            .size()
            .reset_index(name="count")
        )

        # Replace NaN values in 'station' and 'ligne' with a label for better visualization
        df_grouped["num_equip"] = df_grouped["num_equip"].fillna("Non spécifié")
        df_grouped["ligne"] = df_grouped["ligne"].fillna("Non spécifié")

        fig = px.bar(
            df_grouped,
            x="num_equip",
            y="count",
            color="ligne",
            title="Données filtrées",
            labels={
                "num_equip": "Numéro d'équipement",
                "count": "Nombre d'indisponibilités",
                "ligne": "Ligne",
            },
        )

        fig.update_layout(
            xaxis_title="Numéro d'équipement",
            yaxis_title=None,
            xaxis_tickangle=-45,  # Rotate x-axis labels
        )
        fig

    st.subheader("Escaliers")

    col1, col2 = st.columns(2)

    with col1:
        df_esc = df_selected_year[df_selected_year["type_equipement"] == "escalier"]

        df_grouped = (
            df_esc.groupby(["num_equip", "ligne"], dropna=False)
            .size()
            .reset_index(name="count")
        )

        # Replace NaN values in 'station' and 'ligne' with a label for better visualization
        df_grouped["num_equip"] = df_grouped["num_equip"].fillna("Non spécifié")
        df_grouped["ligne"] = df_grouped["ligne"].fillna("Non spécifié")

        fig = px.bar(
            df_grouped,
            x="num_equip",
            y="count",
            color="ligne",
            title="Escaliers - Données brutes",
            labels={
                "num_equip": "Numéro d'équipement",
                "count": "Nombre d'indisponibilités",
                "ligne": "Ligne",
            },
        )
        fig.update_layout(
            xaxis_title="Numéro d'équipement",
            yaxis_title=None,
            xaxis_tickangle=-45,  # Rotate x-axis labels
        )
        fig

    with col2:
        # Filter the dataframe to keep only the rows with non-null duration
        df_filtered = df_selected_year[df_selected_year["duree_indispo"].notnull()]
        df_filtered = df_filtered[df_filtered["type_equipement"] == "escalier"]

        df_grouped = (
            df_filtered.groupby(["num_equip", "ligne"], dropna=False)
            .size()
            .reset_index(name="count")
        )

        # Replace NaN values in 'station' and 'ligne' with a label for better visualization
        df_grouped["num_equip"] = df_grouped["num_equip"].fillna("Non spécifié")
        df_grouped["ligne"] = df_grouped["ligne"].fillna("Non spécifié")

        fig = px.bar(
            df_grouped,
            x="num_equip",
            y="count",
            color="ligne",
            title="Escaliers - Données filtrées",
            labels={
                "num_equip": "Numéro d'équipement",
                "count": "Nombre d'indisponibilités",
                "ligne": "Ligne",
            },
        )

        fig.update_layout(
            xaxis_title="Numéro d'équipement",
            yaxis_title=None,
            xaxis_tickangle=-45,  # Rotate x-axis labels
        )
        fig

    # %% Travail en heures d'indisponibilités
    st.header("Travail en heures d'indisponibilités")
    st.subheader("Tout équipement confondu")

    df_filtered = df_selected_year[df_selected_year["duree_indispo"].notnull()]

    # Replace None values in 'station' with "non spécifié"
    df_filtered["num_equip"] = df_filtered["num_equip"].fillna("Non spécifié")
    df_filtered["ligne"] = df_filtered["ligne"].fillna("Non spécifié")

    df_grouped = (
        df_filtered.groupby(["num_equip", "ligne"])["duree_indispo"]
        .sum()
        .reset_index(name="count")
    )

    q75 = df_filtered["duree_indispo"].quantile(0.75)

    st.write(
        f"Parmi l'ensemble des indisponibilités avec une heure de début et de fin, 75% durent : **{q75:.2f} heures** ou moins."
    )
    st.write(
        f"On filtrera les données pour ne garder que celles avec une durée d'indisponibilité inférieure à {q75:.2f} heures."
    )

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(
            df_grouped,
            x="num_equip",
            y="count",
            color="ligne",
            title="Durée d'indisponibilités par équipement - données non filtrées",
            labels={
                "num_equip": "Numéro d'équipement",
                "count": "Heures d'indisponibilités",
            },
        )
        fig.update_layout(
            xaxis_title="Numéro d'équipement",
            yaxis_title="Durée (h)",
            xaxis_tickangle=-45,
        )
        st.plotly_chart(fig)

    with col2:
        df_filtered = df_selected_year[df_selected_year["duree_indispo"].notnull()]
        df_filtered = df_filtered[df_filtered["duree_indispo"] <= q75]

        # Replace None values in 'station' with "non spécifié"
        df_filtered["num_equip"] = df_filtered["num_equip"].fillna("Non spécifié")
        df_filtered["ligne"] = df_filtered["ligne"].fillna("Non spécifié")

        df_grouped = (
            df_filtered.groupby(["num_equip", "ligne"])["duree_indispo"]
            .sum()
            .reset_index(name="count")
        )

        fig = px.bar(
            df_grouped,
            x="num_equip",
            y="count",
            color="ligne",
            title="Durée d'indisponibilités par équipement - données filtrées",
            labels={
                "num_equip": "Numéro d'équipement",
                "count": "Heures d'indisponibilités",
            },
        )
        fig.update_layout(
            xaxis_title="Numéro d'équipement",
            yaxis_title="Durée (h)",
            xaxis_tickangle=-45,
        )
        st.plotly_chart(fig)

    st.subheader("Ascenseurs")

    df_filtered = df_selected_year[df_selected_year["duree_indispo"].notnull()]
    df_filtered = df_filtered[df_filtered["type_equipement"] == "ascenseur"]

    # Replace None values in 'station' with "non spécifié"
    df_filtered["num_equip"] = df_filtered["num_equip"].fillna("Non spécifié")
    df_filtered["ligne"] = df_filtered["ligne"].fillna("Non spécifié")

    df_grouped = (
        df_filtered.groupby(["num_equip", "ligne"])["duree_indispo"]
        .sum()
        .reset_index(name="count")
    )

    q75 = df_filtered["duree_indispo"].quantile(0.75)

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(
            df_grouped,
            x="num_equip",
            y="count",
            color="ligne",
            title="Durée d'indisponibilités par équipement - données non filtrées",
            labels={
                "num_equip": "Numéro d'équipement",
                "count": "Heures d'indisponibilités",
            },
        )
        fig.update_layout(
            xaxis_title="Numéro d'équipement",
            yaxis_title="Durée (h)",
            xaxis_tickangle=-45,
        )
        st.plotly_chart(fig)

    with col2:
        df_filtered = df_selected_year[df_selected_year["duree_indispo"].notnull()]
        df_filtered = df_filtered[df_filtered["type_equipement"] == "ascenseur"]
        df_filtered = df_filtered[df_filtered["duree_indispo"] <= q75]

        # Replace None values in 'station' with "non spécifié"
        df_filtered["num_equip"] = df_filtered["num_equip"].fillna("Non spécifié")
        df_filtered["ligne"] = df_filtered["ligne"].fillna("Non spécifié")

        df_grouped = (
            df_filtered.groupby(["num_equip", "ligne"])["duree_indispo"]
            .sum()
            .reset_index(name="count")
        )

        fig = px.bar(
            df_grouped,
            x="num_equip",
            y="count",
            color="ligne",
            title="Durée d'indisponibilités par équipement - données filtrées",
            labels={
                "num_equip": "Numéro d'équipement",
                "count": "Heures d'indisponibilités",
            },
        )
        fig.update_layout(
            xaxis_title="Numéro d'équipement",
            yaxis_title="Durée (h)",
            xaxis_tickangle=-45,
        )
        st.plotly_chart(fig)

    st.subheader("Escaliers")

    df_filtered = df_selected_year[df_selected_year["duree_indispo"].notnull()]
    df_filtered = df_filtered[df_filtered["type_equipement"] == "escalier"]

    # Replace None values in 'station' with "non spécifié"
    df_filtered["num_equip"] = df_filtered["num_equip"].fillna("Non spécifié")
    df_filtered["ligne"] = df_filtered["ligne"].fillna("Non spécifié")

    df_grouped = (
        df_filtered.groupby(["num_equip", "ligne"])["duree_indispo"]
        .sum()
        .reset_index(name="count")
    )

    q75 = df_filtered["duree_indispo"].quantile(0.75)

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(
            df_grouped,
            x="num_equip",
            y="count",
            color="ligne",
            title="Durée d'indisponibilités par équipement - données non filtrées",
            labels={
                "num_equip": "Numéro d'équipement",
                "count": "Heures d'indisponibilités",
            },
        )
        fig.update_layout(
            xaxis_title="Numéro d'équipement",
            yaxis_title="Durée (h)",
            xaxis_tickangle=-45,
        )
        st.plotly_chart(fig)

    with col2:
        df_filtered = df_selected_year[df_selected_year["duree_indispo"].notnull()]
        df_filtered = df_filtered[df_filtered["type_equipement"] == "escalier"]
        df_filtered = df_filtered[df_filtered["duree_indispo"] <= q75]

        # Replace None values in 'station' with "non spécifié"
        df_filtered["num_equip"] = df_filtered["num_equip"].fillna("Non spécifié")
        df_filtered["ligne"] = df_filtered["ligne"].fillna("Non spécifié")

        df_grouped = (
            df_filtered.groupby(["num_equip", "ligne"])["duree_indispo"]
            .sum()
            .reset_index(name="count")
        )

        fig = px.bar(
            df_grouped,
            x="num_equip",
            y="count",
            color="ligne",
            title="Durée d'indisponibilités par équipement - données filtrées",
            labels={
                "num_equip": "Numéro d'équipement",
                "count": "Heures d'indisponibilités",
            },
        )
        fig.update_layout(
            xaxis_title="Numéro d'équipement",
            yaxis_title="Durée (h)",
            xaxis_tickangle=-45,
        )
        st.plotly_chart(fig)

# %% Onglet 5 : Patrimoine
if options == "Patrimoine":
    st.title("Patrimoine")

    st.header("Données")

    st.write(
        "Données issues du fichier **'7_Parc_Esc_Méc_et_Asc 2023.xlsx'** disponible ici : [TCL_2017/C-REPORTING/C07 DDR/C7.2 Livrables/2024/A032_Liste_eqpmts_energie_electromeca](https://informatiquesytral.sharepoint.com/:x:/r/sites/dppo/_layouts/15/Doc.aspx?sourcedoc=%7B5ED4BDA8-5FDD-4DCC-AD14-47584B01A890%7D&file=7_Parc_Esc_M%25u00e9c_et_Asc%202023.xlsx&wdLOR=c04AA3002-9F9B-4E2F-9B76-3F0F49867C92&action=default&mobileredirect=true)"
    )

    col1, col2 = st.columns(
        [1, 2]
    )  # Adjust column widths, col1 is twice as wide as col2

    with col1:
        st.dataframe(df2, use_container_width=True)

    # Répartition des équipements par type
    with col2:
        df2_grouped = df2.groupby("type_equipement")["id"].count().reset_index()
        df2_grouped = df2_grouped.rename(columns={"id": "count"}).sort_values(
            by="count", ascending=False
        )

        fig = px.pie(
            df2_grouped,
            names="type_equipement",
            values="count",
            title="Répartition des équipements par type",
            labels={
                "type_equipement": "Type d'équipement",
                "count": "Nombre d'équipements",
            },
        )
        fig.update_layout(legend_title_text="Type d'équipement")
        fig.update_traces(textinfo="percent+label")
        fig

    # %% Equipements par marque
    st.header("Equipements par marque")

    st.markdown(
        "<span style='color:red; font-weight:bold;'>Attention code couleur thyssen et schindler ne match pas</span>",
        unsafe_allow_html=True,
    )

    # Group by 'type_equipement' and 'marque' and count the number of occurrences
    df2_grouped = df2.groupby(["type_equipement", "marque"])["id"].count().reset_index()
    df2_grouped = df2_grouped.rename(columns={"id": "count"}).sort_values(
        by="count", ascending=False
    )
    df2_grouped["percentage"] = df2_grouped["count"] / df2_grouped["count"].sum() * 100

    col1, col2, col3 = st.columns(3)
    with col1:
        # Create a bar chart using Plotly Express
        fig = px.bar(
            df2_grouped,
            x="marque",
            y="count",
            color="type_equipement",
            title="Répartition des équipements par marque (nombre)",
            labels={"marque": "Marque", "count": "Nombre d'équipements"},
            barmode="group",
        )
        fig.update_layout(
            xaxis_title="Marque",
            yaxis_title="Nombre d'équipements",
            legend_title_text="Type d'équipement",
        )
        fig

    with col2:
        df_filtered = df2_grouped[df2_grouped["type_equipement"] == "ascenseur"]
        fig = px.pie(
            df_filtered,
            names="marque",
            values="count",
            title="Répartition des ascenseurs par marque (pourcentage)",
            labels={"marque": "Marque", "count": "Nombre d'équipements"},
        )
        fig.update_layout(legend_title_text="Marque")
        fig.update_traces(textinfo="percent+label")
        st.plotly_chart(fig)

    with col3:
        df_filtered = df2_grouped[df2_grouped["type_equipement"] == "escalier"]
        fig = px.pie(
            df_filtered,
            names="marque",
            values="count",
            title="Répartition des escaliers par marque (pourcentage)",
            labels={"marque": "Marque", "count": "Nombre d'équipements"},
        )
        fig.update_layout(legend_title_text="Marque")
        fig.update_traces(textinfo="percent+label")
        st.plotly_chart(fig)

    # %% Année de mise en service
    st.header("Année de mise en service")

    df2_grouped = (
        df2.groupby(["annee_mise_en_service", "type_equipement", "marque"])["id"]
        .count()
        .reset_index()
    )
    df2_grouped = df2_grouped.rename(columns={"id": "count"}).sort_values(
        by="count", ascending=False
    )

    col1, col2 = st.columns(2)
    with col1:
        fig = px.histogram(
            df2_grouped,
            x="annee_mise_en_service",
            y="count",
            color="type_equipement",
            nbins=10,
            title="Equipements par année de mise en service",
            barmode="group",
        )

        fig.update_layout(
            xaxis_title="Année de mise en service",
            yaxis_title="Nombre",
            legend_title_text="Type d'équipement",
        )

        fig

    with col2:
        fig = px.histogram(
            df2_grouped,
            x="annee_mise_en_service",
            y="count",
            color="marque",
            nbins=10,
            title="Equipements par année de mise en service selon la marque",
            barmode="group",
        )

        fig.update_layout(
            xaxis_title="Année de mise en service",
            yaxis_title="Nombre",
            legend_title_text="Marque",
        )

        fig
    # %% Type de traction ascenseurs et sortie extérieure

    st.header("Caractéristiques ascenseurs")

    df2_filtered = df2[df2["type_equipement"] == "ascenseur"]

    col1, col2 = st.columns(2)

    with col1:
        df2_grouped = (
            df2_filtered.groupby(["traction"], dropna=False)["id"].count().reset_index()
        )

        df2_grouped = df2_grouped.rename(columns={"id": "count"}).sort_values(
            by="count", ascending=False
        )
        df2_grouped["traction"] = df2_grouped["traction"].fillna("Non spécifié")

        fig = px.bar(
            df2_grouped,
            x="traction",
            y="count",
            title="Répartition des ascenseurs par type de traction",
            labels={
                "traction": "Type de traction",
                "count": "Nombre d'équipements",
            },
        )
        fig.update_layout(
            xaxis_title="Type de traction",
            yaxis_title="Nombre d'équipements",
        )
        fig

    with col2:
        df2_grouped = (
            df2_filtered.groupby(["sortie_voirie"], dropna=False)["id"]
            .count()
            .reset_index()
        )

        df2_grouped = df2_grouped.rename(columns={"id": "count"}).sort_values(
            by="count", ascending=False
        )
        df2_grouped["sortie_voirie"] = df2_grouped["sortie_voirie"].fillna(
            "Non spécifié"
        )

        fig = px.bar(
            df2_grouped,
            x="sortie_voirie",
            y="count",
            title="Répartition des ascenseurs par sortie sur voirie (oui ou non spécifié)",
            labels={
                "sortie_voirie": "Sortie sur voirie",
                "count": "Nombre d'équipements",
            },
        )
        fig.update_layout(
            xaxis_title="Sortie sur voirie",
            yaxis_title="Nombre d'équipements",
        )
        fig

    # %% Situation escaliers mécaniques
    st.header("Répartition des escaliers par situation (intérieure ou extérieure)")

    df2_filtered = df2[df2["type_equipement"] == "escalier"]
    df2_grouped = df2_filtered.groupby(["situation"])["id"].count().reset_index()
    df2_grouped = (
        df2_filtered.groupby(["situation"], dropna=False)["id"].count().reset_index()
    )

    df2_grouped = df2_grouped.rename(columns={"id": "count"}).sort_values(
        by="count", ascending=False
    )
    df2_grouped["situation"] = df2_grouped["situation"].fillna("Non spécifié")

    fig = px.bar(
        df2_grouped,
        x="situation",
        y="count",
        labels={"situation": "Situation", "count": "Nombre d'équipements"},
    )
    fig.update_layout(
        xaxis_title="Situation",
        yaxis_title="Nombre d'équipements",
    )
    fig

# %% Onglet 6 : Croisement données fichiers points marquants et patrimoine

if options == "Croisement données":
    st.title("Croisement données")
    st.write(
        "Croisement entre les données des fichiers 'points marquants' et le fichier 'patrimoine'"
    )

    st.header(
        "Heures d'indisponibilités par équipement et station selon l'année de mise en service"
    )

    # Filter the dataframe to keep only the rows with non-null duration
    df_merged_filtered = df_merged[df_merged["duree_indispo"].notnull()]

    # Concatenate 'ligne_x', 'num_equip', and 'station_x' to create a new x-axis label
    df_merged_filtered["x_axis_label"] = (
        df_merged_filtered["ligne_x"]
        + " - "
        + df_merged_filtered["num_equip"]
        + " ("
        + df_merged_filtered["station_x"]
        + ")"
    )

    # Group by 'x_axis_label', 'station_x' and 'annee_mise_en_service' and sum the duration
    df_grouped = (
        df_merged_filtered.groupby(
            ["x_axis_label", "station_x", "annee_mise_en_service"]
        )["duree_indispo"]
        .sum()
        .reset_index(name="count")
    )

    df_grouped = df_grouped.sort_values(by="count", ascending=False)

    fig = px.bar(
        df_grouped,
        x="x_axis_label",
        y="count",
        color="annee_mise_en_service",
        title="Données non filtrées",
        labels={
            "x_axis_label": "Equipement - Station",
            "count": "Heures d'indisponibilités",
            "annee_mise_en_service": "Année de mise en service",
        },
        color_continuous_scale="agsunset",  # Changed colormap
    )

    fig.update_layout(
        xaxis_title="Equipement - Station",
        yaxis_title="Heures d'indisponibilités",
        xaxis_tickangle=-45,  # Rotate x-axis labels
    )

    fig

    # Filter the dataframe to keep only the rows with non-null duration
    df_merged_filtered = df_merged[df_merged["duree_indispo"].notnull()]

    q75 = df_merged_filtered["duree_indispo"].quantile(0.75)

    df_merged_filtered = df_merged_filtered[df_merged_filtered["duree_indispo"] <= q75]

    # Concatenate 'ligne_x', 'num_equip', and 'station_x' to create a new x-axis label
    df_merged_filtered["x_axis_label"] = (
        df_merged_filtered["ligne_x"]
        + " - "
        + df_merged_filtered["num_equip"]
        + " ("
        + df_merged_filtered["station_x"]
        + ")"
    )

    # Group by 'x_axis_label', 'station_x' and 'annee_mise_en_service' and sum the duration
    df_grouped = (
        df_merged_filtered.groupby(
            ["x_axis_label", "station_x", "annee_mise_en_service"]
        )["duree_indispo"]
        .sum()
        .reset_index(name="count")
    )

    df_grouped = df_grouped.sort_values(by="count", ascending=False)

    fig = px.bar(
        df_grouped,
        x="x_axis_label",
        y="count",
        color="annee_mise_en_service",
        title="Données filtrées",
        labels={
            "x_axis_label": "Equipement - Station",
            "count": "Heures d'indisponibilités",
            "annee_mise_en_service": "Année de mise en service",
        },
        color_continuous_scale="agsunset",  # Changed colormap
    )

    fig.update_layout(
        xaxis_title="Equipement - Station",
        yaxis_title="Heures d'indisponibilités",
        xaxis_tickangle=-45,  # Rotate x-axis labels
    )

    fig

    st.header("Filtre selon la ligne (<= q75)")

    option = st.selectbox(
        "Sélectionnez les lignes à afficher",
        df_merged_filtered["ligne_x"].unique(),  # Use unique values from 'ligne_x'
        index=4,  # Default selection (first option)
    )

    df_merged_filtered = df_merged_filtered[df_merged_filtered["ligne_x"] == option]
    df_grouped = (
        df_merged_filtered.groupby(
            ["x_axis_label", "station_x", "annee_mise_en_service"]
        )["duree_indispo"]
        .sum()
        .reset_index(name="count")
    )
    df_grouped = df_grouped.sort_values(by="count", ascending=False)

    fig = px.bar(
        df_grouped,
        x="x_axis_label",
        y="count",
        color="annee_mise_en_service",
        title="Données filtrées",
        labels={
            "x_axis_label": "Equipement - Station",
            "count": "Heures d'indisponibilités",
            "annee_mise_en_service": "Année de mise en service",
        },
        color_continuous_scale="agsunset",  # Changed colormap
    )
    fig.update_layout(
        xaxis_title="Equipement - Station",
        yaxis_title="Heures d'indisponibilités",
        xaxis_tickangle=-45,  # Rotate x-axis labels
    )
    fig

    st.header("Filtre selon la ligne (> q75)")

    # Filter the dataframe to keep only the rows with non-null duration
    df_merged_filtered = df_merged[df_merged["duree_indispo"].notnull()]

    q75 = df_merged_filtered["duree_indispo"].quantile(0.75)

    df_merged_filtered = df_merged_filtered[df_merged_filtered["duree_indispo"] > q75]

    option = st.selectbox(
        "Sélectionnez les lignes à afficher",
        df_merged_filtered["ligne_x"].unique(),  # Use unique values from 'ligne_x'
    )

    # Concatenate 'ligne_x', 'num_equip', and 'station_x' to create a new x-axis label
    df_merged_filtered["x_axis_label"] = (
        df_merged_filtered["ligne_x"]
        + " - "
        + df_merged_filtered["num_equip"]
        + " ("
        + df_merged_filtered["station_x"]
        + ")"
    )

    df_merged_filtered = df_merged_filtered[df_merged_filtered["ligne_x"] == option]
    df_grouped = (
        df_merged_filtered.groupby(
            ["x_axis_label", "station_x", "annee_mise_en_service"]
        )["duree_indispo"]
        .sum()
        .reset_index(name="count")
    )
    df_grouped = df_grouped.sort_values(by="count", ascending=False)

    fig = px.bar(
        df_grouped,
        x="x_axis_label",
        y="count",
        color="annee_mise_en_service",
        title="Données filtrées",
        labels={
            "x_axis_label": "Equipement - Station",
            "count": "Heures d'indisponibilités",
            "annee_mise_en_service": "Année de mise en service",
        },
        color_continuous_scale="agsunset",  # Changed colormap
    )
    fig.update_layout(
        xaxis_title="Equipement - Station",
        yaxis_title="Heures d'indisponibilités",
        xaxis_tickangle=-45,  # Rotate x-axis labels
    )
    fig

# %% Onglet 7 : Scraping
if options == "Scraping":
    st.title("Scraping")
    st.write(
        "Données issues du script de scraping de la page info voyageurs accessibilité TCL"
    )
