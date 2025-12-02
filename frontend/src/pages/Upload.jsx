import { useState } from "react";
import { uploadImage } from "../api/api";
import { useNavigate } from "react-router-dom";

function Upload() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const navigate = useNavigate();

  const handlePredict = async () => {
    if (!file) return alert("Please choose an image.");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await uploadImage(formData);
      setResult(res.data);
    } catch (err) {
      console.error(err);
      alert("Prediction failed.");
    }
  };

  return (
    <div style={{ padding: 40 }}>
      <h1>Sneaker Classification</h1>

      <input
        type="file"
        accept="image/*"
        onChange={(e) => setFile(e.target.files[0])}
      />

      <button onClick={handlePredict} style={{ marginTop: 20 }}>
        Predict Sneaker
      </button>

      {result && (
        <div style={{ marginTop: 30 }}>
          <h2>Prediction Result</h2>
          <p><b>Brand:</b> {result.brand}</p>
          <p><b>Model:</b> {result.model_name}</p>
          <p><b>Price:</b> ${result.predicted_price.toFixed(2)}</p>

          <button
            onClick={() => navigate("/add", { state: { result } })}
            style={{ marginTop: 20 }}
          >
            Add to Inventory
          </button>
        </div>
      )}
    </div>
  );
}

export default Upload;
