"use client";

import { useEffect, useRef, useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import AuthCallback from "@/components/AuthCallback";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

/**
 * GitHub OAuth lands here with a one-time `handoff` code (never the token).
 * We trade it for the token via POST, then load the user profile.
 */
function CallbackContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return; // handoff codes are single-use; don't redeem twice
    started.current = true;

    const handoff = searchParams.get("handoff");
    const error = searchParams.get("error");

    const fail = (reason: unknown) => {
      console.error("Auth error:", reason);
      setStatus("error");
      setTimeout(() => router.push("/"), 3000);
    };

    if (error || !handoff) {
      fail(error || "missing handoff code");
      return;
    }

    (async () => {
      try {
        const exRes = await fetch(`${API_BASE}/auth/github/exchange`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ handoff }),
        });
        if (!exRes.ok) throw new Error("handoff exchange failed");
        const { access_token } = await exRes.json();

        // Remove the code from the address bar / history.
        window.history.replaceState(null, "", "/auth/callback");
        localStorage.setItem("github_token", access_token);

        const meRes = await fetch(`${API_BASE}/auth/github/me`, {
          headers: { Authorization: `Bearer ${access_token}` },
        });
        if (!meRes.ok) throw new Error("profile fetch failed");
        localStorage.setItem("gh_user", JSON.stringify(await meRes.json()));

        setStatus("success");
        setTimeout(() => router.push("/dashboard"), 1500);
      } catch (err) {
        localStorage.removeItem("github_token");
        fail(err);
      }
    })();
  }, [searchParams, router]);

  return <AuthCallback onComplete={() => router.push("/dashboard")} status={status} />;
}

export default function AuthCallbackPage() {
  return (
    <Suspense fallback={
      <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "var(--surface-main)" }}>
        <div style={{ width: "12px", height: "12px", borderRadius: "50%", background: "var(--green)", animation: "pulse-green 1.2s ease-in-out infinite" }} />
      </div>
    }>
      <CallbackContent />
    </Suspense>
  );
}
