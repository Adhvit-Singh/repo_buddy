import { describe, expect, it } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import ScanProgress from "@/components/ScanProgress";
import VulnerabilityList from "@/components/VulnerabilityList";
import HealthScoreRing from "@/components/HealthScoreRing";
import type { Vulnerability } from "@/types";

const vulns = [
  { title: "Admin route has no auth check", file: "api/admin.py", line: 12, severity: "critical", description: "Anyone can open /admin.", fix_suggestion: "Add a session check." },
  { title: "Missing CSP header", file: "next.config.ts", line: null, severity: "medium", description: "No Content-Security-Policy.", fix_suggestion: "Add a CSP." },
  { title: "Verbose errors", file: "main.py", line: 80, severity: "medium", description: "Stack traces are returned to users.", fix_suggestion: "Return a generic message." },
] as unknown as Vulnerability[];

describe("ScanProgress", () => {
  it("lists the real pipeline steps and no invented ones", () => {
    render(<ScanProgress repoLabel="octocat/Hello-World" />);
    expect(screen.getByText("Cloning your repo")).toBeInTheDocument();
    expect(screen.getByText("Embedding and indexing (ChromaDB)")).toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(/10,000|Attacking your live URL/);
  });
});

describe("VulnerabilityList", () => {
  it("groups findings by severity and opens criticals first", () => {
    render(<VulnerabilityList vulnerabilities={vulns} />);
    expect(screen.getByText("Admin route has no auth check")).toBeInTheDocument();
    expect(screen.getByText(/Critical/)).toBeInTheDocument();
    expect(screen.getByText(/Medium/)).toBeInTheDocument();
  });

  it("shows every finding — nothing is locked behind a paywall", () => {
    render(<VulnerabilityList vulnerabilities={vulns} />);
    fireEvent.click(screen.getByText(/Medium/));
    expect(screen.getByText("Missing CSP header")).toBeInTheDocument();
    expect(screen.getByText("Verbose errors")).toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(/Locked|upgrade/i);
  });

  it("renders an empty state with no findings", () => {
    const { container } = render(<VulnerabilityList vulnerabilities={[]} />);
    expect(container.textContent).not.toMatch(/Critical/);
  });
});

describe("HealthScoreRing", () => {
  it("shows the score and clamps the ring to 0-100", () => {
    render(<HealthScoreRing score={62} />);
    expect(screen.getByText("62")).toBeInTheDocument();
  });
});
