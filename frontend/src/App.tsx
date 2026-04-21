import React, { useState, useEffect } from 'react';
import axios from 'axios';


const API_URL = 'http://az-classifier.local';

// TypeScript interfaces for API responses
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

// Main App Component
function App() {
  const [text, setText] = useState('');
  const [result, setResult] = useState<PredictionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [modelInfo, setModelInfo] = useState<ModelInfo | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);

  // Fetch model info and stats on component mount
  useEffect(() => {
    axios.get(`${API_URL}/api/model-info`).then(r => setModelInfo(r.data));
    axios.get(`${API_URL}/api/stats`).then(r => setStats(r.data));
  }, []);

  // Handle prediction request
  const handlePredict = async () => {
    if (!text.trim()) return;
    setLoading(true);
    try {
      const response = await axios.post(`${API_URL}/predict`, { text });
      setResult(response.data);
      const statsResponse = await axios.get(`${API_URL}/api/stats`);
      setStats(statsResponse.data);
    } catch (error) {
      console.error('Prediction failed:', error);
    }
    setLoading(false);
  };

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: 20, fontFamily: 'sans-serif' }}>
      <h1> Azerbaijan News Classifier</h1>

      {/* Inference Playground */}
      <div style={{ background: '#f5f5f5', padding: 20, borderRadius: 8, marginBottom: 20 }}>
        <h2>Classify News Article</h2>
        <textarea
          value={text}
          onChange={e => setText(e.target.value)}
          placeholder="Xəbər mətnini daxil edin..."
          style={{ width: '100%', height: 120, padding: 10, fontSize: 14, borderRadius: 4, border: '1px solid #ccc' }}
        />
        <button
          onClick={handlePredict}
          disabled={loading || !text.trim()}
          style={{ marginTop: 10, padding: '10px 24px', fontSize: 16, background: '#2196F3', color: 'white', border: 'none', borderRadius: 4, cursor: 'pointer' }}
        >
          {loading ? 'Classifying...' : 'Classify'}
        </button>

        {result && (
          <div style={{ marginTop: 20 }}>
            <h3>
              Result: <span style={{ color: '#2196F3' }}>{result.category.toUpperCase()}</span>
              <span style={{ marginLeft: 10, fontSize: 14, color: '#666' }}>
                ({(result.confidence * 100).toFixed(1)}% confidence, {result.latency_ms.toFixed(0)}ms)
              </span>
            </h3>
            <div>
              {Object.entries(result.probabilities)
                .sort(([,a], [,b]) => b - a)
                .map(([cat, prob]) => (
                  <div key={cat} style={{ display: 'flex', alignItems: 'center', marginBottom: 4 }}>
                    <span style={{ width: 100 }}>{cat}</span>
                    <div style={{ flex: 1, background: '#e0e0e0', borderRadius: 4, height: 20, marginRight: 10 }}>
                      <div style={{ width: `${prob * 100}%`, background: '#2196F3', height: '100%', borderRadius: 4 }} />
                    </div>
                    <span style={{ width: 50, textAlign: 'right' }}>{(prob * 100).toFixed(1)}%</span>
                  </div>
                ))}
            </div>
          </div>
        )}
      </div>

      {/* Stats and Model Info */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        <div style={{ background: '#f5f5f5', padding: 20, borderRadius: 8 }}>
          <h2>Prediction Stats</h2>
          {stats && (
            <>
              <p><strong>Total:</strong> {stats.total_predictions}</p>
              {Object.entries(stats.categories).map(([cat, count]) => (
                <p key={cat}>{cat}: {count}</p>
              ))}
            </>
          )}
        </div>

        <div style={{ background: '#f5f5f5', padding: 20, borderRadius: 8 }}>
          <h2>Model Info</h2>
          {modelInfo && (
            <>
              <p><strong>Model:</strong> {modelInfo.model_name}</p>
              <p><strong>Format:</strong> {modelInfo.format}</p>
              <p><strong>Test F1:</strong> {modelInfo.test_f1}</p>
              <p><strong>Accuracy:</strong> {modelInfo.test_accuracy}</p>
              <p><strong>Categories:</strong> {modelInfo.categories.join(', ')}</p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;