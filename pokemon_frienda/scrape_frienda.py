import urllib.request
import urllib.parse
import re
import csv
import os
import time
import sys

BASE_URL = "https://pokemonfrienda.com/new/" # Fallback or keep for reference
TARGET_URL = "https://pokemonfrienda.com/new/bt4.html"
IMAGE_DIR = "frienda_images"
CSV_FILE = "frienda_database.csv"

def main():
    # Handle command line argument for URL
    target_url = TARGET_URL
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
    
    # Ensure target_url ends with a slash if it's a directory? 
    # Actually, urljoin handles this: existing path components are kept if not ending in /, 
    # but strictly speaking if the page is .../wonder/ (directory), relative "img/..." works.
    # If page is .../bt4.html (file), relative "img/..." replaces bt4.html?
    # No, usually "img/..." from "bt4.html" means "bt4.html/../img" ? 
    # Let's check the original site structure.
    # https://pokemonfrienda.com/new/bt4.html -> img is "img/bt4/..."
    # If we are at /new/bt4.html, "img/..." usually resolves to /new/img/...
    # But for /new/wonder/ (index), "img/..." resolves to /new/wonder/img/...
    
    # We should trust urljoin.

    # Create image directory
    if not os.path.exists(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)
        print(f"Created directory: {IMAGE_DIR}")

    # Load existing IDs
    existing_ids = set()
    if os.path.exists(CSV_FILE):
        try:
            with open(CSV_FILE, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    existing_ids.add(row['ID'])
        except Exception:
            pass # File might be empty or corrupted

    # Fetch HTML
    print(f"Fetching {target_url}...")
    try:
        with urllib.request.urlopen(target_url) as response:
            html_content = response.read().decode('utf-8')
    except Exception as e:
        print(f"Error fetching URL: {e}")
        return

    # Regex to find items
    # Looking for: data-modal="friendapick" ... data-img="..." ... alt="..."
    # Note: Attributes might be in any order, but usually consistent.
    # The snippet: <a href="..." ... data-img="img/bt4/2-4-001_kira.webp"><img src="..." alt="ジガルデ" ...>
    
    # We'll use a specific regex that assumes standard ordering or handle robustly.
    # Let's find the <a> tag first.
    
    # Pattern designed to capture data-img and then find the alt inside
    pattern = re.compile(r'data-modal="friendapick"[^>]*data-img="([^"]+)"[^>]*>.*?<img[^>]*alt="([^"]+)"', re.DOTALL)
    
    matches = pattern.findall(html_content)
    
    print(f"Found {len(matches)} items.")
    
    data_list = []

    for img_rel_path, name in matches:
        # img_rel_path example: img/bt4/2-4-001_kira.webp
        
        # Construct full URL relative to the page URL
        img_url = urllib.parse.urljoin(target_url, img_rel_path)
        
        # Extract ID from filename
        # Filename: 2-4-001_kira.webp -> ID: 2-4-001
        # Filename: 2-4-035.webp -> ID: 2-4-035
        filename = os.path.basename(img_rel_path)
        name_part = os.path.splitext(filename)[0] # "2-4-001_kira" or "2-4-035"
        item_id = name_part.split('_')[0] 
        
        if item_id in existing_ids:
            print(f"Skipping {name} (ID: {item_id}) - Already exists in DB")
            continue

        # Sanitize filename for local storage (e.g., replace ★ with _star)
        safe_filename = filename.replace('★', '_star')
        
        # Local filename
        local_filename = os.path.join(IMAGE_DIR, safe_filename)
        
        print(f"Processing {name} (ID: {item_id})...")
        
        # Download image
        if not os.path.exists(local_filename):
            try:
                # Encode URL to handle special characters (like ★)
                # safe=':/' preserves protocol and path separators
                safe_img_url = urllib.parse.quote(img_url, safe=':/')
                urllib.request.urlretrieve(safe_img_url, local_filename)
                print(f"  Downloaded {safe_filename}")
                time.sleep(0.5) # Be polite
            except Exception as e:
                print(f"  Failed to download {img_url}: {e}")
        else:
            print(f"  Already exists: {filename}")

        data_list.append({
            "ID": item_id,
            "Name": name,
            "ImageFile": safe_filename,
            "OriginalURL": img_url,
            "PokeEne": "",
            "HP": "",
            "ATK": "",
            "DEF": "",
            "SP.ATK": "",
            "SP.DEF": "",
            "Speed": "", # Need to figure out how to represent arrows
            "Type": "",
            "Move": ""
        })

    # Write to CSV
    if data_list:
        file_exists = os.path.exists(CSV_FILE)
        mode = 'a' if file_exists else 'w'
        
        fieldnames = ["ID", "Name", "ImageFile", "OriginalURL", "PokeEne", "HP", "ATK", "DEF", "SP.ATK", "SP.DEF", "Speed", "Type", "Move"]
        
        with open(CSV_FILE, mode, newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerows(data_list)
        print(f"Successfully appended {len(data_list)} items to {CSV_FILE}")
    else:
        print("No items found. Regex might need adjustment.")

if __name__ == "__main__":
    main()
