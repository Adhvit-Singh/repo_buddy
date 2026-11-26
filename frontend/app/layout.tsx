import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/ThemeProvider";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "repo_buddy — AI security review for AI-built apps",
  description:
    "Paste a GitHub repo. repo_buddy reads it with retrieval-augmented AI, explains it in plain English, flags security issues and can open a fix PR.",
  keywords: [
    "AI app security",
    "Lovable security scanner",
    "Bolt security audit",
    "Cursor security",
    "DAST live probe",
    "auto-fix vulnerabilities",
    "continuous monitoring",
    "vibe coding security",
  ],
  openGraph: {
    title: "repo_buddy — AI security review for AI-built apps",
    description:
      "Paste a GitHub repo, get a plain-English security report and a fix PR.",
    type: "website",
  },
};

const noFoucScript = `(function(){try{var s=localStorage.getItem('repo-buddy-theme');var t=(s==='light'||s==='dark')?s:(window.matchMedia&&window.matchMedia('(prefers-color-scheme: light)').matches?'light':'dark');document.documentElement.setAttribute('data-theme',t);}catch(e){document.documentElement.setAttribute('data-theme','dark');}})();`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        {/* No-FOUC: must run before paint, so we inline it. */}
        <script dangerouslySetInnerHTML={{ __html: noFoucScript }} />
      </head>
      <body
        className={`${inter.variable} ${jetbrainsMono.variable} antialiased`}
      >
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}
