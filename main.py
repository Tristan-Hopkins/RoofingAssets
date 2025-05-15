import streamlit as st
import os
import json
import shutil
from PIL import Image
import uuid
from pathlib import Path

# Set page config
st.set_page_config(page_title="Roofing Materials Builder", layout="wide")

# Initialize session state
if 'brands' not in st.session_state:
    st.session_state.brands = []
if 'current_brand' not in st.session_state:
    st.session_state.current_brand = None
if 'current_material' not in st.session_state:
    st.session_state.current_material = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = "brands"

# File paths
DATA_DIR = Path("data")
BRANDS_DIR = DATA_DIR / "brands"
BRANDS_DIR.mkdir(parents=True, exist_ok=True)

# Custom CSS for bordered containers
st.markdown("""
<style>
    .custom-container {
        border: 1px solid rgba(250, 250, 250, 0.2);
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
        background-color: rgba(255, 255, 255, 0.03);
    }
    
    .navbar {
        display: flex;
        gap: 20px;
        margin-bottom: 20px;
        background-color: #f0f2f6;
        padding: 10px 15px;
        border-radius: 5px;
        align-items: center;
    }
    .navbar-brand {
        font-weight: bold;
        font-size: 1.2em;
        color: #0e1117;
    }
    .navbar-item {
        padding: 5px 10px;
        border-radius: 5px;
        cursor: pointer;
    }
    .navbar-item:hover {
        background-color: rgba(151, 166, 195, 0.25);
    }
    .active-nav {
        background-color: #3b82f6 !important;
        color: white !important;
    }
    .breadcrumb {
        display: flex;
        align-items: center;
        margin-bottom: 20px;
        font-size: 0.9em;
        color: #6B7280;
    }
    .breadcrumb-item {
        cursor: pointer;
    }
    .breadcrumb-item:hover {
        text-decoration: underline;
    }
    .breadcrumb-separator {
        margin: 0 10px;
    }
    .page-content {
        padding-bottom: 70px;
    }
    .gallery-image {
        width: 100%;
        max-width: 250px; /* Smaller gallery images */
        margin: 0 auto;
        display: block;
    }
</style>
""", unsafe_allow_html=True)

# Functions to load and save data
def load_brands():
    brands = []
    for brand_dir in BRANDS_DIR.iterdir():
        if brand_dir.is_dir():
            config_file = brand_dir / "config.json"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    brands.append({
                        'id': brand_dir.name,
                        **config
                    })
    st.session_state.brands = brands
    return brands

def save_brand(brand):
    brand_dir = BRANDS_DIR / brand['id']
    brand_dir.mkdir(exist_ok=True)
    materials_dir = brand_dir / "materials"
    materials_dir.mkdir(exist_ok=True)
    
    # Save config
    with open(brand_dir / "config.json", 'w') as f:
        # Remove ID from config as it's part of the directory structure
        config = {k: v for k, v in brand.items() if k != 'id'}
        json.dump(config, f, indent=2)

def load_materials(brand_id):
    materials = []
    materials_dir = BRANDS_DIR / brand_id / "materials"
    if materials_dir.exists():
        for material_dir in materials_dir.iterdir():
            if material_dir.is_dir():
                config_file = material_dir / "config.json"
                desc_file = material_dir / "description.html"
                
                if config_file.exists():
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                        material = {
                            'id': material_dir.name,
                            **config
                        }
                        
                        # Load description if it exists
                        if desc_file.exists():
                            with open(desc_file, 'r') as df:
                                material['description'] = df.read()
                        else:
                            material['description'] = '<h1>PRODUCT DESCRIPTION</h1><p>Enter product description here.</p>'
                        
                        materials.append(material)
    return materials

def save_material(brand_id, material):
    material_dir = BRANDS_DIR / brand_id / "materials" / material['id']
    material_dir.mkdir(exist_ok=True)
    gallery_dir = material_dir / "gallery"
    gallery_dir.mkdir(exist_ok=True)
    
    # Save description separately
    description = material.get('description', '')
    with open(material_dir / "description.html", 'w') as f:
        f.write(description)
    
    # Save config without description
    config = {k: v for k, v in material.items() if k != 'description' and k != 'id'}
    with open(material_dir / "config.json", 'w') as f:
        json.dump(config, f, indent=2)

def upload_image(file, path, filename):
    full_path = path / filename
    with open(full_path, "wb") as f:
        f.write(file.getbuffer())
    return str(full_path)

def navigate_to(page, brand=None, material=None):
    st.session_state.current_page = page
    if brand is not None:
        st.session_state.current_brand = brand
    if material is not None:
        st.session_state.current_material = material
    st.experimental_rerun()

# Main app
def main():
    # Load brands
    brands = load_brands()
    
    # Create top navigation
    st.markdown(
        """
        <div class="navbar">
            <div class="navbar-brand">🏠 Roofing Materials Builder</div>
            <div class="navbar-item {'' if st.session_state.current_page != 'brands' else 'active-nav'}" 
                 onclick="window.location.href='?page=brands'">Brands</div>
            <div class="navbar-item {'' if st.session_state.current_page != 'materials' else 'active-nav'}" 
                 onclick="window.location.href='?page=materials'">Materials</div>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Handle URL parameters for navigation
    params = st.experimental_get_query_params()
    if "page" in params:
        st.session_state.current_page = params["page"][0]
    
    # Show breadcrumbs
    if st.session_state.current_page == "materials" and st.session_state.current_brand:
        st.markdown(
            f"""
            <div class="breadcrumb">
                <div class="breadcrumb-item" onclick="window.location.href='?page=brands'">Brands</div>
                <div class="breadcrumb-separator">></div>
                <div>{st.session_state.current_brand['company']} Materials</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    elif st.session_state.current_page == "edit_material" and st.session_state.current_brand and st.session_state.current_material:
        st.markdown(
            f"""
            <div class="breadcrumb">
                <div class="breadcrumb-item" onclick="window.location.href='?page=brands'">Brands</div>
                <div class="breadcrumb-separator">></div>
                <div class="breadcrumb-item" onclick="window.location.href='?page=materials'">{st.session_state.current_brand['company']} Materials</div>
                <div class="breadcrumb-separator">></div>
                <div>{st.session_state.current_material['name']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # Display the appropriate page
    if st.session_state.current_page == "brands":
        show_brands_page()
    elif st.session_state.current_page == "materials" and st.session_state.current_brand:
        show_materials_page()
    elif st.session_state.current_page == "edit_material" and st.session_state.current_material:
        show_material_editor()
    else:
        st.session_state.current_page = "brands"
        show_brands_page()

def show_brands_page():
    st.header("Manage Brands")
    
    # Add new brand button
    with st.expander("➕ Add New Brand", expanded=False):
        with st.form("new_brand_form"):
            brand_name = st.text_input("Brand Name", placeholder="e.g., Malarkey")
            brand_desc = st.text_area("Description", placeholder="Enter a description...")
            brand_logo = st.file_uploader("Brand Logo", type=["jpg", "jpeg", "png"])
            
            submitted = st.form_submit_button("Create Brand")
            if submitted and brand_name:
                brand_id = brand_name.lower().replace(" ", "-")
                brand = {
                    'id': brand_id,
                    'company': brand_name,
                    'description': brand_desc,
                    'logo': f"{brand_id}_logo.jpg"
                }
                
                # Save brand
                save_brand(brand)
                
                # Upload logo if provided
                if brand_logo:
                    brand_dir = BRANDS_DIR / brand_id
                    upload_image(brand_logo, brand_dir, f"{brand_id}_logo.jpg")
                
                # Add to session state
                st.session_state.brands.append(brand)
                st.session_state.current_brand = brand
                st.success(f"Brand {brand_name} created!")
                navigate_to("materials", brand)
    
    # Display existing brands
    if not st.session_state.brands:
        st.warning("No brands created yet. Add your first brand above.")
    else:
        # Display brands in a grid
        cols = st.columns(3)
        for i, brand in enumerate(st.session_state.brands):
            with cols[i % 3]:
                # Use a container with custom styling instead of the border parameter
                st.markdown('<div class="custom-container">', unsafe_allow_html=True)
                
                col1, col2 = st.columns([1, 2])
                with col1:
                    logo_path = BRANDS_DIR / brand['id'] / f"{brand['id']}_logo.jpg"
                    if logo_path.exists():
                        st.image(str(logo_path), width=100)
                    else:
                        st.image("https://via.placeholder.com/100x100?text=No+Logo", width=100)
                with col2:
                    st.markdown(f"### {brand['company']}")
                    st.write(f"{brand.get('description', 'No description')[:100]}...")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔍 View Materials", key=f"view_{brand['id']}"):
                        navigate_to("materials", brand)
                with col2:
                    if st.button("🗑️ Delete", key=f"delete_{brand['id']}"):
                        if st.session_state.current_brand and st.session_state.current_brand['id'] == brand['id']:
                            st.session_state.current_brand = None
                        
                        confirm = st.popover(f"Delete {brand['company']}?")
                        with confirm:
                            st.warning(f"This will delete all materials for {brand['company']}!")
                            if st.button("Confirm Delete"):
                                shutil.rmtree(BRANDS_DIR / brand['id'])
                                st.session_state.brands.remove(brand)
                                st.success(f"Brand {brand['company']} deleted.")
                                st.experimental_rerun()
                
                # Close the custom container div
                st.markdown('</div>', unsafe_allow_html=True)

def show_materials_page():
    brand = st.session_state.current_brand
    st.header(f"{brand['company']} Materials")
    
    # Add new material button
    with st.expander("➕ Add New Material", expanded=False):
        with st.form("new_material_form"):
            col1, col2 = st.columns(2)
            with col1:
                material_name = st.text_input("Material Name", placeholder="e.g., Vista Shingles")
                headline = st.text_input("Headline/Short Description", placeholder="Brief description")
                price = st.number_input("Price ($/sq)", min_value=0.0, value=500.0, step=5.0)
                waste = st.number_input("Waste (%)", min_value=0, max_value=100, value=10)
            
            with col2:
                min_pitch = st.number_input("Min Pitch", min_value=0, max_value=12, value=3)
                max_pitch = st.number_input("Max Pitch", min_value=1, max_value=12, value=12)
                pitch_threshold = st.number_input("Pitch Threshold", min_value=1, max_value=12, value=7)
                price_per_pitch = st.number_input("Price Per Pitch Per Square ($)", min_value=0.0, value=15.0)
            
            submitted = st.form_submit_button("Create Material")
            if submitted and material_name:
                material_id = material_name.lower().replace(" ", "-")
                material = {
                    'id': material_id,
                    'name': material_name,
                    'headline': headline,
                    'price': price,
                    'waste': waste,
                    'minPitch': min_pitch,
                    'maxPitch': max_pitch,
                    'pitchThreshold': pitch_threshold,
                    'pricePerPitch': price_per_pitch,
                    'mainImageName': '', # Added field for main image name
                    'description': '<h1>PRODUCT DESCRIPTION</h1><p>Enter product description here.</p>'
                }
                
                # Save material
                save_material(brand['id'], material)
                
                # Set as current material
                st.session_state.current_material = material
                st.success(f"Material {material_name} created!")
                navigate_to("edit_material", None, material)
    
    # Display materials grid
    materials = load_materials(brand['id'])
    
    if not materials:
        st.warning("No materials created yet. Add your first material above.")
    else:
        # Display materials in a grid with modern cards
        cols = st.columns(3)
        for i, material in enumerate(materials):
            with cols[i % 3]:
                # Use a container with custom styling
                st.markdown('<div class="custom-container">', unsafe_allow_html=True)
                
                # Material image
                main_image_path = BRANDS_DIR / brand['id'] / "materials" / material['id'] / f"{material['id']}_main.jpg"
                if main_image_path.exists():
                    st.image(str(main_image_path), use_column_width=True)
                else:
                    st.image("https://via.placeholder.com/400x300?text=No+Image", use_column_width=True)
                
                # Material name and info
                st.markdown(f"### {material['name']}")
                if material.get('headline'):
                    st.markdown(f"*{material['headline']}*")
                
                # Material specs
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Price:** ${material['price']}/sq")
                with col2:
                    st.markdown(f"**Pitch:** {material['minPitch']}/12 - {material['maxPitch']}/12")
                
                # Action buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✏️ Edit", key=f"edit_{material['id']}"):
                        navigate_to("edit_material", None, material)
                with col2:
                    if st.button("🗑️ Delete", key=f"delete_mat_{material['id']}"):
                        confirm = st.popover(f"Delete {material['name']}?")
                        with confirm:
                            st.warning(f"This action cannot be undone!")
                            if st.button("Confirm Delete"):
                                material_dir = BRANDS_DIR / brand['id'] / "materials" / material['id']
                                shutil.rmtree(material_dir)
                                st.success(f"Material {material['name']} deleted.")
                                st.experimental_rerun()
                
                # Close the custom container div
                st.markdown('</div>', unsafe_allow_html=True)

def show_material_editor():
    material = st.session_state.current_material
    brand = st.session_state.current_brand
    
    st.header(f"Editing {material['name']}")
    
    # Create tabs with better UX
    tabs = st.tabs(["📋 Basic Info", "🖼️ Images", "📝 Description", "🖼️ Gallery"])
    
    with tabs[0]:  # Basic Info Tab
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Material Name", value=material['name'])
            headline = st.text_input("Headline/Short Description", value=material.get('headline', ''))
            
        with col2:
            price = st.number_input("Price ($/sq)", min_value=0.0, value=float(material['price']), step=5.0)
            waste = st.number_input("Waste (%)", min_value=0, max_value=100, value=int(material['waste']))
        
        st.subheader("Pitch Settings")
        col1, col2, col3 = st.columns(3)
        with col1:
            min_pitch = st.number_input("Min Pitch", min_value=0, max_value=12, value=int(material['minPitch']))
        with col2:
            max_pitch = st.number_input("Max Pitch", min_value=1, max_value=12, value=int(material['maxPitch']))
        with col3:
            pitch_threshold = st.number_input("Pitch Threshold", min_value=1, max_value=12, value=int(material['pitchThreshold']))
        
        price_per_pitch = st.number_input("Price Per Pitch Per Square ($)", min_value=0.0, value=float(material['pricePerPitch']))
        
        # Save button for basic info
        if st.button("Save Basic Info"):
            # Update material with form values
            material['name'] = name
            material['headline'] = headline
            material['price'] = price
            material['waste'] = waste
            material['minPitch'] = min_pitch
            material['maxPitch'] = max_pitch
            material['pitchThreshold'] = pitch_threshold
            material['pricePerPitch'] = price_per_pitch
            
            # Save to file
            save_material(brand['id'], material)
            st.success("Basic information saved successfully!")
    
    with tabs[1]:  # Images Tab
        st.subheader("Main Product Image")
        
        col1, col2 = st.columns([1, 2])
        with col1:
            # Display current main image
            main_image_path = BRANDS_DIR / brand['id'] / "materials" / material['id'] / f"{material['id']}_main.jpg"
            if main_image_path.exists():
                st.image(str(main_image_path), use_column_width=True)
            else:
                st.info("No main image uploaded yet")
        
        with col2:
            # Add name/caption for main image
            main_image_name = st.text_input(
                "Main Image Name/Caption", 
                value=material.get('mainImageName', ''),
                help="This name will be displayed when showing the main image"
            )
            
            main_image = st.file_uploader("Upload Main Image", type=["jpg", "jpeg", "png"], key="main_image")
            if main_image:
                # Preview
                st.image(main_image, width=300)
                if st.button("Save Main Image"):
                    material_dir = BRANDS_DIR / brand['id'] / "materials" / material['id']
                    upload_image(main_image, material_dir, f"{material['id']}_main.jpg")
                    # Update the main image name
                    material['mainImageName'] = main_image_name
                    save_material(brand['id'], material)
                    st.success("Main image uploaded successfully!")
                    st.experimental_rerun()
        
        st.divider()
        
        st.subheader("Preview Image")
        st.info("Preview images are shown in material selection screens before the full detail page loads")
        col1, col2 = st.columns([1, 2])
        with col1:
            # Display current preview image
            preview_image_path = BRANDS_DIR / brand['id'] / "materials" / material['id'] / f"{material['id']}_preview.jpg"
            if preview_image_path.exists():
                st.image(str(preview_image_path), use_column_width=True)
            else:
                st.info("No preview image uploaded yet")
                if main_image_path.exists():
                    st.caption("Using main image instead")
                    st.image(str(main_image_path), use_column_width=True, output_format="JPEG")
        
        with col2:
            use_custom_preview = st.checkbox(
                "Use custom preview image", 
                value=preview_image_path.exists(),
                help="When enabled, you can upload a different image for previews"
            )
            
            if use_custom_preview:
                preview_image = st.file_uploader("Upload Preview Image", type=["jpg", "jpeg", "png"], key="preview_image")
                if preview_image:
                    # Preview
                    st.image(preview_image, width=300)
                    if st.button("Save Preview Image"):
                        material_dir = BRANDS_DIR / brand['id'] / "materials" / material['id']
                        upload_image(preview_image, material_dir, f"{material['id']}_preview.jpg")
                        st.success("Preview image uploaded successfully!")
                        st.experimental_rerun()
            else:
                if preview_image_path.exists():
                    if st.button("Use Main Image Instead"):
                        # Delete the custom preview image
                        preview_image_path.unlink()
                        st.success("Now using main image for previews")
                        st.experimental_rerun()
    
    with tabs[2]:  # Description Tab
        st.subheader("Product Description")
        st.info("This HTML content will be displayed on the material detail page")
        
        description = material.get('description', '')
        
        # Add template buttons
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("📋 Insert Template"):
                template = f"""<h1>{material['name']}</h1>
<p>This high-quality roofing material provides excellent protection and curb appeal for your home.</p>

<h2>Features</h2>
<ul>
  <li>Feature 1</li>
  <li>Feature 2</li>
  <li>Feature 3</li>
</ul>

<h2>Technical Specifications</h2>
<table>
  <tr>
    <th>Specification</th>
    <th>Value</th>
  </tr>
  <tr>
    <td>Weight</td>
    <td>X lb/sq</td>
  </tr>
  <tr>
    <td>Dimensions</td>
    <td>X" × X"</td>
  </tr>
</table>

<h2>Installation</h2>
<p>Installation instructions go here.</p>"""
                st.session_state.template = template
                st.experimental_rerun()
        
        with col2:
            preview_description = st.button("👁️ Preview")
        
        # Set up description text area
        new_description = st.text_area(
            "HTML Description", 
            value=st.session_state.get('template', description),
            height=400
        )
        
        if 'template' in st.session_state:
            del st.session_state.template
        
        # Save button for description
        if st.button("Save Description"):
            material['description'] = new_description
            save_material(brand['id'], material)
            st.success("Description saved successfully!")
        
        # Preview section
        if preview_description:
            st.markdown("### Preview:")
            st.markdown(new_description, unsafe_allow_html=True)
    
    with tabs[3]:  # Gallery Tab
        st.subheader("Gallery Images")
        st.info("Gallery images will be displayed on the material detail page")
        
        # Upload new gallery image
        with st.expander("➕ Add Gallery Image", expanded=False):
            # Check if we need to clear the form
            if st.session_state.get('clear_gallery_upload', False):
                st.session_state.clear_gallery_upload = False
                # Reset the widget keys to force recreating them
                st.session_state.pop('gallery_image', None)
                st.session_state.pop('gallery_preview', None)
                st.session_state.pop('gallery_name', None)
                st.experimental_rerun()  # Force a rerun to clear the widgets
            
            col1, col2 = st.columns(2)
            with col1:
                gallery_image = st.file_uploader("Upload Gallery Image", type=["jpg", "jpeg", "png"], key="gallery_image")
                if gallery_image:
                    st.image(gallery_image, width=300)
            
            with col2:
                image_name = st.text_input("Image Name/Caption", key="gallery_name")
                use_custom_gallery_preview = st.checkbox(
                    "Use separate thumbnail image",
                    help="When enabled, you can upload a different image for the gallery thumbnail"
                )
                
                if use_custom_gallery_preview:
                    gallery_preview = st.file_uploader("Upload Thumbnail", type=["jpg", "jpeg", "png"], key="gallery_preview")
                    if gallery_preview:
                        st.image(gallery_preview, width=150)
            
            if gallery_image and st.button("Add to Gallery"):
                # Generate index
                gallery_dir = BRANDS_DIR / brand['id'] / "materials" / material['id'] / "gallery"
                existing_indices = [int(f.stem.split('_')[-1]) for f in gallery_dir.glob(f"{material['id']}_*.jpg") 
                                   if f.stem.split('_')[-1].isdigit() and not f.stem.endswith('_preview')]
                next_index = max(existing_indices) + 1 if existing_indices else 1
                
                # Upload image
                upload_image(gallery_image, gallery_dir, f"{material['id']}_{next_index}.jpg")
                
                # Upload preview if provided
                if use_custom_gallery_preview and gallery_preview:
                    upload_image(gallery_preview, gallery_dir, f"{material['id']}_{next_index}_preview.jpg")
                
                # Save name if provided
                if image_name:
                    with open(gallery_dir / f"{material['id']}_{next_index}_name.txt", 'w') as f:
                        f.write(image_name)
                
                st.success("Gallery image added!")
                
                # Set flag to clear the form on next rerun
                st.session_state.clear_gallery_upload = True
                st.experimental_rerun()
        
        # Display gallery images
        gallery_dir = BRANDS_DIR / brand['id'] / "materials" / material['id'] / "gallery"
        # Look for any jpg files in the gallery directory that don't end with "_preview"
        gallery_images = list(gallery_dir.glob("*.jpg"))
        gallery_images = [img for img in gallery_images if not img.stem.endswith('_preview')]
        
        if not gallery_images:
            st.warning("No gallery images yet. Add images using the section above.")
        else:
            # Get the numeric index from the filename, regardless of prefix
            gallery_indices = []
            for img in gallery_images:
                parts = img.stem.split('_')
                if parts and parts[-1].isdigit():
                    gallery_indices.append(int(parts[-1]))
            
            # Sort indices
            gallery_indices.sort()
            
            # Display gallery images in a grid
            num_columns = 3  # Changed from 2 to 3 for smaller images
            rows = [gallery_indices[i:i + num_columns] for i in range(0, len(gallery_indices), num_columns)]
            
            for row in rows:
                cols = st.columns(num_columns)
                for i, index in enumerate(row):
                    if i < len(row):
                        with cols[i]:
                            # Use custom container styling
                            st.markdown('<div class="custom-container">', unsafe_allow_html=True)
                            
                            # Find the file with this index number at the end
                            image_files = list(gallery_dir.glob(f"*_{index}.jpg"))
                            if not image_files:
                                continue
                                
                            image_path = image_files[0]  # Use the first matching file
                            image_base = image_path.stem  # Get filename without extension
                            image_prefix = image_base.rsplit('_', 1)[0]  # Get everything before the _index
                            
                            preview_path = gallery_dir / f"{image_prefix}_{index}_preview.jpg"
                            name_path = gallery_dir / f"{image_prefix}_{index}_name.txt"
                            
                            image_name = ""
                            if name_path.exists():
                                with open(name_path, 'r') as f:
                                    image_name = f.read()
                            
                            # Display image and caption - smaller size
                            st.image(str(image_path), width=200, caption=image_name if image_name else f"Image {index}")
                            
                            # Edit and Delete buttons
                            col1, col2 = st.columns(2)
                            with col1:
                                with st.expander("✏️ Edit", expanded=False):
                                    # Edit caption
                                    new_name = st.text_input(f"Caption", value=image_name, key=f"name_{index}")
                                    if new_name != image_name:
                                        with open(name_path, 'w') as f:
                                            f.write(new_name)
                                        st.success("Caption saved")
                                    
                                    # Thumbnail settings
                                    has_custom = preview_path.exists()
                                    use_custom = st.checkbox("Custom thumbnail", value=has_custom, key=f"custom_{index}")
                                    
                                    if use_custom and not has_custom:
                                        preview_upload = st.file_uploader(f"Upload thumbnail", key=f"preview_{index}")
                                        if preview_upload and st.button(f"Save thumbnail", key=f"save_preview_{index}"):
                                            upload_image(preview_upload, gallery_dir, f"{image_prefix}_{index}_preview.jpg")
                                            st.success("Thumbnail saved!")
                                            st.experimental_rerun()
                                    elif use_custom and has_custom:
                                        st.image(str(preview_path), width=100, caption="Current thumbnail")
                                        new_preview = st.file_uploader(f"Change thumbnail", key=f"change_preview_{index}")
                                        if new_preview and st.button(f"Update thumbnail", key=f"update_preview_{index}"):
                                            upload_image(new_preview, gallery_dir, f"{image_prefix}_{index}_preview.jpg")
                                            st.success("Thumbnail updated!")
                                            st.experimental_rerun()
                                    elif not use_custom and has_custom:
                                        if st.button(f"Remove custom thumbnail", key=f"remove_preview_{index}"):
                                            preview_path.unlink()
                                            st.success("Using main image as thumbnail")
                                            st.experimental_rerun()
                            
                            with col2:
                                # Delete image button
                                if st.button(f"🗑️ Delete", key=f"delete_gallery_{index}"):
                                    # Delete all related files
                                    image_path.unlink(missing_ok=True)
                                    name_path.unlink(missing_ok=True)
                                    preview_path.unlink(missing_ok=True)
                                    st.success(f"Gallery image {index} deleted.")
                                    st.experimental_rerun()
                            
                            # Close custom container
                            st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
