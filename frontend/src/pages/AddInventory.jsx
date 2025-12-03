import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { addInventory } from "../api/api";
import "./Upload.css";

function AddInventory() {
  const { state } = useLocation();
  const result = state?.result;
  const navigate = useNavigate();

  const [price, setPrice] = useState(result?.predicted_price || "");
  const [qty, setQty] = useState(1);
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    try {
      setSaving(true);
      await addInventory({
        slug: result.slug_used,
        class_name: result.class_name,
        brand: result.brand,
        model: result.model_name,
        product_name: result.product_name,
        product_type: result.product_type,
        price_predicted: result.predicted_price,
        quantity: Number(qty),
        price: Number(price),
      });

      navigate("/dashboard");
    } catch (err) {
      console.error(err);
      alert("Failed to save product.");
    } finally {
      setSaving(false);
    }
  };

  if (!result) {
    return <h2 style={{ padding: 40, color: "#fff" }}>No product selected</h2>;
  }

  return (
    <div className="page">
      <div className="card wide">
        <p className="eyebrow">Add / Update Inventory</p>
        <h2 style={{ marginTop: 4 }}>
          {result.brand} {result.model_name}
        </h2>
        <p className="label" style={{ marginBottom: 12 }}>
          {result.class_name} — {Math.round(result.confidence * 100)}% confidence
        </p>

        <div className="stats-row" style={{ marginBottom: 12 }}>
          <div>
            <p className="label">Predicted</p>
            <p>${Number(result.predicted_price || 0).toFixed(2)}</p>
          </div>
          <div>
            <p className="label">Retail</p>
            <p>${result.retail_price_usd || "--"}</p>
          </div>
          <div>
            <p className="label">Release Age</p>
            <p>
              {result.release_age
                ? `${result.release_age.toFixed(1)} yrs`
                : "--"}
            </p>
          </div>
        </div>

        <div className="controls" style={{ marginTop: 12 }}>
          <div>
            <p className="label">Set Price</p>
            <input
              type="number"
              min="0"
              className="input"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
            />
          </div>
          <div>
            <p className="label">Quantity</p>
            <input
              type="number"
              min="1"
              className="input"
              value={qty}
              onChange={(e) => setQty(e.target.value)}
            />
          </div>
        </div>

        <button className="primary full" onClick={handleSave} disabled={saving}>
          {saving ? "Saving..." : "Save Product"}
        </button>
      </div>
    </div>
  );
}

export default AddInventory;
