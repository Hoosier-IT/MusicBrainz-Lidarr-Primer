import os
import argparse

DEFAULT_OUTPUT_FILE = "folders.txt"

# Common system/service folders to ignore during scanning
IGNORE_DIRS = {
    "@eaDir",         # Synology PhotoStation/AudioStation
    ".DS_Store",      # macOS
    "lost+found",     # Linux filesystem recovery
    "$RECYCLE.BIN",   # Windows Recycle Bin
    "System Volume Information",
}

def create_artist_list(library_path, output_file):
    """
    Scans a music library path for subdirectories and writes their names to an output file.
    """
    if not os.path.isdir(library_path):
        print(f"Error: Library path '{library_path}' is not a valid directory.")
        return

    print(f"Scanning directory: {library_path}")
    artist_folders = []
    try:
        # Get all items in the directory and filter for directories not in the ignore list
        for item in os.listdir(library_path):
            if os.path.isdir(os.path.join(library_path, item)) and item not in IGNORE_DIRS:
                artist_folders.append(item)
    except OSError as e:
        print(f"Error reading directory: {e}")
        return

    if not artist_folders:
        print("No artist folders found in the specified directory.")
        return

    artist_folders.sort() # Sort alphabetically

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            for artist in artist_folders:
                f.write(artist + "\n")
        print(f"Successfully wrote {len(artist_folders)} artist names to '{output_file}'.")
    except IOError as e:
        print(f"Error writing to file '{output_file}': {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scan a music library directory and create a list of artist folders.")
    parser.add_argument("library_path", help="The path to your music library directory.")
    parser.add_argument("-o", "--output", default=DEFAULT_OUTPUT_FILE, help=f"The output file name. Defaults to '{DEFAULT_OUTPUT_FILE}'.")
    args = parser.parse_args()
    create_artist_list(args.library_path, args.output)