# %% Import des librairies
import os
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Import additional libraries
import seaborn as sns
import nltk

# Import machine learning and text processing libraries
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

# Import stopwords from NLTK
from nltk.corpus import stopwords

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
            "Contexte",
            "Indisponibilités par mois",
            "Typologie des indisponibilités",
            "Indisponibilités par ligne",
            "Indisponibilités par station",
            "Indisponibilités par équipement",
            "Patrimoine",
            "Croisement données",
            "Scraping",
            "Classification non supervisée",
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

# %% Onglet 1 : Contexte
if options == "Contexte":
    st.title("Contexte")
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

    df_filtered = df_selected_year[df_selected_year["duree_indispo"].notnull()]
    df_filtered["mois"] = pd.to_datetime(
        df_filtered["date_debut_panne"], format="%d/%m/%Y"
    ).dt.month
    df_filtered["year"] = pd.to_datetime(
        df_filtered["date_debut_panne"], format="%d/%m/%Y"
    ).dt.year

    q75 = df_filtered["duree_indispo"].quantile(0.75)
    df_filtered_q75 = df_filtered[df_filtered["duree_indispo"] <= q75]

    year_list = st.selectbox(
        "Sélectionner une année",
        sorted(df_filtered["year"].unique(), reverse=True),
        index=0,
    )
    ligne_list = st.multiselect(
        "Sélectionner une ou plusieurs lignes",
        ["A", "B", "C", "D", "F", "T1", "T4"],
        default=["A", "B", "C", "D", "F", "T1", "T4"],
    )
    type_equipement_list = st.multiselect(
        "Sélectionner un ou plusieurs types d'équipement",
        df_filtered["type_equipement"].unique(),
        default=df_filtered["type_equipement"].unique(),
    )

    custom_colors = {
        "A": "red",
        "B": "blue",
        "C": "orange",
        "D": "green",
        "F": "lightgreen",
        "T1": "purple",
        "T4": "darkviolet",
    }
    month_names = [
        "Janvier",
        "Fevrier",
        "Mars",
        "Avril",
        "Mai",
        "Juin",
        "Juillet",
        "Aout",
        "Septembre",
        "Octobre",
        "Novembre",
        "Decembre",
    ]

    def plot_data(data, title):
        fig = px.bar(
            data.loc[
                (data["year"] == year_list)
                & (data["ligne"].isin(ligne_list))
                & (data["type_equipement"].isin(type_equipement_list))
            ],
            x="mois",
            y="duree_indispo",
            color="ligne",
            title=title,
            labels={
                "mois": "Mois",
                "duree_indispo": "Durée totale (heures)",
                "ligne": "Ligne",
            },
            category_orders={
                "mois": list(range(1, 13)),
                "ligne": ["A", "B", "C", "D", "F", "T1", "T4"],
            },
            barmode="group",
            color_discrete_map=custom_colors,
        )
        fig.update_layout(
            xaxis=dict(
                tickmode="array", tickvals=list(range(1, 13)), ticktext=month_names
            ),
            xaxis_title=None,
        )
        st.plotly_chart(fig)

    plot_data(
        df_filtered,
        f"Durée totale d'indisponibilités par mois en {year_list} - toutes données",
    )
    plot_data(
        df_filtered_q75,
        f"Durée totale d'indisponibilités par mois en {year_list} - filtrées (durée indisponibilité <= q75)",
    )

# %% Onglet 2 : Typologie des indisponibilités
if options == "Typologie des indisponibilités":
    st.title("Typologie des indisponibilités")

    st.write(
        f"Données fichiers points marquants entre le {df_selected_year['date_debut_panne'].min()} et le {df_selected_year['date_fin_panne'].max()}"
    )

    # %% Travail en nombre d'indisponibilités
    st.subheader("Analyses en nombre d'indisponibilités")

    custom_order = [
        "Non spécifié",
        "Panne",
        "Usure",
        "Mauvaise utilisation",
        "Vandalisme",
        "Amélioration",
        "****",
    ]

    col1, col2 = st.columns(2)

    with col1:
        df_grouped = (
            df_selected_year.groupby("motifs", dropna=False)
            .size()
            .reset_index(name="count")
        )

        # Replace NaN and None values in 'motifs' with "Non spécifié"
        df_grouped["motifs"] = (
            df_grouped["motifs"]
            .fillna("Non spécifié")
            .replace([None, pd.NA], "Non spécifié")
        )

        # Apply custom order
        df_grouped["motifs"] = pd.Categorical(
            df_grouped["motifs"], categories=custom_order, ordered=True
        )
        df_grouped = df_grouped.sort_values(by="motifs")

        fig = px.bar(
            df_grouped,
            x="motifs",
            y="count",
            title="Données brutes",
            labels={"motifs": "Motif", "count": "Nombre d'indisponibilités"},
        )
        fig.update_layout(xaxis_title="Motif", yaxis_title=None)
        st.plotly_chart(fig)

    with col2:
        fig = px.pie(
            df_grouped,
            names="motifs",
            values="count",
            labels={"motifs": "Motif", "count": "Nombre d'indisponibilités"},
        )
        fig.update_traces(textinfo="percent+label")
        st.plotly_chart(fig)

    col1, col2 = st.columns(2)

    with col1:
        # Filter the dataframe to keep only rows with non-null duration
        df_filtered = df_selected_year[df_selected_year["duree_indispo"].notnull()]
        df_grouped = (
            df_filtered.groupby("motifs", dropna=False).size().reset_index(name="count")
        )

        # Replace NaN and None values in 'motifs' with "Non spécifié"
        df_grouped["motifs"] = df_grouped["motifs"].fillna("Non spécifié")

        # Apply custom order
        df_grouped["motifs"] = pd.Categorical(
            df_grouped["motifs"], categories=custom_order, ordered=True
        )
        df_grouped = df_grouped.sort_values(by="motifs")

        fig = px.bar(
            df_grouped,
            x="motifs",
            y="count",
            title="Données filtrées",
            labels={"motifs": "Motif", "count": "Nombre d'indisponibilités"},
        )
        fig.update_layout(xaxis_title="Motif", yaxis_title=None)
        st.plotly_chart(fig)

    with col2:
        fig = px.pie(
            df_grouped,
            names="motifs",
            values="count",
            labels={"motifs": "Motif", "count": "Nombre d'indisponibilités"},
        )
        fig.update_traces(textinfo="percent+label")
        st.plotly_chart(fig)

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

    custom_order_ligne = ["A", "B", "C", "D", "F", "T1", "T4", "P+R", "Non spécifié"]
    custom_colors = {
        "A": "red",
        "B": "blue",
        "C": "orange",
        "D": "green",
        "F": "lightgreen",
        "T1": "purple",
        "T4": "darkviolet",
        "P+R": "pink",
        "Non spécifié": "gray",
    }

    def plot_indisponibilites(data, title):
        data["ligne"] = data["ligne"].fillna("Non spécifié")
        data["ligne"] = pd.Categorical(
            data["ligne"], categories=custom_order_ligne, ordered=True
        )
        grouped = (
            data.groupby("ligne")
            .size()
            .reset_index(name="count")
            .sort_values(by="count", ascending=False)
        )

        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(
                grouped,
                x="ligne",
                y="count",
                title=title,
                labels={"ligne": "Ligne", "count": "Nombre d'indisponibilités"},
                color="ligne",
                color_discrete_map=custom_colors,
            )
            fig.update_layout(xaxis_title="Ligne", yaxis_title=None)
            st.plotly_chart(fig)
        with col2:
            fig = px.pie(
                grouped,
                names="ligne",
                values="count",
                labels={"ligne": "Ligne", "count": "Nombre d'indisponibilités"},
                color="ligne",
                color_discrete_map=custom_colors,
            )
            fig.update_traces(textinfo="percent+label")
            st.plotly_chart(fig)

    plot_indisponibilites(df_selected_year, "Données brutes")
    plot_indisponibilites(
        df_selected_year[df_selected_year["duree_indispo"].notnull()],
        "Données filtrées (durée indisponibilité non nulle)",
    )

    # %% Travail en heures d'indisponibilités
    st.subheader("Analyses en heures d'indisponibilités")

    df_filtered = df_selected_year[df_selected_year["duree_indispo"].notnull()]
    df_filtered["ligne"] = df_filtered["ligne"].fillna("Non spécifié")

    custom_order_ligne = ["A", "B", "C", "D", "F", "T1", "T4", "P+R", "Non spécifié"]
    custom_colors = {
        "A": "red",
        "B": "blue",
        "C": "orange",
        "D": "green",
        "F": "lightgreen",
        "T1": "purple",
        "T4": "darkviolet",
        "P+R": "pink",
        "Non spécifié": "gray",
    }

    def plot_indisponibilites(data, title_suffix):
        data_grouped = (
            data.groupby("ligne")["duree_indispo"]
            .sum()
            .reset_index(name="count")
            .sort_values(by="count", ascending=False)
        )
        data_grouped["ligne"] = pd.Categorical(
            data_grouped["ligne"], categories=custom_order_ligne, ordered=True
        )
        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(
                data_grouped,
                x="ligne",
                y="count",
                title=f"Durée d'indisponibilités par ligne - {title_suffix}",
                labels={"ligne": "Ligne", "count": "Heures d'indisponibilités"},
                color="ligne",
                color_discrete_map=custom_colors,
            )
            fig.update_layout(xaxis_title="Ligne", yaxis_title="Durée (h)")
            st.plotly_chart(fig)
        with col2:
            fig = px.pie(
                data_grouped,
                names="ligne",
                values="count",
                labels={"ligne": "Ligne", "count": "Heures d'indisponibilités"},
                color="ligne",
                color_discrete_map=custom_colors,
            )
            fig.update_traces(textinfo="percent+label")
            st.plotly_chart(fig)

    plot_indisponibilites(df_filtered, "données non filtrées")

    q75 = df_filtered["duree_indispo"].quantile(0.75)
    df_filtered_q75 = df_filtered[df_filtered["duree_indispo"] <= q75]
    plot_indisponibilites(df_filtered_q75, "données filtrées (<= q75)")

# %% Onglet 3 : Indisponibilités par station
if options == "Indisponibilités par station":
    st.title("Indisponibilités par station")

    st.write(
        f"Données fichiers points marquants entre le {df_selected_year['date_debut_panne'].min()} et le {df_selected_year['date_fin_panne'].max()}"
    )

    # %% Analyses en nombre d'indisponibilités
    st.subheader("Analyses en nombre d'indisponibilités")

    st.write(
        "**Lecture des graphiques :** à gauche toutes les données, à droite uniquement celles avec une durée non nulle."
    )

    custom_colors = {
        "A": "red",
        "B": "blue",
        "C": "orange",
        "D": "green",
        "F": "lightgreen",
        "T1": "purple",
        "T4": "darkviolet",
        "P+R": "pink",
        "Non spécifié": "gray",
    }

    def plot_indisponibilites(data, title):
        data["station"] = data["station"].fillna("Non spécifié")
        data["ligne"] = data["ligne"].fillna("Non spécifié")
        fig = px.bar(
            data.groupby(["station", "ligne"]).size().reset_index(name="count"),
            x="station",
            y="count",
            color="ligne",
            title=title,
            labels={
                "station": "Station",
                "count": "Nombre d'indisponibilités",
                "ligne": "Ligne",
            },
            color_discrete_map=custom_colors,
        )
        fig.update_layout(xaxis_title="Station", yaxis_title=None, xaxis_tickangle=-45)
        st.plotly_chart(fig)

    col1, col2 = st.columns(2)
    with col1:
        plot_indisponibilites(df_selected_year, "Données brutes")
    with col2:
        plot_indisponibilites(
            df_selected_year[df_selected_year["duree_indispo"].notnull()],
            "Données filtrées",
        )
    # %% Travail en heures d'indisponibilités
    st.subheader("Analyses en heures d'indisponibilités")

    df_filtered = df_selected_year[df_selected_year["duree_indispo"].notnull()]
    df_filtered["station"] = df_filtered["station"].fillna("Non spécifié")
    df_filtered["ligne"] = df_filtered["ligne"].fillna("Non spécifié")

    q75 = df_filtered["duree_indispo"].quantile(0.75)
    st.write(f"75% des indisponibilités durent **{q75:.2f} heures** ou moins.")

    def plot_duration(data, title):
        grouped = (
            data.groupby(["station", "ligne"])["duree_indispo"]
            .sum()
            .reset_index(name="count")
        )
        fig = px.bar(
            grouped,
            x="station",
            y="count",
            color="ligne",
            title=title,
            labels={"station": "Station", "count": "Heures d'indisponibilités"},
            color_discrete_map=custom_colors,
        )
        fig.update_layout(xaxis_title="Station", yaxis_title="Durée (h)")
        st.plotly_chart(fig)

    col1, col2 = st.columns(2)
    with col1:
        plot_duration(
            df_filtered, "Durée d'indisponibilités par station - données non filtrées"
        )
    with col2:
        plot_duration(
            df_filtered[df_filtered["duree_indispo"] <= q75],
            "Durée d'indisponibilités par station - données filtrées",
        )

# %% Onglet 4 : Indisponibilités par équipement
if options == "Indisponibilités par équipement":
    st.title("Indisponibilités par équipement")

    st.write(
        f"Données fichiers points marquants entre le {df_selected_year['date_debut_panne'].min()} et le {df_selected_year['date_fin_panne'].max()}"
    )

    # %% Analyses en nombre d'indisponibilités
    st.header("Analyses en nombre d'indisponibilités")

    st.write(
        "**Lecture des graphiques :** à gauche toutes les données,"
        " à droite uniquement celles avec une durée d'indisponibilité non nulle."
    )

    type_equipement_list = st.multiselect(
        "Sélectionner un ou plusieurs types d'équipement",
        df_selected_year["type_equipement"].unique(),
        default=df_selected_year["type_equipement"].unique(),
        key="multiselect1",
    )

    custom_colors = {
        "A": "red",
        "B": "blue",
        "C": "orange",
        "D": "green",
        "F": "lightgreen",
        "T1": "purple",
        "T4": "darkviolet",
        "P+R": "pink",
        "Non spécifié": "gray",
    }

    def plot_indisponibilites(data, title):
        grouped = (
            data[data["type_equipement"].isin(type_equipement_list)]
            .groupby(["num_equip", "ligne"], dropna=False)
            .size()
            .reset_index(name="count")
        )
        grouped["num_equip"] = grouped["num_equip"].fillna("Non spécifié")
        grouped["ligne"] = grouped["ligne"].fillna("Non spécifié")

        fig = px.bar(
            grouped,
            x="num_equip",
            y="count",
            color="ligne",
            title=title,
            labels={
                "num_equip": "Numéro d'équipement",
                "count": "Nombre d'indisponibilités",
                "ligne": "Ligne",
            },
            color_discrete_map=custom_colors,
        )
        fig.update_layout(
            xaxis_title="Numéro d'équipement", yaxis_title=None, xaxis_tickangle=-45
        )
        st.plotly_chart(fig)

    col1, col2 = st.columns(2)
    with col1:
        plot_indisponibilites(df_selected_year, "Données brutes")
    with col2:
        plot_indisponibilites(
            df_selected_year[df_selected_year["duree_indispo"].notnull()],
            "Données filtrées",
        )

    # %% Travail en heures d'indisponibilités
    st.header("Analyses en heures d'indisponibilités")

    type_equipement_list = st.multiselect(
        "Sélectionner un ou plusieurs types d'équipement",
        df_selected_year["type_equipement"].unique(),
        default=df_selected_year["type_equipement"].unique(),
        key="multiselect2",
    )

    df_filtered = df_selected_year[
        (df_selected_year["duree_indispo"].notnull())
        & (df_selected_year["type_equipement"].isin(type_equipement_list))
    ]

    q75 = df_filtered["duree_indispo"].quantile(0.75)
    st.write(f"75% des indisponibilités durent **{q75:.2f} heures** ou moins.")

    custom_colors = {
        "A": "red",
        "B": "blue",
        "C": "orange",
        "D": "green",
        "F": "lightgreen",
        "T1": "purple",
        "T4": "darkviolet",
        "P+R": "pink",
        "Non spécifié": "gray",
    }

    def plot_duration(data, title):
        grouped = (
            data.groupby(["num_equip", "ligne"])["duree_indispo"]
            .sum()
            .reset_index(name="count")
        )
        fig = px.bar(
            grouped,
            x="num_equip",
            y="count",
            color="ligne",
            title=title,
            labels={
                "num_equip": "Numéro d'équipement",
                "count": "Heures d'indisponibilités",
            },
            color_discrete_map=custom_colors,
        )
        fig.update_layout(xaxis_tickangle=-45, yaxis_title="Durée (h)")
        st.plotly_chart(fig)

    col1, col2 = st.columns(2)
    with col1:
        plot_duration(df_filtered, "Données non filtrées")
    with col2:
        plot_duration(
            df_filtered[df_filtered["duree_indispo"] <= q75],
            "Données filtrées (<= q75)",
        )

# %% Onglet 5 : Patrimoine
if options == "Patrimoine":
    st.title("Patrimoine")

    st.header("Données")

    st.write(
        "Données issues du fichier **'7_Parc_Esc_Méc_et_Asc 2023.xlsx'** disponible ici : [TCL_2017/C-REPORTING/C07 DDR/C7.2 Livrables/2024/A032_Liste_eqpmts_energie_electromeca](https://informatiquesytral.sharepoint.com/:x:/r/sites/dppo/_layouts/15/Doc.aspx?sourcedoc=%7B5ED4BDA8-5FDD-4DCC-AD14-47584B01A890%7D&file=7_Parc_Esc_M%25u00e9c_et_Asc%202023.xlsx&wdLOR=c04AA3002-9F9B-4E2F-9B76-3F0F49867C92&action=default&mobileredirect=true)"
    )

    col1, col2 = st.columns(
        [2, 1]
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

    # Define custom colormaps for marques
    custom_colors_marque = {
        "Thyssen": "blue",
        "Schindler": "red",
        "Otis": "green",
        "Kone": "purple",
        "Soretex": "orange",
        "Amonter": "pink",
        "Asc Svce": "brown",
    }

    # Group by 'type_equipement' and 'marque' and count the number of occurrences
    df2_grouped = (
        df2.groupby(["type_equipement", "marque"])["id"]
        .count()
        .reset_index()
        .rename(columns={"id": "count"})
        .sort_values(by="count", ascending=False)
    )
    df2_grouped["percentage"] = df2_grouped["count"] / df2_grouped["count"].sum() * 100

    col1, col2, col3 = st.columns(3)

    with col1:
        # Bar chart for all equipment by marque
        fig = px.bar(
            df2_grouped,
            x="marque",
            y="count",
            color="marque",
            title="Répartition des équipements par marque (nombre)",
            labels={"marque": "Marque", "count": "Nombre d'équipements"},
            barmode="group",
            color_discrete_map=custom_colors_marque,
        )
        fig.update_layout(
            xaxis_title="Marque",
            yaxis_title="Nombre d'équipements",
            legend_title_text="Marque",
        )
        st.plotly_chart(fig)

    with col2:
        # Pie chart for ascenseurs by marque
        df_filtered = df2_grouped[df2_grouped["type_equipement"] == "ascenseur"]
        fig = px.pie(
            df_filtered,
            names="marque",
            values="count",
            title="Répartition des ascenseurs par marque (pourcentage)",
            labels={"marque": "Marque", "count": "Nombre d'équipements"},
            color="marque",
            color_discrete_map=custom_colors_marque,
        )
        fig.update_layout(legend_title_text="Marque")
        fig.update_traces(textinfo="percent+label")
        st.plotly_chart(fig)

    with col3:
        # Pie chart for escaliers by marque
        df_filtered = df2_grouped[df2_grouped["type_equipement"] == "escalier"]
        fig = px.pie(
            df_filtered,
            names="marque",
            values="count",
            title="Répartition des escaliers par marque (pourcentage)",
            labels={"marque": "Marque", "count": "Nombre d'équipements"},
            color="marque",
            color_discrete_map=custom_colors_marque,
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

    # Define custom colormaps for marques
    custom_colors_marque = {
        "Thyssen": "blue",
        "Schindler": "red",
        "Otis": "green",
        "Kone": "purple",
        "Soretex": "orange",
        "Amonter": "pink",
        "Asc Svce": "brown",
    }

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
            color_discrete_map=custom_colors_marque,
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

    # Define the folder path
    folder_path = "scraping"

    # List all files in the folder
    files = [
        f
        for f in os.listdir(folder_path)
        if os.path.isfile(os.path.join(folder_path, f))
    ]

    # Initialize an empty DataFrame to store concatenated data
    df = pd.DataFrame()

    # Loop through each file and concatenate
    for file in files:
        file_path = os.path.join(folder_path, file)
        # Assuming files are in CSV format
        data = pd.read_csv(file_path)
        df = pd.concat([df, data], ignore_index=True)

    # Convert 'date' and 'heure' columns to a single datetime column for comparison
    df["datetime"] = pd.to_datetime(df["date"] + " " + df["heure"])

    # Regrouper par 'ligne', 'id', 'station' et calculer les dates min et max de 'remise_en_service_prevue'
    grouped_df = (
        df.groupby(["ligne", "id", "arret"])["datetime"]
        .agg(["min", "max"])
        .reset_index()
    )

    # Create a figure
    fig = go.Figure()

    # Add traces for each row in grouped_df
    for i, row in grouped_df.iterrows():
        fig.add_trace(
            go.Scatter(
                x=[row["min"], row["max"]],
                y=[i, i],
                mode="lines+markers",
                marker=dict(size=10),
                name=f"{row['ligne']} - {row['id']} - {row['arret']}",
            )
        )

    # Define custom colors for specific 'ligne' values
    custom_colors = {
        "A": "red",
        "B": "blue",
        "C": "orange",
        "D": "green",
        "F": "lightgreen",
        "F1": "lightgreen",
        "F2": "lightgreen",
        "T1": "purple",
        "T4": "darkviolet",
        "P+R": "pink",
        "Non spécifié": "gray",
    }

    # Update traces with color based on 'ligne'
    for i, row in grouped_df.iterrows():
        ligne_color = custom_colors.get(
            row["ligne"], "black"
        )  # Default to black if 'ligne' not in custom_colors
        fig.data[i].line.color = ligne_color

    # Update layout
    fig.update_layout(
        title="Dates de Remise en Service Prévue Min et Max par Ligne, ID et Station",
        xaxis_title="Date de Remise en Service Prévue",
        yaxis=dict(
            tickmode="array",
            tickvals=list(range(len(grouped_df))),
            ticktext=grouped_df.apply(
                lambda x: f"{x['ligne']} - {x['id']} - {x['arret']}", axis=1
            ),
        ),
        xaxis=dict(tickangle=45),
        height=1500,
        showlegend=False,
    )

    fig.update_xaxes(nticks=40)

    fig
# %% Onglet 8 : Classification
if options == "Classification non supervisée":
    st.title("Classification non supervisée")
    st.write(
        "Utilisation de l'algorithme K-means pour le clustering des descriptions de pannes."
    )
    st.write("Vectorisation du texte avec TF-IDF.")

    # 1. Charger les données
    try:
        df = pd.read_csv("points_marquants/points_marquants_24_clean.csv", sep=";")
        descriptions = df["commentaire"].dropna().tolist()
    except FileNotFoundError:
        print("Erreur: Le fichier n'a pas été trouvé.")
        exit()
    except KeyError:
        print("Erreur: La colonne 'REDACTION' ou la feuille spécifiée n'existe pas.")
        exit()

    if not descriptions:
        print("Aucune description de panne à analyser.")
        exit()

    # 2. Vectorisation du texte avec TF-IDF
    # Télécharger les stopwords français si ce n'est pas déjà fait
    nltk.download("stopwords")
    french_stop_words = stopwords.words("french")

    vectorizer = TfidfVectorizer(
        stop_words=french_stop_words
    )  # Utilisation des stopwords français
    tfidf_matrix = vectorizer.fit_transform(descriptions)

    # 3. Application de l'algorithme de clustering K-means
    # Déterminer le nombre optimal de clusters (méthode du coude ou silhouette)
    # Ici, nous allons essayer une plage de nombres de clusters
    range_n_clusters = range(2, 20)
    silhouette_scores = []

    # Create a DataFrame to store the silhouette scores for each number of clusters
    silhouette_df = pd.DataFrame(columns=["n_clusters", "silhouette_score"])

    for n_clusters in range_n_clusters:
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(tfidf_matrix)
        silhouette_avg = silhouette_score(tfidf_matrix, cluster_labels)
        silhouette_df = pd.concat(
            [
                silhouette_df,
                pd.DataFrame(
                    {"n_clusters": [n_clusters], "silhouette_score": [silhouette_avg]}
                ),
            ],
            ignore_index=True,
        )
        # print(f"Silhouette score pour {n_clusters} clusters: {silhouette_avg:.4f}")

    # st.dataframe(silhouette_df, use_container_width=True)

    # 4. Choisir le nombre optimal de clusters
    n_clusters_optimal = 17
    kmeans_optimal = KMeans(n_clusters=n_clusters_optimal, random_state=42, n_init=10)
    clusters = kmeans_optimal.fit_predict(tfidf_matrix)

    # 5. Analyse des clusters
    results_df = pd.DataFrame({"commentaire": descriptions, "Cluster": clusters})

    # Transform the clustering results into a DataFrame for better readability
    cluster_summary = []

    for i in range(n_clusters_optimal):
        cluster_descriptions = results_df[results_df["Cluster"] == i][
            "commentaire"
        ].tolist()
        cluster_summary.append(
            {
                "Cluster": i,
                "Nombre de descriptions": len(cluster_descriptions),
                "Exemples de descriptions": cluster_descriptions[
                    :10
                ],  # Limiter à 10 exemples
            }
        )

    cluster_summary_df = pd.DataFrame(cluster_summary)
    st.dataframe(cluster_summary_df, hide_index=True)

    # 6. Afficher les mots-clés pour chaque cluster
    # Extract feature names from the vectorizer
    terms = vectorizer.get_feature_names_out()

    # Compute order_centroids from the cluster centers
    order_centroids = kmeans_optimal.cluster_centers_.argsort()[:, ::-1]

    # Create a DataFrame to store the keywords for each cluster
    keywords_df = pd.DataFrame(
        {
            "Cluster": range(n_clusters_optimal),
            "Top Keywords": [
                ", ".join([terms[ind] for ind in order_centroids[i, :10]])
                for i in range(n_clusters_optimal)
            ],
        }
    )

    st.dataframe(keywords_df, hide_index=True)

    # 7. Visualisation des résultats
    # Score de silhouette pour chaque nombre de clusters
    fig = px.line(
        silhouette_df,
        x="n_clusters",
        y="silhouette_score",
        labels={
            "n_clusters": "Nombre de clusters",
            "silhouette_score": "Score de Silhouette",
        },
        title="Score de Silhouette en fonction du nombre de clusters",
    )
    fig.update_traces(mode="lines+markers")
    fig.update_layout(template="plotly_white")
    fig

    # Distribution des descriptions de pannes par cluster (Pie chart)
    cluster_counts = results_df["Cluster"].value_counts().sort_index()
    fig = px.pie(
        values=cluster_counts.values,
        names=[f"Cluster {i}" for i in range(n_clusters_optimal)],
        title="Distribution des descriptions de pannes par cluster",
        hole=0.3,
    )
    fig

    # Nombre de descriptions de pannes par cluster (Bar chart)
    fig = px.bar(
        x=cluster_counts.index,
        y=cluster_counts.values,
        labels={"x": "Cluster", "y": "Nombre de descriptions"},
        title="Nombre de descriptions de pannes par cluster",
    )
    fig.update_layout(template="plotly_white")
    fig

    # Initialiser PCA avec 2 composantes
    pca = PCA(n_components=2)

    # Calculer les résultats PCA
    pca_result = pca.fit_transform(tfidf_matrix.toarray())

    # Ajouter les résultats PCA au DataFrame
    results_df["PCA Comp 1"] = pca_result[:, 0]
    results_df["PCA Comp 2"] = pca_result[:, 1]

    # Visualisation des clusters avec PCA (2 composantes)
    fig_pca = px.scatter(
        results_df,
        x="PCA Comp 1",
        y="PCA Comp 2",
        color="Cluster",
        title="Visualisation des clusters avec PCA (2 composantes)",
        labels={"PCA Comp 1": "PCA Composante 1", "PCA Comp 2": "PCA Composante 2"},
        color_continuous_scale="Viridis",
    )
    fig_pca.update_layout(template="plotly_white")
    fig_pca

    # Initialiser t-SNE avec 2 composantes
    tsne = TSNE(n_components=2, random_state=42)

    # Calculer les résultats t-SNE
    tsne_result = tsne.fit_transform(tfidf_matrix.toarray())

    # Ajouter les résultats t-SNE au DataFrame
    results_df["TSNE Comp 1"] = tsne_result[:, 0]
    results_df["TSNE Comp 2"] = tsne_result[:, 1]

    # Visualisation des clusters avec t-SNE (2 composantes)
    fig_tsne = px.scatter(
        results_df,
        x="TSNE Comp 1",
        y="TSNE Comp 2",
        color="Cluster",
        title="Visualisation des clusters avec t-SNE (2 composantes)",
        labels={
            "TSNE Comp 1": "t-SNE Composante 1",
            "TSNE Comp 2": "t-SNE Composante 2",
        },
        color_continuous_scale="Viridis",
    )
    fig_tsne.update_layout(template="plotly_white")
    fig_tsne
