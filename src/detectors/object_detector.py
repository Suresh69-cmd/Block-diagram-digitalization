import os
import cv2
import json
from datetime import datetime
from ultralytics import YOLO

# ==========================================
#  1. CONFIGURATION
# ==========================================
PATCH_SIZE = 832
STRIDE = 600
CONF_THRESH = 0.7
IOU_THRESH = 0.5
MARGIN = 15

# Toggle visualization
DRAW_RESULTS = True

CLASSES = {
    0: "valve",
    1: "connector",
    2: "instrumentation",
    3: "tank",
    4: "arrow",
    5: "inlet/outlet",
    6: "crossing",
    7: "general"
}

IGNORE_CLASSES = ["crossing","connector"]  

CLASS_COLORS = {
    "valve": (0, 0, 255),
    "connector": (255, 0, 0),
    "instrumentation": (0, 255, 0),
    "tank": (255, 255, 0),
    "arrow": (0, 255, 255),
    "inlet/outlet": (255, 0, 255),
    "general": (150, 200, 250)
}

# ==========================================
#  2. IOU + NMS         
# ==========================================
def calculate_iou(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    inter = max(0, xB - xA) * max(0, yB - yA)
    if inter == 0:
        return 0.0

    areaA = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    areaB = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

    return inter / float(areaA + areaB - inter)


def global_nms(predictions, iou_thresh):
    if not predictions:
        return []

    predictions = sorted(predictions, key=lambda x: x['conf'], reverse=True)
    kept = []

    for pred in predictions:
        keep = True
        for k in kept:
            if pred['cls_id'] == k['cls_id']:
                if calculate_iou(pred['bbox'], k['bbox']) > iou_thresh:
                    keep = False
                    break
        if keep:
            kept.append(pred)

    return kept


# ==========================================
#  3. DRAW FUNCTION (IMPROVED)
# ==========================================
def draw_prediction(img, pred):
    xmin, ymin, xmax, ymax = map(int, pred["bbox"])
    class_name = pred["class_name"]
    conf = pred["conf"]

    color = CLASS_COLORS.get(class_name, (255, 255, 255))

    # Bounding box
    cv2.rectangle(img, (xmin, ymin), (xmax, ymax), color, 2)

    # Label
    label = f"{class_name} {conf:.2f}"
    (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)

    # Background rectangle
    cv2.rectangle(img, (xmin, ymin - h - 5), (xmin + w, ymin), color, -1)

    # Text
    cv2.putText(img, label, (xmin, ymin - 3),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

    # Center point
    cx = int((xmin + xmax) / 2)
    cy = int((ymin + ymax) / 2)
    cv2.circle(img, (cx, cy), 3, (255, 255, 255), -1)


# ==========================================
#  4. CORE PIPELINE
# ==========================================
def process_single_diagram(image_path, model, output_dir):

    img = cv2.imread(image_path)
    if img is None:
        print(f" Error loading {image_path}")
        return

    h, w = img.shape[:2]
    filename = os.path.basename(image_path)
    base = os.path.splitext(filename)[0]

    print(f" Processing: {filename} ({w}x{h})")

    all_preds = []

    # Sliding window
    for y in range(0, h, STRIDE):
        for x in range(0, w, STRIDE):

            y1 = y
            x1 = x
            y2 = min(y + PATCH_SIZE, h)
            x2 = min(x + PATCH_SIZE, w)

            if y2 - y1 < PATCH_SIZE:
                y1 = max(0, h - PATCH_SIZE)
            if x2 - x1 < PATCH_SIZE:
                x1 = max(0, w - PATCH_SIZE)

            patch = img[y1:y2, x1:x2]

            results = model.predict(
                source=patch,
                imgsz=PATCH_SIZE,
                conf=CONF_THRESH,
                verbose=False
            )[0]

            for box in results.boxes:
                cls_id = int(box.cls[0])
                class_name = CLASSES.get(cls_id, "unknown")

                if class_name in IGNORE_CLASSES:
                    continue

                conf = float(box.conf[0])
                xmin, ymin, xmax, ymax = box.xyxy[0].tolist()

                # Edge filtering
                if (
                    (xmin < MARGIN and x1 > 0) or
                    (ymin < MARGIN and y1 > 0) or
                    (xmax > PATCH_SIZE - MARGIN and x2 < w) or
                    (ymax > PATCH_SIZE - MARGIN and y2 < h)
                ):
                    continue

                # Global mapping
                xmin += x1
                ymin += y1
                xmax += x1
                ymax += y1

                all_preds.append({
                    "cls_id": cls_id,
                    "class_name": class_name,
                    "conf": conf,
                    "bbox": [xmin, ymin, xmax, ymax]
                })

    # Apply NMS
    final_preds = global_nms(all_preds, IOU_THRESH)

    # ==========================================
    # JSON GENERATION
    # ==========================================
    json_data = {
        "metadata": {
            "source_image": filename,
            "created_at": datetime.utcnow().isoformat()
        },
        "blocks": []
    }

    viz = img.copy()

    for i, pred in enumerate(final_preds):
        xmin, ymin, xmax, ymax = pred["bbox"]

        json_data["blocks"].append({
            "id": f"block_{i}",
            "type": pred["class_name"],
            "bbox": {
                "x": round(xmin, 2),
                "y": round(ymin, 2),
                "width": round(xmax - xmin, 2),
                "height": round(ymax - ymin, 2)
            },
            "confidence": round(pred["conf"], 4)
        })

        if DRAW_RESULTS:
            draw_prediction(viz, pred)

    # Save outputs
    json_path = os.path.join(output_dir, f"{base}.json")
    img_path = os.path.join(output_dir, f"{base}.jpg")

    with open(json_path, "w") as f:
        json.dump(json_data, f, indent=2)

    if DRAW_RESULTS:
        cv2.imwrite(img_path, viz)

    print(f" Saved: {base}")


# ==========================================
#  5. RUNNER
# ==========================================
def run_detector(input_path, output_dir, weights):

    print(" Loading model...")
    model = YOLO(weights)

    os.makedirs(output_dir, exist_ok=True)

    if os.path.isfile(input_path):
        process_single_diagram(input_path, model, output_dir)

    elif os.path.isdir(input_path):
        for file in os.listdir(input_path):
            if file.lower().endswith((".jpg", ".png", ".jpeg")):
                process_single_diagram(
                    os.path.join(input_path, file),
                    model,
                    output_dir
                )
    else:
        print(" Invalid input path")

    print(" Done!")


# ==========================================
#  6. LOCAL RUN
# ==========================================
if __name__ == "__main__":
    run_detector(
        input_path="data/input",
        output_dir="data/output",
        weights="weights/best.pt"
    )
