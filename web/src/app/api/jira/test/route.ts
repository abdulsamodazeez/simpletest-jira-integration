import type { JiraCredentials } from "@/lib/jira-server";
import { NextResponse } from "next/server";

export const runtime = "nodejs";

export async function POST(req: Request) {
  try {
    const creds = (await req.json()) as JiraCredentials;
    if (!creds?.baseUrl || !creds?.email || !creds?.apiToken) {
      return NextResponse.json({ error: "Missing credentials" }, { status: 400 });
    }
    const base = creds.baseUrl.replace(/\/$/, "");
    const url = `${base}/rest/api/3/myself`;
    const raw = `${creds.email}:${creds.apiToken}`;
    const auth = `Basic ${Buffer.from(raw, "utf8").toString("base64")}`;
    const resp = await fetch(url, {
      headers: { Accept: "application/json", Authorization: auth },
      signal: AbortSignal.timeout(30000),
    });
    const text = await resp.text();
    let payload: unknown = text;
    try {
      payload = JSON.parse(text);
    } catch {
      /* leave text */
    }
    if (!resp.ok) {
      return NextResponse.json(
        { ok: false, status: resp.status, error: `HTTP ${resp.status}`, raw: payload },
        { status: 200 }
      );
    }
    const u = payload as Record<string, unknown>;
    return NextResponse.json({
      ok: true,
      status: resp.status,
      displayName: u.displayName,
      emailAddress: u.emailAddress,
      accountId: u.accountId,
    });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    return NextResponse.json({ ok: false, error: msg }, { status: 500 });
  }
}
