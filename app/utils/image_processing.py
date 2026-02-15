"""
Image processing for post-typhoon forest damage assessment.
Follows the methodology from: Post-Typhoon Forest Damage Assessment using
Deep-Learning and Unmanned Aerial Vehicle Images (Milagan & Enriquez, 2021).
Six-class semantic segmentation with integer encoding and change detection by pixel count.
"""
import cv2
import numpy as np
import os
import time

# Six-class labels (manuscript order: Building, Land, Road, Vegetation, Water, Unlabeled)
CLASS_BUILDING = 0
CLASS_LAND = 1
CLASS_ROAD = 2
CLASS_VEGETATION = 3
CLASS_WATER = 4
CLASS_UNLABELED = 5

# RGB mask colors from manuscript (HEX); used for integer-encoded labels and visualization
BUILDING = "#3C1098"
LAND = "#8429F6"
ROAD = "#6EC1E4"
VEGETATION = "#FEDD3A"
WATER = "#E2A929"
UNLABELED = "#9B9B9B"

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
    
    # Change detection: vegetation in pre that is no longer vegetation in post
    veg_pre = (segmented_pre == CLASS_VEGETATION)
    veg_post = (segmented_post == CLASS_VEGETATION)
    # Damaged = was vegetation, now not (by segmentation)
    damaged_by_seg = veg_pre & ~veg_post

    # Refine with HSV: in pre-vegetation areas, large color shift suggests damage
    pre_hsv = cv2.cvtColor(pre_image, cv2.COLOR_BGR2HSV)
    post_hsv = cv2.cvtColor(post_image, cv2.COLOR_BGR2HSV)
    h_diff = np.abs(pre_hsv[:, :, 0].astype(np.int32) - post_hsv[:, :, 0].astype(np.int32))
    s_diff = np.abs(pre_hsv[:, :, 1].astype(np.int32) - post_hsv[:, :, 1].astype(np.int32))
    v_diff = np.abs(pre_hsv[:, :, 2].astype(np.int32) - post_hsv[:, :, 2].astype(np.int32))
    # Hue wrap-around: 179 and 0 are close
    h_diff = np.minimum(h_diff, 180 - h_diff)
    significant_hsv_change = (h_diff > 12) | (s_diff > 40) | (v_diff > 40)
    damaged_by_hsv = veg_pre & significant_hsv_change

    # Combined damage mask: lost vegetation by segmentation or strong HSV change
    significant_change = damaged_by_seg | damaged_by_hsv
    refined_post = segmented_post.copy()
    refined_post[significant_change] = CLASS_LAND  # Damaged vegetation -> land (manuscript change detection)

    # Damage and areas using refined comparison
    forest_area_before, forest_area_after, damage_percentage = calculate_damage(
        segmented_pre, refined_post
    )

    # Visualizations
    pre_vis = visualize_segmentation(segmented_pre)
    post_vis = visualize_segmentation(refined_post)
    change_vis = np.zeros_like(pre_image_rgb)
    change_vis[veg_pre] = [0, 255, 0]           # Green: was vegetation
    change_vis[significant_change] = [255, 0, 0]  # Red: damaged
    
    # Save visualizations under static/uploads
    timestamp = int(time.time())
    pre_vis_path = f"static/uploads/pre_vis_{timestamp}.jpg"
    post_vis_path = f"static/uploads/post_vis_{timestamp}.jpg"
    change_vis_path = f"static/uploads/change_vis_{timestamp}.jpg"
    base_dir = os.path.normpath(os.path.join(os.path.dirname(pre_image_path), "..", ".."))
    upload_dir = os.path.join(base_dir, "static", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
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

def _normalize_uint8(arr):
    """Scale array to 0-255 for consistent thresholds across images."""
    if arr.size == 0:
        return arr
    min_val, max_val = arr.min(), arr.max()
    if max_val <= min_val:
        return np.zeros_like(arr, dtype=np.uint8)
    return ((arr.astype(np.float32) - min_val) / (max_val - min_val) * 255).astype(np.uint8)


def perform_segmentation(image):
    """
    Six-class semantic segmentation (manuscript: Building, Land, Road, Vegetation, Water, Unlabeled).
    Uses color indices and rules compatible with the manuscript's integer-encoded masks.
    """
    height, width = image.shape[:2]
    b, g, r = (image[:, :, i].astype(np.float32) for i in (0, 1, 2))
    intensity = (r + g + b) / 3

    # Water (class 4): blue-dominant, relatively dark
    water_mask = (b > r) & (b > g) & (intensity < 180)

    # Vegetation (class 3): green-dominant (G > R and G > B) + Excess Green index
    exg = 2.0 * g - r - b
    green_dominant = (g > r) & (g > b)
    exg_uint = _normalize_uint8(exg)
    if np.any(green_dominant):
        pct = np.percentile(exg_uint[green_dominant], 25)
        veg_thresh = max(35, float(pct)) if np.isfinite(pct) else 70
    else:
        veg_thresh = 70
    vegetation_mask = (exg_uint >= veg_thresh) & green_dominant

    # Road (class 2): light grey, similar R≈G≈B; exclude green so vegetation isn't stolen
    neutral = np.abs(r.astype(np.int32) - g.astype(np.int32)) < 30
    neutral &= np.abs(g.astype(np.int32) - b.astype(np.int32)) < 30
    road_mask = neutral & (intensity >= 80) & (intensity <= 220) & ~green_dominant

    # Building (class 0): dark, non-green (avoid shadowed forest being labeled building)
    building_mask = (intensity < 100) & ~water_mask & ~green_dominant
    building_mask |= (intensity < 70) & ~water_mask & ~green_dominant

    # Land (class 1): red-dominant, brownish; exclude green so forest stays vegetation
    land_mask = (r > g + 15) & (r > b + 15) & ~neutral & ~green_dominant

    # Assign: vegetation and water take precedence so green/dark-green isn't overwritten by land/building
    segmented = np.full((height, width), CLASS_UNLABELED, dtype=np.uint8)
    segmented[land_mask] = CLASS_LAND
    segmented[building_mask & ~land_mask] = CLASS_BUILDING
    segmented[road_mask & ~building_mask & ~land_mask] = CLASS_ROAD
    segmented[vegetation_mask & ~water_mask & ~road_mask] = CLASS_VEGETATION
    segmented[water_mask] = CLASS_WATER

    return segmented

def calculate_damage(segmented_pre, segmented_post):
    """
    Calculate forest damage as the fraction of pre-typhoon vegetation
    that is no longer classified as vegetation in the post image.
    """
    total_pixels = segmented_pre.size
    forest_pixels_before = np.sum(segmented_pre == CLASS_VEGETATION)
    forest_pixels_after = np.sum(segmented_post == CLASS_VEGETATION)
    # Pixels that were vegetation in both (intact)
    vegetation_lost = forest_pixels_before - np.sum(
        (segmented_pre == CLASS_VEGETATION) & (segmented_post == CLASS_VEGETATION)
    )

    forest_area_before = (forest_pixels_before / total_pixels) * 100 if total_pixels else 0
    forest_area_after = (forest_pixels_after / total_pixels) * 100 if total_pixels else 0

    # Damage = % of pre-vegetation area that was lost (0–100)
    if forest_pixels_before > 0:
        damage_percentage = (vegetation_lost / forest_pixels_before) * 100
    else:
        damage_percentage = 0.0

    damage_percentage = max(0.0, min(100.0, damage_percentage))
    return forest_area_before, forest_area_after, damage_percentage

def save_segmented_image(segmented_image, output_path):
    """
    Save segmented image with manuscript HEX colors (six-class).
    """
    color_map = {
        CLASS_BUILDING: hex_to_rgb(BUILDING),
        CLASS_LAND: hex_to_rgb(LAND),
        CLASS_ROAD: hex_to_rgb(ROAD),
        CLASS_VEGETATION: hex_to_rgb(VEGETATION),
        CLASS_WATER: hex_to_rgb(WATER),
        CLASS_UNLABELED: hex_to_rgb(UNLABELED),
    }
    height, width = segmented_image.shape
    colored_segmentation = np.zeros((height, width, 3), dtype=np.uint8)
    for class_idx, color in color_map.items():
        colored_segmentation[segmented_image == class_idx] = color
    cv2.imwrite(output_path, cv2.cvtColor(colored_segmentation, cv2.COLOR_RGB2BGR))

def visualize_segmentation(segmented):
    """
    RGB visualization of six-class segmentation using manuscript HEX colors.
    """
    color_map = {
        CLASS_BUILDING: hex_to_rgb(BUILDING),
        CLASS_LAND: hex_to_rgb(LAND),
        CLASS_ROAD: hex_to_rgb(ROAD),
        CLASS_VEGETATION: hex_to_rgb(VEGETATION),
        CLASS_WATER: hex_to_rgb(WATER),
        CLASS_UNLABELED: hex_to_rgb(UNLABELED),
    }
    height, width = segmented.shape
    visualization = np.zeros((height, width, 3), dtype=np.uint8)
    for class_idx, color in color_map.items():
        visualization[segmented == class_idx] = color
    return visualization 