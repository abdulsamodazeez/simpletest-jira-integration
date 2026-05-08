import type { CatalogObject } from "@/lib/catalog";

const PLATFORM = "/rest/api/3";
const AGILE = "/rest/agile/1.0";

export type JiraCredentials = {
  baseUrl: string;
  email: string;
  apiToken: string;
};

export type JiraFetchResult = {
  ok: boolean;
  status_code: number;
  records: unknown[];
  raw: unknown;
  url: string;
  error?: string | null;
};

function authHeader(c: JiraCredentials): string {
  const raw = `${c.email}:${c.apiToken}`;
  return `Basic ${Buffer.from(raw, "utf8").toString("base64")}`;
}

function resolvePath(obj: unknown, dotted: string): unknown {
  let cur: unknown = obj;
  for (const part of dotted.split(".")) {
    if (cur === null || cur === undefined) return undefined;
    if (typeof cur === "object" && cur !== null && part in (cur as object)) {
      cur = (cur as Record<string, unknown>)[part];
      continue;
    }
    return undefined;
  }
  return cur;
}

function normalizeRecords(payload: unknown, responsePath: string | null): unknown[] {
  if (responsePath) {
    const extracted = resolvePath(payload, responsePath);
    if (extracted === undefined || extracted === null) return [];
    return Array.isArray(extracted) ? extracted : [extracted];
  }
  if (Array.isArray(payload)) return payload;
  if (payload && typeof payload === "object") {
    const o = payload as Record<string, unknown>;
    for (const key of ["values", "issues", "records"]) {
      const v = o[key];
      if (Array.isArray(v)) return v;
    }
  }
  return [payload];
}

function resolveEndpoint(template: string, pathParams: Record<string, string>): string {
  let out = template;
  for (const [key, value] of Object.entries(pathParams)) {
    out = out.replace(new RegExp(`\\{${key}\\}`, "g"), value);
  }
  return out;
}

function isSearchJql(endpoint: string): boolean {
  return endpoint === "/search/jql";
}

export async function executeFetch(
  creds: JiraCredentials,
  obj: CatalogObject,
  params: Record<string, string>
): Promise<JiraFetchResult> {
  const base = creds.baseUrl.replace(/\/$/, "");
  const pathParams: Record<string, string> = {};
  const queryParams: Record<string, string> = {};

  for (const p of obj.params) {
    const val = params[p.name] ?? "";
    if (p.placement === "path") pathParams[p.name] = val;
    else if (p.placement === "query") {
      const use = val || (p.default ?? "");
      if (use) queryParams[p.name] = use;
    }
  }

  const missingPath = obj.params
    .filter((pp) => pp.placement === "path")
    .map((pp) => pp.name)
    .filter((name) => !pathParams[name]);

  if (missingPath.length) {
    return {
      ok: false,
      status_code: 0,
      records: [],
      raw: null,
      url: "",
      error: `Missing required path parameter(s): ${missingPath.join(", ")}`,
    };
  }

  const resolvedPath = resolveEndpoint(obj.endpoint, pathParams);
  const apiBase = obj.api === "agile" ? AGILE : PLATFORM;
  const urlPath = `${base}${apiBase}${resolvedPath}`;
  const headers: Record<string, string> = {
    Accept: "application/json",
    Authorization: authHeader(creds),
  };

  try {
    if (isSearchJql(obj.endpoint)) {
      const jql = params.jql ?? queryParams.jql ?? "";
      if (!jql) {
        return {
          ok: false,
          status_code: 0,
          records: [],
          raw: null,
          url: urlPath,
          error: "JQL is required for search/jql",
        };
      }
      const maxResults = Number(params.maxResults ?? queryParams.maxResults ?? 50);
      const body: Record<string, unknown> = {
        jql,
        maxResults: Number.isFinite(maxResults) ? maxResults : 50,
      };
      const fieldsRaw = params.fields ?? queryParams.fields;
      if (fieldsRaw) {
        body.fields = String(fieldsRaw)
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean);
      }
      headers["Content-Type"] = "application/json";
      const resp = await fetch(urlPath, {
        method: "POST",
        headers,
        body: JSON.stringify(body),
        signal: AbortSignal.timeout(30000),
      });
      const text = await resp.text();
      let payload: unknown = text;
      try {
        payload = JSON.parse(text);
      } catch {
        /* leave as text */
      }
      if (!resp.ok) {
        return {
          ok: false,
          status_code: resp.status,
          records: [],
          raw: payload,
          url: resp.url,
          error: `HTTP ${resp.status}`,
        };
      }
      const records = normalizeRecords(payload, obj.response_path);
      return {
        ok: true,
        status_code: resp.status,
        records,
        raw: payload,
        url: resp.url,
      };
    }

    const qs = new URLSearchParams();
    for (const [k, v] of Object.entries(queryParams)) {
      if (v) qs.set(k, v);
    }
    const url = qs.toString() ? `${urlPath}?${qs}` : urlPath;
    const resp = await fetch(url, {
      method: "GET",
      headers,
      signal: AbortSignal.timeout(30000),
    });
    const text = await resp.text();
    let payload: unknown = text;
    try {
      payload = JSON.parse(text);
    } catch {
      /* leave as text */
    }
    if (!resp.ok) {
      return {
        ok: false,
        status_code: resp.status,
        records: [],
        raw: payload,
        url: resp.url,
        error: `HTTP ${resp.status}`,
      };
    }
    let records = normalizeRecords(payload, obj.response_path);
    if (obj.name === "IssueCustomFields" && Array.isArray(records)) {
      records = records.filter(
        (r) => typeof r === "object" && r && (r as { custom?: boolean }).custom === true
      );
    }
    return {
      ok: true,
      status_code: resp.status,
      records,
      raw: payload,
      url: resp.url,
    };
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    return {
      ok: false,
      status_code: 0,
      records: [],
      raw: null,
      url: urlPath,
      error: `Network error: ${msg}`,
    };
  }
}

export function previewUrl(obj: CatalogObject, params: Record<string, string>): string {
  const base = "<your-site>";
  const pathParams: Record<string, string> = {};
  for (const p of obj.params) {
    if (p.placement === "path") {
      pathParams[p.name] = params[p.name] || `<${p.name}>`;
    }
  }
  const resolvedPath = resolveEndpoint(obj.endpoint, pathParams);
  const apiBase = obj.api === "agile" ? AGILE : PLATFORM;
  let url = `${base}${apiBase}${resolvedPath}`;
  const qp: string[] = [];
  for (const p of obj.params) {
    if (p.placement !== "query") continue;
    const v = params[p.name] || p.default;
    if (v) qp.push(`${p.name}=${encodeURIComponent(v)}`);
  }
  if (isSearchJql(obj.endpoint)) {
    return `${base}${apiBase}/search/jql (POST with JQL body)`;
  }
  if (qp.length) url += `?${qp.join("&")}`;
  return url;
}

export type AssertionResult = { name: string; passed: boolean; detail: string };

export function evaluateAssertions(
  response: JiraFetchResult,
  assertions: {
    min_records?: number;
    max_records?: number | null;
    required_fields?: string[];
  }
): AssertionResult[] {
  const results: AssertionResult[] = [];
  if (!response.ok) {
    results.push({
      name: "response_ok",
      passed: false,
      detail: response.error || `HTTP ${response.status_code}`,
    });
    return results;
  }
  results.push({
    name: "response_ok",
    passed: true,
    detail: `HTTP ${response.status_code}`,
  });
  const count = response.records.length;

  const min = assertions.min_records;
  if (min !== undefined && min !== null) {
    const ok = count >= Number(min);
    results.push({
      name: `min_records >= ${min}`,
      passed: ok,
      detail: `got ${count}`,
    });
  }

  const max = assertions.max_records;
  if (max !== undefined && max !== null) {
    const ok = count <= Number(max);
    results.push({
      name: `max_records <= ${max}`,
      passed: ok,
      detail: `got ${count}`,
    });
  }

  const reqFields = assertions.required_fields || [];
  for (const path of reqFields) {
    if (!path.trim()) continue;
    if (!response.records.length) {
      results.push({
        name: `required_field present: ${path}`,
        passed: false,
        detail: "no records returned",
      });
      continue;
    }
    let missing = 0;
    for (const r of response.records) {
      const v = resolvePath(r, path);
      if (v === undefined || v === null) missing++;
    }
    const ok = missing === 0;
    results.push({
      name: `required_field present: ${path}`,
      passed: ok,
      detail: ok ? "present on all records" : `missing on ${missing} records`,
    });
  }

  return results;
}
