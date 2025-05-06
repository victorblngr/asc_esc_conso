import urllib.request
import base64
import os
from datetime import datetime

# set basic information
username = "boulanger@sytral.fr"
password = "Bougeront-Decroches-Broncho8"
url = "https://data.grandlyon.com/fr/datapusher/ws/rdata/tcl_sytral.tclalerteaccessibilite/all.csv?maxfeatures=-1&start=1&filename=alerte-accessibilite-reseau-transports-commun-lyonnais"

# prepare the request Object
request = urllib.request.Request(url)

# encode the username / password couple into a single base64 string
base64string = (
    base64.b64encode(bytes(f"{username}:{password}", "utf-8")).decode("utf-8").strip()
)

# then add this string into the Authorization header
request.add_header("Authorization", f"Basic {base64string}")

# Ensure the "csv" folder exists
os.makedirs("csv", exist_ok=True)

# Generate a timestamp for the file name
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# and open the url
try:
    with urllib.request.urlopen(request) as response:
        result = response.read().decode("utf-8")
        # Save the result to a CSV file in the "csv" folder with a timestamp
        file_name = f"csv/output_{timestamp}.csv"
        with open(file_name, "w", encoding="utf-8") as file:
            file.write(result)
        print(f"Data saved to {file_name}")
except urllib.error.URLError as e:
    print(f"Error opening URL: {e}")
