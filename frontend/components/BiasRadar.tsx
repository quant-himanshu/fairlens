"use client";

import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis,
  PolarRadiusAxis, ResponsiveContainer, Legend, Tooltip
} from "recharts";
import type { MetricResult } from "@/lib/types";

interface Props {
  metrics: MetricResult[];
  mitigatedMetrics?: MetricResult[];
}

// Normalise a metric value to 0–100 "fairness score"
// (how close it is to the ideal range centre)
function toFairnessScore(m: MetricResult): number {
  const [lo, hi] = m.ideal_range;
  const centre = (lo + hi) / 2;
  const halfRange = (hi - lo) / 2 + 0.15; // add tolerance
  const distance = Math.abs(m.value - centre);
  return Math.max(0, Math.round((1 - distance / halfRange) * 100));
}

function shortName(name: string): string {
  // "Disparate Impact (gender)" → "Disp. Impact"
  return name
    .replace(/\s*\(.*\)/, "")
    .replace("Demographic Parity", "Demo. Parity")
    .replace("Equalized Odds", "Equal. Odds")
    .replace("Calibration Gap", "Calibration")
    .replace("Individual Fairness", "Individual")
    .replace("Counterfactual Fairness", "Counterfact.")
    .replace("Disparate Impact", "Disp. Impact");
}

export function BiasRadar({ metrics, mitigatedMetrics }: Props) {
  // Deduplicate by short name (take the worst score if same metric appears for multiple attrs)
  const byName: Record<string, number> = {};
  for (const m of metrics) {
    const n = shortName(m.name);
    const score = toFairnessScore(m);
    byName[n] = Math.min(byName[n] ?? 100, score);
  }

  const mitigatedByName: Record<string, number> = {};
  if (mitigatedMetrics) {
    for (const m of mitigatedMetrics) {
      const n = shortName(m.name);
      const score = toFairnessScore(m);
      mitigatedByName[n] = Math.min(mitigatedByName[n] ?? 100, score);
    }
  }

  const data = Object.entries(byName).map(([name, score]) => ({
    metric: name,
    Before: score,
    After: mitigatedByName[name] ?? undefined,
  }));

  return (
    <ResponsiveContainer width="100%" height={320}>
      <RadarChart data={data}>
        <PolarGrid stroke="#e5e5e5" />
        <PolarAngleAxis
          dataKey="metric"
          tick={{ fontSize: 11, fill: "#888780" }}
        />
        <PolarRadiusAxis
          angle={30}
          domain={[0, 100]}
          tick={{ fontSize: 10, fill: "#b4b2a9" }}
          tickCount={4}
        />
        <Tooltip
          formatter={(val: number) => [`${val}%`, ""]}
          contentStyle={{ fontSize: 12 }}
        />
        <Radar
          name="Before mitigation"
          dataKey="Before"
          stroke="#E24B4A"
          fill="#E24B4A"
          fillOpacity={0.15}
          strokeWidth={2}
          dot={{ r: 3 }}
        />
        {mitigatedMetrics && (
          <Radar
            name="After mitigation"
            dataKey="After"
            stroke="#1D9E75"
            fill="#1D9E75"
            fillOpacity={0.2}
            strokeWidth={2}
            dot={{ r: 3 }}
          />
        )}
        <Legend
          iconType="square"
          iconSize={10}
          wrapperStyle={{ fontSize: 12, paddingTop: 8 }}
        />
      </RadarChart>
    </ResponsiveContainer>
  );
}
