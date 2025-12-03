import { useState } from "react";
import { uploadImage } from "../api/api";
import { useNavigate } from "react-router-dom";
import "./Upload.css";

function Upload() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const navigate = useNavigate();

  const handlePredict = async () => {
    if (!file) return alert("Please choose an image.");

    const formData = new FormData();
    formData.append("file", file);

    try {
      setLoading(true);
      const res = await uploadImage(formData);
      setResult(res.data);
      setShowDetails(false);
    } catch (err) {
      console.error(err);
      alert("Prediction failed.");
    } finally {
      setLoading(false);
    }
  };

  const renderStatus = () => {
    if (!result) return null;
    if (result.status === "not_sneaker") {
      return <div className="badge badge-error">Not a sneaker — stopped.</div>;
    }
    if (result.confidence_level === "low" || result.status === "low_confidence") {
      return (
        <div className="badge badge-warn">
          Low confidence ({Math.round((result.confidence || 0) * 100)}%) — ask user to
          confirm.
        </div>
      );
    }
    if (result.decision === "continue") {
      return (
        <div className="badge badge-ok">
          {result.confidence_level?.toUpperCase()} confidence — continuing.
        </div>
      );
    }
    return null;
  };

  const similarItems = () => {
    if (!result || !result.similar_images) return [];
    if (Array.isArray(result.similar_images)) return result.similar_images;
    if (Array.isArray(result.similar_images.items)) return result.similar_images.items;
    return [];
  };

  return (
    <div className="page">
      <div className="hero">
        <div>
          <p className="eyebrow">Sneaker Type &amp; Price Prediction</p>
          <h1>
            Upload a photo, <span>auto-detect</span> the sneaker, and get
            pricing.
          </h1>
          <p className="sub">
            CLIP sneaker gate + ResNet50 classification + confidence tiering +
            price model + inventory check.
          </p>
          <div className="controls">
            <label className="file-input">
              <input
                type="file"
                accept="image/*"
                onChange={(e) => setFile(e.target.files[0])}
              />
              {file ? file.name : "Choose image"}
            </label>
            <button className="primary" onClick={handlePredict} disabled={loading}>
              {loading ? "Predicting..." : "Predict"}
            </button>
          </div>
        </div>
      </div>

      {result && (
        <div className="grid">
          <div className="card wide">
            <div className="card-header">
              <div>
                <p className="label">Detected</p>
                <h2>
                  {result.brand} {result.model_name}
                </h2>
              </div>
              {renderStatus()}
            </div>
            {!showDetails && (
              <button className="primary full" onClick={() => setShowDetails(true)}>
                Get info
              </button>
            )}

            {showDetails && (
              <>
                <div className="stats-row">
                  <div>
                    <p className="label">Sneaker Check</p>
                    <p>
                      {result.sneaker_check?.is_sneaker ? "Sneaker" : "Not sneaker"} (
                      {Math.round((result.sneaker_check?.probability || 0) * 100)}%)
                    </p>
                  </div>
                  <div>
                    <p className="label">Class</p>
                    <p>{result.class_name}</p>
                  </div>
                  <div>
                    <p className="label">Confidence</p>
                    <p>{Math.round((result.confidence || 0) * 100)}%</p>
                  </div>
                  <div>
                    <p className="label">Slug</p>
                    <p>{result.slug_used || "N/A"}</p>
                  </div>
                </div>

                <div className="stats-row">
                  <div>
                    <p className="label">Predicted Price</p>
                    <p>${Number(result.predicted_price || 0).toFixed(2)}</p>
                  </div>
                  <div>
                    <p className="label">Retail</p>
                    <p>${result.retail_price_usd || "--"}</p>
                  </div>
                  <div>
                    <p className="label">Release Age</p>
                    <p>
                      {result.release_age ? `${result.release_age.toFixed(1)} yrs` : "--"}
                    </p>
                  </div>
                  <div>
                    <p className="label">Silhouette</p>
                    <p>{result.silhouette || result.product_info?.silhouette || "--"}</p>
                  </div>
                </div>

                <div className="inventory-check">
                  <p className="label">Inventory</p>
                  {result.inventory?.exists ? (
                    <p>
                      Already in stock — qty {result.inventory.current_quantity} @ $
                      {result.inventory.price_modified ||
                        result.inventory.price_predicted ||
                        "--"}
                    </p>
                  ) : (
                    <p>New item — not found in inventory.</p>
                  )}
                </div>

                {(result.decision === "continue" || result.decision === "manual_check") && (
                  <button
                    className="primary full"
                    onClick={() => navigate("/add", { state: { result } })}
                  >
                    {result.decision === "manual_check" ? "Add / Confirm Manually" : "Add / Update Inventory"}
                  </button>
                )}
              </>
            )}
          </div>

          {result.similar_images?.source === "building" && (
            <div className="card">
              <p className="label">Similarity</p>
              <p>Building FAISS index for this class...</p>
            </div>
          )}

          {similarItems().length > 0 && result.similar_images?.source !== "building" && (
            <div className="card">
              <p className="label">Similarity (Top 5)</p>
              <div className="similar-grid">
                {similarItems().map((item) => {
                  const label = `${item.class_name || ""} / ${item.slug || ""}`.trim();
                  return (
                    <div key={item.path} className="similar-item">
                      {item.url ? (
                        <img src={item.url} alt={label} className="similar-img" />
                      ) : (
                        <div className="thumb-placeholder">img</div>
                      )}
                      <p>{label || item.filename || "match"}</p>
                      <p className="label">{item.score ? item.score.toFixed(2) : "--"}</p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default Upload;
