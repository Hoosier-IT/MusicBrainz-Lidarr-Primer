import requests
import time
import os
import argparse
from tqdm import tqdm

# Import the main function from the second script to trigger it later
from add_to_lidarr import main as add_to_lidarr_main

# Default file paths, can be overridden by command-line arguments
DEFAULT_INPUT_FILE = "folders.txt"
DEFAULT_OUTPUT_FILE = "search_results.txt"
BASE_URL = "https://musicbrainz.org/ws/2/artist/"

# IMPORTANT: Update the User-Agent with your own application name and contact information.
# This is required by the MusicBrainz API policy.
HEADERS = {
    "User-Agent": "MusicBrainzLookupScript/1.0 ( your-email@example.com )"
}

def get_best_match(artist_name):
    """
    Queries the MusicBrainz API for a given artist name and returns the best match.
    """
    params = {
        "query": artist_name,
        "fmt": "json",
        "limit": 1
    }
    retries = 3
    for attempt in range(retries):
        try:
            response = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=10)
            # Raise an exception for 4xx or 5xx status codes
            response.raise_for_status()
            data = response.json()
            # Safely access nested dictionary keys
            if data.get("artists"):
                best_match = data["artists"][0]
                mbid = best_match.get("id")
                name = best_match.get("name")
                if mbid and name:
                    return f"{name} - lidarr:{mbid}"
            break # Break the loop if request was successful but no artist found
        except requests.exceptions.RequestException as e:
            tqdm.write(f"  -> Network error for '{artist_name}' (attempt {attempt + 1}/{retries}): {e}")
            if attempt < retries - 1:
                tqdm.write("     Pausing for 5 seconds before retrying...")
                time.sleep(5)
            else:
                tqdm.write(f"  -> All retries failed for '{artist_name}'.")
                return None # All retries failed, halt the script
        except ValueError:  # Catches JSON decoding errors
            tqdm.write(f"  -> Error decoding JSON response for '{artist_name}'. Cannot retry.")
            return None  # Indicates a failure

    # If no artists were found in the response
    return f"{artist_name} - lidarr:NOT_FOUND"

def main(args):
    """
    Main function to read artists, process them, and write results.
    """
    processed_artists = set()
    # --- Resume Logic ---
    if os.path.exists(args.output):
        print(f"Output file found. Reading previously processed artists from '{args.output}'...")
        with open(args.output, "r", encoding="utf-8") as f:
            for line in f:
                # Safely split the line to get the artist name, avoiding errors on malformed lines
                parts = line.rpartition(" - lidarr:")
                if parts[1]:  # This is true only if " - lidarr:" was found
                    processed_artists.add(parts[0].strip())
        print(f"Resuming. Found {len(processed_artists)} previously processed artists.")

    # --- Read Input File ---
    try:
        with open(args.input, "r", encoding="utf-8", errors="replace") as infile:
            # Create a list of all artists to be processed
            all_artists = [line.strip() for line in infile if line.strip()]
    except FileNotFoundError:
        print(f"Error: Input file not found at '{args.input}'")
        return

    artists_to_process = [artist for artist in all_artists if artist not in processed_artists]
    
    if not artists_to_process:
        print("All artists have already been processed. Nothing to do.")
        return

    print(f"\nStarting processing for {len(artists_to_process)} new artists...")

    # --- Processing Loop ---
    # Open output file in append mode to preserve existing data
    completed_successfully = True
    with open(args.output, "a", encoding="utf-8") as outfile, tqdm(artists_to_process, desc="Looking up artists") as pbar:
        for artist_name in pbar:
            pbar.set_postfix_str(artist_name)
            result = get_best_match(artist_name)

            if result:
                tqdm.write(f"  -> Found: {result}")
                outfile.write(result + "\n")
                # Immediately write to disk to prevent data loss on interruption
                outfile.flush()
            else:
                # If a network or JSON error occurred, stop the script.
                # It can be restarted to resume from the point of failure.
                print(f"Stopping script due to a processing failure on '{artist_name}'. Please check the error and restart.")
                completed_successfully = False 
                break

            # Respect the MusicBrainz API rate limit (1 request per second)
            time.sleep(1)
    
    print("\nMusicBrainz lookup finished.")

    # --- Trigger the next script ---
    if completed_successfully and artists_to_process and args.add_to_lidarr:
        print("\n" + "="*40)
        print("All artists looked up. Starting Lidarr import process...")
        print("="*40 + "\n")
        # Pass the output file from this script as the input for the next
        add_to_lidarr_main(
            input_file=args.output,
            lidarr_url=args.lidarr_url,
            api_key=args.api_key,
            root_folder=args.root_folder,
            quality_profile_id=args.quality_profile_id
        )


if __name__ == "__main__":
    # --- Command-Line Argument Parsing ---
    parser = argparse.ArgumentParser(
        description="Look up artist MusicBrainz IDs (MBIDs) from a list of names and save them to a file. Resumes on subsequent runs."
    )
    parser.add_argument(
        "-i", "--input",
        default=DEFAULT_INPUT_FILE,
        help=f"Input file with artist names, one per line. Defaults to '{DEFAULT_INPUT_FILE}'"
    )
    parser.add_argument(
        "-o", "--output",
        default=DEFAULT_OUTPUT_FILE,
        help=f"Output file for results. Defaults to '{DEFAULT_OUTPUT_FILE}'"
    )
    # Arguments for the second script
    parser.add_argument("--add-to-lidarr", action="store_true", help="Automatically run the add_to_lidarr script upon completion.")
    parser.add_argument("--lidarr-url", help="URL for your Lidarr instance (e.g., http://localhost:8686).")
    parser.add_argument("--api-key", help="Your Lidarr API key.")
    parser.add_argument("--root-folder", help="The root folder path in Lidarr for new artists (e.g., /music).")
    parser.add_argument("--quality-profile-id", type=int, default=1, help="The quality profile ID to use for new artists in Lidarr. Defaults to 1.")
    args = parser.parse_args()

    main(args)