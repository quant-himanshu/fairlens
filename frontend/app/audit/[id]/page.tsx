"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import type { AuditResult, ExplainResponse, MitigationResult } from "@/lib/types";
import { VERDICT_CONFIG } from "@/lib/types";
import { MetricCard } from "@/components/MetricCard";
import { BiasRadar } from "@/components/BiasRadar";

export default function AuditPage() {
  const { id } = useParams<{ id: string }>();
  const [audit, setAudit] = useState<AuditResult | null>(null);
  const [explanation, setExplanation] = useState<ExplainResponse | null>(null);
  const [mitigation, setMitigation] = useState<MitigationResult | null>(null);
  const [loadingExplain, setLoadingExplain] = useState(false);
  const [loadingMitigate, setLoadingMitigate] = useState(false);
  const [selectedAttr, setSelectedAttr] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getAudit(id)
      .then((a) => {
        setAudit(a);
        setSelectedAttr(a.sensitive_attributes[0] ?? "");
      })
      .catch((e) => setError(e.message));
  }, [id]);

  const handleExplain = async () => {
    if (!audit) return;
    setLoadingExplain(true);
    try {
      const exp = await api.explain(audit.audit_id);
      setExplanation(exp);
    } catch (e: unknown) {
      setError((e as Error).message);
    } finally {
      setLoadingExplain(false);
    }
  };

  const handleMitigate = async () => {
    if (!audit || !selectedAttr) return;
    setLoadingMitigate(true);
    try {
      const result = await api.mitigate(audit.audit_id, "reweighing", selectedAttr);
      setMitigation(result);
    } catch (e: unknown) {
      setError((e as Error).message);
    } finally {
      setLoadingMitigate(false);
    }
  };

  if (error) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="rounded-xl border border-red-200 bg-red-50 p-6 max-w-md text-center">
        <p className="text-red-800 font-medium">Error</p>
        <p className="text-red-600 text-sm mt-1">{error}</p>
      </div>
    </div>
  );

  if (!audit) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <p className="text-sm text-gray-500">Loading audit...</p>
      </div>
    </div>
  );

  const cfg = VERDICT_CONFIG[audit.overall_verdict];

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 py-8">

        {/* Header */}
        <div className="flex items-start justify-between mb-8">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">
              FairLens Audit Report
            </h1>
            <p className="text-gray-500 text-sm mt-1">
              {audit.dataset_name} · {audit.row_count.toLocaleString()} rows · {audit.sensitive_attributes.join(", ")}
            </p>
          </div>
          <span
            className="rounded-full px-4 py-1.5 text-sm font-medium border"
            style={{ backgroundColor: cfg.bg, color: cfg.color, borderColor: cfg.border }}
          >
            {cfg.label}
          </span>
        </div>

        {/* Summary stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[
            { label: "Total metrics", value: audit.metrics.length },
            { label: "Biased", value: audit.metrics.filter(m => m.verdict === "biased" || m.verdict === "severely_biased").length, warn: true },
            { label: "Marginal", value: audit.metrics.filter(m => m.verdict === "marginal").length },
            { label: "Fair", value: audit.metrics.filter(m => m.verdict === "fair").length, ok: true },
          ].map((s) => (
            <div key={s.label} className="rounded-xl bg-white border border-gray-100 p-4">
              <p className="text-xs text-gray-400 mb-1">{s.label}</p>
              <p className={`text-2xl font-semibold ${s.warn ? "text-red-600" : s.ok ? "text-green-700" : "text-gray-900"}`}>
                {s.value}
              </p>
            </div>
          ))}
        </div>

        {/* Main grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">

          {/* Metrics */}
          <div className="lg:col-span-2 flex flex-col gap-4">
            <h2 className="text-base font-medium text-gray-700">Fairness metrics</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {audit.metrics.map((m, i) => (
                <MetricCard key={i} metric={m} />
              ))}
            </div>
          </div>

          {/* Radar */}
          <div className="flex flex-col gap-4">
            <h2 className="text-base font-medium text-gray-700">Fairness profile</h2>
            <div className="rounded-xl bg-white border border-gray-100 p-4">
              <BiasRadar
                metrics={audit.metrics}
                mitigatedMetrics={mitigation?.after_metrics}
              />
            </div>

            {/* Explain button */}
            <button
              onClick={handleExplain}
              disabled={loadingExplain}
              className="w-full rounded-xl py-2.5 text-sm font-medium border border-purple-200 bg-purple-50 text-purple-800 hover:bg-purple-100 disabled:opacity-50 transition-colors"
            >
              {loadingExplain ? "Analysing with Claude..." : "Explain with Claude AI"}
            </button>

            {/* Mitigate panel */}
            <div className="rounded-xl bg-white border border-gray-100 p-4 flex flex-col gap-3">
              <p className="text-sm font-medium text-gray-700">Apply mitigation</p>
              <select
                value={selectedAttr}
                onChange={(e) => setSelectedAttr(e.target.value)}
                className="text-sm border border-gray-200 rounded-lg px-3 py-2 bg-white text-gray-700"
              >
                {audit.sensitive_attributes.map((a) => (
                  <option key={a} value={a}>{a}</option>
                ))}
              </select>
              <button
                onClick={handleMitigate}
                disabled={loadingMitigate}
                className="w-full rounded-xl py-2.5 text-sm font-medium border border-teal-200 bg-teal-50 text-teal-800 hover:bg-teal-100 disabled:opacity-50 transition-colors"
              >
                {loadingMitigate ? "Mitigating..." : "Apply reweighing"}
              </button>
              {mitigation && (
                <div className="text-xs text-gray-500 space-y-1">
                  <p>Fairness improved: <span className="text-green-700 font-medium">{(mitigation.fairness_improvement * 100).toFixed(0)}%</span></p>
                  <p>Accuracy delta: <span className={mitigation.accuracy_delta >= 0 ? "text-green-700" : "text-red-600"} style={{fontWeight:500}}>{mitigation.accuracy_delta >= 0 ? "+" : ""}{(mitigation.accuracy_delta * 100).toFixed(1)}%</span></p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Claude explanation */}
        {explanation && (
          <div className="rounded-xl border border-purple-200 bg-purple-50 p-6 mb-8">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-6 h-6 rounded-full bg-purple-600 flex items-center justify-center">
                <span className="text-white text-xs font-bold">C</span>
              </div>
              <p className="text-sm font-medium text-purple-800">Claude AI Analysis · {explanation.severity_label}</p>
            </div>
            <div className="space-y-4 text-sm text-purple-900">
              <div>
                <p className="font-medium mb-1">Summary</p>
                <p className="leading-relaxed">{explanation.summary}</p>
              </div>
              <div>
                <p className="font-medium mb-1">Root cause</p>
                <p className="leading-relaxed">{explanation.root_cause}</p>
              </div>
              <div>
                <p className="font-medium mb-1">Business impact</p>
                <p className="leading-relaxed">{explanation.business_impact}</p>
              </div>
              <div>
                <p className="font-medium mb-2">Recommended actions</p>
                <ul className="space-y-1">
                  {explanation.recommended_actions.map((a, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="shrink-0 w-5 h-5 rounded-full bg-purple-200 text-purple-800 flex items-center justify-center text-xs font-medium mt-0.5">{i + 1}</span>
                      <span className="leading-relaxed">{a}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Group stats table */}
        <div className="rounded-xl bg-white border border-gray-100 p-6">
          <h2 className="text-base font-medium text-gray-700 mb-4">Group statistics</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-xs text-gray-400 border-b border-gray-100">
                  <th className="text-left pb-2 font-medium">Attribute</th>
                  <th className="text-left pb-2 font-medium">Group</th>
                  <th className="text-right pb-2 font-medium">Count</th>
                  <th className="text-right pb-2 font-medium">Positive rate</th>
                  <th className="text-right pb-2 font-medium">TPR</th>
                  <th className="text-right pb-2 font-medium">FPR</th>
                </tr>
              </thead>
              <tbody>
                {audit.group_stats.map((g, i) => (
                  <tr key={i} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="py-2 text-gray-500">{g.attribute}</td>
                    <td className="py-2 font-medium text-gray-800">{g.group_name}</td>
                    <td className="py-2 text-right text-gray-600">{g.count.toLocaleString()}</td>
                    <td className="py-2 text-right text-gray-600">{(g.positive_rate * 100).toFixed(1)}%</td>
                    <td className="py-2 text-right text-gray-600">{g.true_positive_rate != null ? `${(g.true_positive_rate * 100).toFixed(1)}%` : "—"}</td>
                    <td className="py-2 text-right text-gray-600">{g.false_positive_rate != null ? `${(g.false_positive_rate * 100).toFixed(1)}%` : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
