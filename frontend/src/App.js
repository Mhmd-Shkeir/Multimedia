import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import "./pages/Upload.css";
import Upload from "./pages/Upload";
import AddInventory from "./pages/AddInventory";
import Dashboard from "./pages/Dashboard";

function App() {
  return (
    <BrowserRouter>
      <div className="app-shell">
        <nav className="nav">
          <div className="nav-brand">Sneaker AI</div>
          <div className="nav-links">
            <NavLink className="nav-link" to="/" end>
              Predict
            </NavLink>
            <NavLink className="nav-link" to="/dashboard">
              Inventory
            </NavLink>
          </div>
        </nav>
        <Routes>
          <Route path="/" element={<Upload />} />
          <Route path="/add" element={<AddInventory />} />
          <Route path="/dashboard" element={<Dashboard />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
