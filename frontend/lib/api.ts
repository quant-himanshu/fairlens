import type { AuditResult, ExplainResponse, MitigationResult, MitigationStrategy } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Request failed");
  }
  return res.json() as Promise<T>;
}

export const api = {
  async uploadAndAudit(
    file: File,
    labelColumn: string,
    groundTruthColumn: string,
    sensitiveAttributes: string[],
    scoreColumn?: string,
  ): Promise<AuditResult> {
    const form = new FormData();
    form.append("file", file);
    form.append("label_column", labelColumn);
    form.append("ground_truth_column", groundTruthColumn);
    form.append("sensitive_attributes", sensitiveAttributes.join(","));
    if (scoreColumn) form.append("score_column", scoreColumn);

    const res = await fetch(`${BASE}/api/audit/upload`, { method: "POST", body: form });
    return handleResponse<AuditResult>(res);
  },

  async getAudit(auditId: string): Promise<AuditResult> {
    const res = await fetch(`${BASE}/api/audit/${auditId}`);
    return handleResponse<AuditResult>(res);
  },

  async explain(auditId: string): Promise<ExplainResponse> {
    const res = await fetch(`${BASE}/api/explain/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ audit_id: auditId }),
    });
    return handleResponse<ExplainResponse>(res);
  },

  async mitigate(
    auditId: string,
    strategy: MitigationStrategy,
    sensitiveAttribute: string,
  ): Promise<MitigationResult> {
    const res = await fetch(`${BASE}/api/audit/mitigate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        audit_id: auditId,
        strategy,
        sensitive_attribute: sensitiveAttribute,
      }),
    });
    return handleResponse<MitigationResult>(res);
  },

  async listDemoDatasets() {
    const res = await fetch(`${BASE}/api/datasets/`);
    return handleResponse<Array<{ name: string; description: string; rows: number }>>(res);
  },

  async getDemoConfig(name: string) {
    const res = await fetch(`${BASE}/api/datasets/${name}/config`);
    return handleResponse<Record<string, unknown>>(res);
  },

  demoCsvUrl(name: string): string {
    return `${BASE}/api/datasets/${name}/download`;
  },
};
