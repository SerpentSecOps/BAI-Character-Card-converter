import base64
import json
from tkinter import Tk, filedialog, messagebox, Label, Button, BOTH, Menu, END
from tkinter.scrolledtext import ScrolledText
from tkinter.font import Font
from PIL import Image
from PIL.ExifTags import TAGS

# Global variable to hold the current file path
current_file_path = None

def extract_base64_from_image(image_path):
    """
    Extracts Base64-encoded data embedded in the metadata of a PNG image and returns the decoded JSON.
    """
    try:
        image = Image.open(image_path)
        exif_data = image._getexif()

        if not exif_data:
            raise ValueError("No EXIF data found in the image.")

        user_comment_raw = None
        for tag, value in exif_data.items():
            tag_name = TAGS.get(tag, tag)
            if tag_name == 'UserComment':
                user_comment_raw = value.decode('utf-8', 'ignore')
                break

        if not user_comment_raw:
            raise ValueError("No 'UserComment' found in the EXIF data.")

        base64_data = user_comment_raw.split('ASCII\x00\x00\x00')[-1]
        decoded_data = base64.b64decode(base64_data).decode('utf-8', 'ignore')

        return decoded_data

    except Exception as e:
        print(f"Error extracting data from {image_path}: {e}")
        return None

def embed_json_to_image(image_path, json_data, output_image_path):
    """
    Embeds the given JSON data back into the image metadata as Base64-encoded data.
    """
    try:
        image = Image.open(image_path)

        # Convert JSON to Base64-encoded string
        json_string = json.dumps(json_data, ensure_ascii=False)
        base64_data = base64.b64encode(json_string.encode('utf-8')).decode('utf-8')

        # Save the new image with the modified metadata
        image.save(output_image_path, "PNG")
        messagebox.showinfo("Success", f"Modified image saved as {output_image_path}")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to save image with new data: {e}")

def load_image_data():
    """Opens a file dialog and loads the image data."""
    global current_file_path
    file_path = filedialog.askopenfilename(
        title="Select PNG File",
        filetypes=[("PNG Files", "*.png")]
    )
    if not file_path:
        return None

    json_data = extract_base64_from_image(file_path)
    if json_data:
        current_file_path = file_path
        return json.loads(json_data), file_path
    else:
        messagebox.showerror("Error", "Failed to extract or decode data.")
        return None, None

def save_changes():
    """Saves changes back into the current PNG file."""
    global current_file_path
    if current_file_path:
        updated_data = text_area.get("1.0", END)
        try:
            json_data = json.loads(updated_data)
            embed_json_to_image(current_file_path, json_data, current_file_path)
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Invalid JSON format. Please correct the data.")
    else:
        messagebox.showerror("Error", "No file is currently open.")

def export_data(file_format):
    """Exports the edited data to a specific format: JSON, MD, or TXT."""
    export_data = text_area.get("1.0", END)

    # Select the file extension based on the format
    file_extension = file_format.lower()

    export_file = filedialog.asksaveasfilename(
        defaultextension=f".{file_extension}",
        filetypes=[(f"{file_format.upper()} Files", f"*.{file_extension}")],
        title=f"Export as {file_format.upper()}"
    )

    if export_file:
        with open(export_file, "w", encoding="utf-8") as f:
            f.write(export_data)
        messagebox.showinfo("Success", f"Data exported as {file_format.upper()}.")

def display_editor(json_data, file_path):
    """Displays the editor GUI with a larger text area and auto-resizing capabilities."""
    editor_window = Tk()
    editor_window.title("Character Sheet Editor")

    # Enable the window to resize
    editor_window.geometry("800x600")
    editor_window.minsize(600, 400)

    # Create a default font with a variable size
    text_font = Font(family="Helvetica", size=12)

    # Function to zoom in and out
    def zoom_in(event=None):
        current_size = text_font['size']
        text_font.configure(size=current_size + 2)
        text_area.configure(font=text_font)  # Update text area font

    def zoom_out(event=None):
        current_size = text_font['size']
        if current_size > 6:  # Set a lower bound for font size
            text_font.configure(size=current_size - 2)
            text_area.configure(font=text_font)  # Update text area font

    # Add keyboard shortcuts for zoom in (Ctrl +) and zoom out (Ctrl -)
    editor_window.bind('<Control-=>', zoom_in)  # Ctrl + for zoom in
    editor_window.bind('<Control-minus>', zoom_out)  # Ctrl - for zoom out

    # Label above text area
    Label(editor_window, text="Edit Character Sheet").pack()

    # ScrolledText for editing, expanding to fill the window
    global text_area
    text_area = ScrolledText(editor_window, wrap='word', font=text_font)
    text_area.pack(expand=True, fill=BOTH, padx=10, pady=10)

    # Load the JSON data into the text area for editing
    text_area.insert(END, json.dumps(json_data, indent=4))

    # Add buttons for Zoom In and Zoom Out with shortcut labels
    Button(editor_window, text="Zoom In (Ctrl +)", command=zoom_in).pack(pady=5)
    Button(editor_window, text="Zoom Out (Ctrl -)", command=zoom_out).pack(pady=5)

    # Add a menu for file operations and zoom controls
    menu_bar = Menu(editor_window)
    editor_window.config(menu=menu_bar)

    file_menu = Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="File", menu=file_menu)
    
    # Open option
    file_menu.add_command(label="Open", command=lambda: load_new_file(editor_window))
    
    # Save option
    file_menu.add_command(label="Save", command=save_changes)
    
    # Export options: JSON, MD, TXT
    export_menu = Menu(file_menu, tearoff=0)
    file_menu.add_cascade(label="Export", menu=export_menu)
    export_menu.add_command(label="Export as JSON", command=lambda: export_data("json"))
    export_menu.add_command(label="Export as MD", command=lambda: export_data("md"))
    export_menu.add_command(label="Export as TXT", command=lambda: export_data("txt"))

    # Quit option
    file_menu.add_command(label="Quit", command=editor_window.quit)

    # View menu for zoom controls
    view_menu = Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="View", menu=view_menu)
    view_menu.add_command(label="Zoom In (Ctrl +)", command=zoom_in)
    view_menu.add_command(label="Zoom Out (Ctrl -)", command=zoom_out)

    editor_window.mainloop()

def load_new_file(parent_window):
    """Handles opening a new file and reloading the editor."""
    json_data, file_path = load_image_data()
    if json_data and file_path:
        parent_window.destroy()
        display_editor(json_data, file_path)

def main():
    root = Tk()
    root.withdraw()  # Hide the root window

    # Load the image and extract the JSON data
    json_data, file_path = load_image_data()
    if json_data and file_path:
        # Display the editor to edit the JSON data
        display_editor(json_data, file_path)

if __name__ == "__main__":
    main()
