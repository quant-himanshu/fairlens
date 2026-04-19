"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

const DEMO_DATASETS = [
  { name: "india-loan", label: "🇮🇳 India Loan Applications", description: "Real patterns from RBI 2023 — gender & location bias in Indian credit", attrs: "gender,location_type,income_tier", label_col: "approved", truth_col: "financially_eligible", score_col: "", isIndia: true },
  { name: "hiring", label: "Hiring bias", description: "Gender & age discrimination in resume screening", attrs: "gender,age_group", label_col: "hired", truth_col: "qualified", score_col: "hire_score" },
  { name: "lending", label: "Lending bias", description: "Racial & zip code discrimination in loan approvals", attrs: "race,zip_income_level", label_col: "approved", truth_col: "creditworthy", score_col: "credit_score_normalized" },
  { name: "healthcare", label: "Healthcare bias", description: "Age & insurance bias in treatment recommendations", attrs: "age_group,insurance_type", label_col: "treatment_recommended", truth_col: "treatment_needed", score_col: "" },
];

export default function HomePage() {
  const router = useRouter();
  const fileRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [labelCol, setLabelCol] = useState("");
  const [truthCol, setTruthCol] = useState("");
  const [sensitiveAttrs, setSensitiveAttrs] = useState("");
  const [scoreCol, setScoreCol] = useState("");
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const runAudit = async (f: File, lc: string, tc: string, attrs: string, sc?: string) => {
    setLoading("Running fairness audit...");
    setError(null);
    try {
      const result = await api.uploadAndAudit(f, lc, tc, attrs.split(",").map(s => s.trim()), sc || undefined);
      router.push(`/audit/${result.audit_id}`);
    } catch (e: unknown) {
      setError((e as Error).message);
      setLoading(null);
    }
  };

  const handleSubmit = () => {
    if (!file || !labelCol || !truthCol || !sensitiveAttrs) {
      setError("Please fill in all required fields.");
      return;
    }
    runAudit(file, labelCol, truthCol, sensitiveAttrs, scoreCol);
  };

  const handleDemo = async (demo: typeof DEMO_DATASETS[0]) => {
    setLoading(`Loading ${demo.label} demo...`);
    setError(null);
    try {
      const res = await fetch(api.demoCsvUrl(demo.name));
      const blob = await res.blob();
      const f = new File([blob], `${demo.name}_biased.csv`, { type: "text/csv" });
      await runAudit(f, demo.label_col, demo.truth_col, demo.attrs, demo.score_col || undefined);
    } catch (e: unknown) {
      setError((e as Error).message);
      setLoading(null);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-16">

        {/* Hero */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 rounded-full bg-purple-100 px-4 py-1.5 text-sm text-purple-700 font-medium mb-6">
            Google Solution Challenge 2026
          </div>
          <h1 className="text-4xl font-semibold text-gray-900 mb-4 tracking-tight">
            FairLens
          </h1>
          <p className="text-xl text-gray-500 max-w-lg mx-auto leading-relaxed">
            Detect, explain, and fix bias in AI decision systems — before they harm real people.
          </p>
        </div>

        {/* Pipeline Auditor CTA */}
        <div
          onClick={() => router.push("/pipeline")}
          className="mb-8 rounded-2xl border border-indigo-900 bg-indigo-950/40 p-5 cursor-pointer hover:border-indigo-700 transition-all group"
        >
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-bold text-indigo-400 uppercase tracking-wider">Layer 3 · Exclusive</span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-900 text-indigo-300 border border-indigo-800">NEW</span>
              </div>
              <p className="text-sm font-semibold text-white">AI Pipeline Bias Auditor</p>
              <p className="text-xs text-gray-400 mt-0.5">Audit multi-stage AI decision pipelines — not just datasets</p>
            </div>
            <span className="text-indigo-400 text-lg group-hover:translate-x-1 transition-transform">→</span>
          </div>
        </div>

        {/* Demo datasets */}
        <div className="mb-10">
          <h2 className="text-sm font-medium text-gray-500 mb-3 uppercase tracking-wide">
            Try a demo dataset
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {DEMO_DATASETS.map((demo) => (
              <button
                key={demo.name}
                onClick={() => handleDemo(demo)}
                disabled={!!loading}
                className="rounded-xl border border-gray-200 bg-white p-4 text-left hover:border-purple-300 hover:bg-purple-50 transition-all disabled:opacity-50"
              >
                <p className="text-sm font-medium text-gray-800 mb-1">{demo.label}</p>
                <p className="text-xs text-gray-400 leading-relaxed">{demo.description}</p>
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-3 mb-8">
          <div className="flex-1 h-px bg-gray-200" />
          <span className="text-xs text-gray-400">or upload your own CSV</span>
          <div className="flex-1 h-px bg-gray-200" />
        </div>

        {/* Upload form */}
        <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
          {/* Drop zone */}
          <div
            onClick={() => fileRef.current?.click()}
            className="rounded-xl border-2 border-dashed border-gray-200 p-8 text-center cursor-pointer hover:border-purple-300 hover:bg-purple-50/30 transition-all mb-6"
          >
            <input
              ref={fileRef}
              type="file"
              accept=".csv"
              className="hidden"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
            {file ? (
              <p className="text-sm font-medium text-gray-700">{file.name}</p>
            ) : (
              <>
                <p className="text-sm font-medium text-gray-600">Drop a CSV file here</p>
                <p className="text-xs text-gray-400 mt-1">Must contain binary outcome column (0/1)</p>
              </>
            )}
          </div>

          {/* Column config */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {[
              { label: "Prediction column *", value: labelCol, set: setLabelCol, placeholder: "e.g. hired" },
              { label: "Ground truth column *", value: truthCol, set: setTruthCol, placeholder: "e.g. qualified" },
              { label: "Sensitive attributes *", value: sensitiveAttrs, set: setSensitiveAttrs, placeholder: "e.g. gender,race" },
              { label: "Score column", value: scoreCol, set: setScoreCol, placeholder: "e.g. probability (optional)" },
            ].map((f) => (
              <div key={f.label}>
                <label className="block text-xs font-medium text-gray-500 mb-1.5">{f.label}</label>
                <input
                  type="text"
                  value={f.value}
                  onChange={(e) => f.set(e.target.value)}
                  placeholder={f.placeholder}
                  className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-800 placeholder:text-gray-300 focus:border-purple-400 focus:outline-none"
                />
              </div>
            ))}
          </div>

          {error && (
            <p className="mt-4 text-sm text-red-600 rounded-lg bg-red-50 border border-red-100 px-3 py-2">{error}</p>
          )}

          <button
            onClick={handleSubmit}
            disabled={!!loading}
            className="mt-6 w-full rounded-xl bg-purple-600 text-white py-3 text-sm font-medium hover:bg-purple-700 disabled:opacity-50 transition-colors"
          >
            {loading ?? "Run Fairness Audit"}
          </button>
        </div>

        {/* How it works */}
        <div className="mt-12 grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
          {[
            { step: "01", text: "Upload CSV" },
            { step: "02", text: "6 fairness metrics computed" },
            { step: "03", text: "Claude explains the bias" },
            { step: "04", text: "Apply one-click fix" },
          ].map((s) => (
            <div key={s.step} className="flex flex-col items-center gap-2">
              <span className="w-8 h-8 rounded-full bg-purple-100 text-purple-700 text-xs font-semibold flex items-center justify-center">{s.step}</span>
              <p className="text-xs text-gray-500 leading-tight">{s.text}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
