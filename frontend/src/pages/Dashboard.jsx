import { useEffect, useState } from "react";
import { listInventory } from "../api/api";
import "./Upload.css";

function Dashboard() {
  const [items, setItems] = useState([]);

  useEffect(() => {
    listInventory().then((res) => setItems(res.data));
  }, []);

  return (
    <div className="page">
      <div className="card wide" style={{ marginBottom: 12 }}>
        <p className="eyebrow">Inventory</p>
        <h2>Dashboard</h2>
      </div>

      {items.length === 0 && (
        <div className="card">
          <p className="label">No items yet</p>
          <p style={{ color: "#e8f0ff" }}>Upload a sneaker to begin.</p>
        </div>
      )}

      <div className="grid">
        {items.map((item) => (
          <div key={item._id} className="card">
            <p className="label">#{item.product_id}</p>
            <h3 style={{ margin: "4px 0" }}>
              {item.brand} {item.model}
            </h3>
            <p style={{ color: "#8ca3c0", marginBottom: 8 }}>
              {item.product_type || item.class_name}
            </p>
            <div className="stats-row">
              <div>
                <p className="label">Predicted</p>
                <p>${Number(item.price_predicted || 0).toFixed(2)}</p>
              </div>
              <div>
                <p className="label">User Price</p>
                <p>
                  {item.price_modified
                    ? `$${Number(item.price_modified).toFixed(2)}`
                    : "—"}
                </p>
              </div>
              <div>
                <p className="label">Quantity</p>
                <p>{item.quantity}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default Dashboard;
