from pathlib import Path
import zipfile

# --- Configuration ---
# Determine the directory where the script is located
SCRIPT_DIR = Path(__file__).resolve().parent

# Directory containing the ZIP files.
# Based on your input, files are in "C:\Users\VBO\code\asc_esc_consolide\info_tcl_hist\"
# If this script is in "C:\Users\VBO\code\asc_esc_consolide\",
# then the relative path to the ZIPs is "info_tcl_hist".
SOURCE_ZIP_DIR_NAME = "info_tcl_hist"
SOURCE_ZIP_DIR = SCRIPT_DIR / SOURCE_ZIP_DIR_NAME

# Directory where ZIP contents will be extracted, relative to the script's location
EXTRACT_DIR_NAME = "extracted_zip_contents"
EXTRACT_LOCATION = SCRIPT_DIR / EXTRACT_DIR_NAME


def extract_local_zip_files(zip_files_directory: Path, extract_to_directory: Path):
    """
    Finds all .zip files in the zip_files_directory,
    and extracts their contents into subdirectories within extract_to_directory.
    """
    if not zip_files_directory.is_dir():
        print(f"Error: Source directory for ZIP files not found: {zip_files_directory}")
        return
    # Create local extract directory if it doesn't exist
    extract_to_directory.mkdir(parents=True, exist_ok=True)
    print(f"Ensured extraction directory exists: {extract_to_directory}")

    zip_files_found = 0
    processed_files = 0

    print(f"Scanning for .zip files in: {zip_files_directory}")
    for item_path in zip_files_directory.iterdir():
        if item_path.is_file() and item_path.name.lower().endswith(".zip"):
            zip_files_found += 1
            zip_file_name = item_path.name
            print(f"Found ZIP file: {zip_file_name}")

            # Create a subdirectory for each zip's contents, named after the zip file (without .zip)
            specific_extract_path = extract_to_directory / zip_file_name[:-4]

            print(
                f"Attempting to extract {zip_file_name} to {specific_extract_path}..."
            )
            try:
                specific_extract_path.mkdir(
                    parents=True, exist_ok=True
                )  # Ensure sub-extract dir exists
                with zipfile.ZipFile(item_path, "r") as zip_ref:
                    zip_ref.extractall(specific_extract_path)
                print(
                    f"Successfully extracted {zip_file_name} to {specific_extract_path}"
                )
                processed_files += 1
            except zipfile.BadZipFile:
                print(
                    f"Error: {zip_file_name} is not a valid ZIP file or is corrupted."
                )
            except Exception as e_zip:
                print(f"Error extracting {zip_file_name}: {e_zip}")

    if zip_files_found == 0:
        print(f"No .zip files found in the directory: {zip_files_directory}")
    else:
        print(f"Processed {processed_files} out of {zip_files_found} ZIP files found.")


if __name__ == "__main__":
    print(f"Script starting. Looking for ZIP files in: {SOURCE_ZIP_DIR}")
    print(f"Extraction target directory: {EXTRACT_LOCATION}")

    extract_local_zip_files(
        SOURCE_ZIP_DIR,
        EXTRACT_LOCATION,
    )
    print("Script finished.")
