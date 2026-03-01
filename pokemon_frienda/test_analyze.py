import os
import sys
import json
from analyze_frienda import setup_gemini, analyze_image

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_analyze.py <image_path>")
        return
        
    image_path = sys.argv[1]
    if not os.path.exists(image_path):
        print(f"Error: {image_path} does not exist.")
        return
        
    client = setup_gemini()
    if not client:
        return
        
    print(f"Testing OCR prompt on: {image_path}")
    result = analyze_image(client, image_path)
    if result:
        print("\n--- OCR Result ---")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("Failed to get result from Gemini.")

if __name__ == "__main__":
    main()
