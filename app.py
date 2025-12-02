from pathlib import Path

from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename

from ai.image_model import predict_class
from ai.slug_selector import get_slug_for_class
from ai.price_model import predict_price_for_slug

# project root
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = str(UPLOAD_DIR)


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict():
    if "file" not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    # save uploaded image (optional – good for debugging)
    filename = secure_filename(file.filename)
    save_path = UPLOAD_DIR / filename
    file.save(save_path)

    # 1) classify sneaker type from image
    pred_info = predict_class(save_path)   # uses ResNet50

    class_name = pred_info["class_name"]   # e.g. "adidas_samba"

    # 2) pick one GOAT slug for this class
    try:
        slug = get_slug_for_class(class_name)
    except FileNotFoundError:
        return jsonify({
            "error": f"No scraped data found for class '{class_name}'",
            "prediction": pred_info,
        }), 500

    # 3) predict price from CatBoost model using CSV features
    try:
        price, feature_row = predict_price_for_slug(slug)
    except Exception as e:
        return jsonify({
            "error": f"Price prediction failed: {e}",
            "prediction": pred_info,
            "slug": slug,
        }), 500

    response = {
        "brand": pred_info["brand"],
        "model": pred_info["model_name"],
        "class_name": class_name,
        "confidence": pred_info["confidence"],
        "slug_used": slug,
        "predicted_price": round(price, 2),
        # optional debug info from CSV:
        "retail_price_usd": feature_row.get("retail_price_usd"),
        "release_age": feature_row.get("release_age"),
    }
    return jsonify(response)


if __name__ == "__main__":
    app.run(debug=True)
