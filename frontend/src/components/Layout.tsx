import { ReactNode } from "react";
import { Outlet, Link, useLocation } from "react-router-dom";

interface LayoutProps {
  children?: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const location = useLocation();
  void children;

  const navItems = [
    { path: "/", label: "Marketplace" },
    { path: "/audit", label: "Skill Audit" },
    { path: "/context", label: "Context Pack" },
    { path: "/gtm", label: "GTM Tools" },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}>
      <header
        style={{
          backgroundColor: "var(--color-bg-secondary)",
          borderBottom: "1px solid var(--color-border)",
          padding: "var(--spacing-md) var(--spacing-lg)",
          position: "sticky",
          top: 0,
          zIndex: 100,
        }}
      >
        <div className="container" style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <Link to="/" style={{ fontWeight: 700, fontSize: "1.25rem", color: "var(--color-primary)" }}>
            Beacon Studio
          </Link>
          <nav style={{ display: "flex", gap: "var(--spacing-lg)" }}>
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                style={{
                  color: location.pathname === item.path ? "var(--color-primary)" : "var(--color-text-muted)",
                  fontWeight: location.pathname === item.path ? 600 : 400,
                  padding: "var(--spacing-xs) 0",
                  borderBottom: location.pathname === item.path ? "2px solid var(--color-primary)" : "2px solid transparent",
                  transition: "all 0.15s ease",
                }}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      <main style={{ flex: 1, padding: "var(--spacing-lg) 0" }}>
        <div className="container">
          <Outlet />
        </div>
      </main>
      <footer
        style={{
          backgroundColor: "var(--color-bg-secondary)",
          borderTop: "1px solid var(--color-border)",
          padding: "var(--spacing-md) 0",
          marginTop: "auto",
        }}
      >
        <div className="container" style={{ textAlign: "center", color: "var(--color-text-muted)", fontSize: "0.875rem" }}>
          Beacon Studio \u00A9 2026 Alan Vo alanvo@gmail.com | AI & Machine Learning
        </div>
      </footer>
    </div>
  );
}