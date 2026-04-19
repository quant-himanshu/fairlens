"use client";

import { VERDICT_CONFIG, type MetricResult } from "@/lib/types";

interface Props {
  metric: MetricResult;
  showDelta?: boolean;
}

export function MetricCard({ metric, showDelta = false }: Props) {
  const cfg = VERDICT_CONFIG[metric.verdict];
  const [lo, hi] = metric.ideal_range;

  // How far out of range is the value? Used for progress bar.
  const rangeSpan = hi - lo;
  const visualMin = lo - rangeSpan * 0.5;
  const visualMax = hi + rangeSpan * 0.5;
  const pct = Math.min(100, Math.max(0,
    ((metric.value - visualMin) / (visualMax - visualMin)) * 100
  ));
  const idealLo = ((lo - visualMin) / (visualMax - visualMin)) * 100;
  const idealHi = ((hi - visualMin) / (visualMax - visualMin)) * 100;

  return (
    <div
      className="rounded-xl border p-4 flex flex-col gap-3"
      style={{ borderColor: cfg.border, backgroundColor: cfg.bg }}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm font-medium leading-tight" style={{ color: cfg.color }}>
          {metric.name}
        </p>
        <span
          className="shrink-0 rounded-full px-2 py-0.5 text-xs font-medium"
          style={{ backgroundColor: cfg.border + "55", color: cfg.color }}
        >
          {cfg.label}
        </span>
      </div>

      {/* Value */}
      <div className="flex items-baseline gap-2">
        <span className="text-2xl font-semibold" style={{ color: cfg.color }}>
          {metric.value.toFixed(3)}
        </span>
        {showDelta && metric.delta !== undefined && (
          <span
            className="text-sm font-medium"
            style={{ color: metric.delta < 0 ? "#3B6D11" : "#993C1D" }}
          >
            {metric.delta > 0 ? "+" : ""}{metric.delta.toFixed(3)}
          </span>
        )}
      </div>

      {/* Range indicator */}
      <div className="relative h-2 rounded-full bg-white/60">
        {/* Ideal zone */}
        <div
          className="absolute h-full rounded-full"
          style={{
            left: `${idealLo}%`,
            width: `${idealHi - idealLo}%`,
            backgroundColor: cfg.border + "88",
          }}
        />
        {/* Current value needle */}
        <div
          className="absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full border-2 border-white"
          style={{ left: `calc(${pct}% - 6px)`, backgroundColor: cfg.color }}
        />
      </div>
      <p className="text-xs" style={{ color: cfg.color + "cc" }}>
        Ideal: {lo} – {hi}
        {metric.affected_group ? ` · Affected: ${metric.affected_group}` : ""}
      </p>

      {/* Description */}
      <p className="text-xs leading-relaxed" style={{ color: cfg.color + "aa" }}>
        {metric.description}
      </p>
    </div>
  );
}
