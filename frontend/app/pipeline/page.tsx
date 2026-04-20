"use client";

import { useState, useEffect, useRef } from "react";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface CounterfactualExample {
  attribute_changed: string;
  person_a: Record<string, unknown>;
  person_b: Record<string, unknown>;
  finding: string;
}

interface PipelineResult {
  audit_id: string;
  pipeline_name: string;
  total_decisions: number;
  overall_verdict: string;
  disparate_impact: number;
  counterfactual_flip_rate: number;
  group_allow_rates: Record<string, number>;
  group_deny_rates: Record<string, number>;
  counterfactual_examples: CounterfactualExample[];
  stage_bias: Record<string, { avg_bias_delta: number; interpretation: string }>;
  architecture_note?: string;
}

const VERDICT_COLOR: Record<string, string> = {
  fair: "#22c55e",
  marginal: "#f59e0b",
  biased: "#ef4444",
  severely_biased: "#dc2626",
};

const STAGES = [
  { id: "input",      label: "Input",       sub: "Validation" },
  { id: "context",    label: "Context",     sub: "Check" },
  { id: "permission", label: "Permission",  sub: "Gate ⚠" },
  { id: "classifier", label: "Classifier",  sub: "ML Score" },
  { id: "decision",   label: "Decision",    sub: "Final" },
];

function PipelineFlow({ activeStage }: { activeStage: number }) {
  return (
    <div className="flex items-center gap-0 w-full overflow-x-auto pb-2">
      {STAGES.map((s, i) => (
        <div key={s.id} className="flex items-center flex-1 min-w-0">
          <div
            className="flex flex-col items-center flex-1 transition-all duration-500"
            style={{ opacity: activeStage >= i ? 1 : 0.3 }}
          >
            <div
              className="w-10 h-10 rounded-full flex items-center justify-center text-xs font-bold border-2 transition-all duration-500"
              style={{
                borderColor: activeStage >= i ? (s.id === "permission" ? "#ef4444" : "#6366f1") : "#374151",
                background: activeStage >= i ? (s.id === "permission" ? "#fee2e2" : "#eef2ff") : "#1f2937",
                color: activeStage >= i ? (s.id === "permission" ? "#dc2626" : "#4f46e5") : "#6b7280",
                transform: activeStage === i ? "scale(1.2)" : "scale(1)",
              }}
            >
              {i + 1}
            </div>
            <p className="text-xs font-semibold mt-1 text-center" style={{ color: activeStage >= i ? "#f9fafb" : "#4b5563" }}>{s.label}</p>
            <p className="text-xs text-center" style={{ color: activeStage >= i ? "#9ca3af" : "#374151" }}>{s.sub}</p>
          </div>
          {i < STAGES.length - 1 && (
            <div className="h-0.5 w-4 flex-shrink-0 transition-all duration-500" style={{ background: activeStage > i ? "#6366f1" : "#374151" }} />
          )}
        </div>
      ))}
    </div>
  );
}

function CounterfactualCard({ example, revealed }: { example: CounterfactualExample; revealed: boolean }) {
  const a = example.person_a;
  const b = example.person_b;
  const attr = example.attribute_changed;
  const decisionA = String(a.decision ?? "").toUpperCase();
  const decisionB = String(b.decision ?? "").toUpperCase();
  const flipped = decisionA !== decisionB;

  const decisionColor = (d: string) =>
    d === "ALLOW" ? "#22c55e" : d === "DENY" ? "#ef4444" : "#f59e0b";

  return (
    <div
      className="rounded-2xl border overflow-hidden transition-all duration-700"
      style={{
        borderColor: flipped ? "#ef444444" : "#22c55e44",
        background: "#111827",
        opacity: revealed ? 1 : 0,
        transform: revealed ? "translateY(0)" : "translateY(20px)",
      }}
    >
      {/* Header */}
      <div className="px-5 py-3 border-b flex items-center justify-between" style={{ borderColor: "#1f2937" }}>
        <span className="text-xs font-mono text-gray-400">
          Attribute changed: <span className="text-indigo-400 font-bold">{attr}</span>
        </span>
        {flipped && (
          <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-red-900/50 text-red-400 border border-red-800">
            BIAS DETECTED
          </span>
        )}
      </div>

      {/* Two-person comparison */}
      <div className="grid grid-cols-2 divide-x" >
        {[
          { person: a, label: "Person A" },
          { person: b, label: "Person B" },
        ].map(({ person, label }) => {
          const dec = String(person.decision ?? "").toUpperCase();
          return (
            <div key={label} className="p-5">
              <p className="text-xs text-gray-500 mb-3 font-mono">{label}</p>
              <div className="space-y-2 mb-4">
                <div className="flex justify-between text-xs">
                  <span className="text-gray-400">{attr}</span>
                  <span className="font-bold text-white">{String(person[attr])}</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-gray-400">Credit history</span>
                  <span className="text-gray-200">{String(person.credit_history_years)}y</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-gray-400">Income</span>
                  <span className="text-gray-200">{(Number(person.income_normalized) * 100).toFixed(0)}%</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-gray-400">Debt ratio</span>
                  <span className="text-gray-200">{(Number(person.debt_ratio) * 100).toFixed(0)}%</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-gray-400">Merit score</span>
                  <span className="text-gray-200">{(Number(person.merit_score) * 100).toFixed(0)}/100</span>
                </div>
              </div>
              <div
                className="rounded-xl py-3 text-center font-black text-lg tracking-wider"
                style={{ background: decisionColor(dec) + "22", color: decisionColor(dec), border: `1.5px solid ${decisionColor(dec)}44` }}
              >
                {dec}
              </div>
            </div>
          );
        })}
      </div>

      {/* Finding */}
      <div className="px-5 py-3 border-t" style={{ borderColor: "#1f2937", background: "#0f172a" }}>
        <p className="text-xs text-gray-400 leading-relaxed">{example.finding}</p>
      </div>
    </div>
  );
}

export default function PipelinePage() {
  const [result, setResult] = useState<PipelineResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeStage, setActiveStage] = useState(-1);
  const [revealedCards, setRevealedCards] = useState<boolean[]>([]);
  const [showMetrics, setShowMetrics] = useState(false);
  const [demoMode, setDemoMode] = useState(false);
  const stageTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const runDemo = async () => {
    setLoading(true);
    setResult(null);
    setActiveStage(-1);
    setRevealedCards([]);
    setShowMetrics(false);
    setDemoMode(true);

    try {
      const res = await fetch(`${BASE}/api/pipeline/demo`);
      const data: PipelineResult = await res.json();

      // Animate pipeline stages one by one
      for (let i = 0; i <= 4; i++) {
        await new Promise(r => setTimeout(r, 500));
        setActiveStage(i);
      }

      await new Promise(r => setTimeout(r, 400));
      setResult(data);
      setShowMetrics(true);

      // Reveal counterfactual cards one by one
      for (let i = 0; i < (data.counterfactual_examples?.length ?? 0); i++) {
        await new Promise(r => setTimeout(r, 600));
        setRevealedCards(prev => { const next = [...prev]; next[i] = true; return next; });
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const verdictColor = result ? (VERDICT_COLOR[result.overall_verdict] ?? "#ef4444") : "#6366f1";

  return (
    <div className="min-h-screen" style={{ background: "#030712", color: "#f9fafb", fontFamily: "'DM Mono', 'Fira Code', monospace" }}>
      <div className="max-w-5xl mx-auto px-4 py-12">

        {/* Header */}
        <div className="mb-12">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-2 h-8 rounded-full bg-indigo-500" />
            <span className="text-xs tracking-widest text-indigo-400 uppercase font-bold">FairLens · Layer 3</span>
          </div>
          <h1 className="text-4xl font-black text-white mb-3 leading-tight">
            AI Pipeline<br />
            <span style={{ color: verdictColor }}>Bias Auditor</span>
          </h1>
          <p className="text-gray-400 text-sm max-w-lg leading-relaxed">
            Audits multi-stage AI decision pipelines for bias — modelled after real production agent architectures.
            Detects <span className="text-white">where</span> in the pipeline discrimination enters.
          </p>
        </div>

        {/* Architecture diagram */}
        <div className="rounded-2xl border p-6 mb-8" style={{ borderColor: "#1f2937", background: "#0f172a" }}>
          <p className="text-xs text-gray-500 mb-4 uppercase tracking-widest">Production AI Decision Architecture</p>
          <PipelineFlow activeStage={activeStage} />
          {activeStage === 2 && (
            <p className="text-xs text-red-400 mt-3 text-center animate-pulse">
              ⚠ Bias detected at Permission Gate — demographic adjustment applied
            </p>
          )}
        </div>

        {/* Run button */}
        {!result && (
          <div className="text-center mb-12">
            <button
              onClick={runDemo}
              disabled={loading}
              className="px-8 py-4 rounded-2xl font-black text-sm tracking-widest uppercase transition-all duration-200 disabled:opacity-50"
              style={{
                background: loading ? "#1f2937" : "linear-gradient(135deg, #4f46e5, #7c3aed)",
                color: "#fff",
                border: "none",
                boxShadow: loading ? "none" : "0 0 40px #4f46e540",
              }}
            >
              {loading ? "AUDITING PIPELINE..." : "▶  RUN LIVE AUDIT DEMO"}
            </button>
            <p className="text-xs text-gray-600 mt-3">Simulates 600 real AI decisions across demographic groups</p>
          </div>
        )}

        {/* Results */}
        {result && showMetrics && (
          <>
            {/* Key metrics */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
              {[
                { label: "Total Decisions", value: result.total_decisions.toLocaleString(), sub: "simulated" },
                {
                  label: "Disparate Impact",
                  value: result.disparate_impact.toFixed(3),
                  sub: result.disparate_impact < 0.8 ? "⚠ Below legal threshold (0.8)" : "Within range",
                  warn: result.disparate_impact < 0.8,
                },
                {
                  label: "Counterfactual Flip",
                  value: `${(result.counterfactual_flip_rate * 100).toFixed(1)}%`,
                  sub: "decisions change on attr swap",
                  warn: result.counterfactual_flip_rate > 0.15,
                },
                {
                  label: "Verdict",
                  value: result.overall_verdict.replace("_", " ").toUpperCase(),
                  sub: "overall fairness",
                  color: verdictColor,
                },
              ].map((m) => (
                <div key={m.label} className="rounded-2xl p-4" style={{ background: "#0f172a", border: "1px solid #1f2937" }}>
                  <p className="text-xs text-gray-500 mb-1">{m.label}</p>
                  <p className="text-xl font-black" style={{ color: m.color ?? (m.warn ? "#ef4444" : "#f9fafb") }}>
                    {m.value}
                  </p>
                  <p className="text-xs mt-1" style={{ color: m.warn ? "#f87171" : "#4b5563" }}>{m.sub}</p>
                </div>
              ))}
            </div>

            {/* Allow rates by group */}
            <div className="rounded-2xl border p-6 mb-8" style={{ borderColor: "#1f2937", background: "#0f172a" }}>
              <p className="text-xs text-gray-500 uppercase tracking-widest mb-4">Approval Rate by Group</p>
              <div className="space-y-3">
                {Object.entries(result.group_allow_rates)
                  .sort(([, a], [, b]) => b - a)
                  .map(([group, rate]) => (
                    <div key={group}>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-gray-300 font-mono">{group}</span>
                        <span className="font-bold" style={{ color: rate > 0.7 ? "#22c55e" : rate > 0.4 ? "#f59e0b" : "#ef4444" }}>
                          {(rate * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="h-2 rounded-full" style={{ background: "#1f2937" }}>
                        <div
                          className="h-2 rounded-full transition-all duration-1000"
                          style={{
                            width: `${rate * 100}%`,
                            background: rate > 0.7 ? "#22c55e" : rate > 0.4 ? "#f59e0b" : "#ef4444",
                          }}
                        />
                      </div>
                    </div>
                  ))}
              </div>
            </div>

            {/* Stage bias */}
            {Object.keys(result.stage_bias).length > 0 && (
              <div className="rounded-2xl border p-6 mb-8" style={{ borderColor: "#1f2937", background: "#0f172a" }}>
                <p className="text-xs text-gray-500 uppercase tracking-widest mb-4">
                  Bias Source: Permission Gate (Stage 3)
                </p>
                <div className="space-y-3">
                  {Object.entries(result.stage_bias).map(([group, info]) => (
                    <div key={group} className="flex items-center justify-between">
                      <span className="text-xs text-gray-300 font-mono">{group}</span>
                      <div className="flex items-center gap-3">
                        <span
                          className="text-xs font-bold font-mono"
                          style={{ color: info.avg_bias_delta < -0.01 ? "#ef4444" : info.avg_bias_delta > 0.01 ? "#22c55e" : "#6b7280" }}
                        >
                          {info.avg_bias_delta > 0 ? "+" : ""}{info.avg_bias_delta.toFixed(4)}
                        </span>
                        <span className="text-xs text-gray-500">{info.interpretation}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Counterfactual examples — THE DEMO MOMENT */}
            {result.counterfactual_examples?.length > 0 && (
              <div className="mb-8">
                <div className="flex items-center gap-3 mb-5">
                  <div className="w-1.5 h-6 rounded-full bg-red-500" />
                  <p className="text-sm font-black text-white uppercase tracking-wider">
                    Counterfactual Evidence
                  </p>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-red-900/40 text-red-400 border border-red-800/50">
                    THE SMOKING GUN
                  </span>
                </div>
                <p className="text-xs text-gray-500 mb-5 leading-relaxed">
                  Same qualifications. Same merit score. Only ONE attribute changed.
                  Watch the decision flip.
                </p>
                <div className="space-y-4">
                  {result.counterfactual_examples.map((ex, i) => (
                    <CounterfactualCard key={i} example={ex} revealed={revealedCards[i] ?? false} />
                  ))}
                </div>
              </div>
            )}

            {/* Architecture note */}
            <div className="rounded-2xl p-5 mt-6" style={{ background: "#0f172a", border: "1px solid #1f2937" }}>
              <p className="text-xs text-indigo-400 font-bold mb-1 uppercase tracking-widest">Architecture Note</p>
              <p className="text-xs text-gray-400 leading-relaxed">
                This pipeline models the real decision architecture found in production AI agent systems:
                multi-stage processing with permission gates, classifier checks, and final decisions.
                FairLens audits each stage to pinpoint exactly where demographic bias enters the system.
              </p>
            </div>

            {/* Re-run */}
            <div className="text-center mt-8">
              <button
                onClick={runDemo}
                className="px-6 py-3 rounded-xl text-xs font-bold uppercase tracking-widest border border-indigo-800 text-indigo-400 hover:bg-indigo-900/30 transition-all"
              >
                ↺ Run Again
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
