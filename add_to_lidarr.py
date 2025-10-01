import requests
import argparse
import sys

def get_existing_artists(lidarr_url, api_key):
    """Fetches all artists from Lidarr and returns a set of their MBIDs."""
    print("Fetching existing artists from Lidarr...")
    existing_mbids = set()
    try:
        headers = {"X-Api-Key": api_key}
        response = requests.get(f"{lidarr_url}/api/v1/artist", headers=headers, timeout=30)
        response.raise_for_status()
        artists = response.json()
        for artist in artists:
            if 'foreignArtistId' in artist:
                existing_mbids.add(artist['foreignArtistId'])
        print(f"Found {len(existing_mbids)} existing artists in Lidarr.")
        return existing_mbids
    except requests.exceptions.RequestException as e:
        print(f"Error: Could not connect to Lidarr to get existing artists: {e}", file=sys.stderr)
        return None

def add_artist_to_lidarr(mbid, lidarr_url, api_key, root_folder, quality_profile_id):
    """Adds a single artist to Lidarr by their MBID."""
    headers = {"X-Api-Key": api_key}
    artist_endpoint = f"{lidarr_url}/api/v1/artist"
    
    payload = {
        "foreignArtistId": mbid,
        "rootFolderPath": root_folder,
        "monitored": True,
        "qualityProfileId": quality_profile_id,
        "addOptions": {
            "searchForMissingAlbums": True
        }
    }
    
    try:
        response = requests.post(artist_endpoint, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        # A 201 status code means the artist was successfully created.
        if response.status_code == 201:
            return "ADDED", response.json().get('artistName', mbid)
        return f"UNEXPECTED_STATUS_{response.status_code}", response.text
    except requests.exceptions.RequestException as e:
        if e.response is not None:
            # Try to parse the JSON error response from Lidarr for more details
            try:
                error_json = e.response.json()
                # Lidarr often returns a list of error objects
                if isinstance(error_json, list) and error_json:
                    error_message = error_json[0].get('errorMessage', str(error_json))
                else:
                    error_message = str(error_json)
                return "FAILED", f"API Error: {error_message}"
            except ValueError: # If the response isn't JSON
                return "FAILED", f"HTTP {e.response.status_code} - {e.response.reason}"
        return "FAILED", str(e) # Fallback for connection errors etc.

def main(input_file, lidarr_url, api_key, root_folder, quality_profile_id=1):
    """Main function to process the file and add artists to Lidarr."""
    if not all([lidarr_url, api_key, root_folder]):
        print("Error: Lidarr URL, API Key, and Root Folder must be provided.", file=sys.stderr)
        return

    existing_mbids = get_existing_artists(lidarr_url, api_key)
    if existing_mbids is None:
        print("Halting execution due to failure fetching existing artists.", file=sys.stderr)
        return

    try:
        with open(input_file, "r", encoding="utf-8", errors="replace") as infile:
            print(f"\nProcessing artists from '{input_file}'...")
            for line in infile:
                line = line.strip()
                if "lidarr:NOT_FOUND" in line:
                    artist_name = line.split(" - ")[0]
                    print(f"-> Skipping '{artist_name}': No MBID found.")
                    continue
                
                if "lidarr:" in line:
                    parts = line.split("lidarr:")
                    artist_name = parts[0].strip(" - ")
                    mbid = parts[1].strip()

                    if mbid in existing_mbids:
                        print(f"-> Skipping '{artist_name}': Already exists in Lidarr.")
                        continue

                    print(f"-> Attempting to add '{artist_name}' ({mbid})...")
                    status, detail = add_artist_to_lidarr(mbid, lidarr_url, api_key, root_folder, quality_profile_id)
                    
                    if status == "ADDED":
                        print(f"  - SUCCESS: Added '{detail}'.")
                    elif status == "ALREADY_EXISTS":
                        print(f"  - INFO: '{artist_name}' already exists in Lidarr.")
                    else:
                        print(f"  - FAILED to add '{artist_name}': {detail}", file=sys.stderr)
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.", file=sys.stderr)
        return

    print("\nLidarr import process finished.")

if __name__ == "__main__":
    # This block only runs when the script is executed directly
    parser = argparse.ArgumentParser(description="Add artists to Lidarr from a file of MBIDs.")
    parser.add_argument("-i", "--input", default="search_results.txt", help="Input file with artist names and MBIDs.")
    parser.add_argument("--lidarr-url", required=True, help="URL for your Lidarr instance (e.g., http://localhost:8686).")
    parser.add_argument("--api-key", required=True, help="Your Lidarr API key.")
    parser.add_argument("--root-folder", required=True, help="The root folder path in Lidarr for new artists (e.g., /music).")
    parser.add_argument("--quality-profile-id", type=int, default=1, help="The quality profile ID to use for new artists. Defaults to 1.")
    args = parser.parse_args()
    main(args.input, args.lidarr_url, args.api_key, args.root_folder, args.quality_profile_id)