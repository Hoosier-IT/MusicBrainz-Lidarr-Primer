# MusicBrainz-Lidarr-Primer

Got an existing library but tired of Lidarr searches failing while they are rebuilding the server cache? Don't have time to search MusicBrainz?

Introducing MusicBrainz-Lidarr-Primer!

A two-stage Python script pipeline to bulk-import artists into Lidarr.

1.  `musicbrainz_lookup.py`: Reads a list of artist names from `folders.txt`, finds their official MusicBrainz ID (MBID), and saves the results to `search_results.txt`.
2.  `add_to_lidarr.py`: Reads `search_results.txt` and adds each artist to your Lidarr instance via its API.

## Features

- **Resilient & Resumable**: If the script fails (e.g., due to a network error), it can be restarted and will automatically resume from where it left off.
- **Automatic Retries**: Handles temporary network blips by automatically retrying failed requests.
- **Efficient**: Proactively checks your Lidarr library to skip artists that are already added.
- **User-Friendly**: Provides a progress bar (`tqdm`) to show progress during the lookup phase.
- **Configurable**: All sensitive information (API keys, URLs) and settings are passed as command-line arguments, not hardcoded.

---

## Prerequisites

- **A running Lidarr instance**
- **Python 3.6+**: These scripts require Python to run.
  - To check if Python is installed, open your terminal and run: `python3 --version`.
  - If it's not installed, follow the instructions for your operating system:
    - **Windows**: Download the latest Python 3 release from python.org. During installation, make sure to check the box that says **"Add Python to PATH"**.
    - **macOS**: The recommended way to install Python is via Homebrew. After installing Homebrew, run: `brew install python`.
    - **Debian/Ubuntu**:
      ```bash
      sudo apt update
      sudo apt install python3
      ```

---

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd <your-repo-directory>
    ```

2.  **Ensure `pip` is installed:**
    `pip` is Python's package installer and is usually included with Python. You can check if it's installed by running `python3 -m pip --version`. If it's not found, you can install it with one of the following methods:

    *   **Using Python's `ensurepip` (Recommended for most systems):**
        ```bash
        python3 -m ensurepip --upgrade
        ```
    *   **On Debian/Ubuntu systems:**
        ```bash
        sudo apt update
        sudo apt install python3-pip
        ```

3.  **Install dependencies:**
    This will install the `requests` and `tqdm` libraries.
    ```bash
    pip3 install -r requirements.txt
    ```

4.  **Create your artist list:**
    Create a file named `folders.txt` in the same directory. Add one artist name per line.

    *Example `folders.txt`:*
    ```
    Led Zeppelin
    Pink Floyd
    The Beatles
    ```

5.  **Update the User-Agent:**
    Open `musicbrainz_lookup.py` and replace the placeholder email in the `HEADERS` dictionary with your own. This is required by the MusicBrainz API policy.
    ```python
    HEADERS = {
        "User-Agent": "MusicBrainzLookupScript/1.0 ( your-real-email@example.com )"
    }
    ```

---

## Usage

You will run the pipeline from your terminal, providing your Lidarr details as arguments.

### Running the Full Pipeline

This command will run the MusicBrainz lookup and then automatically trigger the Lidarr import.

```bash
python3 musicbrainz_lookup.py --add-to-lidarr --lidarr-url "http://LIDARR_HOST:8686" --api-key "YOUR_LIDARR_API_KEY" --root-folder "/path/to/your/music"
```

**Argument Breakdown:**

- `--add-to-lidarr`: This flag tells the first script to automatically start the second script upon completion.
- `--lidarr-url`: The URL for your Lidarr instance.
- `--api-key`: Your Lidarr API key (found in Lidarr under `Settings` > `General`).
- `--root-folder`: The absolute path to your music library's root folder *as seen by Lidarr*.
- `--quality-profile-id` (Optional): The ID of the quality profile to use. Defaults to `1`.

### Running Only the Lidarr Import

If you need to re-run only the import step (e.g., to debug or after changing Lidarr settings), you can run the second script directly. This assumes `search_results.txt` already exists.

```bash
python3 add_to_lidarr.py --lidarr-url "http://LIDARR_HOST:8686" --api-key "YOUR_LIDARR_API_KEY" --root-folder "/path/to/your/music"
```