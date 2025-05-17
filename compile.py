import os
import json
import shutil
from pathlib import Path
from PIL import Image
import io

# Configuration
DATA_DIR = Path("data")
BRANDS_DIR = DATA_DIR / "brands"
OUTPUT_DIR = Path("output")
IMAGES_DIR = OUTPUT_DIR / "images"
OUTPUT_JSON_PATH = OUTPUT_DIR / "all-companies.json"
IMAGE_PREFIX = "https://catalog.sky-quote.com/RoofingMaterials/Images/"

# Supported image file extensions
SUPPORTED_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff"]

# Track copied files to avoid duplicates
copied_files = {}

# Track which images are used in current compilation
used_images = set()

# Track size statistics
total_original_size = 0
total_webp_size = 0
total_images_processed = 0

def clean_string(text):
    """Clean up a string by removing leading/trailing whitespace."""
    if not text:
        return ""
    return text.strip()

def ensure_directories():
    """Create output directories if they don't exist."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    IMAGES_DIR.mkdir(exist_ok=True)

def scan_existing_images():
    """Scan existing images in the output directory and return a set of their filenames."""
    existing_images = set()
    if IMAGES_DIR.exists():
        for img_path in IMAGES_DIR.glob("*.webp"):
            existing_images.add(img_path.name)
    return existing_images

def copy_image(source_path, file_name):
    """
    Copy an image to the output images directory with a unique filename.
    Returns the new path with the image prefix.
    Handles duplicates by reusing existing files.
    Converts images to WebP format at 90% quality.
    Tracks size reduction statistics.
    """
    global total_original_size, total_webp_size, total_images_processed
    
    # Check if file exists
    if not source_path.exists():
        print(f"Warning: Image not found: {source_path}")
        return None
    
    # Get original file size
    original_size = os.path.getsize(source_path)
    
    # Create a hash of the file content to detect duplicates
    with open(source_path, "rb") as f:
        file_content = f.read()
        import hashlib
        file_hash = hashlib.md5(file_content).hexdigest()
    
    # If we've already copied this exact file, return the existing URL
    if file_hash in copied_files:
        return copied_files[file_hash]
    
    # Create a unique filename with webp extension
    unique_name = f"{file_name}.webp"
    dest_path = IMAGES_DIR / unique_name
    
    # Add to used images tracking
    used_images.add(unique_name)
    
    # Convert to WebP and save
    try:
        with Image.open(source_path) as img:
            img.save(dest_path, format="WEBP", quality=90)
            
        # Get the new file size
        webp_size = os.path.getsize(dest_path)
        
        # Update statistics
        total_original_size += original_size
        total_webp_size += webp_size
        total_images_processed += 1
        
        # Log individual file stats
        size_reduction = original_size - webp_size
        reduction_percentage = (size_reduction / original_size) * 100 if original_size > 0 else 0
        print(f"Converted: {source_path.name} → {unique_name} | Size: {original_size/1024:.1f}KB → {webp_size/1024:.1f}KB | Saved: {size_reduction/1024:.1f}KB ({reduction_percentage:.1f}%)")
    except Exception as e:
        print(f"Error converting {source_path} to WebP: {e}")
        return None
    
    # Store the URL with the file hash
    url = f"{IMAGE_PREFIX}{unique_name}"
    copied_files[file_hash] = url
    
    # Return the path with prefix
    return url

def load_description(material_dir):
    """Load HTML description from a file."""
    description_path = material_dir / "description.html"
    if description_path.exists():
        with open(description_path, 'r') as f:
            return f.read()
    return ""

def find_image_file(directory, base_name):
    """Find an image file with any supported extension."""
    for ext in SUPPORTED_IMAGE_EXTENSIONS:
        path = directory / f"{base_name}{ext}"
        if path.exists():
            return path
    return None

def process_gallery_images(gallery_dir, material_id, main_image_name=""):
    """Process gallery images and return gallery data."""
    gallery_images = []
    gallery_preview_images = []
    gallery_names = []
    use_custom_previews = []
    
    # Find all gallery images (that don't end with _preview)
    main_images = []
    for ext in SUPPORTED_IMAGE_EXTENSIONS:
        main_images.extend([img for img in gallery_dir.glob(f"*{ext}") 
                       if not img.stem.endswith('_preview')])
    
    # Sort by index
    def get_index(path):
        parts = path.stem.split('_')
        return int(parts[-1]) if parts and parts[-1].isdigit() else 0
    
    main_images.sort(key=get_index)
    
    # Create a dictionary to track duplicate named images
    image_names_dict = {}  # Maps image name to its index in the arrays
    
    for img_path in main_images:
        # Get the index from the filename
        parts = img_path.stem.split('_')
        if parts and parts[-1].isdigit():
            index = int(parts[-1])
            image_prefix = img_path.stem.rsplit('_', 1)[0]
            
            # Get image name/caption
            name_path = gallery_dir / f"{image_prefix}_{index}_name.txt"
            image_name = ""
            if name_path.exists():
                with open(name_path, 'r') as f:
                    image_name = clean_string(f.read())
            
            # Skip this gallery image if it has the same name as the main image
            if main_image_name and image_name == main_image_name:
                print(f"Skipping gallery image that duplicates main image: '{image_name}'")
                continue
                
            # Copy the main image
            unique_id = f"{material_id}_gallery_{index}"
            new_path = copy_image(img_path, unique_id)
            if not new_path:
                continue
            
            # Check for custom preview
            preview_found = False
            for ext in SUPPORTED_IMAGE_EXTENSIONS:
                preview_path = gallery_dir / f"{image_prefix}_{index}_preview{ext}"
                if preview_path.exists():
                    preview_found = True
                    preview_unique_id = f"{material_id}_gallery_preview_{index}"
                    preview_path = copy_image(preview_path, preview_unique_id)
                    preview_image = preview_path
                    custom_preview = True
                    break
                    
            if not preview_found:
                # Use main image as preview
                preview_image = new_path
                custom_preview = False
            
            # Check if we already have an image with this name
            if image_name in image_names_dict:
                # Update existing entry with this image as an alternative
                existing_idx = image_names_dict[image_name]
                print(f"Found duplicate image name: '{image_name}' - skipping")
                continue
            else:
                # Add the new image
                image_names_dict[image_name] = len(gallery_images)
                gallery_images.append(new_path)
                gallery_preview_images.append(preview_image)
                gallery_names.append(image_name)
                use_custom_previews.append(custom_preview)
    
    return {
        "galleryImages": gallery_images,
        "galleryImagesNames": gallery_names,
        "galleryPreviewImages": gallery_preview_images,
        "useCustomGalleryPreviews": use_custom_previews
    }

def process_material(material_dir, brand_id):
    """Process a material directory and return the material data."""
    config_path = material_dir / "config.json"
    if not config_path.exists():
        print(f"Warning: No config found for material: {material_dir}")
        return None
    
    # Load config
    with open(config_path, 'r') as f:
        material = json.load(f)
    
    # Clean up all string fields
    for key, value in material.items():
        if isinstance(value, str):
            material[key] = clean_string(value)
    
    # Add ID
    material_id = material_dir.name
    material['id'] = material_id
    
    # Load description
    material['description'] = load_description(material_dir)
    
    # Process main image - look for any supported extension
    main_image_path = find_image_file(material_dir, f"{material_id}_main")
    if main_image_path:
        material['image'] = copy_image(main_image_path, f"{brand_id}_{material_id}_main")
    else:
        # Skip placeholder creation
        material['image'] = ""
        print(f"Warning: No main image for material: {material_id}")
    
    # Get main image name/label if available
    main_image_name_path = material_dir / f"{material_id}_main_name.txt"
    main_image_name = ""
    if main_image_name_path.exists():
        with open(main_image_name_path, 'r') as f:
            main_image_name = clean_string(f.read())
    
    # Process preview image - look for any supported extension
    preview_image_path = find_image_file(material_dir, f"{material_id}_preview")
    if preview_image_path:
        material['primaryPreviewImage'] = copy_image(preview_image_path, f"{brand_id}_{material_id}_preview")
        material['useCustomPrimaryPreview'] = True
    else:
        material['primaryPreviewImage'] = material['image']
        material['useCustomPrimaryPreview'] = False
    
    # Process gallery
    gallery_dir = material_dir / "gallery"
    if gallery_dir.exists():
        gallery_data = process_gallery_images(gallery_dir, f"{brand_id}_{material_id}", main_image_name)
        material.update(gallery_data)
    else:
        material['galleryImages'] = []
        material['galleryImagesNames'] = []
        material['galleryPreviewImages'] = []
        material['useCustomGalleryPreviews'] = []
    
    # Set default values for compatibility
    material.setdefault('simpleMode', False)  # Advanced mode by default
    material.setdefault('enabled', True)
    
    return material

def process_brand(brand_dir):
    """Process a brand directory and return the brand data."""
    config_path = brand_dir / "config.json"
    if not config_path.exists():
        print(f"Warning: No config found for brand: {brand_dir}")
        return None
    
    # Load config
    with open(config_path, 'r') as f:
        brand = json.load(f)
    
    # Clean up all string fields
    for key, value in brand.items():
        if isinstance(value, str):
            brand[key] = clean_string(value)
    
    # Add ID
    brand_id = brand_dir.name
    brand['id'] = brand_id
    
    # Process logo - look for any supported extension
    logo_path = find_image_file(brand_dir, f"{brand_id}_logo")
    if logo_path:
        brand['logo'] = copy_image(logo_path, f"{brand_id}_logo")
    else:
        # Skip placeholder creation
        brand['logo'] = ""
        print(f"Warning: No logo for brand: {brand_id}")
    
    # Process materials
    materials_dir = brand_dir / "materials"
    materials = []
    
    if materials_dir.exists():
        for material_dir in materials_dir.iterdir():
            if material_dir.is_dir():
                material = process_material(material_dir, brand_id)
                if material:
                    materials.append(material)
    
    brand['materials'] = materials
    return brand

def preserve_unused_images(existing_images, used_images):
    """
    Identify and log images that exist in the output but weren't used in the current compilation.
    These images are preserved for backward compatibility.
    """
    unused_images = existing_images - used_images
    if unused_images:
        print("\n===== Preserving Unused Images =====")
        for img_name in sorted(unused_images):
            print(f"Image not in new data but preserving: {img_name}")
        print(f"Total preserved images: {len(unused_images)}")
        print("======================================")

def main():
    """Main function to compile all data into a single JSON file."""
    print("Starting compilation process...")
    
    # Ensure output directories exist
    ensure_directories()
    
    # Scan existing images
    existing_images = scan_existing_images()
    print(f"Found {len(existing_images)} existing images in output directory")
    
    # Process all brands
    all_companies = {}
    
    for brand_dir in BRANDS_DIR.iterdir():
        if brand_dir.is_dir():
            brand = process_brand(brand_dir)
            if brand:
                brand_id = brand['id']
                all_companies[brand_id] = brand
    
    # Write the output JSON
    with open(OUTPUT_JSON_PATH, 'w') as f:
        json.dump(all_companies, f, indent=2)
    
    # Identify and preserve unused images
    preserve_unused_images(existing_images, used_images)
    
    # Calculate and print size statistics
    total_size_saved = total_original_size - total_webp_size
    avg_reduction_percentage = (total_size_saved / total_original_size) * 100 if total_original_size > 0 else 0
    
    print("\n===== Image Conversion Statistics =====")
    print(f"Total images processed: {total_images_processed}")
    print(f"Total original size: {total_original_size/1024/1024:.2f}MB")
    print(f"Total WebP size: {total_webp_size/1024/1024:.2f}MB")
    print(f"Total size saved: {total_size_saved/1024/1024:.2f}MB ({avg_reduction_percentage:.1f}%)")
    if total_images_processed > 0:
        print(f"Average file size reduction: {(total_size_saved/total_images_processed)/1024:.2f}KB per image")
    print("======================================")
    
    print(f"Compilation complete! Output saved to {OUTPUT_JSON_PATH}")
    print(f"All images copied to {IMAGES_DIR}")
    print(f"Image URLs use prefix: {IMAGE_PREFIX}")
    print(f"Total unique images: {len(copied_files)}")
    print(f"Total preserved images: {len(existing_images - used_images)}")
    print(f"All images converted to WebP format at 90% quality")

if __name__ == "__main__":
    main()
