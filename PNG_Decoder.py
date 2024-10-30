import base64
import json
from tkinter import Tk, filedialog, messagebox
from PIL import Image
from PIL.ExifTags import TAGS
import os

def extract_base64_from_image(image_path):
    """
    Extracts Base64-encoded data embedded in the metadata of a PNG image and returns the decoded JSON.
    """
    try:
        # Open the image and get its EXIF data
        image = Image.open(image_path)
        exif_data = image._getexif()

        if not exif_data:
            raise ValueError("No EXIF data found in the image.")

        # Search for the 'UserComment' field which contains the Base64-encoded data
        user_comment_raw = None
        for tag, value in exif_data.items():
            tag_name = TAGS.get(tag, tag)
            if tag_name == 'UserComment':
                user_comment_raw = value.decode('utf-8', 'ignore')
                break

        if not user_comment_raw:
            raise ValueError("No 'UserComment' found in the EXIF data.")

        # Extract the Base64 part by removing the ASCII header
        base64_data = user_comment_raw.split('ASCII\x00\x00\x00')[-1]

        # Decode the Base64 string
        decoded_data = base64.b64decode(base64_data).decode('utf-8', 'ignore')

        return decoded_data

    except Exception as e:
        print(f"Error extracting data from {image_path}: {e}")
        return None

def save_json(data, output_file):
    """Saves the extracted data into a JSON file."""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        messagebox.showinfo("Success", f"Data saved to {output_file}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save JSON: {e}")

def select_files():
    """Opens a file dialog to select one or more PNG files."""
    root = Tk()
    root.withdraw()  # Hide the root window
    file_paths = filedialog.askopenfilenames(
        title="Select PNG Files",
        filetypes=[("PNG Files", "*.png")]
    )
    if not file_paths:
        return None
    return file_paths

def export_to_json():
    """Extracts data from selected PNG files and saves them to a JSON file."""
    files = select_files()
    if not files:
        return

    extracted_data = {}

    # Process each selected file
    for file in files:
        print(f"Processing {file}...")
        extracted_content = extract_base64_from_image(file)
        if extracted_content:
            filename = os.path.basename(file)
            extracted_data[filename] = json.loads(extracted_content)

    if extracted_data:
        # Ask for where to save the JSON file
        output_file = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")],
            title="Save JSON File"
        )
        if output_file:
            save_json(extracted_data, output_file)
    else:
        messagebox.showinfo("No Data", "No valid data was found in the selected files.")

def main():
    # Start the extraction and export process
    export_to_json()

if __name__ == "__main__":
    main()
