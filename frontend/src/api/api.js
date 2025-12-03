import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:5000",
});

// =======================
// IMAGE CLASSIFICATION
// =======================
export const uploadImage = (formData) =>
  API.post("/predict", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

// =======================
// INVENTORY
// =======================
export const addInventory = (data) => API.post("/add-to-inventory", data);

export const listInventory = () => API.get("/inventory");

// =======================
// IMAGE PIPELINE (GRIDFS)
// =======================
export const getImageUrl = (imageId) =>
  `http://127.0.0.1:5000/image/${imageId}`;
