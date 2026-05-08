/** Flatten JIRA-style records (e.g. issues with nested `fields`) for a simple data table. */

function cellString(v: unknown): string {
  if (v === null || v === undefined) return "";
  if (typeof v === "object") return JSON.stringify(v);
  return String(v);
}

export function flattenRecord(rec: unknown): Record<string, string> {
  const out: Record<string, string> = {};
  if (!rec || typeof rec !== "object" || Array.isArray(rec)) {
    return { value: cellString(rec) };
  }
  const o = rec as Record<string, unknown>;
  for (const [k, v] of Object.entries(o)) {
    if (k === "fields" && v && typeof v === "object" && !Array.isArray(v)) {
      for (const [fk, fv] of Object.entries(v as Record<string, unknown>)) {
        out[`fields.${fk}`] = cellString(fv);
      }
    } else {
      out[k] = cellString(v);
    }
  }
  return out;
}

export function buildTableModel(
  records: unknown[],
  maxRows: number
): { columns: string[]; rows: Record<string, string>[] } {
  const rows = records.slice(0, maxRows).map(flattenRecord);
  const colSet = new Set<string>();
  for (const r of rows) {
    for (const k of Object.keys(r)) colSet.add(k);
  }
  const columns = Array.from(colSet).sort((a, b) => {
    if (a === "key") return -1;
    if (b === "key") return 1;
    if (a === "id") return -1;
    if (b === "id") return 1;
    return a.localeCompare(b);
  });
  return { columns, rows };
}
