import os
import cv2
import json
from datetime import datetime
from ultralytics import YOLO

# ==========================================
# 📌 1. CONFIGURATION PATHS & PARAMETERS
# ==========================================
WEIGHTS_PATH = r"C:\Users\91630\Desktop\dataset\runs\detect\runs\train\pid_detector-4\weights\best.pt"  # Your trained weights
IMAGE_PATH = r"C:\Users\91630\Desktop\dataset\t5.png"
OUTPUT_DIR = r"C:\Users\91630\Desktop\dataset\output"

# Slicing Parameters
PATCH_SIZE = 832     # Size of the square patch to feed to YOLO
STRIDE = 600         # Stride (Overlap = 232 pixels). Prevents cutting symbols in half.
CONF_THRESH = 0.7   # Minimum confidence to accept a detection
IOU_THRESH = 0.50    # Threshold to merge duplicate boxes in overlap regions

# Class Map based on your YAML
CLASSES = {
    0: "valve", 
    1: "connector", 
    2: "instrumentation", 
    3: "tank", 
    4: "arrow", 
    5: "inlet/outlet"
}

# Ensure output directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
TEST_PATCHES_DIR = os.path.join(OUTPUT_DIR, "test_patches")
os.makedirs(TEST_PATCHES_DIR, exist_ok=True)


# ==========================================
# 📌 2. MATH & NMS HELPER FUNCTIONS
# ==========================================
def calculate_iou(boxA, boxB):
    """Calculates Intersection over Union (IoU) to find overlapping duplicates."""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interArea = max(0, xB - xA) * max(0, yB - yA)
    if interArea == 0:
        return 0.0

    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    return interArea / float(boxAArea + boxBArea - interArea)

def global_nms(predictions, iou_threshold):
    """Filters out duplicate detections from overlapping image patches."""
    if len(predictions) == 0:
        return []

    # Sort predictions by confidence score (highest first)
    predictions = sorted(predictions, key=lambda x: x['conf'], reverse=True)
    kept_boxes = []

    for pred in predictions:
        keep = True
        for kept in kept_boxes:
            # Only compare boxes of the same class
            if pred['cls_id'] == kept['cls_id']:
                iou = calculate_iou(pred['bbox'], kept['bbox'])
                if iou > iou_threshold:
                    keep = False # It's a duplicate of a higher-confidence box, discard
                    break
        if keep:
            kept_boxes.append(pred)
            
    return kept_boxes

# ==========================================
# 📌 3. THE MAIN DIGITIZER PIPELINE
# ==========================================
def process_full_diagram():
    print("🚀 Loading YOLO Model...")
    model = YOLO(WEIGHTS_PATH)
    
    img = cv2.imread(IMAGE_PATH)
    if img is None:
        print(f"❌ Error: Cannot load image at {IMAGE_PATH}")
        return
        
    img_h, img_w, _ = img.shape
    print(f"📐 Loaded Master Diagram: {img_w}x{img_h} pixels")
    
    all_global_predictions = []
    patch_count = 0

    print("✂️ Slicing image and running localized inference...")
    # Slide window across the massive image
    for y in range(0, img_h, STRIDE):
        for x in range(0, img_w, STRIDE):
            
            # Prevent window from going out of bounds
            y_start = y
            x_start = x
            y_end = min(y + PATCH_SIZE, img_h)
            x_end = min(x + PATCH_SIZE, img_w)
            
            # If the patch is too small at the edges, shift it back to maintain PATCH_SIZE
            if y_end - y_start < PATCH_SIZE: y_start = max(0, img_h - PATCH_SIZE)
            if x_end - x_start < PATCH_SIZE: x_start = max(0, img_w - PATCH_SIZE)

            # Crop the patch
            patch_img = img[y_start:y_end, x_start:x_end]
            
            # Run YOLO on the local patch
            results = model.predict(source=patch_img, imgsz=PATCH_SIZE, conf=CONF_THRESH, verbose=False)[0]
            
            patch_has_detections = False
            patch_viz = patch_img.copy() if patch_count < 5 else None # Save first 5 patches for testing
            
            for box in results.boxes:
                cls_id = int(box.cls[0])
                class_name = CLASSES.get(cls_id, "unknown")
                
                # 🚫 THE FIX 1: IGNORE CONNECTORS COMPLETELY
                if class_name == "connector":
                    continue  # Skip this box and move to the next one
                
                conf = float(box.conf[0])
                
                # Local coordinates inside the patch
                local_xyxy = box.xyxy[0].tolist()
                l_xmin, l_ymin, l_xmax, l_ymax = local_xyxy
                
                # 🚫 THE FIX 2: EDGE DISCARDING
                # Define a 15-pixel "danger zone" around the inner border of the patch
                MARGIN = 15 
                
                # Check if the box touches the patch borders 
                # (We ignore the border check if the patch is touching the literal edge of the master image)
                hits_left   = (l_xmin < MARGIN) and (x_start > 0)
                hits_top    = (l_ymin < MARGIN) and (y_start > 0)
                hits_right  = (l_xmax > PATCH_SIZE - MARGIN) and (x_end < img_w)
                hits_bottom = (l_ymax > PATCH_SIZE - MARGIN) and (y_end < img_h)
                
                if hits_left or hits_top or hits_right or hits_bottom:
                    # The object was sliced in half! Ignore it. 
                    # The overlapping patch will catch it perfectly in the center.
                    continue 
                
                patch_has_detections = True
                
                # 🗺️ MAP TO GLOBAL MASTER COORDINATES
                g_xmin = l_xmin + x_start
                g_ymin = l_ymin + y_start
                g_xmax = l_xmax + x_start
                g_ymax = l_ymax + y_start
                
                all_global_predictions.append({
                    "cls_id": cls_id,
                    "class_name": class_name,
                    "conf": conf,
                    "bbox": [g_xmin, g_ymin, g_xmax, g_ymax]
                })
                
                # Draw on intermediate test patch
                if patch_viz is not None:
                    cv2.rectangle(patch_viz, (int(l_xmin), int(l_ymin)), (int(l_xmax), int(l_ymax)), (0,255,0), 2)
                    cv2.putText(patch_viz, f"{class_name}", (int(l_xmin), int(l_ymin)-5), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)

            # Save intermediate test patch
            if patch_has_detections and patch_count < 5:
                cv2.imwrite(os.path.join(TEST_PATCHES_DIR, f"test_patch_{patch_count}.jpg"), patch_viz)
                
            patch_count += 1

    print(f"✅ Processed {patch_count} patches. Total raw detections: {len(all_global_predictions)}")
    
    # ==========================================
    # 📌 4. CLEAN UP & JSON GENERATION
    # ==========================================
    print("🧹 Running Global Non-Maximum Suppression (Removing Duplicates)...")
    final_predictions = global_nms(all_global_predictions, IOU_THRESH)
    print(f"🎯 Final unique detections after NMS: {len(final_predictions)}")

    # Prepare Schema
    json_schema = {
        "metadata": {
            "schema_version": "2020-12",
            "source_image": os.path.basename(IMAGE_PATH),
            "created_at": datetime.utcnow().isoformat() + "Z"
        },
        "blocks": [],
        "text": [], "connections": [],
        "diagram": {"type": "Full_PID_Sheet", "block_count": len(final_predictions), "text_count": 0, "connection_count": 0}
    }

    viz_img = img.copy()

    for idx, pred in enumerate(final_predictions):
        xmin, ymin, xmax, ymax = pred["bbox"]
        width = xmax - xmin
        height = ymax - ymin
        x_center = xmin + (width / 2.0)
        y_center = ymin + (height / 2.0)
        
        # 1. Append to JSON
        json_schema["blocks"].append({
            "id": f"block_{idx}",
            "type": pred["class_name"],
            "label": f"{pred['class_name'].upper()}_{idx}",
            "bbox": {"x": round(xmin, 2), "y": round(ymin, 2), "width": round(width, 2), "height": round(height, 2)},
            "derived_coordinates": {
                "center": {"x": round(x_center, 2), "y": round(y_center, 2)},
                "vertices": {
                    "top_left": {"x": round(xmin, 2), "y": round(ymin, 2)},
                    "top_right": {"x": round(xmax, 2), "y": round(ymin, 2)},
                    "bottom_right": {"x": round(xmax, 2), "y": round(ymax, 2)},
                    "bottom_left": {"x": round(xmin, 2), "y": round(ymax, 2)}
                }
            },
            "confidence": round(pred["conf"], 4)
        })
        
        # 2. Draw on Master Image
        # Draw Box
        cv2.rectangle(viz_img, (int(xmin), int(ymin)), (int(xmax), int(ymax)), (0, 0, 255), 2)
        # Draw Center Point
        cv2.circle(viz_img, (int(x_center), int(y_center)), 4, (0, 255, 0), -1)
        # Draw Label
        label_text = f"{pred['class_name']} {pred['conf']:.2f}"
        cv2.putText(viz_img, label_text, (int(xmin), int(ymin) - 8), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

    # ==========================================
    # 📌 5. SAVE FINAL DELIVERABLES
    # ==========================================
    json_path = os.path.join(OUTPUT_DIR, "final_master_output.json")
    with open(json_path, "w") as f:
        json.dump(json_schema, f, indent=2)
        
    img_output_path = os.path.join(OUTPUT_DIR, "visualized_full_prediction.jpg")
    cv2.imwrite(img_output_path, viz_img)

    print(f"🎉 DONE! Outputs saved to {OUTPUT_DIR}")
    print(f"📄 JSON: {json_path}")
    print(f"🖼️ Master Image: {img_output_path}")
    print(f"🧩 Test Patches saved in: {TEST_PATCHES_DIR}")

if __name__ == "__main__":
    process_full_diagram()