import { catalogByName } from "@/lib/catalog";
import {
  evaluateAssertions,
  executeFetch,
  type JiraCredentials,
} from "@/lib/jira-server";
import { NextResponse } from "next/server";

export const runtime = "nodejs";

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const creds = body.credentials as JiraCredentials | undefined;
    const casePayload = body.case as {
      name?: string;
      object: string;
      params?: Record<string, string>;
      assertions?: Record<string, unknown>;
    };

    if (!creds?.baseUrl || !creds?.email || !creds?.apiToken) {
      return NextResponse.json({ error: "Missing JIRA credentials" }, { status: 400 });
    }
    if (!casePayload?.object) {
      return NextResponse.json({ error: "Missing object name" }, { status: 400 });
    }

    const cat = catalogByName().get(casePayload.object);
    if (!cat) {
      return NextResponse.json({ error: `Unknown object: ${casePayload.object}` }, { status: 400 });
    }

    const params = casePayload.params || {};
    const started = Date.now();
    const response = await executeFetch(creds, cat, params);
    const rawAssert = casePayload.assertions || {};
    const evalOpts: Parameters<typeof evaluateAssertions>[1] = {
      required_fields: (rawAssert.required_fields as string[]) || [],
    };
    if (rawAssert.min_records !== undefined && rawAssert.min_records !== null) {
      evalOpts.min_records = Number(rawAssert.min_records);
    }
    if (rawAssert.max_records !== undefined && rawAssert.max_records !== null) {
      evalOpts.max_records = Number(rawAssert.max_records);
    }
    const assertions = evaluateAssertions(response, evalOpts);

    const passed =
      assertions.every((a) => a.passed) && response.ok;

    return NextResponse.json({
      case_name: casePayload.name || "<unnamed>",
      object_name: casePayload.object,
      passed,
      record_count: response.ok ? response.records.length : 0,
      assertions,
      response: {
        ok: response.ok,
        status_code: response.status_code,
        url: response.url,
        error: response.error ?? null,
        records: response.records,
        raw: response.raw,
      },
      duration_ms: Date.now() - started,
    });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}
