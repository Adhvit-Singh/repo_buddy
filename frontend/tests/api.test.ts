import { describe, expect, it, vi } from "vitest";
import { analyzeUrl, fetchMonitoredRepos, pollJobStatus } from "@/services/api";

function mockFetch(status: number, body: unknown) {
  return vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } }),
  );
}

describe("api client", () => {
  it("starts a scan with a POST containing the GitHub URL", async () => {
    const fetchSpy = mockFetch(200, { status: "processing", scan_id: "abc" });

    const result = await analyzeUrl("https://github.com/octocat/Hello-World");

    expect(result.scan_id).toBe("abc");
    const [url, init] = fetchSpy.mock.calls[0];
    expect(String(url)).toMatch(/\/api\/repos\/analyze-url$/);
    expect(init?.method).toBe("POST");
    expect(JSON.parse(String(init?.body))).toEqual({ github_url: "https://github.com/octocat/Hello-World" });
  });

  it("surfaces the backend's error message", async () => {
    mockFetch(422, { detail: "Only public https://github.com repositories can be scanned." });
    await expect(analyzeUrl("file:///etc/passwd")).rejects.toThrow("Only public https://github.com");
  });

  it("sends the stored GitHub token as a Bearer header", async () => {
    localStorage.setItem("github_token", "gho_test");
    const fetchSpy = mockFetch(200, []);

    await fetchMonitoredRepos();

    const init = fetchSpy.mock.calls[0][1];
    expect((init?.headers as Record<string, string>).Authorization).toBe("Bearer gho_test");
  });

  it("sends no auth header when signed out", async () => {
    const fetchSpy = mockFetch(200, []);
    await fetchMonitoredRepos();
    const init = fetchSpy.mock.calls[0][1];
    expect(init?.headers).toEqual({});
  });

  it("throws when polling fails", async () => {
    mockFetch(404, { detail: "Scan not found" });
    await expect(pollJobStatus("missing")).rejects.toThrow();
  });
});
