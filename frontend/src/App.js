import { BrowserRouter, Routes, Route } from "react-router-dom";
import Upload from "./pages/Upload";
import AddInventory from "./pages/AddInventory";
import Dashboard from "./pages/Dashboard";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Upload />} />
        <Route path="/add" element={<AddInventory />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
