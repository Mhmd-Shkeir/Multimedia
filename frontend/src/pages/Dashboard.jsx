import { useEffect, useState } from "react";
import { listInventory, getImageUrl } from "../api/api";

function Dashboard() {
  const [items, setItems] = useState([]);

  useEffect(() => {
    listInventory().then((res) => setItems(res.data));
  }, []);

  return (
    <div style={{ padding: 40 }}>
      <h1>Inventory Dashboard</h1>

      {items.length === 0 && <p>No items uploaded yet.</p>}

      {items.map((item) => (
        <div
          key={item._id}
          style={{ border: "1px solid #ccc", padding: 20, marginBottom: 20 }}
        >
          <h2>{item.brand} {item.model_name}</h2>
          <p><b>Price:</b> ${item.price}</p>
          <p><b>Quantity:</b> {item.quantity}</p>

          <img
            src={getImageUrl(item._id)}
            alt="Sneaker"
            width={200}
            style={{ marginTop: 10 }}
          />
        </div>
      ))}
    </div>
  );
}

export default Dashboard;
