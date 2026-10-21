import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { PluginCard } from "../components/PluginCard";
import { api } from "../api/client";

interface Plugin {
  id: string;
  name: string;
  description: string;
  harness: string;
  category: string;
  tags: string[];
  installCommand: string;
  author: string;
  stars: number;
  lastUpdated: string;
}

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

const HARNESSES = [
  "claude-code",
  "codex",
  "cursor",
  "opencode",
  "copilot",
  "antigravity",
  "pi",
];

const CATEGORIES = [
  "development",
  "analysis",
  "testing",
  "documentation",
  "deployment",
  "security",
  "productivity",
];

export function Dashboard() {
  const [plugins, setPlugins] = useState<Plugin[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [harnessFilter, setHarnessFilter] = useState<string>("all");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [page, setPage] = useState(1);
  const pageSize = 12;

  useEffect(() => {
    fetchPlugins();
  }, [page, search, harnessFilter, categoryFilter]);

  async function fetchPlugins() {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string | number> = {
        page,
        page_size: pageSize,
      };
      if (search) params.search = search;
      if (harnessFilter !== "all") params.harness = harnessFilter;
      if (categoryFilter !== "all") params.category = categoryFilter;

      const response = await api.get<PaginatedResponse<Plugin>>("/plugins", params);
      setPlugins(response.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load plugins");
    } finally {
      setLoading(false);
    }
  }

  function handleInstall(plugin: Plugin) {
    navigator.clipboard.writeText(plugin.installCommand);
    alert(`Copied install command: ${plugin.installCommand}`);
  }

  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "300px" }}>
        <div className="loading-spinner" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="card" style={{ textAlign: "center", padding: "var(--spacing-xl)" }}>
        <div className="empty-state-icon">⚠️</div>
        <h3>Failed to load plugins</h3>
        <p style={{ marginTop: "var(--spacing-sm)" }}>{error}</p>
        <button className="btn btn-primary" style={{ marginTop: "var(--spacing-md)" }} onClick={fetchPlugins}>
          Retry
        </button>
      </div>
    );
  }

  const filteredPlugins = plugins;
  const hasPlugins = filteredPlugins.length > 0;

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "var(--spacing-lg)", flexWrap: "wrap", gap: "var(--spacing-md)" }}>
        <div>
          <h1 style={{ fontSize: "1.75rem", fontWeight: 700 }}>Plugin Marketplace</h1>
          <p style={{ color: "var(--color-text-muted)", marginTop: "var(--spacing-xs)" }}>
            Discover and install agent plugins across 7+ harnesses
          </p>
        </div>
        <Link to="/plugins/new" className="btn btn-primary">
          + Add Plugin
        </Link>
      </div>

      <div className="card" style={{ marginBottom: "var(--spacing-lg)" }}>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "var(--spacing-md)", alignItems: "center" }}>
          <div style={{ flex: 1, minWidth: "250px" }}>
            <label className="form-label" htmlFor="search">Search plugins</label>
            <input
              id="search"
              type="text"
              className="form-input"
              placeholder="Search by name, description, tags..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <div style={{ minWidth: "180px" }}>
            <label className="form-label" htmlFor="harness">Harness</label>
            <select
              id="harness"
              className="form-input"
              value={harnessFilter}
              onChange={(e) => setHarnessFilter(e.target.value)}
            >
              <option value="all">All Harnesses</option>
              {HARNESSES.map((h) => (
                <option key={h} value={h}>{h}</option>
              ))}
            </select>
          </div>
          <div style={{ minWidth: "180px" }}>
            <label className="form-label" htmlFor="category">Category</label>
            <select
              id="category"
              className="form-input"
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
            >
              <option value="all">All Categories</option>
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {hasPlugins ? (
        <>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: "var(--spacing-md)" }}>
            {filteredPlugins.map((plugin) => (
              <PluginCard key={plugin.id} plugin={plugin} onInstall={handleInstall} />
            ))}
          </div>
          <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: "var(--spacing-md)", marginTop: "var(--spacing-lg)" }}>
            <button
              className="btn btn-secondary"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
            >
              Previous
            </button>
            <span style={{ color: "var(--color-text-muted)" }}>Page {page}</span>
            <button
              className="btn btn-secondary"
              onClick={() => setPage((p) => p + 1)}
              disabled={filteredPlugins.length < pageSize}
            >
              Next
            </button>
          </div>
        </>
      ) : (
        <div className="empty-state">
          <div className="empty-state-icon">📦</div>
          <h3>No plugins found</h3>
          <p style={{ marginTop: "var(--spacing-sm)" }}>
            {search || harnessFilter !== "all" || categoryFilter !== "all"
              ? "Try adjusting your filters or search query."
              : "Be the first to add a plugin!"}
          </p>
          <Link to="/plugins/new" className="btn btn-primary" style={{ marginTop: "var(--spacing-md)", display: "inline-block" }}>
            Add First Plugin
          </Link>
        </div>
      )}
    </div>
  );
}