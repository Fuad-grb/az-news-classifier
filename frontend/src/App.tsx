import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = 'http://az-classifier.local';

interface PredictionResult {
  category: string;
  confidence: number;
  probabilities: Record<string, number>;
  latency_ms: number;
}

interface ModelInfo {
  model_name: string;
  format: string;
  categories: string[];
  test_f1: number;
  test_accuracy: number;
}

interface Stats {
  total_predictions: number;
  categories: Record<string, number>;
}

const categoryColors: Record<string, string> = {
  siyaset: '#e74c3c',
  iqtisadiyyat: '#f39c12',
  idman: '#2ecc71',
  dunya: '#3498db',
  sosial: '#9b59b6',
};

const categoryEmoji: Record<string, string> = {
  siyaset: '🏛',
  iqtisadiyyat: '📊',
  idman: '⚽',
  dunya: '🌍',
  sosial: '👥',
};

function App() {
  const [dark, setDark] = useState(() => {
    const saved = localStorage.getItem('theme');
    return saved ? saved === 'dark' : window.matchMedia('(prefers-color-scheme: dark)').matches;
  });
  const [text, setText] = useState('');
  const [result, setResult] = useState<PredictionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [modelInfo, setModelInfo] = useState<ModelInfo | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    localStorage.setItem('theme', dark ? 'dark' : 'light');
  }, [dark]);

  useEffect(() => {
    axios.get(`${API_URL}/api/model-info`).then(r => setModelInfo(r.data)).catch(() => {});
    axios.get(`${API_URL}/api/stats`).then(r => setStats(r.data)).catch(() => {});
  }, []);

  const handlePredict = async () => {
    if (!text.trim()) return;
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const response = await axios.post(`${API_URL}/predict`, { text });
      setResult(response.data);
      const statsResponse = await axios.get(`${API_URL}/api/stats`);
      setStats(statsResponse.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Prediction failed. Is the API running?');
    }
    setLoading(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && e.ctrlKey) handlePredict();
  };

  const t = {
    bg: dark ? '#0d1117' : '#ffffff',
    surface: dark ? '#161b22' : '#f6f8fa',
    surfaceHover: dark ? '#1c2333' : '#eef1f5',
    border: dark ? '#30363d' : '#d1d9e0',
    text: dark ? '#e6edf3' : '#1f2328',
    textSecondary: dark ? '#8b949e' : '#656d76',
    accent: '#58a6ff',
    accentHover: '#79c0ff',
  };

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: t.bg,
      color: t.text,
      transition: 'background-color 0.3s, color 0.3s',
    }}>
      <div style={{ maxWidth: 960, margin: '0 auto', padding: '24px 20px' }}>

        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 32 }}>
          <div>
            <h1 style={{ margin: 0, fontSize: 24, fontWeight: 600, letterSpacing: '-0.5px' }}>
              <span style={{ opacity: 0.5, marginRight: 8 }}>🇦🇿</span>
              AZ News Classifier
            </h1>
          </div>
          <button
            onClick={() => setDark(!dark)}
            style={{
              background: t.surface,
              border: `1px solid ${t.border}`,
              borderRadius: 8,
              padding: '8px 14px',
              cursor: 'pointer',
              color: t.text,
              fontSize: 16,
              transition: 'all 0.2s',
            }}
            title={dark ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {dark ? '☀️' : '🌙'}
          </button>
        </div>

        {/* Classify Section */}
        <div style={{
          background: t.surface,
          border: `1px solid ${t.border}`,
          borderRadius: 12,
          padding: 24,
          marginBottom: 20,
        }}>
          <h2 style={{ margin: '0 0 16px', fontSize: 16, fontWeight: 600 }}>Classify Article</h2>
          <textarea
            value={text}
            onChange={e => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Enter the news text..."
            style={{
              width: '100%',
              height: 140,
              padding: 14,
              fontSize: 14,
              lineHeight: 1.6,
              borderRadius: 8,
              border: `1px solid ${t.border}`,
              backgroundColor: t.bg,
              color: t.text,
              resize: 'vertical',
              outline: 'none',
              fontFamily: 'inherit',
              boxSizing: 'border-box',
              transition: 'border-color 0.2s',
            }}
            onFocus={e => e.target.style.borderColor = t.accent}
            onBlur={e => e.target.style.borderColor = t.border}
          />
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 12 }}>
            <button
              onClick={handlePredict}
              disabled={loading || !text.trim()}
              style={{
                padding: '10px 28px',
                fontSize: 14,
                fontWeight: 600,
                background: loading || !text.trim() ? t.border : t.accent,
                color: '#fff',
                border: 'none',
                borderRadius: 8,
                cursor: loading || !text.trim() ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s',
                opacity: loading || !text.trim() ? 0.6 : 1,
              }}
            >
              {loading ? '⏳ Classifying...' : 'Classify'}
            </button>
            <span style={{ fontSize: 12, color: t.textSecondary }}>Ctrl+Enter</span>
          </div>

          {error && (
            <div style={{
              marginTop: 16,
              padding: '12px 16px',
              background: dark ? '#2d1215' : '#fef2f2',
              border: `1px solid ${dark ? '#6e2b2b' : '#fca5a5'}`,
              borderRadius: 8,
              color: dark ? '#f87171' : '#dc2626',
              fontSize: 14,
            }}>
              {error}
            </div>
          )}

          {result && (
            <div style={{ marginTop: 20 }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                marginBottom: 16,
                padding: '14px 18px',
                background: dark ? '#1a2332' : '#eff6ff',
                borderRadius: 8,
                border: `1px solid ${dark ? '#253449' : '#bfdbfe'}`,
              }}>
                <span style={{ fontSize: 28 }}>{categoryEmoji[result.category] || '📄'}</span>
                <div>
                  <div style={{
                    fontSize: 20,
                    fontWeight: 700,
                    color: categoryColors[result.category] || t.accent,
                    textTransform: 'uppercase',
                    letterSpacing: '1px',
                  }}>
                    {result.category}
                  </div>
                  <div style={{ fontSize: 13, color: t.textSecondary, marginTop: 2 }}>
                    {(result.confidence * 100).toFixed(1)}% confidence · {result.latency_ms.toFixed(0)}ms
                  </div>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {Object.entries(result.probabilities)
                  .sort(([, a], [, b]) => b - a)
                  .map(([cat, prob]) => (
                    <div key={cat} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <span style={{ width: 24, textAlign: 'center', fontSize: 14 }}>
                        {categoryEmoji[cat] || ''}
                      </span>
                      <span style={{ width: 100, fontSize: 13, color: t.textSecondary }}>{cat}</span>
                      <div style={{
                        flex: 1,
                        background: dark ? '#21262d' : '#e5e7eb',
                        borderRadius: 4,
                        height: 22,
                        overflow: 'hidden',
                      }}>
                        <div style={{
                          width: `${Math.max(prob * 100, 0.5)}%`,
                          background: categoryColors[cat] || t.accent,
                          height: '100%',
                          borderRadius: 4,
                          transition: 'width 0.5s ease-out',
                          opacity: prob > 0.1 ? 1 : 0.5,
                        }} />
                      </div>
                      <span style={{
                        width: 52,
                        textAlign: 'right',
                        fontSize: 13,
                        fontWeight: prob > 0.5 ? 600 : 400,
                        fontVariantNumeric: 'tabular-nums',
                        color: prob > 0.5 ? t.text : t.textSecondary,
                      }}>
                        {(prob * 100).toFixed(1)}%
                      </span>
                    </div>
                  ))}
              </div>
            </div>
          )}
        </div>

        {/* Bottom Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          {/* Stats */}
          <div style={{
            background: t.surface,
            border: `1px solid ${t.border}`,
            borderRadius: 12,
            padding: 20,
          }}>
            <h2 style={{ margin: '0 0 14px', fontSize: 14, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px', color: t.textSecondary }}>
              Prediction Stats
            </h2>
            {stats && (
              <>
                <div style={{ fontSize: 32, fontWeight: 700, marginBottom: 16, fontVariantNumeric: 'tabular-nums' }}>
                  {stats.total_predictions}
                  <span style={{ fontSize: 14, fontWeight: 400, color: t.textSecondary, marginLeft: 8 }}>total</span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {Object.entries(stats.categories)
                    .sort(([, a], [, b]) => b - a)
                    .map(([cat, count]) => (
                      <div key={cat} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14 }}>
                          <span style={{
                            width: 8,
                            height: 8,
                            borderRadius: '50%',
                            backgroundColor: categoryColors[cat] || t.accent,
                            display: 'inline-block',
                          }} />
                          {cat}
                        </span>
                        <span style={{ fontSize: 14, fontWeight: 500, fontVariantNumeric: 'tabular-nums' }}>{count}</span>
                      </div>
                    ))}
                </div>
              </>
            )}
            {!stats && <p style={{ color: t.textSecondary, fontSize: 14 }}>Loading...</p>}
          </div>

          {/* Model Info */}
          <div style={{
            background: t.surface,
            border: `1px solid ${t.border}`,
            borderRadius: 12,
            padding: 20,
          }}>
            <h2 style={{ margin: '0 0 14px', fontSize: 14, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px', color: t.textSecondary }}>
              Model Info
            </h2>
            {modelInfo && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {[
                  ['Model', modelInfo.model_name],
                  ['Format', modelInfo.format],
                  ['Test F1', modelInfo.test_f1.toString()],
                  ['Accuracy', modelInfo.test_accuracy.toString()],
                ].map(([label, value]) => (
                  <div key={label} style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ fontSize: 14, color: t.textSecondary }}>{label}</span>
                    <span style={{ fontSize: 14, fontWeight: 500 }}>{value}</span>
                  </div>
                ))}
                <div style={{ marginTop: 4 }}>
                  <span style={{ fontSize: 13, color: t.textSecondary }}>Categories</span>
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 6 }}>
                    {modelInfo.categories.map(cat => (
                      <span key={cat} style={{
                        padding: '3px 10px',
                        borderRadius: 12,
                        fontSize: 12,
                        fontWeight: 500,
                        background: dark ? '#21262d' : '#e5e7eb',
                        color: categoryColors[cat] || t.text,
                        border: `1px solid ${dark ? '#30363d' : '#d1d9e0'}`,
                      }}>
                        {categoryEmoji[cat]} {cat}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}
            {!modelInfo && <p style={{ color: t.textSecondary, fontSize: 14 }}>Loading...</p>}
          </div>
        </div>

        {/* Footer */}
        <div style={{ textAlign: 'center', marginTop: 32, paddingBottom: 20 }}>
          <p style={{ fontSize: 12, color: t.textSecondary }}>
            Built with XLM-RoBERTa · ONNX Runtime · FastAPI · Kubernetes
          </p>
        </div>
      </div>
    </div>
  );
}

export default App;
