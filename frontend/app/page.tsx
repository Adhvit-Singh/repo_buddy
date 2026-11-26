"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import { fetchPlatformStats } from "@/services/api";
import { PlatformStats } from "@/types";
import {
  ArrowRight, Shield, GitBranch, Activity,
  Eye, Wrench, Bell, Terminal, Lock,
  TrendingUp, ChevronRight, AlertTriangle,
} from "lucide-react";

/* ── small reusable components ── */

function StatPill({ value, label }: { value: string; label: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
      <span style={{ fontWeight: 700, fontSize: "0.9375rem", color: "var(--text-primary)", fontVariantNumeric: "tabular-nums" }}>
        {value}
      </span>
      <span style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>{label}</span>
    </div>
  );
}

function Divider() {
  return <div style={{ width: "1px", height: "16px", background: "var(--border-strong)" }} />;
}

function FeatureCard({
  icon: Icon, title, desc, accent,
}: { icon: React.ElementType; title: string; desc: string; accent?: boolean }) {
  return (
    <div
      style={{
        background: accent ? "var(--green-dim)" : "var(--surface-alt)",
        border: `1px solid ${accent ? "var(--green-border)" : "var(--border-subtle)"}`,
        borderRadius: "10px",
        padding: "1.5rem",
        display: "flex",
        flexDirection: "column",
        gap: "0.875rem",
        transition: "border-color 0.15s",
      }}
    >
      <div
        style={{
          width: "36px",
          height: "36px",
          borderRadius: "8px",
          background: accent ? "rgba(34,197,94,0.12)" : "var(--surface-elevated)",
          border: `1px solid ${accent ? "var(--green-border)" : "var(--border-subtle)"}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <Icon size={16} color={accent ? "var(--green)" : "var(--text-secondary)"} strokeWidth={1.75} />
      </div>
      <div>
        <h3 style={{ fontSize: "0.9375rem", fontWeight: 600, marginBottom: "0.375rem", letterSpacing: "-0.02em" }}>
          {title}
        </h3>
        <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", lineHeight: 1.6, margin: 0 }}>
          {desc}
        </p>
      </div>
    </div>
  );
}


/* ── example live-probe result (illustrative) ── */
function ProbePreview() {
  return (
    <div
      style={{
        background: "#0d0d0d",
        border: "1px solid var(--border-subtle)",
        borderRadius: "10px",
        overflow: "hidden",
        fontFamily: "var(--font-mono), monospace",
        fontSize: "0.75rem",
      }}
    >
      <div style={{ background: "#161616", padding: "10px 14px", display: "flex", alignItems: "center", gap: "6px", borderBottom: "1px solid var(--border-subtle)" }}>
        <div style={{ width: "10px", height: "10px", borderRadius: "50%", background: "#ff5f57" }} />
        <div style={{ width: "10px", height: "10px", borderRadius: "50%", background: "#febc2e" }} />
        <div style={{ width: "10px", height: "10px", borderRadius: "50%", background: "#28c840" }} />
        <span style={{ marginLeft: "8px", color: "var(--text-tertiary)", fontSize: "0.6875rem" }}>repo_buddy — example probe result</span>
      </div>
      <div style={{ padding: "1rem 1.25rem", display: "flex", flexDirection: "column", gap: "4px" }}>
        <div style={{ color: "#888" }}># Check: is the .env file publicly downloadable?</div>
        <div style={{ color: "#888" }}>&nbsp;</div>
        <div style={{ color: "#60a5fa" }}>GET https://your-app.example/<span style={{ color: "#fbbf24" }}>.env</span></div>
        <div style={{ color: "#888" }}>&nbsp;</div>
        <div>
          <span style={{ color: "#ef4444", fontWeight: 700 }}>CRITICAL</span>
          <span style={{ color: "#888" }}> → 200 OK, body looks like an env file</span>
        </div>
        <div style={{ color: "#888" }}>  DATABASE_URL=&quot;<span style={{ color: "#fbbf24" }}>postgres://…</span>&quot;</div>
        <div style={{ color: "#888" }}>&nbsp;</div>
        <div style={{ color: "#888" }}># Fix: never deploy .env — set secrets in your host&apos;s dashboard</div>
        <div style={{ color: "#888" }}>&nbsp;</div>
        <div>
          <span style={{ color: "#22c55e", fontWeight: 700 }}>PASS</span>
          <span style={{ color: "#888" }}> → /.git/config returns 404</span>
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════
   MAIN PAGE
═══════════════════════════════════════════════════════ */
export default function LandingPage() {
  const router = useRouter();
  const [repoUrl, setRepoUrl] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [stats, setStats] = useState<PlatformStats | null>(null);

  useEffect(() => {
    fetchPlatformStats().then(setStats).catch(() => {});
  }, []);

  const handleAnalyze = (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoUrl.trim()) return;
    setIsSubmitting(true);
    router.push(`/explore?url=${encodeURIComponent(repoUrl.trim())}`);
  };

  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const exampleRepos = [
    "vercel/next.js",
    "tiangolo/fastapi",
    "supabase/supabase",
  ];

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", background: "var(--surface-main)" }}>
      <Navbar />

      <main style={{ flex: 1 }}>

        {/* ══════════════════════════════════════════════
            HERO
        ══════════════════════════════════════════════ */}
        <section
          style={{
            paddingTop: "calc(var(--nav-height) + 80px)",
            paddingBottom: "80px",
            paddingLeft: "1.5rem",
            paddingRight: "1.5rem",
          }}
        >
          <div style={{ maxWidth: "680px", margin: "0 auto", textAlign: "center" }}>

            {/* Headline */}
            <h1
              className="animate-in stagger-2"
              style={{
                fontSize: "clamp(2.5rem, 6vw, 4.25rem)",
                fontWeight: 700,
                letterSpacing: "-0.04em",
                lineHeight: 1.08,
                marginBottom: "1.25rem",
              }}
            >
              Is your AI-built app
              <br />
              <span style={{ color: "var(--green)" }}>safe to ship?</span>
            </h1>

            {/* Subtext */}
            <p
              className="animate-in stagger-3"
              style={{
                fontSize: "1.0625rem",
                color: "var(--text-secondary)",
                lineHeight: 1.65,
                maxWidth: "520px",
                margin: "0 auto 2.5rem",
              }}
            >
              Paste a public GitHub repo. repo_buddy reads the code with retrieval-augmented AI,
              explains it in plain English, flags security issues with the file and line, and can
              open a pull request that fixes them.
            </p>

            {/* Scan bar */}
            <form onSubmit={handleAnalyze} className="animate-in stagger-4">
              <div className="scan-bar" style={{ maxWidth: "560px", margin: "0 auto" }}>
                <GitBranch size={15} color="var(--text-tertiary)" strokeWidth={1.75} />
                <input
                  type="text"
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                  placeholder="https://github.com/user/repo"
                  autoComplete="off"
                  spellCheck={false}
                />
                <button
                  type="submit"
                  disabled={!repoUrl.trim() || isSubmitting}
                  className="btn btn-green"
                  style={{ padding: "9px 20px", fontSize: "0.8125rem" }}
                >
                  {isSubmitting ? (
                    <span className="loading-dot">Scanning</span>
                  ) : (
                    <>
                      Scan Now
                      <ArrowRight size={13} style={{ marginLeft: "5px" }} />
                    </>
                  )}
                </button>
              </div>
            </form>

            {/* Example repos */}
            <div
              className="animate-in stagger-5"
              style={{ marginTop: "1rem", display: "flex", alignItems: "center", justifyContent: "center", gap: "8px", flexWrap: "wrap" }}
            >
              <span style={{ fontSize: "0.75rem", color: "var(--text-tertiary)" }}>Try:</span>
              {exampleRepos.map((r) => (
                <button
                  key={r}
                  onClick={() => setRepoUrl(`https://github.com/${r}`)}
                  style={{
                    fontSize: "0.6875rem",
                    color: "var(--text-tertiary)",
                    background: "var(--surface-elevated)",
                    border: "1px solid var(--border-subtle)",
                    padding: "3px 10px",
                    borderRadius: "999px",
                    cursor: "pointer",
                    fontFamily: "var(--font-mono), monospace",
                    transition: "all 0.15s",
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.color = "var(--green)";
                    e.currentTarget.style.borderColor = "var(--green-border)";
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.color = "var(--text-tertiary)";
                    e.currentTarget.style.borderColor = "var(--border-subtle)";
                  }}
                >
                  {r}
                </button>
              ))}
            </div>

            {/* Stats */}
            {stats && stats.total_scans > 0 && (
              <div
                className="animate-in stagger-6"
                style={{ marginTop: "2rem", display: "flex", alignItems: "center", justifyContent: "center", gap: "16px", flexWrap: "wrap" }}
              >
                <StatPill value={stats.total_scans.toLocaleString()} label="repos scanned" />
                <Divider />
                <StatPill value={stats.total_vulnerabilities.toLocaleString()} label="vulnerabilities found" />
                <Divider />
                <StatPill value={(stats.total_criticals ?? 0).toLocaleString()} label="critical findings" />
              </div>
            )}

          </div>
        </section>

        {/* ══════════════════════════════════════════════
            PROOF OF EXPLOIT — the differentiator
        ══════════════════════════════════════════════ */}
        <section style={{ borderTop: "1px solid var(--border-subtle)", borderBottom: "1px solid var(--border-subtle)", padding: "80px 1.5rem" }}>
          <div className="proof-grid" style={{ maxWidth: "var(--max-width)", margin: "0 auto", display: "grid", gridTemplateColumns: "1fr 1fr", gap: "4rem", alignItems: "center" }}>

            <div>
              <div style={{ marginBottom: "1rem" }}>
                <span className="badge badge-red">
                  <AlertTriangle size={10} />
                  Live HTTP probe
                </span>
              </div>
              <h2 style={{ fontSize: "clamp(1.75rem, 3vw, 2.25rem)", fontWeight: 700, letterSpacing: "-0.035em", lineHeight: 1.2, marginBottom: "1rem" }}>
                Reading code isn&apos;t enough.
                <br />
                <span style={{ color: "var(--green)" }}>Check the live app too.</span>
              </h2>
              <p style={{ fontSize: "0.9375rem", color: "var(--text-secondary)", lineHeight: 1.7, marginBottom: "1.5rem" }}>
                Point repo_buddy at your deployed URL and it runs 20 read-only HTTP checks: exposed
                .env and .git files, missing security headers, open CORS, unprotected admin routes,
                secrets in the JavaScript bundle, and stack-specific checks for Supabase, Firebase,
                NextAuth, Clerk, Vercel and Stripe.
              </p>
              <p style={{ fontSize: "0.8125rem", color: "var(--text-tertiary)", lineHeight: 1.6 }}>
                Every result shows the exact request sent and the response received. Checks are
                passive: no writes and no login bypass attempts.
              </p>
            </div>

            <ProbePreview />
          </div>
        </section>

        {/* ══════════════════════════════════════════════
            HOW IT WORKS
        ══════════════════════════════════════════════ */}
        <section style={{ padding: "80px 1.5rem" }}>
          <div style={{ maxWidth: "var(--max-width)", margin: "0 auto" }}>
            <div style={{ textAlign: "center", marginBottom: "3.5rem" }}>
              <h2 style={{ fontSize: "clamp(1.5rem, 3vw, 2rem)", fontWeight: 700, letterSpacing: "-0.035em", marginBottom: "0.5rem" }}>
                Three steps. About a minute.
              </h2>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.9375rem" }}>
                No setup and no security expertise needed.
              </p>
            </div>

            <div className="steps-grid" style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "1px", background: "var(--border-subtle)", border: "1px solid var(--border-subtle)", borderRadius: "12px", overflow: "hidden" }}>
              {[
                { n: "01", title: "Paste your repo", desc: "Any public GitHub URL. No signup needed. Works with Lovable, Bolt, v0, Cursor, Replit — anything built with AI.", icon: GitBranch },
                { n: "02", title: "Understand what you built", desc: "repo_buddy explains your app's architecture in plain English, with a diagram, the tech stack and how data flows.", icon: Terminal },
                { n: "03", title: "Fix with one click", desc: "Copy the fix suggestion into Cursor or your IDE, or sign in with GitHub and let repo_buddy open a fix PR for you to review.", icon: Shield },
              ].map((step) => (
                <div
                  key={step.n}
                  style={{
                    background: "var(--surface-alt)",
                    padding: "2rem",
                    display: "flex",
                    flexDirection: "column",
                    gap: "1rem",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <span style={{ fontSize: "0.6875rem", fontWeight: 700, color: "var(--text-tertiary)", fontVariantNumeric: "tabular-nums", letterSpacing: "0.05em" }}>
                      {step.n}
                    </span>
                    <div style={{ flex: 1, height: "1px", background: "var(--border-subtle)" }} />
                    <step.icon size={14} color="var(--green)" strokeWidth={1.75} />
                  </div>
                  <h3 style={{ fontSize: "1rem", fontWeight: 600, letterSpacing: "-0.02em", margin: 0 }}>
                    {step.title}
                  </h3>
                  <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", lineHeight: 1.6, margin: 0 }}>
                    {step.desc}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ══════════════════════════════════════════════
            FEATURES
        ══════════════════════════════════════════════ */}
        <section style={{ borderTop: "1px solid var(--border-subtle)", padding: "80px 1.5rem" }}>
          <div style={{ maxWidth: "var(--max-width)", margin: "0 auto" }}>
            <div style={{ textAlign: "center", marginBottom: "3.5rem" }}>
              <h2 style={{ fontSize: "clamp(1.5rem, 3vw, 2rem)", fontWeight: 700, letterSpacing: "-0.035em", marginBottom: "0.5rem" }}>
                Built for people who ship with AI
              </h2>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.9375rem", maxWidth: "420px", margin: "0 auto" }}>
                You built it fast. repo_buddy helps you understand what you built.
              </p>
            </div>

            <div className="features-grid" style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: "1rem" }}>
              <FeatureCard
                icon={Eye}
                title="Plain-English Report"
                desc="No jargon. Every finding is explained as what an attacker could actually do to your users, with the file and line it came from."
              />
              <FeatureCard
                icon={Lock}
                accent
                title="Live HTTP Probe"
                desc="20 passive checks against your deployed URL, each with the exact request and response as evidence."
              />
              <FeatureCard
                icon={Activity}
                title="Continuous Monitoring"
                desc="Add a GitHub webhook and every push triggers a scan of just the changed files, so new issues show up within minutes."
              />
              <FeatureCard
                icon={Wrench}
                title="Auto-Fix PRs"
                desc="Sign in with GitHub to generate a pull request with the fix written for you. It is AI-generated, so review it before merging."
              />
              <FeatureCard
                icon={TrendingUp}
                title="Health Score Trend"
                desc="Every scan is saved, so you can track your health score over time and compare scans side by side."
              />
              <FeatureCard
                icon={Bell}
                title="Critical Alerts"
                desc="Optional email and Slack alerts when a push introduces a critical finding."
              />
            </div>
          </div>
        </section>

        {/* ══════════════════════════════════════════════
            FINAL CTA
        ══════════════════════════════════════════════ */}
        <section style={{ borderTop: "1px solid var(--border-subtle)", padding: "100px 1.5rem" }}>
          <div style={{ maxWidth: "480px", margin: "0 auto", textAlign: "center" }}>
            <h2 style={{ fontSize: "clamp(1.75rem, 4vw, 2.5rem)", fontWeight: 700, letterSpacing: "-0.04em", marginBottom: "1rem" }}>
              Scan your repo.
              <br />
              <span style={{ color: "var(--green)" }}>Free and open source.</span>
            </h2>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.9375rem", lineHeight: 1.6, marginBottom: "2rem" }}>
              Paste any public GitHub URL above, no account needed. Sign in only to track repos or open fix PRs.
            </p>
            <a
              href={`${apiBase}/auth/github/login`}
              className="btn btn-green"
              style={{ padding: "13px 32px", fontSize: "0.9375rem" }}
            >
              Sign in with GitHub
              <ChevronRight size={15} style={{ marginLeft: "6px" }} />
            </a>
            <p style={{ marginTop: "1rem", fontSize: "0.75rem", color: "var(--text-tertiary)" }}>
              Public repos only · MIT licensed
            </p>
            <div style={{ marginTop: "2rem", display: "flex", alignItems: "center", justifyContent: "center", gap: "6px" }}>
              <span style={{ fontSize: "0.6875rem", color: "var(--text-tertiary)", letterSpacing: "0.05em" }}>Built by Adhvit Singh</span>
            </div>
          </div>
        </section>

      </main>

      <Footer />
    </div>
  );
}
