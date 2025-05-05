import pandas as pd
import os
import logging

# --- Configuration ---
# Setup basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Define base path
BASE_FOLDER = "points_marquants"
# Ensure the base folder path is correct relative to the script execution directory
folder_path = os.path.join(os.getcwd(), BASE_FOLDER)

# Check if the directory exists, create if not (optional, depends on workflow)
# if not os.path.exists(folder_path):
#     os.makedirs(folder_path)
#     logging.info(f"Created directory: {folder_path}")

# Columns to keep and their new names
COLUMNS_TO_KEEP = [
    "DATE Début",
    "HEURE Début",
    "DATE Fin",
    "HEURE Fin",
    "LIGNE",
    "STATION",
    "N° EQUIP.",
    "COMMENTAIRE",
    "Motifs",
]
COLUMN_RENAME_MAP = {
    "DATE Début": "date_debut_panne",
    "HEURE Début": "heure_debut_panne",
    "DATE Fin": "date_fin_panne",
    "HEURE Fin": "heure_fin_panne",
    "LIGNE": "ligne",
    "STATION": "station",
    "N° EQUIP.": "num_equip",
    "COMMENTAIRE": "commentaire",
    "Motifs": "motifs",
}

# --- Helper Functions ---


def convert_time_format(time_val):
    """Converts various time representations to HH:MM string format."""
    if pd.isna(time_val):
        return None
    if isinstance(
        time_val, pd.Timestamp
    ):  # Handle datetime.time objects if read_excel parses them
        return time_val.strftime("%H:%M")
    time_str = str(time_val)
    # Handle float times like 0.5 for noon
    try:
        float_time = float(time_str)
        if 0 <= float_time <= 1:
            # Convert fractional day to HH:MM
            total_minutes = int(float_time * 24 * 60)
            hours = total_minutes // 60
            minutes = total_minutes % 60
            return f"{hours:02d}:{minutes:02d}"
    except ValueError:
        pass  # It's not a simple float, proceed with string parsing

    # Handle string formats like '9h', '14h30', '17H'
    time_str = time_str.replace("h", ":").replace("H", ":")
    if ":" in time_str:
        parts = time_str.split(":")
        hour = parts[0].strip()
        minute = parts[1].strip() if len(parts) > 1 and parts[1].strip() else "00"
        # Basic validation/cleanup
        try:
            hour_int = int(hour)
            minute_int = int(minute)
            if 0 <= hour_int <= 23 and 0 <= minute_int <= 59:
                return f"{hour_int:02d}:{minute_int:02d}"
        except ValueError:
            pass  # Invalid format
    # Handle potential integer times (less likely but possible)
    try:
        int_time = int(time_str)
        if 0 <= int_time <= 23:  # Assume it's just the hour
            return f"{int_time:02d}:00"
    except ValueError:
        pass

    logging.warning(f"Could not parse time format: {time_val}. Returning None.")
    return None  # Return None if format is unrecognized


def calculate_duration(row):
    """Calculates duration in hours and days between start and end date/time."""
    if (
        pd.isna(row["date_debut_panne"])
        or pd.isna(row["date_fin_panne"])
        or pd.isna(row["heure_debut_panne"])
        or pd.isna(row["heure_fin_panne"])
    ):
        return None, None

    try:
        # Combine date (already datetime) and time string
        start_str = (
            f"{row['date_debut_panne'].strftime('%Y-%m-%d')} {row['heure_debut_panne']}"
        )
        end_str = (
            f"{row['date_fin_panne'].strftime('%Y-%m-%d')} {row['heure_fin_panne']}"
        )

        start_dt = pd.to_datetime(start_str, format="%Y-%m-%d %H:%M", errors="coerce")
        end_dt = pd.to_datetime(end_str, format="%Y-%m-%d %H:%M", errors="coerce")

        if pd.isna(start_dt) or pd.isna(end_dt):
            logging.warning(
                f"Could not parse combined datetime for row: {row.name}. Start: '{start_str}', End: '{end_str}'"
            )
            return None, None

        duration_timedelta = end_dt - start_dt
        duration_hours = duration_timedelta.total_seconds() / 3600
        duration_days = duration_hours / 24
        return duration_hours, duration_days
    except Exception as e:
        logging.error(
            f"Error calculating duration for row {row.name}: {e}. Data: {row['date_debut_panne']}, {row['heure_debut_panne']}, {row['date_fin_panne']}, {row['heure_fin_panne']}"
        )
        return None, None


# --- Main Processing Function ---


def process_maintenance_file(
    input_filename, output_base_name, skiprows=0, sheet_name=0
):
    """Reads, cleans, transforms, and saves maintenance data from an Excel file."""
    input_path = os.path.join(folder_path, input_filename)
    output_csv_path = os.path.join(folder_path, f"{output_base_name}.csv")
    output_excel_path = os.path.join(folder_path, f"{output_base_name}.xlsx")

    logging.info(f"Processing file: {input_filename}")

    try:
        df = pd.read_excel(input_path, skiprows=skiprows, sheet_name=sheet_name)
    except FileNotFoundError:
        logging.error(f"Input file not found: {input_path}. Skipping.")
        return None
    except Exception as e:
        logging.error(f"Error reading Excel file {input_path}: {e}")
        return None

    # --- Data Cleaning and Transformation ---
    # Ensure required columns exist
    missing_cols = [col for col in COLUMNS_TO_KEEP if col not in df.columns]
    if missing_cols:
        logging.error(
            f"Missing required columns in {input_filename}: {missing_cols}. Skipping."
        )
        return None

    df_processed = df[
        COLUMNS_TO_KEEP
    ].copy()  # Select and copy to avoid SettingWithCopyWarning
    df_processed.rename(columns=COLUMN_RENAME_MAP, inplace=True)

    # Convert dates first (errors='coerce' handles unparseable dates -> NaT)
    # Keep them as datetime objects for now
    df_processed["date_debut_panne"] = pd.to_datetime(
        df_processed["date_debut_panne"], errors="coerce"
    )
    df_processed["date_fin_panne"] = pd.to_datetime(
        df_processed["date_fin_panne"], errors="coerce"
    )

    # Convert times using the helper function
    df_processed["heure_debut_panne"] = df_processed["heure_debut_panne"].apply(
        convert_time_format
    )
    df_processed["heure_fin_panne"] = df_processed["heure_fin_panne"].apply(
        convert_time_format
    )

    # Handle potential NaNs introduced by conversions before proceeding
    df_processed.dropna(
        subset=["date_debut_panne", "num_equip"], inplace=True
    )  # Essential columns

    # Create 'type_equipement'
    # Ensure 'num_equip' is string type before using .str accessor
    df_processed["num_equip"] = df_processed["num_equip"].astype(str)
    df_processed["type_equipement"] = (
        df_processed["num_equip"]
        .str.startswith("Asc")
        .map({True: "ascenseur", False: "escalier"})
    )

    # Create 'annee_debut_panne'
    df_processed["annee_debut_panne"] = df_processed[
        "date_debut_panne"
    ].dt.year  # Works directly on datetime objects

    # Calculate durations
    durations = df_processed.apply(calculate_duration, axis=1, result_type="expand")
    df_processed[["duree_indispo", "jour_indispo"]] = durations

    # Clean 'ligne' column
    df_processed["ligne"] = (
        df_processed["ligne"].astype(str).str.replace("T1 ", "T1", regex=False)
    )

    # Extract 'id'
    df_processed["id"] = (
        df_processed["num_equip"].str.extract(r"(\d+)", expand=False).astype(float)
    )

    # Convert dates back to string format DD/MM/YYYY *only for saving intermediate files*
    df_save = df_processed.copy()
    df_save["date_debut_panne"] = df_save["date_debut_panne"].dt.strftime("%d/%m/%Y")
    # Handle NaT in date_fin_panne before formatting
    df_save["date_fin_panne"] = (
        df_save["date_fin_panne"].dt.strftime("%d/%m/%Y").fillna("")
    )

    # --- Save Processed Files ---
    try:
        df_save.to_csv(output_csv_path, sep=";", index=False, encoding="utf-8-sig")
        logging.info(f"Saved cleaned CSV: {output_csv_path}")
        df_save.to_excel(output_excel_path, index=False)
        logging.info(f"Saved cleaned Excel: {output_excel_path}")
    except Exception as e:
        logging.error(f"Error saving output files for {output_base_name}: {e}")

    # Return the DataFrame with dates as datetime objects for merging
    return df_processed


# --- File Processing Loop ---

files_to_process = [
    {
        "input": "Points marquants maintenance 2024.xlsx",
        "output": "points_marquants_24_clean",
        "skiprows": 0,
    },
    {
        "input": "Points marquants maintenance Janv 2025.xlsx",
        "output": "points_marquants_janv_25_clean",
        "skiprows": 1,
    },
    {
        "input": "Points marquants maintenance Fevrier 2025.xlsx",
        "output": "points_marquants_fev_25_clean",
        "skiprows": 1,
        "sheet_name": "Fevr 25",
    },
    {
        "input": "Points marquants maintenance Mars 2025.xlsx",
        "output": "points_marquants_mars_25_clean",
        "skiprows": 1,
    },
]

processed_dataframes = {}
for file_info in files_to_process:
    df = process_maintenance_file(
        file_info["input"],
        file_info["output"],
        skiprows=file_info["skiprows"],
        sheet_name=file_info.get("sheet_name", 0),  # Use .get() for optional keys
    )
    if df is not None:
        processed_dataframes[file_info["output"]] = df

# --- Merging Logic (Jan, Feb, Mar 2025) ---

# Select the relevant dataframes for merging
dfs_to_merge = []
keys_to_merge = [
    "points_marquants_janv_25_clean",
    "points_marquants_fev_25_clean",
    "points_marquants_mars_25_clean",
]
for key in keys_to_merge:
    if key in processed_dataframes:
        dfs_to_merge.append(processed_dataframes[key])
    else:
        logging.warning(
            f"DataFrame '{key}' not found in processed data. It might have failed during processing."
        )

if not dfs_to_merge:
    logging.error("No dataframes available for merging. Exiting.")
    exit()

# Concatenate the selected dataframes
merged_df = pd.concat(dfs_to_merge, ignore_index=True)
logging.info(
    f"Concatenated {len(dfs_to_merge)} dataframes. Total rows before deduplication: {len(merged_df)}"
)

# Clean before deduplication
merged_df.dropna(
    subset=["date_debut_panne", "num_equip"], inplace=True
)  # Keep rows with essential keys
merged_df.dropna(how="all", inplace=True)  # Remove completely empty rows if any

# --- Deduplication: Keep row with the most recent 'date_fin_panne' ---
# Ensure 'date_fin_panne' is datetime for correct sorting
# (It should already be datetime from the processing function)
# If 'date_fin_panne' could be string here, convert it:
# merged_df['date_fin_panne'] = pd.to_datetime(merged_df['date_fin_panne'], format='%d/%m/%Y', errors='coerce')


# Sort by identifying keys and then by 'date_fin_panne' descending
# Place NaT dates last so valid dates are preferred
merged_df_sorted = merged_df.sort_values(
    by=[
        "date_debut_panne",
        "num_equip",
        "date_fin_panne",
    ],  # date_fin_panne is datetime here
    ascending=[True, True, False],  # Sort date_fin_panne descending (recent first)
    na_position="last",  # Put entries without a valid end date at the bottom
)

# Drop duplicates based on start date and equipment, keeping the first (most recent end date)
final_df = merged_df_sorted.drop_duplicates(
    subset=["date_debut_panne", "num_equip"], keep="first"
).reset_index(drop=True)

logging.info(f"Total rows after deduplication: {len(final_df)}")

# --- Final Output ---
# Convert dates back to string DD/MM/YYYY for the final output file
final_df["date_debut_panne"] = final_df["date_debut_panne"].dt.strftime("%d/%m/%Y")
final_df["date_fin_panne"] = (
    final_df["date_fin_panne"].dt.strftime("%d/%m/%Y").fillna("")
)  # Handle NaT

print("\n--- Final Merged DataFrame (Most Recent Entries) ---")
print(final_df)

# Save the final merged result
try:
    final_output_filename = "points_marquants_2025_fusionnes_recent.csv"
    final_output_path = os.path.join(
        os.getcwd(), final_output_filename
    )  # Save in current dir
    final_df.to_csv(final_output_path, index=False, sep=";", encoding="utf-8-sig")
    logging.info(f"Final merged data saved to: {final_output_path}")
except Exception as e:
    logging.error(f"Error saving final merged file: {e}")
