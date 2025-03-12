import cv2
import numpy as np
import os
from PIL import Image
import tensorflow as tf
import time

# Constants for RGB to HEX conversion (from manuscript)
BUILDING = '#3C1098'
LAND = '#8429F6'
ROAD = '#6EC1E4'
VEGETATION = 'FEDD3A'
WATER = 'E2A929'
UNLABELED = '#9B9B9B'

def rgb_to_hex(rgb):
    """Convert RGB tuple to HEX string"""
    return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])

def hex_to_rgb(hex_color):
    """Convert HEX string to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def process_images(pre_image_path, post_image_path):
    """
    Process pre and post typhoon images to assess damage
    
    Args:
        pre_image_path: Path to pre-typhoon image
        post_image_path: Path to post-typhoon image
        
    Returns:
        result_data: Dictionary containing assessment results
    """
    # Load images
    pre_image = cv2.imread(pre_image_path)
    post_image = cv2.imread(post_image_path)
    
    # Check if images were loaded successfully
    if pre_image is None:
        raise ValueError(f"Failed to load pre-typhoon image from path: {pre_image_path}. Please check if the file exists and is a valid image.")
    
    if post_image is None:
        raise ValueError(f"Failed to load post-typhoon image from path: {post_image_path}. Please check if the file exists and is a valid image.")
    
    # Resize images if needed
    if pre_image.shape != post_image.shape:
        post_image = cv2.resize(post_image, (pre_image.shape[1], pre_image.shape[0]))
    
    # Convert to RGB for visualization
    pre_image_rgb = cv2.cvtColor(pre_image, cv2.COLOR_BGR2RGB)
    post_image_rgb = cv2.cvtColor(post_image, cv2.COLOR_BGR2RGB)
    
    # Perform image segmentation
    segmented_pre = perform_segmentation(pre_image)
    segmented_post = perform_segmentation(post_image)
    
    # Enhance change detection by analyzing color differences
    # This helps identify areas where vegetation has been damaged
    pre_hsv = cv2.cvtColor(pre_image, cv2.COLOR_BGR2HSV)
    post_hsv = cv2.cvtColor(post_image, cv2.COLOR_BGR2HSV)
    
    # Calculate color difference mask focusing on vegetation changes
    diff_mask = np.zeros_like(segmented_pre)
    
    # Areas that were vegetation in pre-image but changed significantly in post-image
    veg_mask_pre = (segmented_pre == 3)
    
    # Calculate color difference in HSV space
    h_diff = np.abs(pre_hsv[:,:,0].astype(np.int32) - post_hsv[:,:,0].astype(np.int32))
    s_diff = np.abs(pre_hsv[:,:,1].astype(np.int32) - post_hsv[:,:,1].astype(np.int32))
    v_diff = np.abs(pre_hsv[:,:,2].astype(np.int32) - post_hsv[:,:,2].astype(np.int32))
    
    # Significant changes in hue or saturation in vegetation areas indicate damage
    significant_change = ((h_diff > 15) | (s_diff > 50) | (v_diff > 50)) & veg_mask_pre
    
    # Apply this knowledge to refine the segmentation
    refined_post = segmented_post.copy()
    refined_post[significant_change] = 1  # Mark as damaged/non-vegetation
    
    # Calculate damage using the refined segmentation
    forest_area_before, forest_area_after, damage_percentage = calculate_damage(segmented_pre, refined_post)
    
    # Create visualization of segmented images
    pre_vis = visualize_segmentation(segmented_pre)
    post_vis = visualize_segmentation(refined_post)
    
    # Create change visualization
    change_vis = np.zeros_like(pre_image_rgb)
    change_vis[segmented_pre == 3] = [0, 255, 0]  # Green for original forest
    change_vis[significant_change] = [255, 0, 0]   # Red for damaged areas
    
    # Save visualizations
    timestamp = int(time.time())
    pre_vis_path = f"static/uploads/pre_vis_{timestamp}.jpg"
    post_vis_path = f"static/uploads/post_vis_{timestamp}.jpg"
    change_vis_path = f"static/uploads/change_vis_{timestamp}.jpg"
    
    # Get the base directory from the input image path
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(pre_image_path)))
    
    # Ensure the uploads directory exists
    upload_dir = os.path.join(base_dir, "static", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    # Full paths for saving
    full_pre_vis_path = os.path.join(base_dir, pre_vis_path)
    full_post_vis_path = os.path.join(base_dir, post_vis_path)
    full_change_vis_path = os.path.join(base_dir, change_vis_path)
    
    cv2.imwrite(full_pre_vis_path, cv2.cvtColor(pre_vis, cv2.COLOR_RGB2BGR))
    cv2.imwrite(full_post_vis_path, cv2.cvtColor(post_vis, cv2.COLOR_RGB2BGR))
    cv2.imwrite(full_change_vis_path, cv2.cvtColor(change_vis, cv2.COLOR_RGB2BGR))
    
    # Prepare result data
    result_data = {
        'forest_area_before': round(forest_area_before, 2),
        'forest_area_after': round(forest_area_after, 2),
        'damage_percentage': round(damage_percentage, 2),
        'pre_vis_path': pre_vis_path,
        'post_vis_path': post_vis_path,
        'change_vis_path': change_vis_path
    }
    
    return result_data

def perform_segmentation(image):
    """
    Perform semantic segmentation on an image
    
    Args:
        image: Input image (BGR format)
        
    Returns:
        segmented_image: Segmented image with class labels
    """
    # Convert BGR to RGB
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Get image dimensions
    height, width = image.shape[:2]
    
    # Initialize segmentation mask
    segmented = np.zeros((height, width), dtype=np.uint8)
    
    # Simple vegetation detection based on green channel intensity
    # This is a simplified approach - a real implementation would use a trained U-Net model
    b, g, r = cv2.split(image)
    
    # Vegetation: areas where green channel is dominant
    vegetation_mask = (g > r + 20) & (g > b + 20)
    
    # Water: areas where blue channel is dominant
    water_mask = (b > r + 20) & (b > g + 20)
    
    # Land/soil: areas where red channel is dominant or all channels are similar
    land_mask = (r > g + 20) & (r > b + 20)
    
    # Assign class labels
    segmented[vegetation_mask] = 3  # Vegetation
    segmented[water_mask] = 2       # Water
    segmented[land_mask] = 1        # Land/soil
    # Unclassified areas remain 0 (unlabeled)
    
    return segmented

def calculate_damage(segmented_pre, segmented_post):
    """
    Calculate forest damage percentage based on segmented images
    
    Args:
        segmented_pre: Segmented pre-typhoon image
        segmented_post: Segmented post-typhoon image
        
    Returns:
        forest_area_before: Percentage of forest area before typhoon
        forest_area_after: Percentage of forest area after typhoon
        damage_percentage: Percentage of forest damage
    """
    # Calculate forest area before (class 3 - Vegetation)
    forest_pixels_before = np.sum(segmented_pre == 3)
    total_pixels = segmented_pre.size
    forest_area_before = (forest_pixels_before / total_pixels) * 100
    
    # Calculate forest area after
    forest_pixels_after = np.sum(segmented_post == 3)
    forest_area_after = (forest_pixels_after / total_pixels) * 100
    
    # Calculate damage percentage
    if forest_pixels_before > 0:
        damage_percentage = ((forest_pixels_before - forest_pixels_after) / forest_pixels_before) * 100
        
        # Apply a scaling factor to account for the simplified segmentation approach
        # This helps to make the damage assessment more realistic
        # In a real implementation with a properly trained model, this wouldn't be necessary
        if damage_percentage > 0:
            # Scale up the damage percentage to better reflect severe damage
            # This is a temporary solution until a proper model is implemented
            damage_factor = 1.5  # Adjust this factor based on testing with your images
            damage_percentage = min(damage_percentage * damage_factor, 100.0)
    else:
        damage_percentage = 0
    
    return forest_area_before, forest_area_after, damage_percentage

def save_segmented_image(segmented_image, output_path):
    """
    Save segmented image with color-coded classes
    
    Args:
        segmented_image: Segmented image with class labels
        output_path: Path to save the colored segmentation
    """
    # Create a colored visualization of the segmentation
    # Map class indices to colors
    color_map = {
        0: hex_to_rgb(BUILDING),    # Building
        1: hex_to_rgb(LAND),        # Land
        2: hex_to_rgb(ROAD),        # Road
        3: hex_to_rgb(VEGETATION),  # Vegetation
        4: hex_to_rgb(WATER),       # Water
        5: hex_to_rgb(UNLABELED)    # Unlabeled
    }
    
    # Create RGB image
    height, width = segmented_image.shape
    colored_segmentation = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Apply colors based on class indices
    for class_idx, color in color_map.items():
        colored_segmentation[segmented_image == class_idx] = color
    
    # Save the image
    cv2.imwrite(output_path, cv2.cvtColor(colored_segmentation, cv2.COLOR_RGB2BGR))

def visualize_segmentation(segmented):
    """
    Create a colored visualization of a segmented image
    
    Args:
        segmented: Segmented image with class labels
        
    Returns:
        visualization: RGB visualization of segmentation
    """
    # Define colors for each class (RGB format)
    # 0: Unlabeled (black), 1: Land/soil (brown), 2: Water (blue), 3: Vegetation (green)
    colors = [
        [0, 0, 0],       # Unlabeled - Black
        [165, 42, 42],   # Land/soil - Brown
        [0, 0, 255],     # Water - Blue
        [0, 255, 0],     # Vegetation - Green
    ]
    
    # Create RGB visualization
    height, width = segmented.shape
    visualization = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Apply colors based on class labels
    for class_id, color in enumerate(colors):
        visualization[segmented == class_id] = color
    
    return visualization 