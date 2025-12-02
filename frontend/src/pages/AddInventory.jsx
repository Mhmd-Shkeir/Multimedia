import { useLocation, useNavigate } from "react-router-dom";
import { useState } from "react";
import { addInventory } from "../api/api";

function AddInventory() {
  const { state } = useLocation();
  const result = state?.result;
  const navigate = useNavigate();

  const [price, setPrice] = useState(result.predicted_price);
  const [qty, setQty] = useState(1);

  const handleSave = async () => {
    try {
      await addInventory({
        ...result,
        price: Number(price),
        quantity: Number(qty)
      });

      alert("Product saved!");
      navigate("/dashboard");
    } catch (err) {
      console.error(err);
      alert("Failed to save product.");
    }
  };

  return (
    <div style={{ padding: 40 }}>
      <h1>Add To Inventory</h1>

      <p><b>Brand:</b> {result.brand}</p>
      <p><b>Model:</b> {result.model_name}</p>

      <label>Price:</label>
      <input
        type="number"
        value={price}
        onChange={(e) => setPrice(e.target.value)}
      />

      <br /><br />

      <label>Quantity:</label>
      <input
        type="number"
        value={qty}
        onChange={(e) => setQty(e.target.value)}
      />

      <br /><br />

      <button onClick={handleSave}>
        Save Product
      </button>
    </div>
  );
}

export default AddInventory;
