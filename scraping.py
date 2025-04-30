# %%
import os
import pandas as pd
import plotly.graph_objects as go

# %%
# Define the folder path
folder_path = "scraping"

# List all files in the folder
files = [
    f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))
]

# Initialize an empty DataFrame to store concatenated data
df = pd.DataFrame()

# Loop through each file and concatenate
for file in files:
    file_path = os.path.join(folder_path, file)
    # Assuming files are in CSV format
    data = pd.read_csv(file_path)
    df = pd.concat([df, data], ignore_index=True)

# %%
# Convert 'date' and 'heure' columns to a single datetime column for comparison
df["datetime"] = pd.to_datetime(df["date"] + " " + df["heure"])

# Regrouper par 'ligne', 'id', 'station' et calculer les dates min et max de 'remise_en_service_prevue'
grouped_df = (
    df.groupby(["ligne", "id", "arret"])["datetime"].agg(["min", "max"]).reset_index()
)

# %%
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
    height=1000,
    width=1200,
    showlegend=False,
)

fig.update_xaxes(nticks=40)

fig
