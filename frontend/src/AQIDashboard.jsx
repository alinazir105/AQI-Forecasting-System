import { useState, useEffect } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

const API_BASE = import.meta.env.VITE_API_URL

const AQI_CONFIG = {
  1: { label: "Good",      bg: "#d1fae5", text: "#065f46", border: "#6ee7b7", dot: "#10b981" },
  2: { label: "Fair",      bg: "#fef9c3", text: "#713f12", border: "#fde047", dot: "#eab308" },
  3: { label: "Moderate",  bg: "#ffedd5", text: "#7c2d12", border: "#fdba74", dot: "#f97316" },
  4: { label: "Poor",      bg: "#fee2e2", text: "#7f1d1d", border: "#fca5a5", dot: "#ef4444" },
  5: { label: "Very Poor", bg: "#fae8ff", text: "#581c87", border: "#e879f9", dot: "#a855f7" },
};

const POLLUTANTS = [
  { key: "pm25",  label: "PM2.5",  unit: "µg/m³" },
  { key: "pm10",  label: "PM10",   unit: "µg/m³" },
  { key: "co",    label: "CO",     unit: "µg/m³" },
  { key: "no2",   label: "NO₂",    unit: "µg/m³" },
  { key: "so2",   label: "SO₂",    unit: "µg/m³" },
  { key: "o3",    label: "O₃",     unit: "µg/m³" },
];

function useFetch(url) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  useEffect(() => {
    setLoading(true);
    fetch(url)
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  }, [url]);
  return { data, loading, error };
}

function AqiBadge({ index, size = "md" }) {
  const cfg = AQI_CONFIG[index] || AQI_CONFIG[3];
  const pad = size === "lg" ? "8px 18px" : "4px 12px";
  const fs = size === "lg" ? 15 : 12;
  return (
    <span style={{
      background: cfg.bg, color: cfg.text, border: `1px solid ${cfg.border}`,
      borderRadius: 99, padding: pad, fontSize: fs, fontWeight: 600,
      letterSpacing: "0.02em", display: "inline-block"
    }}>
      {cfg.label}
    </span>
  );
}

function Spinner() {
  return (
    <div style={{ display: "flex", justifyContent: "center", padding: "3rem" }}>
      <div style={{
        width: 36, height: 36, borderRadius: "50%",
        border: "3px solid #e2e8f0", borderTopColor: "#6366f1",
        animation: "spin 0.8s linear infinite"
      }} />
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

function CurrentCard({ data }) {
  if (!data || data.error) return null;
  const cfg = AQI_CONFIG[data.aqi_index] || AQI_CONFIG[3];
  return (
    <div style={{
      background: cfg.bg, border: `1.5px solid ${cfg.border}`,
      borderRadius: 20, padding: "28px 32px",
      display: "flex", alignItems: "center", justifyContent: "space-between",
      flexWrap: "wrap", gap: 20,
    }}>
      <div>
        <p style={{ margin: 0, fontSize: 13, color: cfg.text, opacity: 0.7, fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.08em" }}>
          Current Air Quality · Karachi
        </p>
        <p style={{ margin: "6px 0 0", fontSize: 13, color: cfg.text, opacity: 0.6 }}>
          {data.datetime ? new Date(data.datetime).toLocaleString("en-PK", { dateStyle: "medium", timeStyle: "short" }) : data.date}
        </p>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
        <div style={{ textAlign: "center" }}>
          <p style={{ margin: 0, fontSize: 48, fontWeight: 700, color: cfg.text, lineHeight: 1, fontFamily: "'DM Mono', monospace" }}>
            {data.pm25?.toFixed(1)}
          </p>
          <p style={{ margin: "4px 0 0", fontSize: 12, color: cfg.text, opacity: 0.6 }}>PM2.5 µg/m³</p>
        </div>
        <AqiBadge index={data.aqi_index} size="lg" />
      </div>
    </div>
  );
}

function ForecastCard({ day, index }) {
  const cfg = AQI_CONFIG[day.aqi_index] || AQI_CONFIG[3];
  const date = new Date(day.date);
  const label = index === 0 ? "Tomorrow"
    : index === 1 ? "In 2 days"
    : date.toLocaleDateString("en-PK", { weekday: "long" });

  return (
    <div style={{
      background: "#fff", border: "1px solid #e2e8f0", borderRadius: 16,
      padding: "22px 20px", flex: 1, minWidth: 160,
      transition: "box-shadow 0.2s", cursor: "default",
    }}
      onMouseEnter={e => e.currentTarget.style.boxShadow = "0 4px 20px rgba(0,0,0,0.08)"}
      onMouseLeave={e => e.currentTarget.style.boxShadow = "none"}
    >
      <p style={{ margin: 0, fontSize: 12, color: "#64748b", fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.06em" }}>{label}</p>
      <p style={{ margin: "2px 0 14px", fontSize: 13, color: "#94a3b8" }}>
        {date.toLocaleDateString("en-PK", { month: "short", day: "numeric" })}
      </p>
      <p style={{ margin: "0 0 10px", fontSize: 36, fontWeight: 700, color: "#0f172a", lineHeight: 1, fontFamily: "'DM Mono', monospace" }}>
        {day.predicted_pm25.toFixed(1)}
      </p>
      <p style={{ margin: "0 0 14px", fontSize: 12, color: "#94a3b8" }}>PM2.5 µg/m³</p>
      <AqiBadge index={day.aqi_index} />
    </div>
  );
}

function ForecastChart({ forecast }) {
  const data = forecast.map((d, i) => ({
    name: i === 0 ? "Tomorrow" : i === 1 ? "+2 days" : "+3 days",
    pm25: parseFloat(d.predicted_pm25.toFixed(1)),
    aqi: d.aqi_index,
  }));

  const CustomDot = (props) => {
    const { cx, cy, payload } = props;
    const cfg = AQI_CONFIG[payload.aqi] || AQI_CONFIG[3];
    return <circle cx={cx} cy={cy} r={6} fill={cfg.dot} stroke="#fff" strokeWidth={2} />;
  };

  return (
    <div style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: 16, padding: "24px 20px" }}>
      <p style={{ margin: "0 0 20px", fontSize: 14, fontWeight: 600, color: "#0f172a" }}>PM2.5 Forecast Trend</p>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis dataKey="name" tick={{ fontSize: 12, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fontSize: 12, fill: "#94a3b8" }} axisLine={false} tickLine={false} width={40} />
          <Tooltip
            contentStyle={{ borderRadius: 10, border: "1px solid #e2e8f0", fontSize: 13 }}
            formatter={(v) => [`${v} µg/m³`, "PM2.5"]}
          />
          <Line type="monotone" dataKey="pm25" stroke="#6366f1" strokeWidth={2.5}
            dot={<CustomDot />} activeDot={{ r: 8 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function PollutantGrid({ data }) {
  if (!data || data.error) return null;
  return (
    <div style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: 16, padding: "24px 20px" }}>
      <p style={{ margin: "0 0 16px", fontSize: 14, fontWeight: 600, color: "#0f172a" }}>Current Pollutant Levels</p>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))", gap: 12 }}>
        {POLLUTANTS.map(({ key, label, unit }) => {
          const val = data[key];
          return (
            <div key={key} style={{ background: "#f8fafc", borderRadius: 12, padding: "14px 16px" }}>
              <p style={{ margin: 0, fontSize: 11, color: "#94a3b8", fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.06em" }}>{label}</p>
              <p style={{ margin: "6px 0 2px", fontSize: 22, fontWeight: 700, color: "#0f172a", fontFamily: "'DM Mono', monospace" }}>
                {val != null ? parseFloat(val).toFixed(1) : "—"}
              </p>
              <p style={{ margin: 0, fontSize: 11, color: "#cbd5e1" }}>{unit}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function AqiLegend() {
  return (
    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
      {Object.entries(AQI_CONFIG).map(([idx, cfg]) => (
        <span key={idx} style={{
          background: cfg.bg, color: cfg.text, border: `1px solid ${cfg.border}`,
          borderRadius: 99, padding: "3px 10px", fontSize: 11, fontWeight: 500
        }}>
          {idx} — {cfg.label}
        </span>
      ))}
    </div>
  );
}

export default function AQIDashboard() {
  const { data: current, loading: loadingCurrent } = useFetch(`${API_BASE}/current`);
  const { data: forecastData, loading: loadingForecast } = useFetch(`${API_BASE}/forecast`);

  const forecast = forecastData?.forecast || [];
  const loading = loadingCurrent || loadingForecast;

  return (
    <div style={{
      minHeight: "100vh", background: "#f8fafc",
      fontFamily: "'DM Sans', 'Segoe UI', sans-serif",
      padding: "0 0 60px",
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=DM+Mono:wght@500&display=swap');
        * { box-sizing: border-box; }
      `}</style>

      <div style={{ background: "#fff", borderBottom: "1px solid #e2e8f0", padding: "16px 0" }}>
        <div style={{ maxWidth: 900, margin: "0 auto", padding: "0 24px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{ width: 32, height: 32, borderRadius: 8, background: "#6366f1", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.5">
                <path d="M12 2a10 10 0 1 0 10 10" /><path d="M12 6v6l4 2" />
              </svg>
            </div>
            <span style={{ fontWeight: 600, fontSize: 16, color: "#0f172a" }}>Karachi AQI</span>
          </div>
          <span style={{ fontSize: 12, color: "#94a3b8" }}>Powered by OpenWeather · Ridge Regression Model</span>
        </div>
      </div>

      <div style={{ maxWidth: 900, margin: "0 auto", padding: "32px 24px" }}>
        {loading ? <Spinner /> : (
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>

            <CurrentCard data={current} />

            <div>
              <p style={{ margin: "0 0 12px", fontSize: 13, fontWeight: 600, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.06em" }}>
                3-Day Forecast
              </p>
              <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
                {forecast.map((day, i) => <ForecastCard key={day.date} day={day} index={i} />)}
              </div>
            </div>

            {forecast.length > 0 && <ForecastChart forecast={forecast} />}

            <PollutantGrid data={current} />

            <div style={{ background: "#fff", border: "1px solid #e2e8f0", borderRadius: 16, padding: "20px 24px" }}>
              <p style={{ margin: "0 0 10px", fontSize: 13, fontWeight: 600, color: "#64748b", textTransform: "uppercase", letterSpacing: "0.06em" }}>AQI Scale</p>
              <AqiLegend />
            </div>

            <p style={{ margin: 0, fontSize: 12, color: "#cbd5e1", textAlign: "center" }}>
              Forecasts are generated using a Ridge Regression model trained on 4+ years of OpenWeather hourly data for Karachi (24.8607°N, 67.0011°E).
              Predictions reflect daily average PM2.5 and carry an average error of ~27.7 µg/m³.
            </p>

          </div>
        )}
      </div>
    </div>
  );
}