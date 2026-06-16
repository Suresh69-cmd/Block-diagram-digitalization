import os
import cv2
import json
from datetime import datetime
from ultralytics import YOLO

# ==========================================
# 📌 1. CONFIGURATION PARAMETERS
# ==========================================
# Slicing Parameters
PATCH_SIZE = 832     
STRIDE = 600         
CONF_THRESH = 0.6   
IOU_THRESH = 0.50    

# Class Map based on your YAML
CLASSES = {
    0: "valve", 
    1: "connector", 
    2: "instrumentation", 
    3: "tank", 
    4: "arrow", 
    5: "inlet/outlet"
}

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

    predictions = sorted(predictions, key=lambda x: x['conf'], reverse=True)
    kept_boxes = []

    for pred in predictions:
        keep = True
        for kept in kept_boxes:
            if pred['cls_id'] == kept['cls_id']:
                iou = calculate_iou(pred['bbox'], kept['bbox'])
                if iou > iou_threshold:
                    keep = False 
                    break
        if keep:
            kept_boxes.append(pred)
            
    return kept_boxes

# ==========================================
# 📌 3. CORE PROCESSING FUNCTION
# ==========================================
def process_single_diagram(image_path, model, output_dir):
    """Processes a single image and saves the JSON and Visualized JPG to output_dir."""
    
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Cannot load image at {image_path}")
        return
        
    img_h, img_w, _ = img.shape
    filename = os.path.basename(image_path)
    base_name = os.path.splitext(filename)[0]
    
    print(f"Processing [{filename}] ({img_w}x{img_h} pixels)...")
    
    all_global_predictions = []

    # Slide window across the massive image
    for y in range(0, img_h, STRIDE):
        for x in range(0, img_w, STRIDE):
            
            y_start = y
            x_start = x
            y_end = min(y + PATCH_SIZE, img_h)
            x_end = min(x + PATCH_SIZE, img_w)
            
            if y_end - y_start < PATCH_SIZE: y_start = max(0, img_h - PATCH_SIZE)
            if x_end - x_start < PATCH_SIZE: x_start = max(0, img_w - PATCH_SIZE)

            patch_img = img[y_start:y_end, x_start:x_end]
            
            results = model.predict(source=patch_img, imgsz=PATCH_SIZE, conf=CONF_THRESH, verbose=False)[0]
            
            IGNORE_CLASSES = ["connector"]

            for box in results.boxes:
                cls_id = int(box.cls[0])
                class_name = CLASSES.get(cls_id, "unknown")
                
                # 🚫 IGNORE CONNECTORS
                
                if class_name in IGNORE_CLASSES:
                    continue 
                
                conf = float(box.conf[0])
                local_xyxy = box.xyxy[0].tolist()
                l_xmin, l_ymin, l_xmax, l_ymax = local_xyxy
                
                # 🚫 EDGE DISCARDING (15-pixel margin)
                MARGIN = 15 
                hits_left   = (l_xmin < MARGIN) and (x_start > 0)
                hits_top    = (l_ymin < MARGIN) and (y_start > 0)
                hits_right  = (l_xmax > PATCH_SIZE - MARGIN) and (x_end < img_w)
                hits_bottom = (l_ymax > PATCH_SIZE - MARGIN) and (y_end < img_h)
                
                if hits_left or hits_top or hits_right or hits_bottom:
                    continue 
                
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

    # ==========================================
    # 📌 4. CLEAN UP & JSON GENERATION
    # ==========================================
    final_predictions = global_nms(all_global_predictions, IOU_THRESH)

    json_schema = {
        "metadata": {
            "schema_version": "2020-12",
            "source_image": filename,
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
        
        # Append to JSON
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
        
        # Draw on Master Image
        cv2.rectangle(viz_img, (int(xmin), int(ymin)), (int(xmax), int(ymax)), (0, 0, 255), 2)
        cv2.circle(viz_img, (int(x_center), int(y_center)), 4, (0, 255, 0), -1)
        label_text = f"{pred['class_name']} {pred['conf']:.2f}"
        cv2.putText(viz_img, label_text, (int(xmin), int(ymin) - 8), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

    # ==========================================
    # 📌 5. SAVE DYNAMIC DELIVERABLES
    # ==========================================
    json_path = os.path.join(output_dir, f"{base_name}_output.json")
    with open(json_path, "w") as f:
        json.dump(json_schema, f, indent=2)
        
    img_output_path = os.path.join(output_dir, f"{base_name}_visualized.jpg")
    cv2.imwrite(img_output_path, viz_img)

    print(f"Saved JSON: {os.path.basename(json_path)}")
    print(f"Saved Image: {os.path.basename(img_output_path)}\n")

# ==========================================
# 📌 6. BATCH ROUTER (FILE vs FOLDER)
# ==========================================
def run_detector(input_source, output_dir, weights_path):
    """Main entry point for the object detection pipeline."""
    print("Loading YOLO Model...")
    model = YOLO(weights_path)
    
    # Ensure the dynamic output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # If the input is a single image file
    if os.path.isfile(input_source):
        process_single_diagram(input_source, model, output_dir)
        
    # If the input is a folder containing multiple images
    elif os.path.isdir(input_source):
        print(f"Found directory. Processing all images in {input_source}...\n")
        valid_extensions = (".png", ".jpg", ".jpeg")
        
        for file in os.listdir(input_source):
            if file.lower().endswith(valid_extensions):
                full_path = os.path.join(input_source, file)
                process_single_diagram(full_path, model, output_dir)
    else:
        print(f"Error: Input source '{input_source}' is not a valid file or directory.")
        
    print("ALL PROCESSING COMPLETE!")
