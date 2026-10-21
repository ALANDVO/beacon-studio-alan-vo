import { Routes, Route, Navigate } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Dashboard } from "./pages/Dashboard";

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/audit" element={<div className="card"><h2>Skill Audit</h2><p>Coming soon: Static analysis for AI agent skills</p></div>} />
        <Route path="/context" element={<div className="card"><h2>Company Context Pack</h2><p>Coming soon: Interview-driven context generation</p></div>} />
        <Route path="/gtm" element={<div className="card"><h2>GTM Tools</h2><p>Coming soon: Offer stack scorer, proof assets, MCP tool picker</p></div>} />
        <Route path="/plugins/new" element={<div className="card"><h2>Add Plugin</h2><p>Coming soon: Plugin submission form</p></div>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}

export default App;