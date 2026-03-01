import os
import csv
import time
import json
from google import genai
from google.genai import types
from PIL import Image
from dotenv import load_dotenv

class QuotaExceededError(Exception):
    pass

# Configuration
load_dotenv() # Load variables from .env
API_KEY = os.environ.get("GEMINI_API_KEY")
IMAGE_DIR = "frienda_images"
CSV_FILE = "data/frienda_database.csv"
OUTPUT_CSV = os.environ.get("FRIENDA_OUTPUT_CSV", "frienda_database_complete.csv")

def setup_gemini():
    if not API_KEY:
        print("Error: GEMINI_API_KEY environment variable not set.")
        print("Please export your API key: export GEMINI_API_KEY='your_key_here'")
        return None
    
    client = genai.Client(api_key=API_KEY)
    return client

# --- Few-Shot Prompting Setup ---
few_shot_cache = None

def get_few_shot_examples():
    global few_shot_cache
    if few_shot_cache is not None:
        return few_shot_cache
        
    examples = []
    
    # Example 1: 1-1-001_kira.webp (Koraidon - 5 Star, Speed 4)
    img1_path = os.path.join(IMAGE_DIR, "1-1-001_kira.webp")
    if os.path.exists(img1_path):
        try:
            ex1_img = Image.open(img1_path).copy()
            ex1_output = '''{
  "PokeEne": "244",
  "HP": "130",
  "ATK": "113",
  "DEF": "97",
  "SP_ATK": "73",
  "SP_DEF": "85",
  "Speed": "4",
  "Type": "かくとう, ドラゴン",
  "Move": "アクセルブレイク",
  "MoveType": "かくとう",
  "Special": "",
  "Rarity": "5"
}'''
            examples.extend([
                "【入出力の例1（星5、すばやさ4の例）】以下の画像から情報を抽出しなさい:",
                ex1_img,
                "出力結果:\n" + ex1_output
            ])
        except Exception as e:
            print(f"Could not load example 1: {e}")

    # Example 2: 1-1-016_kira.webp (Blastoise - 4 Star, Speed 2)
    img2_path = os.path.join(IMAGE_DIR, "1-1-016_kira.webp")
    if os.path.exists(img2_path):
        try:
            ex2_img = Image.open(img2_path).copy()
            ex2_output = '''{
  "PokeEne": "180",
  "HP": "102",
  "ATK": "64",
  "DEF": "77",
  "SP_ATK": "66",
  "SP_DEF": "80",
  "Speed": "2",
  "Type": "みず",
  "Move": "ハイドロポンプ",
  "MoveType": "みず",
  "Special": "",
  "Rarity": "4"
}'''
            examples.extend([
                "【入出力の例2（星4、すばやさ2の例）】以下の画像から情報を抽出しなさい:",
                ex2_img,
                "出力結果:\n" + ex2_output
            ])
        except Exception as e:
            print(f"Could not load example 2: {e}")

    few_shot_cache = examples
    return examples

def analyze_image(client, image_path):
    print(f"Analyzing {image_path}...")
    try:
        img = Image.open(image_path)
    except Exception as e:
        print(f"Error opening image {image_path}: {e}")
        return None
        
    prompt = """
        このポケモンフレンダのピック画像から、以下の情報を読み取ってJSON形式で出力してください。
        数値がない場合は空文字にしてください。
        
        {
            "PokeEne": "ポケエネの数値 (例: 352)",
            "HP": "HPの数値 (例: 307)",
            "ATK": "ATK(攻撃)の数値",
            "DEF": "DEF(防御)の数値",
            "SP_ATK": "SP.ATK(特攻)の数値",
            "SP_DEF": "SP.DEF(特防)の数値",
            "Speed": "裏面の「すばやさ」という文字の下に矢羽が5つ並んでいます。その中で黄色く塗られている個数がすばやさの数値（1〜5の整数）です。グレーで塗られている矢羽は数えないでください。",
            "Type": "ポケモンのタイプアイコンの属性。**タイプが2種類ある場合は必ず2つとも読み取り、カンマと半角スペース区切りで出力してください**（例: じめん, ドラゴン や ほのお, ひこう）。必ずカタカナまたはひらがなで表記すること。漢字は不可。※わざのタイプ(MoveType)は1種類ですが、ポケモンのTypeは最大2種類あることに特に注意してください。",
            "Move": "わざの名前（ピックに記載されている通りの日本語表記で。英語に翻訳しないこと）",
            "MoveType": "わざのタイプ (必ずカタカナまたはひらがなで表記すること。漢字は不可)",
            "Special": "特殊ギミックがある場合のみ出力 (メガシンカ, テラスタル, タッグわざ, Zわざ)。なければ空文字",
            "Rarity": "フレンダピックの表面・裏面それぞれに、キャラ名の上に星が2〜5個並んでいます。星は重なって描かれているため、完全な形の星を数えようとすると誤認識する可能性があります。星型の頂点の山の数を数えるなどして、星がいくつあるか（2〜5の整数）判定してください。星がない場合や「スペシャル」と書かれている場合は文字列で『スペシャル』と出力してください。"
        }
    """
    
    # Prefix prompt with few-shot examples
    contents = get_few_shot_examples()
    contents.extend([
        "【本番の推論】以下の画像から情報を抽出し、JSONのみを出力しなさい:",
        prompt,
        img
    ])
    
    # New SDK usage
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        parsed_data = json.loads(response.text)
        if isinstance(parsed_data, list) and len(parsed_data) > 0:
            parsed_data = parsed_data[0]
        return parsed_data
    except Exception as e:
        error_str = str(e)
        if "429" in error_str or "quota" in error_str.lower() or "RESOURCE_EXHAUSTED" in error_str:
                print(f"!!! QUOTA EXCEEDED: Stopping future requests. !!!")
                raise QuotaExceededError(e)

        if "404" in error_str or "NOT_FOUND" in error_str:
            print(f"  Model not found or not supported. Error: {e}")
            # Try to list models to help debug
            try:
                print("  Available models:")
                for m in client.models.list():
                    if "generateContent" in m.supported_generation_methods:
                        print(f"    - {m.name}")
            except:
                pass
        else:
            print(f"Error analyzing {image_path}: {e}")
        return None

def main():
    if not os.path.exists(CSV_FILE):
        print(f"Error: {CSV_FILE} not found. Run scrape_frienda.py first.")
        return

    model = setup_gemini()
    if not model:
        return

    # Read existing completed IDs/Data
    completed_ids = set()
    completed_data = {}
    if os.path.exists(OUTPUT_CSV):
        try:
            with open(OUTPUT_CSV, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                fieldnames = list(reader.fieldnames)
                # Ensure all potential new fields are in fieldnames for future writes
                for new_field in ["MoveType", "Special", "Rarity"]:
                    if new_field not in fieldnames:
                        fieldnames.append(new_field)
                
                for row in reader:
                    # Check if the row exists in the complete file. 
                    # We accept it even if PokeEne is missing, so we can preserve manual edits (like URLs)
                    # and allow the script to append new fields like Series without overwriting.
                    if row.get('ID'): 
                        # Only mark as "complete" if analysis data (PokeEne) is present
                        if row.get('PokeEne'):
                            completed_ids.add(row['ID'])
                        
                        # Always store data to preserve manual edits (like OriginalURL)
                        completed_data[row['ID']] = row
        except Exception:
            pass

    # Read base CSV to find work
    rows = []
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # We use the complete CSV's fieldnames if available to ensure consistency, 
        # but base CSV might dictate the order. Let's merge.
        base_fieldnames = list(reader.fieldnames)
        
        # Ensure we have a master list of fieldnames including new ones
        master_fieldnames = base_fieldnames.copy()
        for f in ["MoveType", "Special", "Rarity", "Variant", "Series"]:
             if f not in master_fieldnames:
                 master_fieldnames.append(f)

        # Filter out rows that might be missing 'ID' due to header issues or empty lines
        rows = [row for row in list(reader) if 'ID' in row and row['ID']]
        
        # Priority Logic
        # 1. _kira files
        # 2. Parallel (A)
        # 3. Wonder (W)
        # 4. Shiny (★/_star)
        # 5. Others
        def get_priority(row):
            item_id = row['ID']
            filename = row.get('ImageFile', '')
            score = 0
            
            if '_kira' in filename:
                score += 10
            
            # User request: Prioritize Special (starts with p)
            if item_id.lower().startswith('p'):
                score += 8

            if 'A' in item_id and item_id.endswith('A'):
                score += 5
            
            if 'W' in item_id:
                score += 5
            
            if '★' in item_id or '_star' in filename:
                score += 5
            
            return score

        # Sort rows by priority (descending)
        rows.sort(key=get_priority, reverse=True)

    print(f"Loaded {len(rows)} items. Found {len(completed_ids)} already completed.")

    stop_processing = False

    updated_rows = []
    for row in rows:
        # Remove potential restkey (None) if the csv was malformed
        if None in row:
            del row[None]
        
        # Ensure all fields are present (default empty) to prevent KeyError during write if missing
        for f in master_fieldnames:
            if f not in row:
                row[f] = ""
        
        item_id = row['ID']
        
        # Determine Series based on ID
        series = "その他"
        if item_id.lower().startswith("p"):
            series = "スペシャル"
        elif item_id.startswith("1-1"):
            series = "1だん"
        elif item_id.startswith("1-2"):
            series = "2だん"
        elif item_id.startswith("1-3"):
            series = "3だん"
        elif item_id.startswith("1-4"):
            series = "4だん"
        elif item_id.startswith("1-5"):
            series = "5だん"
        elif item_id.startswith("2-1"):
            series = "ベストタッグ1だん"
        elif item_id.startswith("2-2"):
            series = "ベストタッグ2だん"
        elif item_id.startswith("2-3"):
            series = "ベストタッグ3だん"
        elif item_id.startswith("2-4"):
            series = "ベストタッグ4だん"

        if stop_processing:
            # If stopped, just add the row (either completed or base) to keep data
            row_to_add = {}
            if row['ID'] in completed_data:
                 row_to_add = completed_data[row['ID']]
            else:
                 row_to_add = row
            
            # Ensure Series is added
            row_to_add['Series'] = series
            # Ensure Variant is added/updated
            variant = ""
            if "A" in item_id and item_id.endswith("A"):
                variant = "パラレル"
            elif "W" in item_id:
                variant = "ワンダー"
            elif "★" in item_id or "_star" in row.get('ImageFile', ''):
                variant = "色違い"
            row_to_add['Variant'] = variant

            updated_rows.append(row_to_add)
            continue

        item_id = row['ID']
        
        # Skip if already analyzed
        if item_id in completed_ids:
            print(f"Skipping {row['Name']} (ID: {item_id}) - Already analyzed")
            # Merge: Start with current row (contains OriginalURL), update with analysis results
            merged_row = row.copy()
            merged_row.update(completed_data[item_id])
            # Restore OriginalURL if it was overwritten or missing in completed_data
            if 'OriginalURL' in row and row['OriginalURL']:
                 merged_row['OriginalURL'] = row['OriginalURL']
            
            # Re-evaluate Variant even for completed items (in case logic changed)
            variant = ""
            if "A" in item_id and item_id.endswith("A"):
                variant = "パラレル"
            elif "W" in item_id:
                variant = "ワンダー"
            elif "★" in item_id or "_star" in row.get('ImageFile', ''):
                variant = "色違い"
            
            merged_row['Variant'] = variant
            
            # Determine Series based on ID (re-evaluate)
            series = "その他"
            if item_id.lower().startswith("p"):
                series = "スペシャル"
            elif item_id.startswith("1-1"):
                series = "1だん"
            elif item_id.startswith("1-2"):
                series = "2だん"
            elif item_id.startswith("1-3"):
                series = "3だん"
            elif item_id.startswith("1-4"):
                series = "4だん"
            elif item_id.startswith("1-5"):
                series = "5だん"
            elif item_id.startswith("2-1"):
                series = "ベストタッグ1だん"
            elif item_id.startswith("2-2"):
                series = "ベストタッグ2だん"
            elif item_id.startswith("2-3"):
                series = "ベストタッグ3だん"
            elif item_id.startswith("2-4"):
                series = "ベストタッグ4だん"
            
            merged_row['Series'] = series
            
            updated_rows.append(merged_row)
            continue

        # Merge partial data if exists (to preserve manual edits)
        if item_id in completed_data:
            for k, v in completed_data[item_id].items():
                if v: # Only overwrite with non-empty values from completed_data
                     row[k] = v

        image_filename = row['ImageFile']
        image_path = os.path.join(IMAGE_DIR, image_filename)
        
        # Determine Variant for new items too
        variant = ""
        if "A" in item_id and item_id.endswith("A"):
            variant = "パラレル"
        elif "W" in item_id:
            variant = "ワンダー"
        elif "★" in item_id or "_star" in image_filename:
            variant = "色違い"
        
        row['Variant'] = variant
        
        if os.path.exists(image_path):
            # Only analyze if data is missing (optional optimization)
            # But here we want to fill empty fields
            
            try:
                data = analyze_image(model, image_path)
            except QuotaExceededError:
                print("Quota limit reached. Stopping further API calls and saving progress.")
                stop_processing = True
                updated_rows.append(row)
                continue
            
            if data:
                # Helper to update only if empty
                def update_if_empty(key, val):
                    if not row.get(key) and val:
                        row[key] = val

                update_if_empty('PokeEne', data.get('PokeEne', ''))
                update_if_empty('HP', data.get('HP', ''))
                update_if_empty('ATK', data.get('ATK', ''))
                update_if_empty('DEF', data.get('DEF', ''))
                update_if_empty('SP.ATK', data.get('SP_ATK', ''))
                update_if_empty('SP.DEF', data.get('SP_DEF', ''))
                update_if_empty('Speed', data.get('Speed', ''))
                update_if_empty('Type', data.get('Type', ''))
                update_if_empty('Move', data.get('Move', ''))
                update_if_empty('MoveType', data.get('MoveType', ''))
                update_if_empty('Special', data.get('Special', ''))
                update_if_empty('Rarity', data.get('Rarity', ''))

                print(f"  -> Extracted: {row['Name']} (PE: {row['PokeEne']}, Rarity: {row['Rarity']}, Move: {row['Move']}, Type: {row['MoveType']}, Special: {row['Special']})")
            
            # Rate limiting / politeness
            time.sleep(1) 
        else:
            print(f"  Image not found: {image_path}")
        
        # Determine Series based on ID
        series = "その他"
        if item_id.lower().startswith("p"):
            series = "スペシャル"
        elif item_id.startswith("1-1"):
            series = "1だん"
        elif item_id.startswith("1-2"):
            series = "2だん"
        elif item_id.startswith("1-3"):
            series = "3だん"
        elif item_id.startswith("1-4"):
            series = "4だん"
        elif item_id.startswith("1-5"):
            series = "5だん"
        elif item_id.startswith("2-1"):
            series = "ベストタッグ1だん"
        elif item_id.startswith("2-2"):
            series = "ベストタッグ2だん"
        elif item_id.startswith("2-3"):
            series = "ベストタッグ3だん"
        elif item_id.startswith("2-4"):
            series = "ベストタッグ4だん"
        
        row['Series'] = series
        
        updated_rows.append(row)

    # Save to new CSV
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=master_fieldnames)
        writer.writeheader()
        writer.writerows(updated_rows)

    # Run type consolidation step automatically to resolve fluctuations
    import consolidate_types
    print("\nRunning type consolidation to resolve any inconsistencies...")
    consolidate_types.consolidate_types()

    print(f"\nDone! Saved complete database to {OUTPUT_CSV}")

    if stop_processing:
        import sys
        sys.exit(2)

if __name__ == "__main__":
    main()
