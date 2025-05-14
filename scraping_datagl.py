import urllib.request
import urllib.error
import base64
import os
from datetime import datetime
from pathlib import Path

# --- Configuration ---
# Retrieve credentials from environment variables for security

# USERNAME = os.environ.get("SYTRAL_USERNAME")
# PASSWORD = os.environ.get("SYTRAL_PASSWORD")

USERNAME = "boulanger@sytral.fr"
PASSWORD = "Bougeront-Decroches-Broncho8"

URL = "https://data.grandlyon.com/fr/datapusher/ws/rdata/tcl_sytral.tclalerteaccessibilite/all.csv?maxfeatures=-1&start=1&filename=alerte-accessibilite-reseau-transports-commun-lyonnais"
OUTPUT_DIR_NAME = "csv_data"  # Or keep as "csv" if preferred
FILENAME_PREFIX = "output_alerte_accessibilite"


def main():
    """
    Main function to fetch accessibility alert data from Grand Lyon,
    and save it to a CSV file.
    """
    if not USERNAME or not PASSWORD:
        print(
            "Error: SYTRAL_USERNAME and/or SYTRAL_PASSWORD environment variables not set."
        )
        print("Please set these variables before running the script.")
        return

    # Prepare the request Object
    request = urllib.request.Request(URL)

    # Encode the username / password couple into a single base64 string
    auth_string = f"{USERNAME}:{PASSWORD}"
    base64_auth_string = (
        base64.b64encode(auth_string.encode("utf-8")).decode("utf-8").strip()
    )

    # Add the Authorization header
    request.add_header("Authorization", f"Basic {base64_auth_string}")
    print(f"Attempting to download data for user: {USERNAME} from {URL}")

    # Ensure the output directory exists
    output_dir = Path(OUTPUT_DIR_NAME)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate a timestamp for the file name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"{FILENAME_PREFIX}_{timestamp}.csv"
    file_path = output_dir / file_name

    # Open the URL and save the data
    try:
        with urllib.request.urlopen(request) as response:
            if response.status == 200:
                print(f"Successfully connected. HTTP Status: {response.status}")
                result = response.read().decode("utf-8")
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(result)
                print(f"Data successfully saved to {file_path}")
            else:
                print(
                    f"Failed to download data. HTTP Status: {response.status} {response.reason}"
                )
    except urllib.error.HTTPError as e:
        # HTTPError provides more specific error information
        print(f"HTTP Error: {e.code} - {e.reason}")
        if e.code == 401:
            print(
                "Authentication failed. Please check your credentials (SYTRAL_USERNAME, SYTRAL_PASSWORD)."
            )
        # You might want to log e.read() to see the server's error message, but be cautious with sensitive data.
    except urllib.error.URLError as e:
        print(
            f"URL Error: {e.reason} (Could not reach the server or other network issue)"
        )
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
