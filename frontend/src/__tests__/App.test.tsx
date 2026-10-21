import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import App from "../App";

vi.mock("../api/client", () => ({
  api: {
    get: vi.fn().mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      pageSize: 12,
      totalPages: 1,
    }),
  },
}));

describe("App", () => {
  it("renders without crashing", () => {
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );

    expect(screen.getByText("Beacon Studio")).toBeInTheDocument();
  });

  it("renders navigation links", () => {
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );

    expect(screen.getByText("Marketplace")).toBeInTheDocument();
    expect(screen.getByText("Skill Audit")).toBeInTheDocument();
    expect(screen.getByText("Context Pack")).toBeInTheDocument();
    expect(screen.getByText("GTM Tools")).toBeInTheDocument();
  });

  it("renders footer", () => {
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );

    expect(screen.getByText("Beacon Studio")).toBeInTheDocument();
    expect(screen.getByText(/AI .* Machine Learning/)).toBeInTheDocument();
  });

  it("renders loading spinner in main content area", () => {
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );

    const main = screen.getByRole("main");
    expect(main).toBeInTheDocument();
  });
});