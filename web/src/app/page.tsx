"use client";

import { CATALOG, type CatalogObject } from "@/lib/catalog";
import { buildTableModel } from "@/lib/flattenRecords";
import Image from "next/image";
import { useEffect, useMemo, useState } from "react";

type RunResponse = {
  passed: boolean;
  record_count: number;
  assertions: { name: string; passed: boolean; detail: string }[];
  response: {
    ok: boolean;
    status_code: number;
    url: string;
    error: string | null;
    records: unknown[];
    raw: unknown;
  };
  duration_ms: number;
  case_name: string;
};

function defaultParams(obj: CatalogObject): Record<string, string> {
  const o: Record<string, string> = {};
  for (const p of obj.params) {
    if (p.default != null && p.default !== "") o[p.name] = String(p.default);
    else o[p.name] = "";
  }
  return o;
}

export default function Page() {
  const [baseUrl, setBaseUrl] = useState("");
  const [email, setEmail] = useState("");
  const [apiToken, setApiToken] = useState("");
  const [testOk, setTestOk] = useState<string | null>(null);

  const defaultObj =
    CATALOG.find((o) => o.name === "Issues")?.name ?? CATALOG[0]?.name ?? "";
  const [objectName, setObjectName] = useState(defaultObj);
  const selected = useMemo(
    () => CATALOG.find((o) => o.name === objectName) ?? CATALOG[0],
    [objectName]
  );

  const [params, setParams] = useState<Record<string, string>>(() =>
    defaultObj ? defaultParams(CATALOG.find((o) => o.name === defaultObj)!) : {}
  );

  useEffect(() => {
    if (selected) setParams(defaultParams(selected));
  }, [objectName, selected]);

  const [caseName, setCaseName] = useState("Pull Issues");
  useEffect(() => {
    setCaseName(`Pull ${objectName}`);
  }, [objectName]);

  const [minRecords, setMinRecords] = useState(1);
  const [capMax, setCapMax] = useState(false);
  const [maxRecords, setMaxRecords] = useState(1000);
  const [requiredFieldsRaw, setRequiredFieldsRaw] = useState("");

  const [loading, setLoading] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [lastRun, setLastRun] = useState<RunResponse | null>(null);
  const [recordsView, setRecordsView] = useState<"table" | "json">("table");

  const recordsTable = useMemo(() => {
    if (!lastRun?.response.records?.length) return null;
    return buildTableModel(lastRun.response.records, 100);
  }, [lastRun]);

  useEffect(() => {
    if (lastRun) setRecordsView("table");
  }, [lastRun]);

  const creds = { baseUrl: baseUrl.trim(), email: email.trim(), apiToken };

  async function connectJira() {
    setConnecting(true);
    setTestOk(null);
    try {
      const r = await fetch("/api/jira/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(creds),
      });
      const data = await r.json();
      if (data.ok && data.displayName) {
        setTestOk(`${data.displayName}${data.emailAddress ? ` · ${data.emailAddress}` : ""}`);
      } else {
        setTestOk(`Failed: ${data.error || data.raw || r.status}`);
      }
    } catch (e) {
      setTestOk(`Error: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setConnecting(false);
    }
  }

  async function runCase() {
    setLoading(true);
    setLastRun(null);
    const required_fields = requiredFieldsRaw
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    const assertions: Record<string, unknown> = {
      min_records: minRecords,
      required_fields,
    };
    if (capMax) assertions.max_records = maxRecords;

    const body = {
      credentials: creds,
      case: {
        name: caseName,
        object: objectName,
        params,
        assertions,
      },
    };

    try {
      const r = await fetch("/api/jira/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await r.json();
      if (!r.ok) {
        setLastRun({
          passed: false,
          record_count: 0,
          assertions: [{ name: "request", passed: false, detail: data.error || r.statusText }],
          response: {
            ok: false,
            status_code: r.status,
            url: "",
            error: data.error || null,
            records: [],
            raw: data,
          },
          duration_ms: 0,
          case_name: caseName,
        });
        return;
      }
      setLastRun(data as RunResponse);
    } catch (e) {
      setLastRun({
        passed: false,
        record_count: 0,
        assertions: [{ name: "request", passed: false, detail: String(e) }],
        response: {
          ok: false,
          status_code: 0,
          url: "",
          error: String(e),
          records: [],
          raw: null,
        },
        duration_ms: 0,
        case_name: caseName,
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="wrap">
      <div className="mast-bar" aria-hidden />
      <header className="site-header">
        <div className="brand-row">
          <Image
            src="/logo-resize.png"
            alt="SimpleTest"
            width={36}
            height={36}
            className="brand-logo"
            priority
          />
          <div>
            <div className="brand-title">JIRA lab</div>
            <p className="muted" style={{ marginTop: 6, marginBottom: 0 }}>
              Build &amp; run a live pull against JIRA Cloud — aligned with the Salesforce Data Cloud JIRA
              connector catalog.
            </p>
          </div>
        </div>
      </header>

      <section className="card">
        <h2>JIRA connection</h2>
        <p className="muted">Credentials are sent only to this app&apos;s API over HTTPS (not stored on our servers).</p>
        <div className="field" style={{ marginBottom: 14 }}>
          <label>Site URL</label>
          <input
            type="url"
            placeholder="https://your-site.atlassian.net"
            value={baseUrl}
            onChange={(e) => setBaseUrl(e.target.value)}
            autoComplete="off"
          />
        </div>
        <div className="row">
          <div className="field">
            <label>Atlassian email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="off"
            />
          </div>
          <div className="field">
            <label>API token</label>
            <input
              type="password"
              value={apiToken}
              onChange={(e) => setApiToken(e.target.value)}
              autoComplete="off"
            />
          </div>
        </div>
        <div style={{ marginTop: 14 }}>
          <button type="button" className="btn btn-primary" onClick={connectJira} disabled={connecting}>
            {connecting ? "Connecting…" : "Connect"}
          </button>
          <p className="muted" style={{ marginTop: 10, marginBottom: 0, fontSize: "0.82rem" }}>
            Verifies your site and token with JIRA (<code>GET /rest/api/3/myself</code>), then you can run pulls below.
          </p>
          {testOk && (
            <p className="muted" style={{ marginTop: 10, marginBottom: 0 }}>
              {testOk.startsWith("Failed") || testOk.startsWith("Error") ? (
                <span style={{ color: "var(--fail)" }}>{testOk}</span>
              ) : (
                <span style={{ color: "var(--success)" }}>Connected as {testOk}</span>
              )}
            </p>
          )}
        </div>
      </section>

      <section className="card">
        <h2>Build &amp; run</h2>
        <p className="muted">{selected?.description}</p>
        {selected?.notes ? (
          <p className="muted" style={{ fontSize: "0.85rem" }}>
            {selected.notes}
          </p>
        ) : null}

        <div className="field" style={{ marginTop: 16 }}>
          <label>JIRA object</label>
          <select value={objectName} onChange={(e) => setObjectName(e.target.value)}>
            {CATALOG.map((o) => (
              <option key={o.name} value={o.name}>
                {o.name}
              </option>
            ))}
          </select>
        </div>

        <div className="field" style={{ marginTop: 14 }}>
          <label>Test case name</label>
          <input value={caseName} onChange={(e) => setCaseName(e.target.value)} />
        </div>

        <h3 style={{ fontSize: "1rem", margin: "20px 0 10px" }}>Parameters</h3>
        {selected?.params?.length ? (
          selected.params.map((p) => (
            <div className="field" key={p.name} style={{ marginBottom: 12 }}>
              <label>
                {p.name} ({p.required ? "required" : "optional"}) — {p.description}
              </label>
              <input
                value={params[p.name] ?? ""}
                onChange={(e) => setParams((prev) => ({ ...prev, [p.name]: e.target.value }))}
              />
            </div>
          ))
        ) : (
          <p className="muted">No parameters for this object.</p>
        )}

        <h3 style={{ fontSize: "1rem", margin: "20px 0 10px" }}>Assertions</h3>
        <div className="row">
          <div className="field" style={{ maxWidth: 160 }}>
            <label>min_records</label>
            <input
              type="number"
              min={0}
              value={minRecords}
              onChange={(e) => setMinRecords(Number(e.target.value))}
            />
          </div>
          <div className="field" style={{ maxWidth: 200 }}>
            <label>
              <input
                type="checkbox"
                checked={capMax}
                onChange={(e) => setCapMax(e.target.checked)}
                style={{ width: "auto", marginRight: 8 }}
              />
              Cap max_records
            </label>
            <input
              type="number"
              min={0}
              value={maxRecords}
              disabled={!capMax}
              onChange={(e) => setMaxRecords(Number(e.target.value))}
            />
          </div>
        </div>
        <div className="field" style={{ marginTop: 12 }}>
          <label>required_fields (comma-separated paths, e.g. key, fields.summary)</label>
          <input value={requiredFieldsRaw} onChange={(e) => setRequiredFieldsRaw(e.target.value)} />
        </div>

        <p className="muted" style={{ marginTop: 14, fontSize: "0.8rem" }}>
          Uses your site&apos;s JIRA Cloud REST API.
        </p>

        <div style={{ marginTop: 18 }}>
          <button type="button" className="btn btn-primary" onClick={runCase} disabled={loading}>
            {loading ? "Running…" : "Run test case"}
          </button>
        </div>
      </section>

      {lastRun && (
        <section className="card">
          <h2>Last run — {lastRun.case_name}</h2>
          <p>
            Result:{" "}
            <span className={lastRun.passed ? "badge-pass" : "badge-fail"}>
              {lastRun.passed ? "PASS" : "FAIL"}
            </span>
            <span className="muted" style={{ marginLeft: 12 }}>
              {lastRun.record_count} records · HTTP {lastRun.response.status_code} · {lastRun.duration_ms} ms
            </span>
          </p>
          {lastRun.response.error && (
            <p style={{ color: "var(--fail)" }}>{lastRun.response.error}</p>
          )}
          <p style={{ fontWeight: 600, marginTop: 16 }}>Assertions</p>
          <ul style={{ margin: "8px 0", paddingLeft: 20 }}>
            {lastRun.assertions.map((a) => (
              <li key={a.name} style={{ color: a.passed ? "var(--success)" : "var(--fail)" }}>
                {a.passed ? "✓" : "✗"} {a.name} — {a.detail}
              </li>
            ))}
          </ul>
          {lastRun.response.url ? (
            <p className="muted" style={{ fontSize: "0.85rem", wordBreak: "break-all" }}>
              <code>{lastRun.response.url}</code>
            </p>
          ) : null}
          {lastRun.response.records?.length > 0 && recordsTable ? (
            <div style={{ marginTop: 16 }}>
              <p style={{ fontWeight: 600, marginBottom: 8 }}>Records</p>
              <div className="view-toggle" role="tablist" aria-label="Record view">
                <button
                  type="button"
                  className={recordsView === "table" ? "active" : ""}
                  onClick={() => setRecordsView("table")}
                >
                  Table
                </button>
                <button
                  type="button"
                  className={recordsView === "json" ? "active" : ""}
                  onClick={() => setRecordsView("json")}
                >
                  JSON
                </button>
              </div>
              {recordsView === "table" ? (
                <>
                  {lastRun.record_count > 100 ? (
                    <p className="muted" style={{ fontSize: "0.8rem", marginBottom: 8 }}>
                      Showing the first 100 of {lastRun.record_count} records.
                    </p>
                  ) : null}
                  <div className="data-table-wrap">
                  <table className="data-table">
                    <thead>
                      <tr>
                        {recordsTable.columns.map((col) => (
                          <th key={col}>{col}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {recordsTable.rows.map((row, ri) => (
                        <tr key={ri}>
                          {recordsTable.columns.map((col) => (
                            <td key={col} title={row[col] ?? ""}>
                              {row[col] ?? ""}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                </>
              ) : (
                <pre
                  style={{
                    marginTop: 8,
                    padding: 14,
                    background: "var(--surface-alt)",
                    border: "1px solid var(--border)",
                    borderRadius: "var(--rs)",
                    overflow: "auto",
                    fontSize: 12,
                    maxHeight: 420,
                  }}
                >
                  {JSON.stringify(lastRun.response.records.slice(0, 100), null, 2)}
                </pre>
              )}
            </div>
          ) : null}
          <details style={{ marginTop: 12 }}>
            <summary style={{ cursor: "pointer", fontWeight: 600 }}>Raw response</summary>
            <pre
              style={{
                marginTop: 12,
                padding: 14,
                background: "var(--surface-alt)",
                border: "1px solid var(--border)",
                borderRadius: "var(--rs)",
                overflow: "auto",
                fontSize: 12,
                maxHeight: 320,
              }}
            >
              {JSON.stringify(lastRun.response.raw, null, 2)}
            </pre>
          </details>
        </section>
      )}
    </div>
  );
}
