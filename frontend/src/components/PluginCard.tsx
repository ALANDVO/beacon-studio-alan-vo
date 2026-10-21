import { ReactNode } from "react";

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

interface PluginCardProps {
  plugin: Plugin;
  onInstall?: (plugin: Plugin) => void;
  children?: ReactNode;
}

export function PluginCard({ plugin, onInstall, children }: PluginCardProps) {
  const harnessColors: Record<string, string> = {
    "claude-code": "#D97757",
    "codex": "#000000",
    "cursor": "#000000",
    "opencode": "#6E56CF",
    "copilot": "#000000",
    "antigravity": "#4285F4",
    "pi": "#FF6B35",
  };

  const harnessColor = harnessColors[plugin.harness.toLowerCase()] || "var(--color-primary)";

  return (
    <div className="card" style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: "var(--spacing-sm)" }}>
        <h3 style={{ fontSize: "1.125rem", fontWeight: 600 }}>{plugin.name}</h3>
        <span
          className="badge"
          style={{
            backgroundColor: `${harnessColor}20`,
            color: harnessColor,
            border: `1px solid ${harnessColor}40`,
          }}
        >
          {plugin.harness}
        </span>
      </div>
      <p style={{ color: "var(--color-text-muted)", fontSize: "0.875rem", marginBottom: "var(--spacing-sm)", flex: 1 }}>
        {plugin.description}
      </p>
      <div style={{ display: "flex", flexWrap: "wrap", gap: "var(--spacing-xs)", marginBottom: "var(--spacing-sm)" }}>
        <span className="badge badge-primary">{plugin.category}</span>
        {plugin.tags.slice(0, 3).map((tag) => (
          <span key={tag} className="badge" style={{ backgroundColor: "var(--color-bg-tertiary)", color: "var(--color-text-muted)" }}>
            {tag}
          </span>
        ))}
        {plugin.tags.length > 3 && (
          <span className="badge" style={{ backgroundColor: "var(--color-bg-tertiary)", color: "var(--color-text-muted)" }}>
            +{plugin.tags.length - 3} more
          </span>
        )}
      </div>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: "auto", paddingTop: "var(--spacing-sm)", borderTop: "1px solid var(--color-border)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "var(--spacing-md)", fontSize: "0.75rem", color: "var(--color-text-muted)" }}>
          <span>By {plugin.author}</span>
          <span>⭐ {plugin.stars}</span>
          <span>Updated {new Date(plugin.lastUpdated).toLocaleDateString()}</span>
        </div>
        {onInstall && (
          <button
            className="btn btn-primary"
            onClick={() => onInstall(plugin)}
            style={{ fontSize: "0.75rem", padding: "4px 12px" }}
          >
            Install
          </button>
        )}
      </div>
      {children}
    </div>
  );
}