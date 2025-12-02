import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:5000", // Flask backend
});

// Upload image → predict sneaker info
export const uploadImage = (formData) =>
  API.post("/predict", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

// Add to inventory
export const addInventory = (data) =>
  API.post("/inventory/add", data);

// List items in inventory
export const listInventory = () =>
  API.get("/inventory/list");

// Fetch image from backend
export const getImageUrl = (id) =>
  `http://127.0.0.1:5000/inventory/image/${id}`;
