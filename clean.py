import os
from pathlib import Path

# --- Configuration ---
# The absolute path to the directory containing subfolders to be cleaned.
BASE_EXTRACT_DIR = Path(r"C:\Users\VBO\code\asc_esc_consolide\extracted_zip_contents")


def clean_folders_in_directory(directory_to_clean: Path):
    """
    Cleans the subfolders within the specified directory by keeping only .csv files.
    All other files in these subfolders will be deleted.
    """
    print(f"Starting cleanup of subfolders in: {directory_to_clean}")
    if not directory_to_clean.is_dir():
        print(f"Error: Target directory not found: {directory_to_clean}")
        return

    cleaned_subfolders_count = 0
    for item_path in directory_to_clean.iterdir():
        if item_path.is_dir():  # Process only subfolders
            subfolder_path = item_path
            print(f"\nProcessing subfolder: {subfolder_path.name}")
            files_in_subfolder = 0
            csv_files_kept = 0
            files_deleted = 0

            for file_path in subfolder_path.iterdir():
                if file_path.is_file():
                    files_in_subfolder += 1
                    if file_path.suffix.lower() == ".csv":
                        print(f"  Keeping CSV file: {file_path.name}")
                        csv_files_kept += 1
                    else:
                        print(f"  Deleting non-CSV file: {file_path.name}")
                        try:
                            file_path.unlink()  # Deletes the file
                            files_deleted += 1
                        except OSError as e:
                            print(f"    Error deleting file {file_path.name}: {e}")

            print(
                f"  Subfolder '{subfolder_path.name}' summary: {csv_files_kept} CSV file(s) kept, {files_deleted} file(s) deleted out of {files_in_subfolder} total files."
            )
            cleaned_subfolders_count += 1

    if cleaned_subfolders_count == 0:
        print(f"\nNo subfolders found in {directory_to_clean} to clean.")
    else:
        print(f"\nCleanup finished. Processed {cleaned_subfolders_count} subfolder(s).")


if __name__ == "__main__":
    clean_folders_in_directory(BASE_EXTRACT_DIR)
    print("File cleaning script finished.")
