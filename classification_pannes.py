# %%
# Import necessary libraries
import pandas as pd
import nltk
import seaborn as sns
import plotly.express as px

# Import machine learning and text processing libraries
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

# Import stopwords from NLTK
from nltk.corpus import stopwords

# %%
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

# %%
# 2. Vectorisation du texte avec TF-IDF
# Télécharger les stopwords français si ce n'est pas déjà fait
nltk.download("stopwords")
french_stop_words = stopwords.words("french")

vectorizer = TfidfVectorizer(
    stop_words=french_stop_words
)  # Utilisation des stopwords français
tfidf_matrix = vectorizer.fit_transform(descriptions)

# %%
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

print(silhouette_df)

# %%
# 4. Choisir le nombre optimal de clusters
n_clusters_optimal = 17
kmeans_optimal = KMeans(n_clusters=n_clusters_optimal, random_state=42, n_init=10)
clusters = kmeans_optimal.fit_predict(tfidf_matrix)

# %%
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
print(cluster_summary_df)

# %%
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

print(keywords_df)


# %%
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
fig.show()

# Distribution des descriptions de pannes par cluster (Pie chart)
cluster_counts = results_df["Cluster"].value_counts().sort_index()
fig = px.pie(
    values=cluster_counts.values,
    names=[f"Cluster {i}" for i in range(n_clusters_optimal)],
    title="Distribution des descriptions de pannes par cluster",
    hole=0.3,
)
fig.show()

# Nombre de descriptions de pannes par cluster (Bar chart)
fig = px.bar(
    x=cluster_counts.index,
    y=cluster_counts.values,
    labels={"x": "Cluster", "y": "Nombre de descriptions"},
    title="Nombre de descriptions de pannes par cluster",
)
fig.update_layout(template="plotly_white")
fig.show()

# %%
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
fig_pca.show()

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
    labels={"TSNE Comp 1": "t-SNE Composante 1", "TSNE Comp 2": "t-SNE Composante 2"},
    color_continuous_scale="Viridis",
)
fig_tsne.update_layout(template="plotly_white")
fig_tsne.show()
